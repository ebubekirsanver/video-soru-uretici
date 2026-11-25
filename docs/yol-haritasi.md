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
  - Özet konu zamanları (2026-10-19): **Yapılan:** blok etiketi kontrolü (modelin verdiği `start_seconds` isteme verilen blok etiketlerinden biri mi; yanıtta `start_verified`, arayüzde "(doğrulanamadı)" işareti; değer değiştirilmez). **Yapılmayan:** konunun videoda gerçekten orada başladığının doğrulanması. **Planlanan (henüz yapılmadı, hocayla netleşince):** modelden konu başına kısa alıntı isteyip zamanı `QuoteLocator` ile hesaplama; özet istemine sürüm numarası verme; konu başlangıçlarının elle ölçümü.
- Aşama 6'da RAG'siz taban çizgisi (`POST /api/questions`, istem `questions-v1`) ve kod tarafında doğrulama eklendi: yapı denetimi, kaynak alıntısının transkriptte aranması, tekrar ayıklama, tekrarlanabilir seçenek karıştırma.
  - Not: soru istemi alıntı için "en az 5 kelime" istiyor (`questions_v1_system.txt`, kural 10); kod ise 3-4 kelimelik alıntıyı transkriptte tek geçiyorsa kabul ediyor (`quotes.py`, `MIN_UNIQUE_QUOTE_WORDS = 3`). Bu bilinçli bir tolerans; `questions-v1` taban çizgisi olarak sabit tutuldu. İstem değişikliği `v2` olarak ve yeni veriyle değerlendirilecek.
