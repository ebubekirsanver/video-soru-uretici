from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException

from app.config import get_settings
from app.schemas import (
    QuestionOut,
    QuestionsRequest,
    QuestionsResponse,
    SummaryRequest,
    SummaryResponse,
    SummaryTopic,
    SupportOut,
    TranscriptRequest,
    TranscriptResponse,
    TranscriptSegment,
)
from app.services.chunking import CHUNKING_VERSION
from app.services.embeddings import EmbeddingUnavailable
from app.services.llm import LLMClient, LLMError, LLMNotConfigured, get_llm
from app.services.metrics import RunMetrics, error_record
from app.services.questions import PROMPT_VERSION, generate_questions
from app.services.retrieval import get_index_provider
from app.services.runs import save_run
from app.services.summary import summarize
from app.services.support_check import SUPPORT_PROMPT_VERSION, check_support
from app.services.text_clean import clean_transcript, prepare_transcript
from app.services.topic_questions import PROMPT_VERSION_V2, generate_topic_questions
from app.services.transcript import Transcript, TranscriptUnavailable, fetch_transcript
from app.services.writing_check import check_questions as check_writing
from app.services.youtube import InvalidYouTubeUrl, extract_video_id

router = APIRouter(prefix="/api", tags=["transkript"])


def _video_id_or_none(url: str) -> str | None:
    try:
        return extract_video_id(url)
    except InvalidYouTubeUrl:
        return None


def _save_error_run(kind, purpose, body, exc: HTTPException, metrics: RunMetrics) -> None:
    """Hatalı isteği `-error` kaydı olarak yazar (SAVE_RUNS kapalıysa yazmaz).

    Hata metni kayda girmeden önce API anahtarı ve anahtar benzeri dizgilerden temizlenir.
    """
    error = error_record(
        exc.status_code,
        exc.detail,
        metrics,
        purpose,
        known_secrets=(get_settings().openai_api_key,),
        kind=getattr(exc, "run_kind", None),
    )
    save_run(kind, _video_id_or_none(body.url), body, None, metrics=metrics.as_dict(), error=error)


def _resolve_topics(body: QuestionsRequest, context: Transcript, llm: LLMClient, m: RunMetrics) -> tuple[list[str], str]:
    """Konu tabanlı üretimin konuları ve kaynağı.

    `topics` gönderildiyse hepsi kullanılır (count yok sayılır); deneyde iki
    koşula aynı konular böyle verilir. Gönderilmediyse konular özet
    servisinden alınır ve ilk `count` konu kullanılır.
    """
    if body.topics:
        return list(body.topics), "request"
    with m.model_step("llm_summary", "summary_parse", "summary"):
        summary = summarize(context, m.track(llm, "summary"))
    return [t.title for t in summary.topics][: body.count], "summary"


def _load_transcript(url: str) -> Transcript:
    """Bağlantıdan video kimliğini çıkarır ve transkripti getirir; hataları HTTP hatasına çevirir."""
    try:
        video_id = extract_video_id(url)
    except InvalidYouTubeUrl as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    try:
        return fetch_transcript(video_id, get_settings().transcript_language_list)
    except TranscriptUnavailable as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/transcript", response_model=TranscriptResponse)
def get_transcript(body: TranscriptRequest) -> TranscriptResponse:
    """YouTube bağlantısından zaman damgalı transkript döndürür."""
    transcript = _load_transcript(body.url)

    return TranscriptResponse(
        video_id=transcript.video_id,
        language=transcript.language,
        is_generated=transcript.is_generated,
        segment_count=len(transcript.segments),
        duration_seconds=transcript.duration_seconds,
        segments=[TranscriptSegment(text=s.text, start=s.start, duration=s.duration) for s in transcript.segments],
    )


