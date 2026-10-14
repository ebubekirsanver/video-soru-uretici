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
from app.services.llm import LLMClient, LLMError, LLMNotConfigured, get_llm
from app.services.questions import PROMPT_VERSION, generate_questions
from app.services.runs import save_run
from app.services.summary import summarize
from app.services.support_check import SUPPORT_PROMPT_VERSION, check_support
from app.services.text_clean import clean_transcript, prepare_transcript
from app.services.transcript import Transcript, TranscriptUnavailable, fetch_transcript
from app.services.youtube import InvalidYouTubeUrl, extract_video_id

router = APIRouter(prefix="/api", tags=["transkript"])


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
    transcript = prepare_transcript(_load_transcript(body.url), body.transcript_mode)
    if not transcript.segments:
        raise HTTPException(status_code=404, detail="Temizlikten sonra özetlenecek transkript kalmadı.")

    try:
        result = summarize(transcript, llm)
    except LLMNotConfigured as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except LLMError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    response = SummaryResponse(
        video_id=transcript.video_id,
        language=transcript.language,
        transcript_mode=body.transcript_mode,
        model=llm.model,
        summary=result.summary,
        topics=[SummaryTopic(title=t.title, start_seconds=t.start_seconds) for t in result.topics],
    )
    save_run("summary", response.video_id, body, response)
    return response


# response_model_exclude_unset: destek kontrolü kapalıyken "support" alanları yanıtta hiç görünmez,
# yanıt şeması eskisiyle aynı kalır. Diğer alanlar her zaman açıkça verildiği için (null olsalar da) görünür.
@router.post("/questions", response_model=QuestionsResponse, response_model_exclude_unset=True, tags=["soru"])
def get_questions(body: QuestionsRequest, llm: LLMClient = Depends(get_llm)) -> QuestionsResponse:
    """Transkriptin tamamından (RAG'siz) doğrulanmış çoktan seçmeli sorular üretir.

    `check_support=true` ise her doğrulanmış soru için alıntının doğru cevabı destekleyip
    desteklemediği ayrıca modele sorulur (model değerlendirmesi, kesin değildir).
    """
    raw = _load_transcript(body.url)
    context = prepare_transcript(raw, body.transcript_mode)
    if not context.segments:
        raise HTTPException(status_code=404, detail="Temizlikten sonra soru üretilecek transkript kalmadı.")

    try:
        # Alıntılar, mod ne olursa olsun temizlenmiş transkriptte aranır
        questions = generate_questions(context, clean_transcript(raw), llm, body.count)
    except LLMNotConfigured as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except LLMError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    # Destek kontrolü varsayılan olarak kapalı: her doğrulanmış soru için ek bir ücretli çağrı yapar
    supports = check_support(questions, llm) if body.check_support else None

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
            **({"support": SupportOut(label=supports[i].label, reason=supports[i].reason)} if supports else {}),
        )
        question_outs.append(out)

    response = QuestionsResponse(
        video_id=raw.video_id,
        transcript_mode=body.transcript_mode,
        model=llm.model,
        prompt_version=PROMPT_VERSION,
        requested_count=body.count,
        returned_count=len(questions),
        verified_count=sum(q.verified for q in questions),
        questions=question_outs,
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
    save_run("questions", response.video_id, body, response, quote_audit=quote_audit, support_check=support_check)
    return response
