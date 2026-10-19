"""Başarılı özet ve soru yanıtlarını yerelde JSON dosyasına kaydetme.

Swagger ekranı yenilenince sonuç kaybolmasın diye her başarılı yanıt
`backend/runs/` altına yazılır. Dosyaya istek gövdesi, yanıt ve (sorularda)
modelin ham alıntılarını içeren denetim listesi yazılır; ayarlar ve ortam
değişkenleri (API anahtarı dahil) hiç kullanılmaz.
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

# Kayıt biçimi sürümü. 1: saved_at, endpoint, request, response.
# 2: + record_version ve sorularda quote_audit (modelin ham alıntısı, kırpılan kelimeler).
# 3: + destek kontrolü açıkken support_check (istem sürümü, her soru için etiket,
#    gerekçe ve modelin ham yanıtı). Kapalıyken alan yazılmaz.
# Yeni sürümler yalnızca alan ekler; eski kayıtlar load_run ile okunabilir kalır.
# Sürüm yalnızca kaydın kendi alanları değişince artar. `response` içindeki alan
# eklemeleri (ör. özet konularındaki start_verified) API yanıtının parçasıdır ve
# kayıt biçimini değiştirmez; bu yüzden sürüm 3'te kaldı.
RECORD_VERSION = 3


def _now() -> datetime:
    """Yerel saat dilimiyle şimdiki zaman (testlerde sabitlenebilsin diye ayrı)."""
    return datetime.now().astimezone()


def save_run(
    kind: RunKind,
    video_id: str,
    request: BaseModel,
    response: BaseModel,
    quote_audit: list[dict] | None = None,
    support_check: dict | None = None,
) -> Path | None:
    """Kaydı `YYYYMMDD-HHMMSS-<video_id>-<kind>.json` adıyla yazar; yazılan dosyanın yolunu döndürür.

    `quote_audit` ve `support_check` yalnızca kayda yazılır, API yanıtında yer
    almaz; `response` alanı API yanıtıyla birebir aynı kalır (yanıtta açıkça
    verilmemiş alanlar kayda da yazılmaz). SAVE_RUNS kapalıysa ya da yazma
    başarısız olursa None döner.
    """
    settings = get_settings()
    if not settings.save_runs:
        return None

    try:
        now = _now()
        record = {
            "record_version": RECORD_VERSION,
            "saved_at": now.isoformat(timespec="seconds"),
            "endpoint": f"/api/{kind}",
            "request": request.model_dump(mode="json"),
            # exclude_unset: uç noktadaki response_model_exclude_unset ile aynı çıktı
            "response": response.model_dump(mode="json", exclude_unset=True),
        }
        if quote_audit is not None:
            record["quote_audit"] = quote_audit
        if support_check is not None:
            record["support_check"] = support_check
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


def load_run(path: Path) -> dict:
    """Kayıt dosyasını okur; eski sürüm kayıtlarda eksik alanlara varsayılan değer verir.

    Sürüm 1 kayıtlarında `record_version` ve `quote_audit` yoktur: sürüm 1 ve
    boş liste olarak doldurulur. `support_check` yalnızca destek kontrolü açık
    çalıştırılmış sürüm 3 kayıtlarında vardır; yoksa None olur. Böylece okuyan
    kod hata vermez.
    """
    record = json.loads(Path(path).read_text(encoding="utf-8"))
    record.setdefault("record_version", 1)
    record.setdefault("quote_audit", [])
    record.setdefault("support_check", None)
    return record