- **Sırada:** Aşama 7 (gömme + ChromaDB + erişim; RAG'li üretim taban çizgisiyle karşılaştırılacak) ya da ertelenen Aşama 3 / 4. Aşama 7'deki anlamsal bölütleme için Aşama 4'ün önce yapılması mantıklı olabilir.

## Durum güncellemesi (2026-10-14)

- **Aşama 12 (web arayüzü) parçalara bölündü (12a-12e). Aşama 12'nin geneli: prototip tamamlandı; arayüz ileride yeniden tasarlanacak.**
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
- **Aşama 9: kısmen — alıntı-cevap destek kontrolü (3 deneme) ve kodla kontrol edilen soru yazım kuralları (`writing-rules-v1`, 2026-10-20).** Her denemede elle etiketler model çağrısından önce verilip commit'lendi; model tek çalıştırmayla, `support-v1` ile etiketledi.
  - Deneme 1 ([bulgu](bulgular/asama-9-destek-kontrolu-1.md)): 5 soruda 3 eşleşme, 2 farklı.
  - Deneme 2 ([bulgu](bulgular/asama-9-destek-kontrolu-2.md)): 9 soruda 7 eşleşme, 2 farklı.
  - Deneme 3 ([bulgu](bulgular/asama-9-destek-kontrolu-3.md)): genelleme denemesinin 18 doğrulanmış sorusu; sayıma giren 17 soruda 11 eşleşme, 6 farklı; ingilizce S3 (elle "belirsiz") sayım dışı.
  - Birleşik: sayıma giren 31 soruda 21 eşleşme, 10 farklı.
  - Sınırlar: tek etiketleyen; sorular bağımsız değil (aynı videodan birden çok soru, Deneme 1 ve 2'de aynı kemosentez videosu); her deneme tek çalıştırma.
  - **Yapılan:** alıntı-cevap destek kontrolü; kodla kontrol edilebilen soru yazım kuralları (2026-10-20, `writing-rules-v1`, `services/writing_check.py`, [kural belgesi](soru-yazim-hatalari.md)): 19 maddenin 11'i (3, 4, 6, 9, 10, 11, 12, 14, 16, 17, 19), yalnızca işaretleme (soru atılmaz, API yanıtı değişmez, sonuç kayıtta `writing_check`); eski sorular üzerinde ilk değerlendirme ([bulgu](bulgular/asama-9-yazim-kurallari-1.md)): 36 soru, 12 işaret, kullanıcı etiketiyle 9 doğru, 3 yanlış (yalnızca yanlış pozitifler ölçüldü). **Yapılmayan:** sadakat (RAGAs), Bloom uyum, yazım hatalarının model gerektiren ya da Türkçede kuralı bulunamayan maddeleri (1, 2, 5, 7, 8, 13, 15, 18), yazım kurallarının kaçırdığı hataların ölçülmesi, tekrar ayıklama (benzerlik eşiğiyle).
- **Aşama 14 (izleme ve günlükleme): kısmen.** **Yapılan:** çalıştırma kaydı (`backend/runs/`, `services/runs.py`); aşama bazlı süre (`metrics.stages`), her model çağrısının süresi, model adı ve token sayıları (`metrics.llm_calls`), atılan soru sayıları (`metrics.dropped`), hatalı isteklerin `-error` kaydı (`error`: status_code, kind, detail, stage); `record_version` 4 (`services/metrics.py`); gerçek çalıştırmada elle doğrulandı (20 Ekim, [bulgu](bulgular/asama-14-gercek-calistirma-1.md)). **Yapılmayan:** maliyet hesabı (fiyat kullanıcıdan gelecek, kayda yazılmıyor); kayıtları görme/özetleme aracı yok; günlük (logging) yapılandırması bakılmadı.
- **Sonraki adımlar:** Bir sonraki destek kontrolü denemesinden önce elle etiketleme ölçütü ikili olarak (doğrudan destekliyor / değil) önceden belirlenecek.
- **12e · Destek kontrolü arayüzde: yapıldı** (2026-10-17). "Soruları üret" yanında varsayılan kapalı onay kutusu (`check_support`); model değerlendirmesi şık seçildikten sonra kartta gösterilir. Yalnızca frontend değişti. Tarayıcıda gözle doğrulandı (kullanıcı), kısmen:
  - Görülenler: onay kutusu varsayılan olarak işaretsiz; kutu kapalıyken kartlarda model değerlendirmesi ve üst satırda "Destek kontrolü" yok; kutu işaretliyken üst satırda "Destek kontrolü: support-v1" var ve şık seçilmeden önce kartlarda model değerlendirmesi görünmüyor; kemosentez videosunda şık seçildikten sonra alıntının altında "Model değerlendirmesi: alıntı cevabı destekliyor" ve gerekçe göründü (birkaç soruda); doğrulanamayan bir soruda şık seçilince "Alıntı transkriptte bulunamadı", modelin alıntısı, "kontrol edilmedi: alıntı transkriptte bulunamadığı için model çağrılmadı" ve "Kaynak süresi: yok" göründü.
  - 19 Ekim tarayıcı denemesinde ayrıca doğrulandı ([gözlem](bulgular/asama-12e-tarayici-gozlemi-1.md)): onay kutusu ve açıklama metni; kutunun istek sırasında kilitlenmesi; sayfa altındaki not; "desteklemiyor" ve "destekliyor" etiketlerinin gerçek yanıtta görünüşü.
  - Doğrulanmadı: "kısmen" hâli; "kontrol edilemedi" hâli; dar ekran; karanlık tema dışındaki görünümler.
  - Gözlem: aynı videoda üç ayrı çalıştırmada sorular farklı çıktı, birinde 5 yerine 4 soru döndü (3'ü doğrulanmış). Doğrulanamayan bir soruda alıntı "350-400 S D", soru ve cevap "350-400 °C" yazıyor (kayıttaki asıl neden henüz incelenmedi).
- **12f · Arayüzde Konu + Bloom yolu: yapıldı, tarayıcıda denenmedi** (2026-11-17). "Soruları üret" yanında üç seçenek: Konu + Bloom, RAG (varsayılan; `context_mode: "rag"`, `count: 6`); Konu + Bloom, tam transkript (`context_mode: "full"`, `count: 6`); taban çizgisi (bugünkü istek). `prompt_version` gönderilmez, backend varsayılanı `questions-v3` kullanılır. Kartta hedef Bloom düzeyi etiketi ve konu başlığı; sonuçta koşul, istem sürümü ve "6 konudan N'i için soru üretildi"; soru üretilmeyen konu varsa not. Bu istekte zaman aşımı 300 sn. Yalnızca frontend değişti; `npm run typecheck` geçti. Gerçek istekle ve tarayıcıda gözle doğrulanmadı.
- Aşama 7, 8, 10 ve 11 yapılmadı; Aşama 3 ve 4 ertelenmiş durumda.

## Plan güncellemesi (2026-10-31): Hafta-1 geri bildirimi sonrası

Danışmanın Hafta-1 geri bildiriminden sonra literatür değerlendirmesi yeniden yazıldı ve kapsam daraltıldı. Yukarıdaki "Durum" bölümleri geçmiş kaydıdır, değiştirilmedi.

### Araştırma soruları ve başarı ölçütleri

| | Soru | Başarı ölçütü |
|---|---|---|
| AS1 | Türkçe ders videolarında RAG ile seçilen bağlam, transkriptin tamamını vermeye göre üretilen soruların kalitesini (kabul edilebilir soru oranı, kaynağa dayalılık) artırıyor mu? | RAG koşulunda kabul edilebilir (0–1 yazım hatası) soru oranı en az %70 ve tam transkript koşulundan yüksek |
| AS2 | Bloom yönlendirmeli istem, soruların hedeflenen Bloom düzeyine uyumunu ne ölçüde sağlıyor? | Hedef Bloom düzeyine uyum en az %60, değerlendiriciler arası Cohen's kappa en az 0,60 |
| AS3 | Öğrenciler sistemi ve soruları kullanılabilirlik, açıklık ve yararlılık açısından nasıl değerlendiriyor? | Ortalama SUS en az 68; açıklık ve yararlılık ortalaması 5 üzerinden en az 3,5 |

### Veri seti ve değerlendirme

- **Pilot:** 6 alandan (biyoloji, tarih, matematik, İngilizce, edebiyat, Python) 6 pilot video, toplam ~120 dk. Hepsinde otomatik Türkçe altyazı var.
- **Asıl değerlendirme:** Aynı 6 alandan ikişer, toplam 12 video.
  - Her videoda iki koşul (RAG / tam transkript) × Bloom'un 6 düzeyinden birer soru = 144 soru.
  - İki koşulda aynı model (GPT-4o-mini) ve aynı istem.
- **Değerlendiriciler:** İki değerlendirici, kör (koşul gizli, karışık sıra). Her soru için şunlar puanlanır:
  - Bloom düzeyi
  - 19 maddelik yazım hatası listesine göre hata sayısı
  - kaynağa dayalılık
  - cevaplanabilirlik (1–5)
- **Uyum ve öğrenci değerlendirmesi:** Cohen's kappa. 10 öğrenciyle SUS.
- **Yardımcı ölçütler:** RAGAs ve otomatik yazım denetimi yalnızca yardımcı ölçüttür.

### Mimari kararları

- **LLM:** Yalnızca GPT-4o-mini (Llama-3 çıkarıldı).
- **Transkript:** Altyazı varsa altyazı, yoksa Whisper large-v3.
- **Bölütleme ve erişim:** Ana deneyde sabit boyutlu bölütleme ve çok dilli gömme modeli (BGE-M3) + ChromaDB. Parça üst verisi: video_id ve zaman.
- **İsteme verilen bağlam:** Erişimle seçilen en ilgili birkaç parça, en ilgilisi başta olacak biçimde verilir.
- **Adım bazlı kayıt:** Erişilen parçalar, isteme verilen bağlam ve üretim çıktısı kaydedilir.
- **Otomatik denetim:** Kaynağa dayalılık, yazım hataları, tekrar eleme. Düzeltme/yeniden üretim turları az tutulur (literatüre göre 1–2).
- **Öğrenciye ulaşma:** Sorular öğretmen onayından sonra öğrenciye gider.

### İş-zaman planı

| Dönem | İş |
|---|---|
| Güz 7–8 | Video seçimi ve veri seti tablosu |
| Güz 9–10 (19 Kasım–6 Aralık) | Tam transkript koşulu ve RAG hattı (bölütleme, gömme, erişim) → prototip sürüm 1. Hafta-4 eki (danışman). Tamamlandı: video seçimi (17 Kasım), beyan ve paragraf ile alt küme kuralı (18 Kasım), danışman onayı (25 Kasım). Kalanlar: ölçme ve değerlendirme uzmanının belirlenmesi, puanlama takvimi |
| Güz 11–12 | Bloom yönlendirmeli istem, çeldirici adımı, tekrar eleme; pilot videolarda üretim |
| Güz 13–14 | Değerlendirme yönergesi, iki değerlendiriciyle pilot etiketleme ve kappa |
| Güz 11–14 | Hafta-4 eki (danışman): ölçme ve değerlendirme uzmanıyla yönergenin kısa bir okuması; en çok ayrışılan ölçütün kaydı |
| Deneme etiketlemesi (Aralık 2026) | Açılış 1–3 Aralık; bağımsız puanlama 3–10 Aralık; uyum hesabı 11–12 Aralık; tartışma 13–16 Aralık; yönerge 2. sürüm 17–25 Aralık |
| Bahar 1–2 | Düzeltmeler ve öğretmen onay ekranı → prototip sürüm 2 |
| Bahar 3–4 | 144 soru üretimi |
| Bahar 5–6 | Kör uzman değerlendirmesi. Hafta-4 eki (danışman): alt kümede ölçme ve değerlendirme uzmanı puanlaması; alt küme kappası için bootstrap güven aralığı |
| Bahar 7–8 | Öğrenci değerlendirmesi (SUS) |
| Bahar 9–10 | Analizler |
| Bahar 11–14 | Rapor ve sunum |

### Aşamaların yeni plandaki yeri

"Şu anki durum" sütunu yukarıdaki durum bölümlerinden ve ilerleme günlüğünden alındı.

| Aşama | Ana deney mi, ikincil mi | İş-zaman planında hafta | Şu anki durum |
|---|---|---|---|
| 0 · Proje iskeleti | belirtilmedi | planda haftası yok | tamamlandı |
| 1 · FastAPI iskeleti | belirtilmedi | planda haftası yok | tamamlandı |
| 2 · URL ayrıştırma + transkript | belirtilmedi | planda haftası yok | tamamlandı |
| 3 · Whisper yedeği, WER | yalnızca altyazısı olmayan video seçilirse gerekli (pilot videoların hepsinde otomatik altyazı var) | planda haftası yok | ertelendi |
| 4 · Bölümleme | ana (yalnızca sabit boyut) | Güz 9–10 | kısmen (7a) |
| 5 · LLM katmanı + özet | belirtilmedi | planda haftası yok | tamamlandı |
| 6 · Temel soru üretimi (RAG'siz) | ana: AS1'in tam transkript koşulu | Güz 9–10'da RAG koşuluyla aynı istemle karşılaştırılacak | tamamlandı; kodu var (questions-v1) |
| 7 · Gömme + ChromaDB + erişim | ana | Güz 9–10 | kısmen (7a, 7b: soru üretimine bağlandı; konular ayrı adımdan, topics-v1; iki koşul gerçek videoda bir kez işlerlik denemesiyle çalıştırıldı, kalite ölçülmedi) |
| 8 · Bloom yönlendirmeli istem | ana | Güz 11–12 | kısmen (istem questions-v3 ve konu–düzey eşlemesi kodlandı; Pilot 1'de denendi; questions-v4 açıldı, varsayılan v3, Pilot 2'den sonra ana deney istemi questions-v3 olarak donduruldu, git etiketi istem-v3-ana-deney (c0c68cd); düzey uyumu ölçülmedi) |
| 9 · Otomatik doğrulama | ana (kalan kısımlar); RAGAs ve otomatik yazım denetimi değerlendirmede yalnızca yardımcı ölçüt | kalan kısımlar Güz 11–12 | kısmen (alıntı-cevap destek kontrolü, kodla yazım kuralları `writing-rules-v1`) |
| 10 · Yeniden üretim döngüsü | belirtilmedi (en çok 1–2 tur) | planda haftası yok | yapılmadı |
| 11 · Asenkron görev kuyruğu | belirtilmedi | planda haftası yok | yapılmadı |
| 12 · Web arayüzü | belirtilmedi | planda haftası yok | prototip tamamlandı (12a-12e); 12f yapıldı, tarayıcıda denendi (2026-11-17, kullanıcı) |
| 13 · Öğretmen onay ekranı | belirtilmedi | Bahar 1–2 | yapılmadı |
| 14 · İzleme ve günlükleme | belirtilmedi | planda haftası yok | kısmen (kayıt tarafı tamam) |
| 15 · Değerlendirme | ana | Bahar 3–10 | yapılmadı |

### Ana deneyler

- **AS1:** RAG / tam transkript karşılaştırması. 12 video × 2 koşul × 6 Bloom düzeyi = 144 soru, iki kör değerlendirici.
- **AS2:** Bloom yönlendirmeli istemin hedef düzeye uyumu, Cohen's kappa.
- **AS3:** 10 öğrenciyle SUS; açıklık ve yararlılık puanları.
- **Hafta-3 geri bildirimi (2026-11-10):** Pilot videolar ana deneyde kullanılmayacak; 12 videonun seçim kuralı ve altı videoluk yedek plan seçimden önce `docs/video-secim-kurali.md` dosyasına yazıldı. Değerlendirmede "tanıma hatası kaynaklı mı" işareti var; altyazı türü (elle / otomatik) değişken olarak kaydedilir; iki dilli videoların sonuçları hem dâhil hem hariç hesaplanır.
- **Hafta-4 geri bildirimi (2026-11-18):**
  - **Değerlendiriciler:** aynı bölümden, projede yer almayan iki öğrenci; karşılıklı değerlendirme yapılmayacak.
  - **Alan öğretmeni alt kümesi:** danışmanın "Bu etiketlerin doğru olduğunu nereden biliyorsunuz?" sorusu üzerine, iki değerlendiricinin ortak etiketlerinin geçerliliği bir alan öğretmeniyle sınanacak. Öğretmen 144 sorudan 36'sını puanlar; etiketleri ana analize katılmaz, geçerlilik göstergesi olarak raporlanır. Alt küme puanlamadan önce sabit tohumla, alan, koşul ve Bloom düzeyine göre dengeli seçilir. Kural `docs/alt-kume-secim-kurali.md`; betikler `backend/evaluation/subset.py` ve `validity.py`. Seçim dosyası puanlama bitene kadar depo dışında kalır, depoya yalnızca SHA-256 özet değeri girer.
  - **Yapay zekâ beyanı:** video aramaları (Claude in Chrome ile yapılan aramalar) beyana eklenecek.
- **Hafta-5 geri bildirimi (2026-11-25):**
  - **Onay:** danışman değerlendirici planını ve 36 soruluk alt küme planını onayladı.
  - **Puanlayıcı:** alt kümeyi alan öğretmeni yerine eğitim fakültesinin ölçme ve değerlendirme alanından bir araştırma görevlisi ya da öğretim elemanı puanlayacak. Gerekçe: sorular altı alandan geliyor ve tek bir alan öğretmeni bunların en fazla birinde uzman olur; Bloom düzeyi ve soru yazım hataları alan bilgisinden çok ölçme ve değerlendirme bilgisine dayanır. Seçim kuralı bu değişiklikten etkilenmiyor; değişiklik kuralın "Değişiklikler" bölümüne tarihiyle yazıldı. Kodda ve dosya adlarında "alan öğretmeni / ogretmen" adı geçmişle uyum için korundu.
  - **Bootstrap güven aralığı:** alt kümedeki 36 soruda uzmanla uyum kappalarına, büyük örneklem aralığının yanında yüzdelik bootstrap aralığı da veriliyor (B = 2000, tohum 20261125; `validity.py --bootstrap`). Küçük örneklemde büyük örneklem yaklaşımından daha güvenilir.
  - **Deneme etiketlemesi:** iki değerlendiricinin deneme etiketlemesinde en çok ayrıştığı ölçüt kaydedilecek.
- **Anahtar yanlış kuralı (2026-11-25):**
  - **Ne:** modelin doğru diye işaretlediği seçenek videoya göre yanlışsa değerlendirici "Hatalı maddeler"e A yazar. A yazım hatası sayısına 1 olarak katılır, soru başka hatası olmasa da kabul edilemez sayılır; kaynağa dayalı = hayır, cevaplanabilirlik = 1 işaretlenir (yönerge, Bölüm 4).
  - **Neden:** Moore vd.'nin 19 maddelik listesi cevabın doğruluğuna bakmıyor; kural olmazsa cevabı yanlış ama düzgün yazılmış bir soru "kabul edilebilir" sayılır.
  - **Ne zaman:** hiçbir soru puanlanmadan önce eklendi (puanlama öncesi netleştirme).
  - **Ek sonuç:** şeffaflık için AS1'in kabul edilebilirlik sonucu ek olarak kural uygulanmadan, yalnızca 19 maddeye göre de verilecek.
  - Yönerge metni değerlendirici ve uzman dosyalarının "Yönerge" sayfasına yazılıyor; deneme etiketlemesi dosyaları bu kuralla yeniden üretildi (`docs/bulgular/degerlendirme-denemesi-2/`).
- **İstem (2026-11-04):** Pilot 2'den sonra ana deney istemi `questions-v3` olarak donduruldu (git etiketi `istem-v3-ana-deney`); `questions-v4` kullanılmayacak. Gerekçe: docs/bulgular/pilot-2/pilot-2.md, "Karar".

### İkincil deneyler

Bunlar yalnızca ana deneyler bittikten sonra, zaman kalırsa yapılır. AS1–AS3'ü yanıtlamak için gerekli değildir.

- Sabit ve anlamsal bölütleme
- Farklı gömme modelleri
- Yeniden sıralama (cross-encoder)
- Ham ve temiz transkript
- Ön test/son test

### Not

Yeni mimari görseli 31 Ekim'de eklendi; docs/mimari-kod-karsilastirmasi.md 19 Ekim'deki eski görsele göredir. Görsel 4 Kasım 2026'da Hafta-2 geri bildirimine göre güncellendi (bölütleme: sabit boyutlu ana deney, anlamsal ikincil deney; soru üretimine 6 konu × 6 Bloom düzeyi eklendi).