@router.post("/summary", response_model=SummaryResponse, tags=["özet"])
def get_summary(body: SummaryRequest, llm: LLMClient = Depends(get_llm)) -> SummaryResponse:
    """YouTube bağlantısından Türkçe özet ve zaman damgalı konu başlıkları döndürür."""
    # Aşama süreleri ve model çağrıları yalnızca çalıştırma kaydına yazılır
    m = RunMetrics()
    try:
        with m.stage("transcript_fetch"):
            raw = _load_transcript(body.url)
        with m.stage("clean"):
            transcript = prepare_transcript(raw, body.transcript_mode)
            if not transcript.segments:
                raise HTTPException(status_code=404, detail="Temizlikten sonra özetlenecek transkript kalmadı.")

        try:
            with m.model_step("llm_summary", "summary_parse", "summary"):
                result = summarize(transcript, m.track(llm, "summary"))
        except LLMNotConfigured as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except LLMError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
    except HTTPException as exc:
        _save_error_run("summary", "summary", body, exc, m)
        raise

    response = SummaryResponse(
        video_id=transcript.video_id,
        language=transcript.language,
        transcript_mode=body.transcript_mode,
        model=llm.model,
        summary=result.summary,
        topics=[
            SummaryTopic(title=t.title, start_seconds=t.start_seconds, start_verified=t.start_verified)
            for t in result.topics
        ],
    )
    save_run("summary", response.video_id, body, response, metrics=m.as_dict())
    return response


