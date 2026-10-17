# Aşama 9 · Destek kontrolü denemesi 3

**Amaç:** Alıntı-cevap destek kontrolünün (`services/support_check.py`, istem `support-v1`) verdiği etiketleri, aynı sorular için verilen elle etiketlerle karşılaştırmak.
**Sorular:** 2026-10-17 tarihli dört `/api/questions` kaydındaki alıntısı doğrulanmış 18 soru (matematik `edSvMQ77TmU`, edebiyat `fgOxbhEMnQQ`, python `CEr_UiR4Gvk`, ingilizce `FetnCoTS9qY`; istem `questions-v1`). Kaynak kayıtlar: [genelleme-1-matematik.json](genelleme-1-matematik.json), [genelleme-1-edebiyat.json](genelleme-1-edebiyat.json), [genelleme-1-python.json](genelleme-1-python.json), [genelleme-1-ingilizce.json](genelleme-1-ingilizce.json) ([genelleme denemesi 1](genelleme-denemesi-1.md)). Sorular yeniden üretilmez.
**Etiketler:** destekliyor (alıntı doğru cevabı doğrudan söylüyor) / kısmen (ilgili ama cevabı doğrudan vermiyor ya da dolaylı) / desteklemiyor (alıntıdan cevap çıkarılamıyor).

> Durum: elle etiketler model çağrısından önce verildi ve commit'lendi (`945ef52`). Model etiketleri sonra, tek çalıştırmayla alındı; sonuç değiştirilmeden kaydedildi.

**Elle etiketleme yöntemi:**
- Etiketler kullanıcı tarafından, yalnızca doğrulanmış kaynak alıntısına bakılarak verildi.
- Ölçüt: "Yalnızca doğrulanmış alıntıyı okuyan biri doğru cevabı çıkarabilir mi?" Alıntıdaki yazım hataları etiketi düşürmedi.
- Videoya bakılmadı.
- Etiketleyen tek kişi (kullanıcı); etiketler model sonuçları görülmeden verildi ve model çağrısından önce commit'lendi.

**Elle etiket özeti (18 soru):** 14 destekliyor, 3 desteklemiyor, 1 belirsiz (ingilizce S3).

**Tabloya alınmayanlar:** alıntısı transkriptte bulunamayan 2 soru (matematik S3, ingilizce S5); destek kontrolü bunlar için çağrı yapmaz; bu denemenin kapsamı dışındadır.

