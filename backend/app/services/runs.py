"""Özet ve soru isteklerini yerelde JSON dosyasına kaydetme.

Swagger ekranı yenilenince sonuç kaybolmasın diye her başarılı yanıt
`backend/runs/` altına yazılır. Dosyaya istek gövdesi, yanıt ve (sorularda)
modelin ham alıntılarını içeren denetim listesi yazılır; ayarlar ve ortam
değişkenleri (API anahtarı dahil) hiç kullanılmaz.
Aşama 14'ten beri aşama süreleri ve model çağrıları (`metrics`) da yazılır;
hatalı istekler de `-error` son ekiyle kaydedilir (`error`).
Yazma hatası isteği bozmaz, yalnızca günlüğe düşer.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Literal
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from pydantic import BaseModel

from app.config import get_settings

logger = logging.getLogger(__name__)

RunKind = Literal["summary", "questions", "topics"]

# Kayıt biçimi sürümü. 1: saved_at, endpoint, request, response.
# 2: + record_version ve sorularda quote_audit (modelin ham alıntısı, kırpılan kelimeler).
# 3: + destek kontrolü açıkken support_check (istem sürümü, her soru için etiket,
#    gerekçe ve modelin ham yanıtı). Kapalıyken alan yazılmaz.
# Yeni sürümler yalnızca alan ekler; eski kayıtlar load_run ile okunabilir kalır.
# Sürüm yalnızca kaydın kendi alanları değişince artar. `response` içindeki alan
# eklemeleri (ör. özet konularındaki start_verified) API yanıtının parçasıdır ve
# kayıt biçimini değiştirmez; bu yüzden sürüm 3'te kaldı.
# 4 (Aşama 14): + outcome ("ok"/"error"), metrics (aşama süreleri, model
#    çağrıları ve token sayıları, sorularda atılan soru sayıları) ve hata
#    kayıtlarında error (status_code, kind, detail, stage). Hata kayıtlarında
#    response null'dır. Kaydın kendi alanları değiştiği için sürüm arttı.
# 5 (Aşama 9, b): + sorularda writing_check (kural sürümü ve soru başına kodla
#    bulunan yazım hatası işaretleri) ve metrics.stages içinde writing_check_ms.
# 6 (Aşama 7b): + context_mode verilmiş soru isteklerinde topic_generation
#    (istem sürümü, koşul, k, konular ve kaynağı, parçalama sürümü, gömme modeli,
#    konu başına bağlamın kelime sayısı ve RAG'de erişilen parçalar, soru
#    üretilmeyen konular); metrics.stages içinde index_ms ve retrieval_ms.
#    Konu başına sonuç (per_topic[].outcome: ok / empty / invalid / duplicate)
#    ve outcome_counts sürüm 6 henüz hiçbir gerçek kayıtta kullanılmamışken
#    eklendi; bu yüzden sürüm 6'da kaldı.
# 7 (konu çıkarma, topics-v1): + /api/topics kayıtları (endpoint /api/topics,
#    topic_extraction: istem sürümü, istenen ve dönen konu sayısı, eksiklik,
#    atılan konular, konular). Soru kayıtlarında topic_generation.topics_source
#    artık "topics-v1" ya da "request" olabilir; topics-v1 ise
#    topic_generation.topic_extraction da yazılır. backend/runs'ta sürüm 6
#    kayıtları bulunduğu için sürüm arttı.
#    + context_mode verilmiş soru kayıtlarında similarity_check (kural sürümü,
#    eşik ve geçici olup olmadığı, eşiği geçen soru çiftleri ve skorları) ve
#    metrics.stages içinde similarity_check_ms. Sürüm 7 henüz hiçbir gerçek
#    kayıtta kullanılmamışken eklendi; bu yüzden sürüm 7'de kaldı.
#    + Aşama 8 (questions-v3): topic_generation içinde bloom_mapping (konu –
#    hedef düzey), bloom_mapping_source ("request" / "seeded") ve
#    questions_reasoning (her sorunun reasoning metni); per_topic[].bloom_level.
#    Sürüm 7 henüz hiçbir gerçek kayıtta kullanılmamışken eklendi; sürüm 7'de kaldı.
# 8 (transkript önbelleği): + metrics.transcript_source ("cache" / "youtube");
#    hata kayıtlarında error.kind "youtube_blocked" olabilir. backend/runs'ta
#    sürüm 7 kayıtları bulunduğu için sürüm arttı.
# 9 (questions-v4): + topic_generation.per_topic[].skip_reason (v4'te modelin boş
#    liste gerekçesi; v3'te ve soru dönen konularda null). request içinde
#    prompt_version (context_mode verilmiş isteklerde).
# 10 (çıktı token sınırı): + topic_generation.max_tokens ve
#    topic_generation.per_topic[].truncated (yanıt sınırda kesildiyse true; konunun
#    sonucu "invalid"). backend/runs'ta sürüm 9 kayıtları bulunduğu için sürüm arttı.
RECORD_VERSION = 10


def _now() -> datetime:
    """Yerel saat dilimiyle şimdiki zaman (testlerde sabitlenebilsin diye ayrı)."""
    return datetime.now().astimezone()


def strip_share_code(url: str) -> str:
    """Bağlantıdaki YouTube paylaşım kodunu (`si=...`) siler; diğer parametreler kalır."""
    parts = urlsplit(url)
    if not parts.query:
        return url
    query = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True) if k != "si"]
    return urlunsplit(parts._replace(query=urlencode(query)))


def save_run(
    kind: RunKind,
    video_id: str | None,
    request: BaseModel,
    response: BaseModel | None,
    quote_audit: list[dict] | None = None,
    support_check: dict | None = None,
    metrics: dict | None = None,
    error: dict | None = None,
    writing_check: dict | None = None,
    topic_generation: dict | None = None,
    topic_extraction: dict | None = None,
    similarity_check: dict | None = None,
) -> Path | None:
    """Kaydı `YYYYMMDD-HHMMSS-<video_id>-<kind>.json` adıyla yazar; yazılan dosyanın yolunu döndürür.

    `quote_audit`, `support_check`, `writing_check` ve `metrics` yalnızca kayda yazılır, API
    yanıtında yer almaz; `response` alanı API yanıtıyla birebir aynı kalır
    (yanıtta açıkça verilmemiş alanlar kayda da yazılmaz). `error` verilirse
    kayıt hata kaydıdır: dosya adı `-error` ile biter, `response` null olur.
    Video kimliği bilinmiyorsa (geçersiz bağlantı) dosya adında `unknown` yazar.
    SAVE_RUNS kapalıysa ya da yazma başarısız olursa None döner.
    """
    settings = get_settings()
    if not settings.save_runs:
        return None

    try:
        now = _now()
        request_data = request.model_dump(mode="json")
        if isinstance(request_data.get("url"), str):
            request_data["url"] = strip_share_code(request_data["url"])
        record = {
            "record_version": RECORD_VERSION,
            "saved_at": now.isoformat(timespec="seconds"),
            "endpoint": f"/api/{kind}",
            "outcome": "error" if error is not None else "ok",
            "request": request_data,
            # exclude_unset: uç noktadaki response_model_exclude_unset ile aynı çıktı
            "response": response.model_dump(mode="json", exclude_unset=True) if response is not None else None,
        }
        if error is not None:
            record["error"] = error
        if metrics is not None:
            record["metrics"] = metrics
        if quote_audit is not None:
            record["quote_audit"] = quote_audit
        if support_check is not None:
            record["support_check"] = support_check
        if writing_check is not None:
            record["writing_check"] = writing_check
        if topic_generation is not None:
            record["topic_generation"] = topic_generation
        if topic_extraction is not None:
            record["topic_extraction"] = topic_extraction
        if similarity_check is not None:
            record["similarity_check"] = similarity_check
        text = json.dumps(record, ensure_ascii=False, indent=2)

        runs_dir = Path(settings.runs_dir)
        runs_dir.mkdir(parents=True, exist_ok=True)
        stem = f"{now:%Y%m%d-%H%M%S}-{video_id or 'unknown'}-{kind}" + ("-error" if error is not None else "")
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
    çalıştırılmış sürüm 3 kayıtlarında vardır; yoksa None olur. Sürüm 3 ve
    öncesinde yalnızca başarılı istekler kaydedildiği için `outcome` "ok",
    `metrics` ve `error` None olur. `writing_check` sürüm 5'ten önce yoktur
    (ve özet kayıtlarında hiç yoktur); yoksa None olur. `topic_generation`
    yalnızca sürüm 6'dan beri, context_mode verilmiş isteklerde vardır; yoksa None.
    `topic_extraction` yalnızca sürüm 7'den beri /api/topics kayıtlarında vardır; yoksa None. Böylece okuyan kod hata vermez.
    """
    record = json.loads(Path(path).read_text(encoding="utf-8"))
    record.setdefault("record_version", 1)
    record.setdefault("quote_audit", [])
    record.setdefault("support_check", None)
    record.setdefault("outcome", "ok")
    record.setdefault("metrics", None)
    record.setdefault("error", None)
    record.setdefault("writing_check", None)
    record.setdefault("topic_generation", None)
    record.setdefault("topic_extraction", None)
    record.setdefault("similarity_check", None)
    return record
