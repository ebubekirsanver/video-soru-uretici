# Mimari ile kodun karşılaştırması

**Tarih:** 19 Ekim 2026 · **Kod durumu:** commit `b6431b7`

> **Kodlanmış hâl = RAG'siz taban çizgisi. Mimari görseli ([02-teknik-mimari.png](02-teknik-mimari.png)) hedef sistemdir.** Bu tablo, hedefteki her bileşenin bugünkü kodda karşılığı olup olmadığını gösterir; bir değerlendirme ya da başarı iddiası değildir.

**Yöntem:** Mimari görseli, [literatür değerlendirmesi](01-literatur-degerlendirmesi.docx) ve [yol haritası](yol-haritasi.md) okundu. Deponun bütün kaynak dosyaları (`backend/app`, `frontend/app`, `frontend/lib`) ve bağımlılık dosyaları (`backend/requirements.txt`, `frontend/package.json`) listelendi; her bileşen için anahtar sözcükler kodda arandı ve belirsiz eşleşmeler satır satır açılıp bakıldı. Testler (`backend/tests`) tabloya dahil edilmedi.

**Durum ölçütü:** *var* = bileşenin işlevi kodda bulunuyor · *kısmen* = görseldeki tanımın yalnızca bir parçası kodda · *yok* = kodda hiçbir karşılığı yok.

