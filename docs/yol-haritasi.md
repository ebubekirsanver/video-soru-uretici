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

## Durum (2026-10-12)

- **Tamamlanan:** 0, 1, 2, 5, 6
- **Ertelenen:** 3 (Whisper yedeği, WER ölçümü) ve 4 (bölümleme). Uçtan uca dikey dilimi (URL → transkript → özet → soru) önce bitirmek için Aşama 5 ve 6 öne alındı.
- Aşama 5'te ham/temiz transkript seçimi (`transcript_mode`) ve ~30 sn'lik zaman damgalı bloklama (`services/chunking.py`) eklendi; bloklama Aşama 4'te yeniden kullanılacak.
- Aşama 6'da RAG'siz taban çizgisi (`POST /api/questions`, istem `questions-v1`) ve kod tarafında doğrulama eklendi: yapı denetimi, kaynak alıntısının transkriptte aranması, tekrar ayıklama, tekrarlanabilir seçenek karıştırma.
- **Sırada:** Aşama 7 (gömme + ChromaDB + erişim; RAG'li üretim taban çizgisiyle karşılaştırılacak) ya da ertelenen Aşama 3 / 4. Aşama 7'deki anlamsal bölütleme için Aşama 4'ün önce yapılması mantıklı olabilir.

## Durum güncellemesi (2026-10-14)

- **Aşama 12 (web arayüzü) parçalara bölündü (12a-12e). Aşama 12'nin geneli: yapılmadı.**
  - **12a · Arayüz iskeleti ve sağlık göstergesi: tamamlandı.** `frontend/` altında Next.js iskeleti, ana sayfada `/health` göstergesi, backend'de yalnızca `http://localhost:3000` kaynağına izin veren CORS. Tarayıcıda gözle doğrulandı: backend açıkken yeşil "Sunucu çalışıyor", backend kapatılınca kırmızı durum göründü.
  - **12b · YouTube bağlantısı formu: yapıldı** (2026-10-14). Form `POST /api/summary` çağırıyor; hata durumları anahtarsız gerçek backend'e karşı denendi. Başarılı özet yolu ve tarayıcıda gözle kontrol henüz yapılmadı.
  - **12c · Biçimli özet ekranı: tamamlandı** (2026-10-14). Özet, konu başlıkları ve dakika:saniye zamanları okunaklı bir kartta; başlık videoyu o saniyeden açar. Tarayıcıda gözle doğrulandı (kullanıcı): gerçek bir özet kartı gösterildi (özet, konu başlıkları ve zamanlar, doğrulanmadı notu), hata durumunda kart temizlendi. Zaman bağlantısının videoyu doğru saniyede açıp açmadığı henüz denenmedi. Gözlem: aynı videoda iki ayrı çalıştırmada model farklı konu zamanları üretti (ör. üçüncü konu 9:51 ve 9:19).
  - **12d · Soru kartları: tamamlandı** (2026-10-14). Özet kartının altında ayrı "Soruları üret" isteği; etkileşimli soru kartlarında cevap seçilince doğru/yanlış, kaynak alıntısı, doğrulama durumu ve videoya atlayan kaynak süresi gösterilir. Elle kontrol (kullanıcı): 5 sorudan 2'sinin (Soru 1 ve Soru 2) kaynak süresi videoda açılıp kontrol edildi, kalan 3'ü kontrol edilmedi, saniye ölçülmedi. Soru 2'de alıntı transkriptte bulunuyor ve süresi konuşmayla uyuşuyor, ama doğru cevap ("Kemosentetik canlılar") bu kaynakla desteklenmiyor; "kaynağı doğrulanmış" etiketi kaynağın cevabı kanıtladığı anlamına gelmiyor ([bulgu](bulgular/asama-12d-test-1.md)).
  - **12e: yapılmadı.**
- Aşama 7-11 yapılmadı; arayüz iskeletine bunlardan önce geçildi. Aşama 3 ve 4 hâlâ ertelenmiş durumda.
