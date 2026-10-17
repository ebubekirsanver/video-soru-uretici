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
  - **12d · Soru kartları: tamamlandı** (2026-10-14). Özet kartının altında ayrı "Soruları üret" isteği; etkileşimli soru kartlarında cevap seçilince doğru/yanlış, kaynak alıntısı, doğrulama durumu ve videoya atlayan kaynak süresi gösterilir. Elle kontrol (kullanıcı): 5 sorudan 2'sinin (Soru 1 ve Soru 2) kaynak süresi videoda açılıp kontrol edildi, kalan 3'ü kontrol edilmedi, saniye ölçülmedi. Soru 2'de alıntı transkriptte bulunuyor ve süresi konuşmayla uyuşuyor; alıntı konuyla ilgili ama doğru cevabı ("Kemosentetik canlılar") doğrudan söylemiyor (elle etiket: kısmen); "kaynağı doğrulanmış" etiketi kaynağın cevabı kanıtladığı anlamına gelmiyor ([bulgu](bulgular/asama-12d-test-1.md)).
  - **12e: yapılmadı.**
- Aşama 7-11 yapılmadı; arayüz iskeletine bunlardan önce geçildi. Aşama 3 ve 4 hâlâ ertelenmiş durumda.

## Durum güncellemesi (2026-10-14, Aşama 9)

- **Aşama 9 (otomatik doğrulama): kısmen — alıntı-cevap destek kontrolü (ilk adım).**
  - **Yapıldı:** `POST /api/questions` isteğinde `check_support: true` ile açılan, varsayılanı kapalı model kontrolü (istem `support-v1`). Her doğrulanmış soru için modele soru, doğru cevabın metni ve alıntı verilir; model alıntının cevabı "destekliyor", "kısmen" ya da "desteklemiyor" olduğunu söyler. Gerekçe: Aşama 12d tarayıcı testinde alıntısı transkriptte bulunan, konuyla ilgili ama doğru cevabı doğrudan söylemeyen bir soru görüldü (elle etiket: kısmen; [bulgu](bulgular/asama-12d-test-1.md)).
  - Bu bir **model değerlendirmesidir**.
  - **İlk deneme yapıldı** ([destek kontrolü denemesi 1](bulgular/asama-9-destek-kontrolu-1.md)): Aşama 12d testinin 5 sorusu yeniden üretilmeden, `support-v1` ile tek çalıştırmayla kontrol edildi. Elle etiketler model çağrısından önce verildi. Elle etiket ile model etiketi 5 sorunun 3'ünde eşleşti, 2'sinde farklı. İsabet iddiası yok: 5 soru, tek etiketleyen, tek çalıştırma.
  - **Yapılmadı:** sadakat (faithfulness) kontrolü, Bloom düzeyi kontrolü, yazım hatası kontrolü, tekrar kontrolü (Aşama 6'daki birebir metin tekrarı ayıklama dışında).
- Aşama 7, 8, 10 ve 11 yapılmadı.

## Durum güncellemesi (2026-10-17)

- **Genelleme denemesi 1** ([bulgu](bulgular/genelleme-denemesi-1.md)): 4 yeni video (matematik, edebiyat, python, ingilizce), video başına tek çalıştırma, 20 soru, 18'inin alıntısı transkriptte bulundu (matematik 4/5, edebiyat 5/5, python 5/5, ingilizce 4/5). Yazım gözlemleri kaydedildi: ingilizce transkriptte "used to" 0, "yüz" 25 kez geçiyor; özet "used to", soru metinleri "Yüz kalıbı" yazıyor. Python transkriptinde "guido One rossum", "mat plot lip", "non python" yazımları var.
- **Aşama 9: kısmen — yalnızca alıntı-cevap destek kontrolü (3 deneme).** Her denemede elle etiketler model çağrısından önce verilip commit'lendi; model tek çalıştırmayla, `support-v1` ile etiketledi.
  - Deneme 1 ([bulgu](bulgular/asama-9-destek-kontrolu-1.md)): 5 soruda 3 eşleşme, 2 farklı.
  - Deneme 2 ([bulgu](bulgular/asama-9-destek-kontrolu-2.md)): 9 soruda 7 eşleşme, 2 farklı.
  - Deneme 3 ([bulgu](bulgular/asama-9-destek-kontrolu-3.md)): genelleme denemesinin 18 doğrulanmış sorusu; sayıma giren 17 soruda 11 eşleşme, 6 farklı; ingilizce S3 (elle "belirsiz") sayım dışı.
  - Birleşik: sayıma giren 31 soruda 21 eşleşme, 10 farklı.
  - Sınırlar: tek etiketleyen; sorular bağımsız değil (aynı videodan birden çok soru, Deneme 1 ve 2'de aynı kemosentez videosu); her deneme tek çalıştırma.
  - **Yapılmadı:** sadakat (faithfulness), Bloom düzeyi, yazım hatası ve tekrar kontrolü.
- **Sonraki adımlar:** Bir sonraki destek kontrolü denemesinden önce elle etiketleme ölçütü ikili olarak (doğrudan destekliyor / değil) önceden belirlenecek.
- **12e · Destek kontrolü arayüzde: yapıldı** (2026-10-17). "Soruları üret" yanında varsayılan kapalı onay kutusu (`check_support`); model değerlendirmesi şık seçildikten sonra kartta gösterilir. Yalnızca frontend değişti. Tarayıcıda gözle doğrulanması kullanıcının onayını bekliyor.
- Aşama 7, 8, 10 ve 11 yapılmadı; Aşama 3 ve 4 ertelenmiş durumda.