# response_model_exclude_unset: destek kontrolü kapalıyken "support" alanları yanıtta hiç görünmez,
# yanıt şeması eskisiyle aynı kalır. Diğer alanlar her zaman açıkça verildiği için (null olsalar da) görünür.
@router.post("/questions", response_model=QuestionsResponse, response_model_exclude_unset=True, tags=["soru"])
def get_questions(
    body: QuestionsRequest,
    llm: LLMClient = Depends(get_llm),
    index_provider=Depends(get_index_provider),
) -> QuestionsResponse:
    """Doğrulanmış çoktan seçmeli sorular üretir.

    `context_mode` verilmezse transkriptin tamamından (RAG'siz) questions-v1 ile
    üretir (eski taban çizgisi). Verilirse konu başına bir soru questions-v2 ile
    üretilir (AS1): `full` transkriptin tamamını, `rag` konu için erişilen
    parçaları bağlam olarak verir.

    `check_support=true` ise her doğrulanmış soru için alıntının doğru cevabı destekleyip
    desteklemediği ayrıca modele sorulur (model değerlendirmesi, kesin değildir).
    """
    # Aşama süreleri, model çağrıları ve atılan soru sayıları yalnızca çalıştırma kaydına yazılır
    m = RunMetrics()
    try:
        with m.stage("transcript_fetch"):
            raw = _load_transcript(body.url)
        with m.stage("clean"):
            context = prepare_transcript(raw, body.transcript_mode)
            if not context.segments:
                raise HTTPException(status_code=404, detail="Temizlikten sonra soru üretilecek transkript kalmadı.")
            # Alıntılar, mod ne olursa olsun temizlenmiş transkriptte aranır
            reference = clean_transcript(raw)

        topics = topic_generation = None
        try:
            if body.context_mode is None:
                dropped: dict = {}
                # quote_verify_ms: yanıt ayrıştırma, yapı denetimi, tekrar ayıklama,
                # alıntı doğrulama ve seçenek karıştırma (model çağrısı dışındaki süre)
                with m.model_step("llm_questions", "quote_verify", "questions"):
                    questions = generate_questions(context, reference, m.track(llm, "questions"), body.count, dropped=dropped)
                m.dropped = dropped
            else:
                topics, topics_source = _resolve_topics(body, context, llm, m)
                rag = body.context_mode == "rag"
                # Dizin yalnızca RAG isteğinde açılır
                index = index_provider() if rag else None
                # Dizinleme (index_ms) ve erişim (retrieval_ms) ayrı ölçülür, quote_verify_ms'ten düşülür
                with m.model_step("llm_questions", "quote_verify", "questions", exclude=("index", "retrieval")):
                    generation = generate_topic_questions(
                        topics, body.context_mode, context, reference, m.track(llm, "questions"),
                        index=index, k=body.k, timer=m.accumulate,
                    )
                questions = generation.questions
                m.dropped = generation.dropped
                topic_generation = {
                    "prompt_version": PROMPT_VERSION_V2,
                    "context_mode": body.context_mode,
                    "k": body.k if rag else None,
                    "topics": topics,
                    "topics_source": topics_source,
                    "chunking": CHUNKING_VERSION if rag else None,
                    "embedding_model": index.embedder.model if rag else None,
                    "per_topic": [asdict(t) for t in generation.traces],
                    "no_question_topics": generation.no_question_topics,
                }
        except EmbeddingUnavailable as exc:
            error = HTTPException(status_code=503, detail=str(exc))
            error.run_kind = "embedding_unavailable"
            raise error from exc
        except LLMNotConfigured as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except LLMError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
    except HTTPException as exc:
        _save_error_run("questions", "questions", body, exc, m)
        raise

    # Yazım kuralları (yalnızca kodla, model çağrısı yok) karıştırılmış son sorular üzerinde
    # çalışır; sonuç yalnızca kayda yazılır, soru atılmaz
    with m.stage("writing_check"):
        writing_check = check_writing(questions)

    # Destek kontrolü varsayılan olarak kapalı: her doğrulanmış soru için ek bir ücretli çağrı yapar
    supports = None
    if body.check_support:
        with m.stage("support_check"):
            supports = check_support(questions, m.track(llm, "support"))

    question_outs = []
    for i, q in enumerate(questions):
        out = QuestionOut(
            question=q.question,
            options=q.options,
            correct_index=q.correct_index,
            explanation=q.explanation,
            source_quote=q.source_quote,
            source_start_seconds=q.source_start_seconds,
            verified=q.verified,
            quote_match=q.quote_match,
            **({"topic": q.topic} if body.context_mode else {}),
            **({"support": SupportOut(label=supports[i].label, reason=supports[i].reason)} if supports else {}),
        )
        question_outs.append(out)

    response = QuestionsResponse(
        video_id=raw.video_id,
        transcript_mode=body.transcript_mode,
        model=llm.model,
        prompt_version=PROMPT_VERSION_V2 if body.context_mode else PROMPT_VERSION,
        # Konu tabanlı üretimde istenen soru sayısı kullanılan konu sayısıdır
        requested_count=len(topics) if body.context_mode else body.count,
        returned_count=len(questions),
        verified_count=sum(q.verified for q in questions),
        questions=question_outs,
        **({"context_mode": body.context_mode} if body.context_mode else {}),
        **({"support_prompt_version": SUPPORT_PROMPT_VERSION} if supports is not None else {}),
    )
    # Modelin ham alıntısı yalnızca yerel kayda yazılır, yanıtta yer almaz
    quote_audit = [
        {
            "index": i,
            "question": q.question,
            "model_quote": q.model_quote,
            "source_quote": q.source_quote,
            "quote_match": q.quote_match,
            "trimmed_head": q.trimmed_head,
            "trimmed_tail": q.trimmed_tail,
        }
        for i, q in enumerate(questions, 1)
    ]
    # Destek kontrolünün modelden gelen ham yanıtı da yalnızca yerel kayda yazılır
    support_check = None
    if supports is not None:
        support_check = {
            "prompt_version": SUPPORT_PROMPT_VERSION,
            "results": [
                {"index": i, "question": q.question, "label": s.label, "reason": s.reason, "model_raw": s.model_raw}
                for i, (q, s) in enumerate(zip(questions, supports), 1)
            ],
        }
    save_run(
        "questions",
        response.video_id,
        body,
        response,
        quote_audit=quote_audit,
        support_check=support_check,
        metrics=m.as_dict(),
        writing_check=writing_check,
        topic_generation=topic_generation,
    )
    return response
