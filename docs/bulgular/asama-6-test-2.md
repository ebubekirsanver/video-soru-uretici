# Aşama 6 · Test 2 bulguları

**Tarih:** 12 Ekim 2026
**Test:** `POST /api/questions` · iki video: `109kCbVtU1U` (kemosentez) ve `aaCHLYO3Fzg` (tarih) · `count: 5` · `transcript_mode: clean`
**Model / istem:** gpt-4o-mini · `questions-v1` (RAG'siz taban çizgisi)
**Ham sonuçlar:** [asama-6-test-2-kemosentez.json](asama-6-test-2-kemosentez.json) · [asama-6-test-2-tarih.json](asama-6-test-2-tarih.json)

> Karşılaştırma için bkz. [Test 1](asama-6-test-1.md): aynı kemosentez videosunun kural değişikliklerinden önceki ilk çalıştırması (A) ve aynı 4 sorunun yeni kurallarla yeniden ölçümü (B). Bu dosyadaki bölüm adları (C, C.1–C.3) Test 1 dosyasında kullanılan adlarla aynı bırakılmıştır.
## C · İkinci test (kural değişikliklerinden sonra)

> Bunlar, [Test 1, Bulgu 6](asama-6-test-1.md#bulgu-6--tanıdan-sonra-yapılan-ayarlar)'daki kural değişikliklerinden **sonraki ilk gerçek çalıştırmalardır**. Model yeni sorular üretti; [Test 1'in B bölümündeki](asama-6-test-1.md#b--yeniden-ölçüm-kural-değişikliklerinden-sonra) yeniden ölçümden farklı olarak bu bir yeni çalıştırmadır. Ayarlar: `count: 5`, `transcript_mode: clean`, gpt-4o-mini, `questions-v1`. Ham yanıtlar `backend/runs/` kayıtlarının birebir kopyasıdır.

**Tablo sütunları:**
- *Kelime:* `source_quote`'un normalleştirilmiş kelime sayısı. Güncel kodda `source_quote`, transkriptte bulunan metindir; `trimmed` sorularda bu, kırpılmış hâldir.
- *Elle zaman kontrolü:* Kullanıcının videoda gözle okuduğu cümle başlangıcıdır (hassasiyet yaklaşık ±1 sn). Boş hücre, o sorunun zamanının elle kontrol edilmediği anlamına gelir.

### C.1 · Kemosentez videosu (`109kCbVtU1U`)

Ham yanıt: [asama-6-test-2-kemosentez.json](asama-6-test-2-kemosentez.json). İstenen 5, dönen 4, doğrulanan 4/4.

| # | Soru | `verified` | `quote_match` | `source_start_seconds` | Kelime | Elle zaman kontrolü |
|---|---|---|---|---|---|---|
| 1 | Kemosentetik canlılar hangi enerji kaynağını kullanarak besin üretimi gerçekleştirir? | true | exact | 568,959 (9:28) | 18 | Cümle 9:31'de (571 sn); kod ~2,0 sn önde. Aynı alıntı ve zaman önceki bir çalıştırmada da çıktı, ölçüm o zaman yapıldı. |
| 2 | Hidrotermal bacaların bulunduğu ortamda hangi canlılar yaşayabilir? | true | exact | 247,64 (4:07) | 16 | Cümle 4:13'te (253 sn); kod ~5,4 sn önde |
| 3 | Kemosentez sırasında hangi madde açığa çıkmaz? | true | trimmed | 1175,919 (19:35) | 3 | Zaman doğru (saniyesi ölçülmedi) |
| 4 | Kemosentetik canlıların hücre yapısı nedir? | true | exact | 442,72 (7:22) | 6 | |

### C.2 · Tarih videosu (`aaCHLYO3Fzg`)

Ham yanıt: [asama-6-test-2-tarih.json](asama-6-test-2-tarih.json). İstenen 5, dönen 5, doğrulanan 5/5.

| # | Soru | `verified` | `quote_match` | `source_start_seconds` | Kelime | Elle zaman kontrolü |
|---|---|---|---|---|---|---|
| 1 | Malazgirt Savaşı hangi yıllarda gerçekleşmiştir? | true | exact | 79,52 (1:19) | 5 | Cümle 1:21'de (81 sn); kod ~1,5 sn önde. Aynı alıntı ve zaman önceki bir çalıştırmada da çıktı, ölçüm o zaman yapıldı. |
| 2 | Danışmentlilerin kurulduğu bölgeler arasında hangisi yer almaz? | true | trimmed | 244,319 (4:04) | 10 | Cümle 4:06'da (246 sn); kod ~1,7 sn önde |
| 3 | Kösedağ Savaşı'nda Türkiye Selçuklu Devleti kime karşı savaşmıştır? | true | trimmed | 1786,96 (29:46) | 7 | Zaman doğru (saniyesi ölçülmedi) |
| 4 | Mir Kefalon Savaşı'nın önemi nedir? | true | exact | 1740,36 (29:00) | 13 | |
| 5 | 1. Haçlı Seferi'nin temel amacı nedir? | true | exact | 607,279 (10:07) | 8 | |

Dakika:saniye gösteriminde saniye aşağı yuvarlanmıştır (YouTube'daki gibi).

### C.3 · İkinci test bulguları

**(a) Zaman hassasiyeti.** Elle kontrol edilen 6 zamanın 6'sı doğru yere düşüyor. Saniyesi ölçülen 4 sorunun dördünde de kod, cümleden **önce** başlatıyor. Fark 1,5 ile 5,4 sn arasında, ortalaması yaklaşık **2,6 sn**. Kesin farklar 2,04 / 5,36 / 1,48 / 1,68 sn, ortalaması 2,64; ölçüm hassasiyeti ±1 sn olduğu için ondalık kesin değildir. Bu, segment çözünürlüğünün doğal sonucudur: alıntı bir segmentin ortasında başladığında kod segmentin başını verir. Örneğin kemosentez S1'in segmenti (568,959 sn) *"gidiyoruz zaten. Yani şimdi kemosentez"* metniyle başlıyor; alıntı bu segmentin son kelimesinden başlıyor. Önceki blok tabanlı hesapta fark, ilk testin Soru 3'ünde yaklaşık 7,3 sn idi ([Test 1, Bulgu 1](asama-6-test-1.md#bulgu-1--zamanı-modelden-değil-alıntıdan-hesaplamak-doğru-karardı)). Video önce başladığı için öğrenci cümleyi kaçırmaz, yalnızca birkaç saniye bekler.

**(b) Çıktı belirsizliği.** Aynı kemosentez videosunda ikinci çalıştırma farklı sorular üretti, bazıları tekrar etti:
- *"Kemosentez sırasında hangi madde açığa çıkmaz?"* iki çalıştırmada da **birebir aynı** metinle çıktı. Alıntısı farklı: ilk testte *"Kemosentezde oksijen açığa çıkmıyormuş."*, burada *"oksijen üretilmez demiştim."*
- İki soru aynı konuyu farklı sözcüklerle tekrarladı: ilk testin Soru 1'i ile buradaki S1 (enerji kaynağı), ilk testin Soru 3'ü ile buradaki S4 (hücre yapısı; aynı alıntı ve aynı 442,72 sn).
- Hidrotermal baca konusu her iki çalıştırmada da var, ama soru ve alıntı farklı.

**(c) Olumsuz soru kökü iki farklı videoda çıktı:** kemosentez S3 *"…açığa çıkmaz?"*, tarih S2 *"…yer almaz?"*. İlk testteki aynı gözlemle ([Test 1, Bulgu 4](asama-6-test-1.md#bulgu-4--soru-yazım-kalitesi-sorunları-aşama-9-için-not)) birlikte bu, kalıbın tek seferlik olmadığını gösteriyor (Aşama 9'daki yazım denetimi için).

**(d) Alıntı doğrulaması cevabı kanıtlamıyor (tarih S2).** Doğru cevap "İzmir", ama alıntı (*"Tokat, Amasya, Kayseri, Sivas, Malatya bu bölgelere yayılmış bir beylik."*) yalnızca diğer şıkları içeriyor. Soru olumsuz köklü olduğu için doğru cevap zaten alıntıda geçmeyen şıktır. `verified=true` yalnızca alıntının videoda geçtiğini gösterir; cevabın alıntıdan çıkarılabilir olduğunu göstermez. Sadakat denetimi Aşama 9'da yapılacak.

**(e) Alıntı ile cevap tam örtüşmüyor (kemosentez S2).** Alıntı *"…kemosentez yapan bakterilerle beslenen farklı biyolojik canlılara rastlanabilir"* diyor; yani baca çevresindeki canlılar kemosentetik bakterilerle beslenen canlılardır. Doğru cevap ise "Kemosentetik canlılar". Alıntı cevabı destekliyor ama aynı şeyi söylemiyor. Bu da (d) ile aynı sınıfta, alıntı–cevap tutarlılığı sorunudur.

**(f) 3 kelimelik kırpılmış alıntı işe yaradı (kemosentez S3).** *"oksijen üretilmez demiştim."* yeni kuralların izin verdiği en kısa biçim: kırpılmış, 3 kelime, transkriptte tek geçiş. Doğrulandı ve zamanı elle kontrolde doğru çıktı. Tek örnektir; kuralın genel olarak güvenilir olduğunu göstermez.

**(g) Küçük dil sorunu (tarih S1).** *"Malazgirt Savaşı hangi yıllarda gerçekleşmiştir?"* tek bir yıl (1071) soruluyorken çoğul "yıllarda" kullanıyor.

## Sınırlar

- C bölümü (ikinci test): **2 video, 9 soru** (kemosentez 4 + tarih 5), her video için tek çalıştırma; küçük örneklemdir. 6 sorunun zamanı elle kontrol edildi, bunların 4'ünün saniyesi ölçüldü (±1 sn). Kalan 3 sorunun zamanı kontrol edilmedi. Saniye farklarının ortalaması 4 ölçüme dayanır.
- C bölümünde 9 sorunun 9'u doğrulandı. Hiç ret olmadığı için kuralların meşru alıntıyı haksız yere reddetmeme yönü bu testte sınanmadı. Kırpmayla kabul edilen 3 alıntıdan (kemosentez S3, tarih S2 ve S3) yalnızca ikisi C.3'te ayrıca tartışıldı; kırpmanın doğru sözcükleri attığı bu kayıtlardan doğrulanamıyor (bir sonraki madde).
- Çalıştırma kayıtları, doğrulanan sorularda modelin yazdığı özgün alıntıyı değil transkriptteki metni saklıyor. Bu yüzden `trimmed` sorularda modelin alıntıya hangi sözcükleri eklediği bu kayıtlardan görülemiyor.
