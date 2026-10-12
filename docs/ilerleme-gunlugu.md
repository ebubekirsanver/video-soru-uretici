# İlerleme günlüğü

Her aşamada yapılanlar, kararlar ve doğrulama sonucu burada tutulur.

## Aşama 0 · Proje iskeleti (2026-10-12)

- Repo yapısı kuruldu: `backend/`, `docs/`.
- Literatür değerlendirmesi ve teknik mimari `docs/` altına eklendi.
- Kararlar: video dili Türkçe ağırlıklı, LLM OpenAI GPT-4o-mini, önce dikey dilim (URL → transkript → özet → soru), sonra RAG, Bloom ve doğrulama katmanları.

## Aşama 1 · FastAPI backend iskeleti (2026-10-12)

- `backend/app` altında FastAPI uygulaması, `config.py` ile ortam değişkeni ayarları.
- `GET /health` ve pytest altyapısı eklendi.
- Doğrulama: `cd backend && pytest` → 1 test geçti. Swagger: `/docs`.
