# Aşama 9 · Destek kontrolü denemesi 3

**Amaç:** Alıntı-cevap destek kontrolünün (`services/support_check.py`, istem `support-v1`) verdiği etiketleri, aynı sorular için verilen elle etiketlerle karşılaştırmak.
**Sorular:** 2026-10-17 tarihli dört `/api/questions` kaydındaki alıntısı doğrulanmış 18 soru (matematik `edSvMQ77TmU`, edebiyat `fgOxbhEMnQQ`, python `CEr_UiR4Gvk`, ingilizce `FetnCoTS9qY`; istem `questions-v1`). Kaynak kayıtlar: [genelleme-1-matematik.json](genelleme-1-matematik.json), [genelleme-1-edebiyat.json](genelleme-1-edebiyat.json), [genelleme-1-python.json](genelleme-1-python.json), [genelleme-1-ingilizce.json](genelleme-1-ingilizce.json) ([genelleme denemesi 1](genelleme-denemesi-1.md)). Sorular yeniden üretilmez.
**Etiketler:** destekliyor (alıntı doğru cevabı doğrudan söylüyor) / kısmen (ilgili ama cevabı doğrudan vermiyor ya da dolaylı) / desteklemiyor (alıntıdan cevap çıkarılamıyor).

> Durum: elle etiketler verildi; model etiketleri henüz alınmadı (model çağrısı yapılmadı).

**Elle etiketleme yöntemi:**
- Etiketler kullanıcı tarafından, yalnızca doğrulanmış kaynak alıntısına bakılarak verildi.
- Ölçüt: "Yalnızca doğrulanmış alıntıyı okuyan biri doğru cevabı çıkarabilir mi?" Alıntıdaki yazım hataları etiketi düşürmedi.
- Videoya bakılmadı.
- Etiketleyen tek kişi (kullanıcı); etiketler model sonuçları görülmeden verildi ve model çağrısından önce commit'lendi.

**Elle etiket özeti (18 soru):** 14 destekliyor, 3 desteklemiyor, 1 belirsiz (ingilizce S3).

**Tabloya alınmayanlar:** alıntısı transkriptte bulunamayan 2 soru (matematik S3, ingilizce S5); destek kontrolü bunlar için çağrı yapmaz; bu denemenin kapsamı dışındadır.

