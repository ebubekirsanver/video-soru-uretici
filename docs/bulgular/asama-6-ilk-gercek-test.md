# Aşama 6 · İlk gerçek test bulguları

**Tarih:** 12 Ekim 2026
**Test:** `POST /api/questions` · video `109kCbVtU1U` (Türkçe, kemosentez dersi, yaklaşık 25 dk, YouTube otomatik altyazısı) · `count: 5` · `transcript_mode: clean`
**Model / istem:** gpt-4o-mini · `questions-v1` (RAG'siz taban çizgisi)
**Ham sonuç:** [asama-6-ilk-gercek-test.json](asama-6-ilk-gercek-test.json)

> Bu bir ön denemedir: tek video, tek çalıştırma, 4 soru. Sonuçlar genellenemez, sistemin neyi yakaladığını ve hangi zayıflıkları gösterdiğini belgelemek içindir. Ölçülü karşılaştırmalar Aşama 15'te yapılacaktır.

## A · İlk çalıştırma sonucu (API yanıtı, test anındaki kod)

Bu bölüm, `POST /api/questions` çağrısının ham yanıtıdır ([JSON](asama-6-ilk-gercek-test.json)). Test anındaki kod zamanı 30 sn'lik blok başlangıcından hesaplıyor ve 5 kelimeden kısa alıntıyı reddediyordu; kırpmalı eşleştirme yoktu.

| Ölçü | Değer |
|---|---|
| İstenen soru | 5 |
| Dönen soru | 4 (modelin 5 soru döndürüp 1'inin yapı denetiminde ya da tekrar nedeniyle mi atıldığı, yoksa modelin yalnızca 4 soru mu döndürdüğü sunucu günlüğünden doğrulanmadı) |
| **Doğrulanan (alıntı transkriptte bulundu)** | **2 / 4** |
| Doğru şık dağılımı (karıştırma sonrası) | 0, 3, 2, 1 → tek şıkta yığılma yok |

| # | Soru konusu | Alıntı (kelime) | Geçiş sayısı | Modelin alıntıya yazdığı `[saniye]` | `verified` | `source_start_seconds` | Sapma (sn) |
|---|---|---|---|---|---|---|---|
| 1 | Kemosentetik canlıların enerji kaynağı | 15 | 0 | 219 | false | null | – |
| 2 | Hidrotermal bacaların yeri | 14 | 1 | 124 | true | 124,96 | 0,96 |
| 3 | Kemosentetik canlıların hücre yapısı | 6 | 1 | **591** | true | **435,4** | **155,6** |
| 4 | Kemosentezde açığa çıkmayan madde | 4 | 1 | 806 | false | null | – |

- `verified`, `source_start_seconds`, alıntı metinleri ve modelin yazdığı `[saniye]` değerleri API yanıtından alınmıştır.
- Kelime sayısı ve geçiş sayısı tanı sırasında ölçülmüştür (aşağıya bak). Kelime sayısı alıntının normalleştirilmiş halidir, baştaki `[sayı]` etiketi sayılmaz. Geçiş sayısı, alıntının (eklenmiş kelimeler dahil) transkriptte birebir kaç kez geçtiğidir.
- Sapma = |modelin yazdığı saniye − kodun hesapladığı saniye|. Kod alıntıyı doğrulayamadığında (null) sapma hesaplanmadı.

## B · Yeniden ölçüm (kural değişikliklerinden sonra)

> **Model yeniden çalıştırılmadı.** Bu bölüm, ilk çalıştırmada üretilen aynı 4 sorunun aynı alıntılarının, tanıdan sonra değiştirilen doğrulama koduyla (Bulgu 6) yeniden denetlenmesidir. Yeni soru üretilmemiştir; bu nedenle bir "ikinci çalıştırma" sonucu değildir.

| # | `verified` | `source_start_seconds` | `quote_match` | İlk çalıştırmaya göre değişen |
|---|---|---|---|---|
| 1 | **true** | 216,84 | **trimmed** | Baştaki "Yani" kırpıldı; `source_quote` transkriptteki metinle değiştirildi |
| 2 | true | 134,16 | exact | Zaman blok başı (124,96) yerine cümlenin başladığı segment |
| 3 | true | 442,72 | exact | Zaman blok başı (435,4) yerine cümlenin başladığı segment |
| 4 | **true** | 813,28 | exact | 4 kelimelik tek geçişli alıntı artık kabul ediliyor |

Güncel kodda doğrulanan her alıntının `source_quote` değeri transkriptteki özgün metinle değiştirilir. Bu yüzden modelin eklediği `[124]`, `[591]` gibi etiketler yanıtta görünmez. Doğrulanamayan alıntılarda yalnızca baştaki etiket silinir.

**Doğrulanan: 4 / 4** (ilk çalıştırmada 2 / 4). Bu artış doğrulama kurallarının değişmesinden kaynaklanır, modelin daha iyi soru üretmesinden değil. Kurallar bu dört soruya bakılarak ayarlandığı için bu sonuç kuralların başarısının kanıtı sayılmamalıdır (bkz. Sınırlar).

**Tanı ve yeniden ölçüm yöntemi:** Transkript aynı videodan `fetch_transcript` ile yeniden çekildi (Türkçe otomatik altyazı, 680 segment, 1513,8 sn; OpenAI çağrısı yapılmadı). Temizlenip 30 sn'lik bloklara ayrıldı (49 blok). Alıntılar kodla aynı normalleştirmeyle (`quotes.normalize`) aranarak tüm tam kelime geçişleri sayıldı. Yeniden ölçümde alıntılar JSON dosyasından okunup güncel `QuoteLocator.match` ile tam transkriptte arandı. İlk çalıştırmanın kod değerleri (124,96 ve 435,4) yeniden çekilen transkript üzerinde o zamanki kodla da yeniden üretildi ve API yanıtıyla aynı çıktı. Geçici tanı betikleri commit'lenmedi.

## C · İkinci test (kural değişikliklerinden sonra)

> Bunlar, Bulgu 6'daki kural değişikliklerinden **sonraki ilk gerçek çalıştırmalardır**. Model yeni sorular üretti; B bölümündeki yeniden ölçümden farklı olarak bu bir yeni çalıştırmadır. Ayarlar: `count: 5`, `transcript_mode: clean`, gpt-4o-mini, `questions-v1`. Ham yanıtlar `backend/runs/` kayıtlarının birebir kopyasıdır.

**Tablo sütunları:**
- *Kelime:* `source_quote`'un normalleştirilmiş kelime sayısı. Güncel kodda `source_quote`, transkriptte bulunan metindir; `trimmed` sorularda bu, kırpılmış hâldir.
- *Elle zaman kontrolü:* Kullanıcının videoda gözle okuduğu cümle başlangıcıdır (hassasiyet yaklaşık ±1 sn). Boş hücre, o sorunun zamanının elle kontrol edilmediği anlamına gelir.

### C.1 · Kemosentez videosu (`109kCbVtU1U`)

Ham yanıt: [asama-6-ikinci-test-kemosentez.json](asama-6-ikinci-test-kemosentez.json). İstenen 5, dönen 4, doğrulanan 4/4.

| # | Soru | `verified` | `quote_match` | `source_start_seconds` | Kelime | Elle zaman kontrolü |
|---|---|---|---|---|---|---|
| 1 | Kemosentetik canlılar hangi enerji kaynağını kullanarak besin üretimi gerçekleştirir? | true | exact | 568,959 (9:28) | 18 | Cümle 9:31'de (571 sn); kod ~2,0 sn önde. Aynı alıntı ve zaman önceki bir çalıştırmada da çıktı, ölçüm o zaman yapıldı. |
| 2 | Hidrotermal bacaların bulunduğu ortamda hangi canlılar yaşayabilir? | true | exact | 247,64 (4:07) | 16 | Cümle 4:13'te (253 sn); kod ~5,4 sn önde |
| 3 | Kemosentez sırasında hangi madde açığa çıkmaz? | true | trimmed | 1175,919 (19:35) | 3 | Zaman doğru (saniyesi ölçülmedi) |
| 4 | Kemosentetik canlıların hücre yapısı nedir? | true | exact | 442,72 (7:22) | 6 | |

### C.2 · Tarih videosu (`aaCHLYO3Fzg`)

Ham yanıt: [asama-6-ikinci-test-tarih.json](asama-6-ikinci-test-tarih.json). İstenen 5, dönen 5, doğrulanan 5/5.

| # | Soru | `verified` | `quote_match` | `source_start_seconds` | Kelime | Elle zaman kontrolü |
|---|---|---|---|---|---|---|
| 1 | Malazgirt Savaşı hangi yıllarda gerçekleşmiştir? | true | exact | 79,52 (1:19) | 5 | Cümle 1:21'de (81 sn); kod ~1,5 sn önde. Aynı alıntı ve zaman önceki bir çalıştırmada da çıktı, ölçüm o zaman yapıldı. |
| 2 | Danışmentlilerin kurulduğu bölgeler arasında hangisi yer almaz? | true | trimmed | 244,319 (4:04) | 10 | Cümle 4:06'da (246 sn); kod ~1,7 sn önde |
| 3 | Kösedağ Savaşı'nda Türkiye Selçuklu Devleti kime karşı savaşmıştır? | true | trimmed | 1786,96 (29:46) | 7 | Zaman doğru (saniyesi ölçülmedi) |
| 4 | Mir Kefalon Savaşı'nın önemi nedir? | true | exact | 1740,36 (29:00) | 13 | |
| 5 | 1. Haçlı Seferi'nin temel amacı nedir? | true | exact | 607,279 (10:07) | 8 | |

Dakika:saniye gösteriminde saniye aşağı yuvarlanmıştır (YouTube'daki gibi).

### C.3 · İkinci test bulguları

**(a) Zaman hassasiyeti.** Elle kontrol edilen 6 zamanın 6'sı doğru yere düşüyor. Saniyesi ölçülen 4 sorunun dördünde de kod, cümleden **önce** başlatıyor. Fark 1,5 ile 5,4 sn arasında, ortalaması yaklaşık **2,6 sn**. Kesin farklar 2,04 / 5,36 / 1,48 / 1,68 sn, ortalaması 2,64; ölçüm hassasiyeti ±1 sn olduğu için ondalık kesin değildir. Bu, segment çözünürlüğünün doğal sonucudur: alıntı bir segmentin ortasında başladığında kod segmentin başını verir. Örneğin kemosentez S1'in segmenti (568,959 sn) *"gidiyoruz zaten. Yani şimdi kemosentez"* metniyle başlıyor; alıntı bu segmentin son kelimesinden başlıyor. Önceki blok tabanlı hesapta fark, ilk testin Soru 3'ünde yaklaşık 7,3 sn idi (Bulgu 1). Video önce başladığı için öğrenci cümleyi kaçırmaz, yalnızca birkaç saniye bekler.

**(b) Çıktı belirsizliği.** Aynı kemosentez videosunda ikinci çalıştırma farklı sorular üretti, bazıları tekrar etti:
- *"Kemosentez sırasında hangi madde açığa çıkmaz?"* iki çalıştırmada da **birebir aynı** metinle çıktı. Alıntısı farklı: ilk testte *"Kemosentezde oksijen açığa çıkmıyormuş."*, burada *"oksijen üretilmez demiştim."*
- İki soru aynı konuyu farklı sözcüklerle tekrarladı: ilk testin Soru 1'i ile buradaki S1 (enerji kaynağı), ilk testin Soru 3'ü ile buradaki S4 (hücre yapısı; aynı alıntı ve aynı 442,72 sn).
- Hidrotermal baca konusu her iki çalıştırmada da var, ama soru ve alıntı farklı.

**(c) Olumsuz soru kökü iki farklı videoda çıktı:** kemosentez S3 *"…açığa çıkmaz?"*, tarih S2 *"…yer almaz?"*. İlk testteki aynı gözlemle (Bulgu 4) birlikte bu, kalıbın tek seferlik olmadığını gösteriyor (Aşama 9'daki yazım denetimi için).

**(d) Alıntı doğrulaması cevabı kanıtlamıyor (tarih S2).** Doğru cevap "İzmir", ama alıntı (*"Tokat, Amasya, Kayseri, Sivas, Malatya bu bölgelere yayılmış bir beylik."*) yalnızca diğer şıkları içeriyor. Soru olumsuz köklü olduğu için doğru cevap zaten alıntıda geçmeyen şıktır. `verified=true` yalnızca alıntının videoda geçtiğini gösterir; cevabın alıntıdan çıkarılabilir olduğunu göstermez. Sadakat denetimi Aşama 9'da yapılacak.

**(e) Alıntı ile cevap tam örtüşmüyor (kemosentez S2).** Alıntı *"…kemosentez yapan bakterilerle beslenen farklı biyolojik canlılara rastlanabilir"* diyor; yani baca çevresindeki canlılar kemosentetik bakterilerle beslenen canlılardır. Doğru cevap ise "Kemosentetik canlılar". Alıntı cevabı destekliyor ama aynı şeyi söylemiyor. Bu da (d) ile aynı sınıfta, alıntı–cevap tutarlılığı sorunudur.

**(f) 3 kelimelik kırpılmış alıntı işe yaradı (kemosentez S3).** *"oksijen üretilmez demiştim."* yeni kuralların izin verdiği en kısa biçim: kırpılmış, 3 kelime, transkriptte tek geçiş. Doğrulandı ve zamanı elle kontrolde doğru çıktı. Tek örnektir; kuralın genel olarak güvenilir olduğunu göstermez.

**(g) Küçük dil sorunu (tarih S1).** *"Malazgirt Savaşı hangi yıllarda gerçekleşmiştir?"* tek bir yıl (1071) soruluyorken çoğul "yıllarda" kullanıyor.

## Bulgu 1 · Zamanı modelden değil, alıntıdan hesaplamak doğru karardı

Soru 3'te model, alıntının başına `[591]` yazdı. Videoda cümle (*"Kemosentetik canlıların tamamının prokaryot olduğunu unutma"*) **yalnızca 7:15'te başlayan bölümde** geçiyor; elle kontrol edildi ve transkriptle doğrulandı:

- Alıntı transkriptte **tam 1 kez** geçiyor.
- Kodun hesapladığı 435,4 sn, alıntının bulunduğu bloğun (435,4–467,96 sn) **ilk segmentinin başlangıcıdır** (`"yapıyoruz? Enerji üretimini"`).
- Cümlenin kendisi aynı blokta, **442,72 sn'de (7:22)** başlayan segmentte söyleniyor. Test anında kodun verdiği zaman cümleden 7,3 sn önceydi; bu, blok çözünürlüğünün (~30 sn) beklenen sonucuydu. Bu gözlem üzerine zaman segment düzeyinde hesaplanmaya başlandı; güncel kod 442,72 verir (Bulgu 6).
- Modelin yazdığı `[591]`, istemde gerçekten var olan bir blok etiketidir (591,2–624,4 sn), ama bu blok alıntıyı içermiyor; kemosentetik canlıların yaşadığı yerlerden (çöplükler, sindirim sistemleri) bahsediyor.

Modelin değeri kodun değerinden **155,6 sn**, cümlenin gerçek başlangıcından **148,3 sn** sapıyor. Modelin zamanına güvenseydik öğrenci, sorunun dayandığı cümleden yaklaşık 2,5 dakika sonraki ve başka bir konuyu anlatan bir noktaya yönlendirilecekti. Bu nedenle `source_start_seconds` değeri **kod tarafında, doğrulanmış alıntının transkriptteki yerinden** hesaplanır (bkz. `backend/app/services/quotes.py`).

Not: Aynı fikir videoda başka sözcüklerle de tekrarlanıyor (582,3 sn *"Bu canlıların tamamı prokaryot hücre…"*, 736,2 sn *"…tamamının prokaryot hücre yapısına sahip"*, 1131,8 sn *"…tamamı prokaryottu"*). Ancak alıntılanan cümle kelimesi kelimesine yalnızca bir yerde geçiyor ve model bu tekrarların hiçbirine değil, 591'e işaret etmiş.

## Bulgu 2 · Doğrulama gerçekten çalışıyor, ama kural ayarı gerekiyor

İlk çalıştırmada 4 sorunun 2'si doğrulanamadı. Bu, kod tarafı doğrulamanın modelin çıktısını körü körüne kabul etmediğini gösteriyor.

- **Soru 4:** Alıntı (*"Kemosentezde oksijen açığa çıkmıyormuş."*) meşru bir cümle: transkriptte kelimesi kelimesine ve **tam 1 kez** geçiyor (813,28 sn'deki segmentte başlıyor, 806,96 sn'de başlayan blokta). Ancak 4 kelime olduğu için "5 kelimeden kısa alıntı doğrulanmaz" kuralına takıldı; kural meşru kısa alıntıları da eliyordu. Kural ayarlandı (Bulgu 6); güncel kodla soru doğrulanıyor.
- **Soru 1:** Eşleşmemenin nedeni **kelime farkı**: model alıntının başına transkriptte olmayan bir **"Yani"** eklemiş. Alıntının geri kalan 14 kelimesi transkriptle birebir aynı.

  | | Metin |
  |---|---|
  | Alıntı | `[219]` **Yani** kimyasal bir enerjiyi kullanarak besin üretimini gerçekleştiriyorsa o canlıya da kemosentetik canlı adını vermiştik. |
  | Transkript | …biz buna fotosentetik canlı **demiştik.** Kimyasal bir enerjiyi kullanarak besin üretimini gerçekleştiriyorsa o canlıya da kemosentetik canlı adını vermiştik. |

  - **Noktalama neden değil:** normalleştirme noktalamayı zaten yok sayıyor.
  - **Bloklar arası geçiş neden değil:** alıntı 216,84 sn'deki segmentte (187,16 sn'de başlayan bloğun son segmenti) başlayıp 219,2 sn'de başlayan bloğa uzanıyor. Kod blokları/segmentleri tek metinde birleştirip aradığı için bu durum eşleşmeyi engellemez. Modelin yazdığı `[219]`, alıntının büyük kısmının bulunduğu bloğun etiketi.
  - Alıntı, eklenen kelimeyle birlikte transkriptte 0 kez geçiyor. Test anındaki kod "kelimeler birebir aynı olmalı" kuralını uyguladığı için soru doğrulanmadı. Kural tasarlandığı gibi çalıştı: model alıntıyı kelimesi kelimesine aktarmamıştı.
  - Ancak eklenen sözcük alıntının kenarında bir dolgu sözcüğüdür ve sorunun dayandığı bilgi transkriptte birebir duruyor. Bu nedenle kenar kırpma eklendi (Bulgu 6); güncel kodla soru `quote_match: "trimmed"` olarak doğrulanıyor ve `source_quote` transkriptteki metinle değiştiriliyor.

## Bulgu 3 · Sorular hatırlama düzeyinde kaldı

4 sorunun hepsi bilgi hatırlama düzeyinde (Bloom'un ilk basamağı). Bu, Tourigny vd.'nin (2026) bulgusuyla uyumlu: modeller hedeflenen Bloom düzeyinin altında soru üretme eğiliminde. Aşama 8'deki Bloom yönlendirmeli istem ve düzey doğrulaması bu gözlemle gerekçelendirilmiştir.

## Bulgu 4 · Soru yazım kalitesi sorunları (Aşama 9 için not)

- **Olumsuz soru kökü:** Soru 4 *"hangi madde açığa çıkmaz?"* biçiminde. Soru yazım kılavuzlarında kaçınılması önerilen bir kalıp (Arif vd., 2024'teki 19 maddelik listenin kapsamında).
- **Tartışmalı çeldirici:** Soru 4'te "karbon dioksit" şıkkı, bazı kemosentez türleri için tartışılabilir.
- **Zayıf çeldiriciler:** Soru 2'de "Sıcaklık 0°C'dir", "Yüzeyde bulunur" gibi şıklar belirgin biçimde elenebiliyor.

Bu sorunlar Aşama 9'daki otomatik yazım hatası denetiminin ve Aşama 10'daki yeniden üretimin neden gerektiğini gösteriyor.

## Bulgu 5 · Model, alıntıya saniye eklememe kuralına (kural 10) uymadı

İstemin 10. kuralı (`questions_v1_system.txt`) satır başındaki köşeli parantez içindeki saniyenin alıntıya katılmamasını istiyor. Buna rağmen **4 sorunun 4'ünde** alıntı `[sayı]` ile başlıyor.

- Yazılan dört değerin dördü de (124, 219, 591, 806) istemde gerçekten var olan blok etiketleridir; model etiketi transkriptten kopyalıyor.
- Soru 2 (124) ve Soru 4 (806) için etiket alıntının bulunduğu bloğu gösteriyor. Soru 1 (219) için etiket, iki bloğa yayılan alıntının büyük kısmının bulunduğu bloğu gösteriyor. Soru 3 (591) için etiket alıntıyı içermeyen yanlış bir bloğu gösteriyor.
- Model, Soru 1'de alıntının başına transkriptte olmayan bir kelime ("Yani") de ekledi. Bu, "kelimesi kelimesine" kuralının da her zaman uygulanmadığını gösteriyor (Bulgu 2).
- Kural ihlali doğrulamayı bozmadı: temizleme adımı köşeli parantez etiketlerini sildiği için `[591]` normalleştirmede atılıyor ve alıntı yine bulunuyor. Yani ihlal, kodun zamanı modelden değil alıntıdan hesaplaması sayesinde zararsız kaldı.
- Çıkarım: İstemdeki bir yasak, modelin uyacağını garanti etmiyor; kural kodda denetlenmeli ya da etkisiz hale getirilmelidir. Bu, Aşama 9'daki otomatik denetimler için bir gerekçedir.

## Bulgu 6 · Tanıdan sonra yapılan ayarlar

Bu bulgular üzerine alıntı doğrulamasında üç değişiklik yapıldı (`backend/app/services/quotes.py`, testlerde gerçek transkript kesitleri kullanıldı). İstem (`questions-v1`) karşılaştırma için sabit taban çizgisi olarak bırakıldı, değiştirilmedi.

1. **Zaman segment düzeyinde:** `source_start_seconds` artık 30 sn'lik bloğun başlangıcı değil, alıntının başladığı transkript segmentinin başlangıcıdır. Soru 3 için 435,4 → 442,72; Soru 2 için 124,96 → 134,16. Video atlaması cümlenin söylendiği ana birkaç saniye içinde denk gelir.
2. **Kısa alıntı kuralı:** 5 ve üzeri kelime eskisi gibi transkriptte geçmesi yeterli; 3-4 kelimelik alıntı yalnızca transkriptte **tam 1 kez** geçerse doğrulanır; 3 kelimeden kısası hiç doğrulanmaz. Tek geçiş şartı, kısa alıntının tek bir yeri gösterdiğini garanti eder. Soru 4 bu kuralla doğrulanıyor (813,28 sn).
3. **Kenar kırpma:** Alıntı birebir bulunamazsa kenarlarından toplam en fazla 2 kelime kırpılarak yeniden aranır. Kalan parça 1. ve 2. maddedeki kuralları geçmek zorundadır; ortadaki kelime farkları hiçbir zaman kabul edilmez. Kırpılarak bulunan alıntıda `source_quote` transkriptte gerçekten geçen metinle değiştirilir ve yanıtta `quote_match: "trimmed"` yazar. Birebir bulunan alıntıda `quote_match: "exact"` olur. Böylece hangi soruların kırpmayla doğrulandığı sayılabilir. Soru 1 bu kuralla doğrulanıyor (216,84 sn).

Bu ayarlardan sonraki yeniden ölçüm B bölümündedir (4/4). Model yeniden çalıştırılmamıştır.

## Sınırlar

- A ve B bölümleri: tek video, tek çalıştırma, 4 soru; istatistiksel bir sonuç değildir.
- C bölümü (ikinci test): **2 video, 9 soru** (kemosentez 4 + tarih 5), her video için tek çalıştırma; küçük örneklemdir. 6 sorunun zamanı elle kontrol edildi, bunların 4'ünün saniyesi ölçüldü (±1 sn). Kalan 3 sorunun zamanı kontrol edilmedi. Saniye farklarının ortalaması 4 ölçüme dayanır.
- C bölümünde 9 sorunun 9'u doğrulandı. Hiç ret olmadığı için kuralların meşru alıntıyı haksız yere reddetmeme yönü bu testte sınanmadı. Kırpmayla kabul edilen 3 alıntıdan (kemosentez S3, tarih S2 ve S3) yalnızca ikisi C.3'te ayrıca tartışıldı; kırpmanın doğru sözcükleri attığı bu kayıtlardan doğrulanamıyor (bir sonraki madde).
- Çalıştırma kayıtları, doğrulanan sorularda modelin yazdığı özgün alıntıyı değil transkriptteki metni saklıyor. Bu yüzden `trimmed` sorularda modelin alıntıya hangi sözcükleri eklediği bu kayıtlardan görülemiyor.
- **Kurallar bu 4 soruya bakılarak ayarlandı.** 5 kelime sınırı, 3-4 kelimede tek geçiş şartı ve en fazla 2 kelimelik kenar kırpma, aynı dört sorunun tanısından çıkarıldı. B bölümündeki 4/4 sonucu bu yüzden kuralların başarısını göstermez; kurallar ayarlandıkları veriye "uydurulmuş" olabilir. Kurallar başka videolarda ve yeni üretilmiş sorularda ayrıca test edilmelidir. Özellikle izlenmesi gerekenler: haksız yere reddedilen meşru alıntılar ve kırpmayla kabul edilen ama dayanağı zayıf alıntılar.
- B bölümü bir yeniden ölçümdür; model yeniden çalıştırılmadı. Modelin aynı istemle yeniden üreteceği sorular farklı olabilir.
- `verified=true`, sorunun ya da cevabın doğru olduğunu değil, dayandığı alıntının videoda geçtiğini gösterir (C.3 (d) ve (e)).
- Soru kalitesi bu değerlendirmede yalnızca geliştirici tarafından incelenmiştir; öğretmen değerlendirmesi planlanan ölçümlere (Aşama 15) bırakılmıştır.
