# Yol haritası

Her aşama çalışan, gösterilebilir bir çıktı verir ve ayrı commit(ler)le kaydedilir. Aşamaların gerekçesi literatür değerlendirmesindeki çıkarımlara dayanır.

| # | Aşama | Çıktı (hocaya gösterilecek) | Literatür dayanağı |
|---|---|---|---|
| 0 | Proje iskeleti, dokümanlar | Repo, README, mimari | – |
| 1 | FastAPI backend iskeleti | `/health`, Swagger arayüzü | – |
| 2 | URL ayrıştırma + zaman damgalı transkript | `POST /api/transcript` | Jacobs & Jaschke 2024 |
| 3 | Transkript kalite ölçümü, Whisper yedeği | Altyazı yoksa Whisper; WER ölçümü | Türkçe WER bulguları |
| 4 | Bölümleme (sabit boyut + zaman damgalı) | Parçalar ve üst veri | Qu vd. 2025 |
| 5 | LLM soyut katmanı + özet | `POST /api/summary` | Arif vd. 2024 |
| 6 | Temel soru üretimi (RAG'siz, tüm bağlam) | İlk sorular, taban çizgisi | Arif vd. 2024 |
| 7 | Gömme + ChromaDB + erişim | İlgili bölüm seçimi | Chen vd. 2024, Liu N.F. 2024 |
| 8 | Bloom yönlendirmeli istem protokolü | Düzeye göre sorular | Maity 2025, Doughty 2024 |
| 9 | Otomatik doğrulama (sadakat, Bloom, yazım, tekrar) | Doğrulama raporu | Es 2024, Tourigny 2026 |
| 10 | Yeniden üretim döngüsü (en çok N) | Geçemeyen soru yeniden üretilir | Yao 2025 |
| 11 | Asenkron görev kuyruğu (Celery + Redis) | Uzun videolarda arka plan işi | – |
| 12 | Web arayüzü (React/Next.js) | URL gir, Bloom seç, soruları gör, videoya atla | Elkins 2024 |
| 13 | Öğretmen onay ekranı | Soruyu onayla/düzenle/sil | R. Liu 2024 |
| 14 | İzleme ve günlükleme | Aşama bazlı gecikme, hata, token | Barnett 2024 |
| 15 | Değerlendirme | RAG'li / RAG'siz karşılaştırma, SUS, öğretmen puanı | Miladi 2025 |

Aşama sırası ve içeriği ilerledikçe güncellenebilir.