| # | Soru | Doğru cevap | Kaynak alıntısı | Kaynak süresi | Alıntı eşleşmesi (quote_match) | Elle etiket (destekliyor/kısmen/desteklemiyor) | Model etiketi |
|---|---|---|---|---|---|---|---|
| matematik S1 | Açıortay teoremi neyi ifade eder? | Bir açının kollarının oranı | C'nin X'e oranı, yani sağ bölü sağ parça B'nin Y'ye oranına eşit, | 1:47 (107,68 sn) | exact | destekliyor |  |
| matematik S2 | İç açıortay teoremi hangi durumlarda kullanılır? | Açıortay çizildiğinde | açıortay teoremi aklına gelecek. | 5:50 (350,28 sn) | exact | desteklemiyor |  |
| matematik S4 | Açıortay teoremi ispatında hangi yöntem önerilmektedir? | Eşlik benzerlik yöntemi | bence en anlaşılırı pek çok teoremde olduğu gibi eşlik benzerlik yöntemiyle ispatlamak | 2:44 (164,48 sn) | exact | destekliyor |  |
| matematik S5 | Açıortay teoremi uygulandığında hangi oranlar eşit olur? | Kenar uzunlukları | C'nin X'e oranı B'nin Y'ye oranına | 5:17 (317,44 sn) | trimmed | desteklemiyor |  |
| edebiyat S1 | Milli Edebiyat Dönemi'nin temel özelliklerinden biri nedir? | Halka yönelme | Milli Edebiyat yani milliyetçi bir edebiyat. Kendi toprağımızdan doğan, halka yönelen bir edebiyat. | 0:13 (13,44 sn) | exact | destekliyor |  |
| edebiyat S2 | Milli Edebiyat Dönemi'nde hangi dil anlayışı benimsenmiştir? | Sade Türkçe | Sade Türkçe, ağır ve süslü dilden kaçınılmış, halka yakın, anlaşılır bir dil kullanılacak. | 1:23 (83,28 sn) | exact | destekliyor |  |
| edebiyat S3 | Milli Edebiyat Dönemi'nde hangi akım ön plana çıkmıştır? | Türkçülük | Türkçülük ise bütün Türkleri bir araya toplamaktır, kültür, dil ve fikir birliği sağlamaktır. | 8:12 (492,36 sn) | exact | destekliyor |  |
| edebiyat S4 | Milli Edebiyat Dönemi'nde eserlerinde Anadolu insanını konu alan yazar kimdir? | Refik Halit Karay | Refik Halit Karay Anadolu'ya yönelecek ve Memleket Hikayelerini yazacak. | 11:37 (697,64 sn) | exact | destekliyor |  |
| edebiyat S5 | Milli Edebiyat Dönemi'nde hangi tür hikaye yazılmaktadır? | Olay hikayesi | Olay hikayesi deyince aklımıza Ömer Seyfettin, durum hikayesi deyince de Memduh Şevket Esendal gelmesi lazım. | 10:22 (622,92 sn) | exact | desteklemiyor |  |
| python S1 | Python hangi yıl yayınlanmıştır? | 1991 | python popüler bir programlama dilidir ve guido One rossum tarafından yaratılmış ve 1991'de yayınlanmıştır | 1:05 (65,519 sn) | exact | destekliyor |  |
| python S2 | Python hangi sürümünü bu eğitimde kullanacağını belirtmiştir? | Python 3.13 | bu eğitimde kullanacağımız python 3'tür python 3.13 sürümünü kullanacağım | 3:11 (191,319 sn) | exact | destekliyor |  |
| python S3 | Python ile hangi alanda çalışmalar yapılabilir? | Veri analizi | python' kullanır bakın pandas non python mat plot lip gibi kütüphaneler sayesinde veri setleri üzerinde kolaylıkla analiz yapılabiliyor | 5:58 (358,759 sn) | exact | destekliyor |  |
| python S4 | Python'un ilk resmi sürümü ne zaman çıkmıştır? | 1994 | ilk res sürümü Ocak 1994'te geldi | 3:58 (238,159 sn) | trimmed | destekliyor |  |
| python S5 | Python 2'nin son sürümü ne zaman çıkmıştır? | 2010 | 2010'a geldiğimizde python' artık python 2'nin sonuna doğru gelmiş olduk | 4:15 (255,0 sn) | exact | destekliyor |  |
| ingilizce S1 | Yüz kalıbı hangi durumlarda kullanılır? | Geçmişte sürekli yapılan ama artık yapılmayan eylemler için | yüz kalıbı şu amaçlarla kullanılır geçmişte sürekli olarak yapılan Ama artık yapılmayan eylemleriniz den yada alışkanlıklarınızdan bahsedecek siniz | 5:04 (304,98 sn) | exact | destekliyor |  |
| ingilizce S2 | Yüz kalıbının olumsuz hali nasıl oluşturulur? | Özne + didn't + yüz ifadesi | Eğer yüz kalıbını kullanarak olumsuz bir cümle bu istiyorsak şu kalıplara dikkat etmeliyiz Biz cümleyi bir özne ile başlarız ay ve Yuh Bey he she it özel lerinden biri Tabletimi yazdıktan sonra negatifi geçiyor lan did kelimesini kullanırız | 7:47 (467,649 sn) | exact | destekliyor |  |
| ingilizce S3 | Yüz kalıbı ile soru cümlesi oluştururken hangi ifade cümlenin başında yer alır? | Did | Eğer yüz ifadesini soru yapacaksak şu kurallara dikkat etmeliyiz Biz sürekli olarak cümlenin başında da ifadesini kullanırız | 10:12 (612,71 sn) | exact | belirsiz (emin değilim) |  |
| ingilizce S4 | Yüz kalıbı ile olumlu bir cümle kurmak için hangi özne kullanılmaz? | It | o anlamına gelir it cansız hayvan ürünlerinde kullanılır o anlamına | 5:56 (356,139 sn) | exact | destekliyor |  |

## Sınırlar

- ingilizce S3 için kullanıcı üç etiketten birini seçmedi ("belirsiz (emin değilim)"). Bu soru eşleşme sayımına dahil edilmeyecek; model çağrısı yine yapılacak ve sonucu kaydedilecek.
- Tek etiketleyen.
- 4 video, her biri tek çalıştırma.
- Deneme 1 ve 2 ile aynı model (gpt-4o-mini) ve istem (`support-v1`).
- Sorular bağımsız değil: aynı videodan 5'er soru (doğrulanmış olarak 4-5).
- Transkriptlerde yazım hataları var: "yüz" / "used to", "guido One rossum", "mat plot lip". Alıntılar bu yazımlarla değerlendirildi.
