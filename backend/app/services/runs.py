"""Başarılı özet ve soru yanıtlarını yerelde JSON dosyasına kaydetme.

Swagger ekranı yenilenince sonuç kaybolmasın diye her başarılı yanıt
`backend/runs/` altına yazılır. Dosyaya yalnızca istek gövdesi ve yanıt
yazılır; ayarlar ve ortam değişkenleri (API anahtarı dahil) hiç kullanılmaz.
Yazma hatası isteği bozmaz, yalnızca günlüğe düşer.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

from app.config import get_settings

logger = logging.getLogger(__name__)

RunKind = Literal["summary", "questions"]


def _now() -> datetime:
    """Yerel saat dilimiyle şimdiki zaman (testlerde sabitlenebilsin diye ayrı)."""
    return datetime.now().astimezone()


def save_run(kind: RunKind, video_id: str, request: BaseModel, response: BaseModel) -> Path | None:
    """Kaydı `YYYYMMDD-HHMMSS-<video_id>-<kind>.json` adıyla yazar; yazılan dosyanın yolunu döndürür.

    SAVE_RUNS kapalıysa ya da yazma başarısız olursa None döner.
    """
    settings = get_settings()
    if not settings.save_runs:
        return None

    try:
        now = _now()
        record = {
            "saved_at": now.isoformat(timespec="seconds"),
            "endpoint": f"/api/{kind}",
            "request": request.model_dump(mode="json"),
            "response": response.model_dump(mode="json"),
        }
        text = json.dumps(record, ensure_ascii=False, indent=2)

        runs_dir = Path(settings.runs_dir)
        runs_dir.mkdir(parents=True, exist_ok=True)
        stem = f"{now:%Y%m%d-%H%M%S}-{video_id}-{kind}"
        path = runs_dir / f"{stem}.json"
        suffix = 2
        while True:
            try:
                # "x" kipi: dosya varsa üzerine yazmaz, aynı saniyedeki ikinci kayıt -2 alır
                with path.open("x", encoding="utf-8") as f:
                    f.write(text)
                return path
            except FileExistsError:
                path = runs_dir / f"{stem}-{suffix}.json"
                suffix += 1
    except (OSError, TypeError, ValueError):
        logger.exception("Çalıştırma kaydı yazılamadı (%s, %s); yanıt yine döndürülüyor.", kind, video_id)
        return None