| # | Soru | Doğru cevap | Kaynak alıntısı | Kaynak süresi | Alıntı eşleşmesi (quote_match) | Elle etiket (destekliyor/kısmen/desteklemiyor) | Model etiketi | Etiket eşleşmesi |
|---|---|---|---|---|---|---|---|---|
| matematik S1 | Açıortay teoremi neyi ifade eder? | Bir açının kollarının oranı | C'nin X'e oranı, yani sağ bölü sağ parça B'nin Y'ye oranına eşit, | 1:47 (107,68 sn) | exact | destekliyor | kısmen | farklı |
| matematik S2 | İç açıortay teoremi hangi durumlarda kullanılır? | Açıortay çizildiğinde | açıortay teoremi aklına gelecek. | 5:50 (350,28 sn) | exact | desteklemiyor | desteklemiyor | aynı |
| matematik S4 | Açıortay teoremi ispatında hangi yöntem önerilmektedir? | Eşlik benzerlik yöntemi | bence en anlaşılırı pek çok teoremde olduğu gibi eşlik benzerlik yöntemiyle ispatlamak | 2:44 (164,48 sn) | exact | destekliyor | destekliyor | aynı |
| matematik S5 | Açıortay teoremi uygulandığında hangi oranlar eşit olur? | Kenar uzunlukları | C'nin X'e oranı B'nin Y'ye oranına | 5:17 (317,44 sn) | trimmed | desteklemiyor | kısmen | farklı |
| edebiyat S1 | Milli Edebiyat Dönemi'nin temel özelliklerinden biri nedir? | Halka yönelme | Milli Edebiyat yani milliyetçi bir edebiyat. Kendi toprağımızdan doğan, halka yönelen bir edebiyat. | 0:13 (13,44 sn) | exact | destekliyor | destekliyor | aynı |
| edebiyat S2 | Milli Edebiyat Dönemi'nde hangi dil anlayışı benimsenmiştir? | Sade Türkçe | Sade Türkçe, ağır ve süslü dilden kaçınılmış, halka yakın, anlaşılır bir dil kullanılacak. | 1:23 (83,28 sn) | exact | destekliyor | destekliyor | aynı |
| edebiyat S3 | Milli Edebiyat Dönemi'nde hangi akım ön plana çıkmıştır? | Türkçülük | Türkçülük ise bütün Türkleri bir araya toplamaktır, kültür, dil ve fikir birliği sağlamaktır. | 8:12 (492,36 sn) | exact | destekliyor | destekliyor | aynı |
| edebiyat S4 | Milli Edebiyat Dönemi'nde eserlerinde Anadolu insanını konu alan yazar kimdir? | Refik Halit Karay | Refik Halit Karay Anadolu'ya yönelecek ve Memleket Hikayelerini yazacak. | 11:37 (697,64 sn) | exact | destekliyor | destekliyor | aynı |
| edebiyat S5 | Milli Edebiyat Dönemi'nde hangi tür hikaye yazılmaktadır? | Olay hikayesi | Olay hikayesi deyince aklımıza Ömer Seyfettin, durum hikayesi deyince de Memduh Şevket Esendal gelmesi lazım. | 10:22 (622,92 sn) | exact | desteklemiyor | kısmen | farklı |
| python S1 | Python hangi yıl yayınlanmıştır? | 1991 | python popüler bir programlama dilidir ve guido One rossum tarafından yaratılmış ve 1991'de yayınlanmıştır | 1:05 (65,519 sn) | exact | destekliyor | destekliyor | aynı |
| python S2 | Python hangi sürümünü bu eğitimde kullanacağını belirtmiştir? | Python 3.13 | bu eğitimde kullanacağımız python 3'tür python 3.13 sürümünü kullanacağım | 3:11 (191,319 sn) | exact | destekliyor | destekliyor | aynı |
| python S3 | Python ile hangi alanda çalışmalar yapılabilir? | Veri analizi | python' kullanır bakın pandas non python mat plot lip gibi kütüphaneler sayesinde veri setleri üzerinde kolaylıkla analiz yapılabiliyor | 5:58 (358,759 sn) | exact | destekliyor | destekliyor | aynı |
| python S4 | Python'un ilk resmi sürümü ne zaman çıkmıştır? | 1994 | ilk res sürümü Ocak 1994'te geldi | 3:58 (238,159 sn) | trimmed | destekliyor | destekliyor | aynı |
| python S5 | Python 2'nin son sürümü ne zaman çıkmıştır? | 2010 | 2010'a geldiğimizde python' artık python 2'nin sonuna doğru gelmiş olduk | 4:15 (255,0 sn) | exact | destekliyor | kısmen | farklı |
| ingilizce S1 | Yüz kalıbı hangi durumlarda kullanılır? | Geçmişte sürekli yapılan ama artık yapılmayan eylemler için | yüz kalıbı şu amaçlarla kullanılır geçmişte sürekli olarak yapılan Ama artık yapılmayan eylemleriniz den yada alışkanlıklarınızdan bahsedecek siniz | 5:04 (304,98 sn) | exact | destekliyor | destekliyor | aynı |
| ingilizce S2 | Yüz kalıbının olumsuz hali nasıl oluşturulur? | Özne + didn't + yüz ifadesi | Eğer yüz kalıbını kullanarak olumsuz bir cümle bu istiyorsak şu kalıplara dikkat etmeliyiz Biz cümleyi bir özne ile başlarız ay ve Yuh Bey he she it özel lerinden biri Tabletimi yazdıktan sonra negatifi geçiyor lan did kelimesini kullanırız | 7:47 (467,649 sn) | exact | destekliyor | kısmen | farklı |
| ingilizce S3 | Yüz kalıbı ile soru cümlesi oluştururken hangi ifade cümlenin başında yer alır? | Did | Eğer yüz ifadesini soru yapacaksak şu kurallara dikkat etmeliyiz Biz sürekli olarak cümlenin başında da ifadesini kullanırız | 10:12 (612,71 sn) | exact | belirsiz (emin değilim) | desteklemiyor | sayım dışı |
| ingilizce S4 | Yüz kalıbı ile olumlu bir cümle kurmak için hangi özne kullanılmaz? | It | o anlamına gelir it cansız hayvan ürünlerinde kullanılır o anlamına | 5:56 (356,139 sn) | exact | destekliyor | desteklemiyor | farklı |