**Sayılar:** 25 bileşen · 4 var · 8 kısmen · 13 yok. (25'e görseldeki "yeniden dene" oku ayrı bir satır olarak dahildir; bu ok, "Geçemeyen → yeniden üret" maddesiyle aynı işi anlatır.)

## Sunum ve kullanıcı katmanı

| Katman/bileşen | Karşılık gelen kod dosyası | Durum | Kısa not |
|---|---|---|---|
| React / Next.js web arayüzü | `frontend/app/*.tsx`, `frontend/package.json` | var | Next 16.3.8, React 19.2.8 |
| YouTube bağlantı girişi | `frontend/app/summary-form.tsx`, `frontend/lib/youtube.ts` | var | Tarayıcı denetimi backend'deki `extract_video_id` ile aynı kurallarla |
| Video oynatıcı senkronizasyonu | — | yok | Gömülü oynatıcı yok (`iframe`/`embed`/`player` eşleşmesi yok); yalnızca yeni sekmede `youtu.be/…?t=` bağlantısı açılıyor |
| Bloom düzeyi seçimi | — | yok | Arayüzde ve API'de "bloom" eşleşmesi yok |
| Her soru için video anına bağlantı | `frontend/app/question-card.tsx`, `frontend/lib/format.ts` | var | Kaynak süresi `youtubeTimeUrl` ile bağlantı veriyor; özet konu başlıklarında da var (`summary-result.tsx`) |
| Öğretmen onay ekranı | — | yok | Onay, düzenleme ya da silme ekranı yok |

## Uygulama ve orkestrasyon katmanı

| Katman/bileşen | Karşılık gelen kod dosyası | Durum | Kısa not |
|---|---|---|---|
| FastAPI REST API (istek yönetimi) | `backend/app/main.py`, `routers.py`, `schemas.py` | var | `/health`, `/api/transcript`, `/api/summary`, `/api/questions`; CORS yalnızca `localhost:3000` |
| Görev kuyruğu (Celery + Redis) | — | yok | `celery`/`redis` eşleşmesi yok, bağımlılık dosyasında da yok; uç noktalar eşzamanlı (`async def` yok) |
| Ön işleme servisi (Transcript API + Whisper yedeği) | `services/transcript.py`, `services/youtube.py`, `services/text_clean.py` | kısmen | `youtube-transcript-api` ve ham/temiz seçimi var; Whisper yalnızca bir yorumda geçiyor ("ileride… Aşama 3") |
| Semantic chunking (zaman damgalı bölümleme) | `services/chunking.py` | kısmen | Yalnızca sabit ~30 sn'lik zaman damgalı bloklama (`group_into_blocks`) var; anlamsal bölütleme yok |
| İzleme ve günlükleme (gecikme, hata, token, sürüm) | `services/runs.py`, `logger.warning` çağrıları (`questions.py`, `support_check.py`) | kısmen | Başarılı yanıtlar ve istem sürümü JSON olarak kaydediliyor, bazı uyarılar günlüğe düşüyor; aşama bazlı gecikme ve LLM token ölçümü yok (`quotes.py`'deki "token" sözcük anlamında) |
| Yeniden sıralama (cross-encoder, isteğe bağlı) | — | yok | `rerank`/`cross-encoder` eşleşmesi yok |
| RAG iş akışı orkestrasyonu (Bloom düzeyi · bağlam seçimi · deneme sayacı · kaynak gösterme) | `services/questions.py`, `services/prompts.py`, `services/quotes.py` | kısmen | Yalnızca kaynak gösterme var (`source_quote`, `source_start_seconds`). Bağlam seçimi yok: transkriptin tamamı veriliyor (RAG'siz taban çizgisi). Bloom ve deneme sayacı yok |

## Veri ve indeksleme katmanı

| Katman/bileşen | Karşılık gelen kod dosyası | Durum | Kısa not |
|---|---|---|---|
| ChromaDB vektör veri tabanı · HNSW indeksi | — | yok | Eşleşme yok, bağımlılık dosyasında da yok |
| Gömme modeli (BGE-M3 / OpenAI Embeddings) | — | yok | `bge`/`embedding` eşleşmesi yok |
| Zaman damgası + parça üst verisi (video_id, parça no) | `services/transcript.py`, `services/chunking.py` | kısmen | Segment ve bloklarda başlangıç/bitiş zamanı var; bloklarda `video_id` ve parça numarası alanı yok (video_id yalnızca transkript ve yanıt düzeyinde) |
| Önbellek (Redis): transkript ve gömme tekrar kullanımı | — | yok | Transkript her istekte YouTube'dan yeniden çekiliyor; koddaki `lru_cache` yalnızca ayarlar ve istem dosyaları için |
| SQLite / PostgreSQL: kullanıcı kayıtları, iş durumu | — | yok | Veri tabanı yok; yalnızca `backend/runs/` altına yerel JSON kayıtları (git dışında) |

## Yapay zekâ ve bilişsel doğrulama katmanı

| Katman/bileşen | Karşılık gelen kod dosyası | Durum | Kısa not |
|---|---|---|---|
| LLM çıkarım servisi (Llama-3 / GPT-4o-mini) | `services/llm.py` | kısmen | GPT-4o-mini var (`LLMClient` arayüzü, `OpenAIClient`); Llama-3 uygulaması yok |
| Bloom yönlendirmeli CoT istem motoru + örnek sorular | `app/prompts/questions_v1_*.txt` | yok | Soru istemi var, ama Bloom düzeyi, düşünce zinciri ve örnek soru içermiyor |
| Denetim 1 · RAGAs sadakat (transkriptle destekli mi) | `services/quotes.py`, `services/support_check.py` | kısmen | RAGAs yok. Yakın iki kontrol var: alıntının transkriptte birebir aranması ve alıntının doğru cevabı destekleyip desteklemediğini soran model kontrolü (`support-v1`, varsayılan kapalı) |
| Denetim 2 · Bloom düzeyi uyumu | — | yok | — |
| Denetim 3 · soru yazım hataları ve tekrar eden sorular | `services/questions.py` | kısmen | Yalnızca normalleştirilmiş metni birebir aynı olan soruların atılması (`drop_duplicates`) ve yapı denetimi (4 farklı seçenek, geçerli `correct_index`) var. 19 maddelik yazım hatası denetimi ve benzerlik eşiğiyle tekrar ayıklama yok |
| Geçemeyen → yeniden üret (en çok N) → öğretmen incelemesi | — | yok | Doğrulanamayan soru yeniden üretilmiyor, yalnızca işaretleniyor; öğretmen incelemesi yok |
| Görseldeki "yeniden dene" oku | — | yok | Yukarıdaki maddeyle aynı |

## Mimaride olup kodda hiç bulunmayan bileşenler

1. Video oynatıcı senkronizasyonu (gömülü oynatıcı)
2. Bloom düzeyi seçimi (arayüz)
3. Öğretmen onay ekranı
4. Görev kuyruğu (Celery + Redis)
5. Whisper yedeği (yalnızca bir kod yorumunda anılıyor)
6. Semantic chunking (yalnızca sabit boyutlu bloklama var)
7. Yeniden sıralama (cross-encoder)
8. RAG'de bağlam seçimi ve deneme sayacı
9. ChromaDB vektör veri tabanı ve HNSW indeksi
10. Gömme modeli (BGE-M3 / OpenAI Embeddings)
11. Redis önbelleği
12. SQLite / PostgreSQL veri tabanı
13. Llama-3 çıkarım servisi
14. Bloom yönlendirmeli CoT istem motoru ve örnek sorular
15. RAGAs sadakat denetimi (yakın iki kontrol var ama RAGAs değil)
16. Bloom düzeyi uyum denetimi
17. 19 maddelik soru yazım hatası denetimi ve benzerlik eşiğiyle tekrar ayıklama
18. Yeniden üretim döngüsü (en çok N) ve öğretmen incelemesi

(Bu liste tablodaki "yok" satırları ile "kısmen" satırlarının eksik kalan parçalarından oluşur; bu yüzden sayısı tablodaki "yok" sayısıyla aynı değildir.)

## Tabloda olmayan iki not

- **Gecikme ve token ölçümü yok.** Literatür değerlendirmesinin "çıkarımlarım" bölümü yanıt süresinin izleneceğini, mimari görseli aşama bazlı gecikme ve token ölçümünü söylüyor; kodda bunların karşılığı yok.
- **RAG'li taraf henüz kurulamaz.** Literatür bölümü RAG'li ve RAG'siz kurulumların aynı video setinde karşılaştırılacağını söylüyor; kodda yalnızca RAG'siz kurulum olduğu için karşılaştırmanın RAG'li tarafı henüz kurulamaz.
