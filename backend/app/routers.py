from fastapi import APIRouter, HTTPException

from app.config import get_settings
from app.schemas import TranscriptRequest, TranscriptResponse, TranscriptSegment
from app.services.transcript import TranscriptUnavailable, fetch_transcript
from app.services.youtube import InvalidYouTubeUrl, extract_video_id

router = APIRouter(prefix="/api", tags=["transkript"])


@router.post("/transcript", response_model=TranscriptResponse)
def get_transcript(body: TranscriptRequest) -> TranscriptResponse:
    """YouTube bağlantısından zaman damgalı transkript döndürür."""
    try:
        video_id = extract_video_id(body.url)
    except InvalidYouTubeUrl as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    try:
        transcript = fetch_transcript(video_id, get_settings().transcript_language_list)
    except TranscriptUnavailable as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return TranscriptResponse(
        video_id=transcript.video_id,
        language=transcript.language,
        is_generated=transcript.is_generated,
        segment_count=len(transcript.segments),
        duration_seconds=transcript.duration_seconds,
        segments=[TranscriptSegment(text=s.text, start=s.start, duration=s.duration) for s in transcript.segments],
    )
