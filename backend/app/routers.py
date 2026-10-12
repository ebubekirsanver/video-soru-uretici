from fastapi import APIRouter, Depends, HTTPException

from app.config import get_settings
from app.schemas import (
    SummaryRequest,
    SummaryResponse,
    SummaryTopic,
    TranscriptRequest,
    TranscriptResponse,
    TranscriptSegment,
)
from app.services.llm import LLMClient, LLMError, LLMNotConfigured, get_llm
from app.services.summary import summarize
from app.services.text_clean import prepare_transcript
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

    return SummaryResponse(
        video_id=transcript.video_id,
        language=transcript.language,
        transcript_mode=body.transcript_mode,
        model=llm.model,
        summary=result.summary,
        topics=[SummaryTopic(title=t.title, start_seconds=t.start_seconds) for t in result.topics],
    )