## Model çalıştırması

- **Ham sonuç:** [asama-9-destek-kontrolu-3.json](asama-9-destek-kontrolu-3.json) (ilk ve tek çalıştırma, değiştirilmeden).
- **Betik:** [asama-9-destek-kontrolu-3.py](asama-9-destek-kontrolu-3.py). Sorular yeniden üretilmeden doğrudan `check_support` fonksiyonuna verildi. Çalıştırmadan önce, betikteki çağrı sayacının (`CountingLLM`) arayüzü sahte istemcilerle (API'ye gitmeden) denetlendi.
- 2026-10-17 19:31:14–19:31:33 (+03:00), model gpt-4o-mini, istem `support-v1`, 18 çağrı (beklenen 18, yapılan 18). Doğrulanamayan 2 soru için çağrı yapılmadı ("kontrol edilmedi").
- Kod commit'i `945ef52`. İstem dosyalarının SHA256 özetleri 1. ve 2. denemedekiyle aynı (`support-v1` değişmedi). Kaynak kayıtların özetleri JSON'da.

**Eşleşme (bu deneme):** sayıma giren 17 soruda tam eşleşme 11, farklı 6.

| Elle etiket → Model etiketi | Sayı | Sorular |
|---|---|---|
| destekliyor → kısmen | 3 | Deneme 3 · matematik S1; Deneme 3 · python S5; Deneme 3 · ingilizce S2 |
| desteklemiyor → kısmen | 2 | Deneme 3 · matematik S5; Deneme 3 · edebiyat S5 |
| destekliyor → desteklemiyor | 1 | Deneme 3 · ingilizce S4 |

**Sayım dışı:** ingilizce S3 · elle "belirsiz (emin değilim)", model "desteklemiyor".

| # | Elle etiket | Model etiketi | Model gerekçesi |
|---|---|---|---|
| matematik S1 | destekliyor | kısmen | Alıntı, oranlardan bahsediyor ancak açının kollarının oranı ifadesini doğrudan vermiyor. |
| matematik S2 | desteklemiyor | desteklemiyor | Alıntıda açıortay teoreminin kullanımıyla ilgili bir bilgi yok. |
| matematik S4 | destekliyor | destekliyor | Alıntıda eşlik benzerlik yöntemiyle ispatlama önerilmektedir. |
| matematik S5 | desteklemiyor | kısmen | Alıntı, oranlar hakkında bilgi veriyor ancak doğrudan kenar uzunlukları ile ilgili değil. |
| edebiyat S1 | destekliyor | destekliyor | Alıntıda halka yönelme ifadesi doğrudan geçmektedir. |
| edebiyat S2 | destekliyor | destekliyor | Alıntıda Sade Türkçe'nin tanımı ve kullanım amacı belirtilmiştir. |
| edebiyat S3 | destekliyor | destekliyor | Alıntıda Türkçülüğün önemi vurgulanmaktadır. |
| edebiyat S4 | destekliyor | destekliyor | Alıntıda Refik Halit Karay'ın Anadolu'ya yöneldiği ve eserler yazdığı belirtiliyor. |
| edebiyat S5 | desteklemiyor | kısmen | Alıntıda olay hikayesinin örneği verilmiş, ancak bu türün yazıldığına dair doğrudan bir ifade yok. |
| python S1 | destekliyor | destekliyor | Alıntıda Python'un 1991'de yayınlandığı belirtiliyor. |
| python S2 | destekliyor | destekliyor | Alıntıda Python 3.13 sürümünün kullanılacağı belirtiliyor. |
| python S3 | destekliyor | destekliyor | Alıntıda veri setleri üzerinde analiz yapılabileceği belirtiliyor. |
| python S4 | destekliyor | destekliyor | Alıntıda Python'un ilk resmi sürümünün Ocak 1994'te çıktığı belirtiliyor. |
| python S5 | destekliyor | kısmen | Alıntı, Python 2'nin 2010 yılına doğru geldiğini belirtiyor ama kesin bir tarih vermiyor. |
| ingilizce S1 | destekliyor | destekliyor | Alıntıda yüz kalıbının geçmişte sürekli yapılan ama artık yapılmayan eylemler için kullanıldığı belirtiliyor. |
| ingilizce S2 | destekliyor | kısmen | Alıntıda yüz kalıbının olumsuz hali için 'did' kelimesinin kullanılması gerektiği belirtiliyor, ancak tam cümle yapısı verilmemiş. |
| ingilizce S3 | belirsiz (emin değilim) | desteklemiyor | Alıntıda cümlenin başında yer alacak ifade belirtilmemiş. |
| ingilizce S4 | destekliyor | desteklemiyor | Alıntıda 'it' öznesinin kullanılmamasıyla ilgili bir bilgi yok. |

## Deneme 1, 2 ve 3 birleşik

Deneme 1: [asama-9-destek-kontrolu-1.md](asama-9-destek-kontrolu-1.md) (5 soru). Deneme 2: [asama-9-destek-kontrolu-2.md](asama-9-destek-kontrolu-2.md) (9 soru). Deneme 3: bu dosya (18 soru). Üç deneme aynı model ve istemle (`support-v1`) ve aynı ölçütle yapıldı.

**Eşleşme:** sayıma giren 31 soruda tam eşleşme 21, farklı 10. Sayım dışı 1 soru: Deneme 3 · ingilizce S3 (elle belirsiz).

| Elle etiket → Model etiketi | Sayı | Sorular |
|---|---|---|
| destekliyor → kısmen | 3 | Deneme 3 · matematik S1; Deneme 3 · python S5; Deneme 3 · ingilizce S2 |
| kısmen → desteklemiyor | 2 | Deneme 1 · 12d S2; Deneme 2 · tarih S2 |
| destekliyor → desteklemiyor | 2 | Deneme 1 · 12d S5; Deneme 3 · ingilizce S4 |
| desteklemiyor → kısmen | 2 | Deneme 3 · matematik S5; Deneme 3 · edebiyat S5 |
| kısmen → destekliyor | 1 | Deneme 2 · kemosentez S2 |

| Deneme | # | Soru | Elle etiket | Model etiketi | Etiket eşleşmesi |
|---|---|---|---|---|---|
| Deneme 1 | 12d S1 | Kemosentetik canlılar hangi enerji kaynağını kullanarak besin üretirler? | destekliyor | destekliyor | aynı |
| Deneme 1 | 12d S2 | Hidrotermal bacaların etrafında hangi canlılar yaşayabilir? | kısmen | desteklemiyor | farklı |
| Deneme 1 | 12d S3 | Kemosentez sırasında hangi madde açığa çıkmaz? | destekliyor | destekliyor | aynı |
| Deneme 1 | 12d S4 | Kemosentetik canlıların hücre yapısı nedir? | destekliyor | destekliyor | aynı |
| Deneme 1 | 12d S5 | Kemosentez hangi koşullarda gerçekleşebilir? | destekliyor | desteklemiyor | farklı |
| Deneme 2 | kemosentez S1 | Kemosentetik canlılar hangi enerji kaynağını kullanarak besin üretimi gerçekleştirir? | destekliyor | destekliyor | aynı |
| Deneme 2 | kemosentez S2 | Hidrotermal bacaların bulunduğu ortamda hangi canlılar yaşayabilir? | kısmen | destekliyor | farklı |
| Deneme 2 | kemosentez S3 | Kemosentez sırasında hangi madde açığa çıkmaz? | destekliyor | destekliyor | aynı |
| Deneme 2 | kemosentez S4 | Kemosentetik canlıların hücre yapısı nedir? | destekliyor | destekliyor | aynı |
| Deneme 2 | tarih S1 | Malazgirt Savaşı hangi yıllarda gerçekleşmiştir? | destekliyor | destekliyor | aynı |
| Deneme 2 | tarih S2 | Danışmentlilerin kurulduğu bölgeler arasında hangisi yer almaz? | kısmen | desteklemiyor | farklı |
| Deneme 2 | tarih S3 | Kösedağ Savaşı'nda Türkiye Selçuklu Devleti kime karşı savaşmıştır? | destekliyor | destekliyor | aynı |
| Deneme 2 | tarih S4 | Mir Kefalon Savaşı'nın önemi nedir? | destekliyor | destekliyor | aynı |
| Deneme 2 | tarih S5 | 1. Haçlı Seferi'nin temel amacı nedir? | destekliyor | destekliyor | aynı |
| Deneme 3 | matematik S1 | Açıortay teoremi neyi ifade eder? | destekliyor | kısmen | farklı |
| Deneme 3 | matematik S2 | İç açıortay teoremi hangi durumlarda kullanılır? | desteklemiyor | desteklemiyor | aynı |
| Deneme 3 | matematik S4 | Açıortay teoremi ispatında hangi yöntem önerilmektedir? | destekliyor | destekliyor | aynı |
| Deneme 3 | matematik S5 | Açıortay teoremi uygulandığında hangi oranlar eşit olur? | desteklemiyor | kısmen | farklı |
| Deneme 3 | edebiyat S1 | Milli Edebiyat Dönemi'nin temel özelliklerinden biri nedir? | destekliyor | destekliyor | aynı |
| Deneme 3 | edebiyat S2 | Milli Edebiyat Dönemi'nde hangi dil anlayışı benimsenmiştir? | destekliyor | destekliyor | aynı |
| Deneme 3 | edebiyat S3 | Milli Edebiyat Dönemi'nde hangi akım ön plana çıkmıştır? | destekliyor | destekliyor | aynı |
| Deneme 3 | edebiyat S4 | Milli Edebiyat Dönemi'nde eserlerinde Anadolu insanını konu alan yazar kimdir? | destekliyor | destekliyor | aynı |
| Deneme 3 | edebiyat S5 | Milli Edebiyat Dönemi'nde hangi tür hikaye yazılmaktadır? | desteklemiyor | kısmen | farklı |
| Deneme 3 | python S1 | Python hangi yıl yayınlanmıştır? | destekliyor | destekliyor | aynı |
| Deneme 3 | python S2 | Python hangi sürümünü bu eğitimde kullanacağını belirtmiştir? | destekliyor | destekliyor | aynı |
| Deneme 3 | python S3 | Python ile hangi alanda çalışmalar yapılabilir? | destekliyor | destekliyor | aynı |
| Deneme 3 | python S4 | Python'un ilk resmi sürümü ne zaman çıkmıştır? | destekliyor | destekliyor | aynı |
| Deneme 3 | python S5 | Python 2'nin son sürümü ne zaman çıkmıştır? | destekliyor | kısmen | farklı |
| Deneme 3 | ingilizce S1 | Yüz kalıbı hangi durumlarda kullanılır? | destekliyor | destekliyor | aynı |
| Deneme 3 | ingilizce S2 | Yüz kalıbının olumsuz hali nasıl oluşturulur? | destekliyor | kısmen | farklı |
| Deneme 3 | ingilizce S3 | Yüz kalıbı ile soru cümlesi oluştururken hangi ifade cümlenin başında yer alır? | belirsiz (emin değilim) | desteklemiyor | sayım dışı |
| Deneme 3 | ingilizce S4 | Yüz kalıbı ile olumlu bir cümle kurmak için hangi özne kullanılmaz? | destekliyor | desteklemiyor | farklı |

## Sınırlar

- ingilizce S3 için kullanıcı üç etiketten birini seçmedi ("belirsiz (emin değilim)"). Bu soru eşleşme sayımına dahil edilmedi; model çağrısı yine yapıldı ve sonucu kaydedildi (model: desteklemiyor).
- Tek etiketleyen.
- 4 video, her biri tek çalıştırma.
- Deneme 1 ve 2 ile aynı model (gpt-4o-mini) ve istem (`support-v1`).
- Sorular bağımsız değil: aynı videodan 5'er soru (doğrulanmış olarak 4-5).
- Transkriptlerde yazım hataları var: "yüz" / "used to", "guido One rossum", "mat plot lip". Alıntılar bu yazımlarla değerlendirildi.
- Modelin sıcaklığı 0,2; aynı istemle yeniden çalıştırma farklı etiket verebilir. Her deneme için yalnızca ilk çalıştırma kaydedildi.
- Birleşik tablodaki 32 sorunun 9'u aynı kemosentez videosundan (Deneme 1'den 5, Deneme 2'den 4), 5'i tarih videosundan, 18'i Deneme 3'ün dört videosundan (video başına 4-5) gelir. Sorular birbirinden bağımsız değildir.
