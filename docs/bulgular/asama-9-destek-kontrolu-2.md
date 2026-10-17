# Aşama 9 · Destek kontrolü denemesi 2

**Amaç:** Alıntı-cevap destek kontrolünün (`services/support_check.py`, istem `support-v1`) verdiği etiketleri, aynı sorular için verilen elle etiketlerle karşılaştırmak.
**Sorular:** Test 2 kayıtlarındaki 9 soru: [asama-6-test-2-kemosentez.json](asama-6-test-2-kemosentez.json) (video `109kCbVtU1U`, 4 soru) ve [asama-6-test-2-tarih.json](asama-6-test-2-tarih.json) (video `aaCHLYO3Fzg`, 5 soru); istem `questions-v1`. Sorular yeniden üretilmez.
**Etiketler:** destekliyor (alıntı doğru cevabı doğrudan söylüyor) / kısmen (ilgili ama cevabı doğrudan vermiyor ya da dolaylı) / desteklemiyor (alıntıdan cevap çıkarılamıyor).

> Durum: elle etiketler model çağrısından önce verildi ve commit'lendi (`996f653`). Model etiketleri sonra, tek çalıştırmayla alındı; sonuç değiştirilmeden kaydedildi.

**Elle etiketleme yöntemi:**
- Etiketler kullanıcı tarafından, yalnızca doğrulanmış kaynak alıntısına bakılarak verildi.
- Ölçüt: "Yalnızca doğrulanmış alıntıyı okuyan biri doğru cevabı çıkarabilir mi?"
- Videoya bakılmadı.
- Etiketleyen tek kişi (kullanıcı); etiketler model sonuçları görülmeden verildi ve model çağrısından önce commit'lendi.

**Dürüstlük notu:** Kullanıcı önce 9 sorunun hepsini "destekliyor" olarak etiketledi. Ardından asistan, kemosentez S2 ve tarih S2 için önceki bulgu notlarında ([asama-6-test-2.md](asama-6-test-2.md), C.3 (e) ve (d)) zaten bir sınır kaydedildiğine dikkat çekti: kemosentez S2'de alıntı ile cevap arasında tam örtüşme yok; tarih S2'de alıntı İzmir'i saymıyor, cevap bir çıkarımla bulunuyor. Kullanıcı bu iki etiketi, model sonucu görülmeden, "kısmen" olarak değiştirdi.

**Kayıt biçimi notu:** Test 2 kayıtları eski biçimdedir (`record_version` ve `quote_audit` yok). `trimmed` sorularda modelin yazdığı özgün alıntı ve kırpılan sözcükler bu kayıtlardan görülemez; tablodaki alıntı transkriptteki hâlidir.

| # | Soru | Doğru cevap | Kaynak alıntısı | Kaynak süresi | Alıntı eşleşmesi (quote_match) | Elle etiket (destekliyor/kısmen/desteklemiyor) | Model etiketi | Etiket eşleşmesi |
|---|---|---|---|---|---|---|---|---|
| kemosentez S1 | Kemosentetik canlılar hangi enerji kaynağını kullanarak besin üretimi gerçekleştirir? | Kimyasal enerji | kemosentez yapan canlılar için ne diyoruz? Kimyasal bir enerji kullanılıyor ve buna bağlı olarak da besin üretimi gerçekleşiyor. | 9:28 (568,959 sn) | exact | destekliyor | destekliyor | aynı |
| kemosentez S2 | Hidrotermal bacaların bulunduğu ortamda hangi canlılar yaşayabilir? | Kemosentetik canlılar | Bu nedenle okyanus derinliklerinde özellikle bu bacaların etrafında kemosentez yapan bakterilerle beslenen farklı biyolojik canlılara rastlanabilir. | 4:07 (247,64 sn) | exact | kısmen | destekliyor | farklı |
| kemosentez S3 | Kemosentez sırasında hangi madde açığa çıkmaz? | Oksijen | oksijen üretilmez demiştim. | 19:35 (1175,919 sn) | trimmed | destekliyor | destekliyor | aynı |
| kemosentez S4 | Kemosentetik canlıların hücre yapısı nedir? | Prokaryot | Kemosentetik canlıların tamamının prokaryot olduğunu unutma. | 7:22 (442,72 sn) | exact | destekliyor | destekliyor | aynı |
| tarih S1 | Malazgirt Savaşı hangi yıllarda gerçekleşmiştir? | 1071 | Bu savaş 1071'de gerçekleşti | 1:19 (79,52 sn) | exact | destekliyor | destekliyor | aynı |
| tarih S2 | Danışmentlilerin kurulduğu bölgeler arasında hangisi yer almaz? | İzmir | Tokat, Amasya, Kayseri, Sivas, Malatya bu bölgelere yayılmış bir beylik. | 4:04 (244,319 sn) | trimmed | kısmen | desteklemiyor | farklı |
| tarih S3 | Kösedağ Savaşı'nda Türkiye Selçuklu Devleti kime karşı savaşmıştır? | Moğollar | Türkiye Selçuklu Devleti ile Moğollar arasında yapıldı. | 29:46 (1786,96 sn) | trimmed | destekliyor | destekliyor | aynı |
| tarih S4 | Mir Kefalon Savaşı'nın önemi nedir? | Anadolu'dan Türklerin atılma ihtimalini ortadan kaldırması | Bu savaşta Türkiye Selçuklu Devleti Bizans'ı yenince Anadolu'dan Türklerin atılamayacağı kesinleşmişti. | 29:00 (1740,36 sn) | exact | destekliyor | destekliyor | aynı |
| tarih S5 | 1. Haçlı Seferi'nin temel amacı nedir? | Kudüs'ü ele geçirmek | Temel dini amaçları neymiş? Kudüs'ü ele geçirmekmiş. | 10:07 (607,279 sn) | exact | destekliyor | destekliyor | aynı |

## Model çalıştırması

- **Ham sonuç:** [asama-9-destek-kontrolu-2.json](asama-9-destek-kontrolu-2.json) (ilk ve tek çalıştırma, değiştirilmeden).
- **Betik:** [asama-9-destek-kontrolu-2.py](asama-9-destek-kontrolu-2.py). Sorular yeniden üretilmeden doğrudan `check_support` fonksiyonuna verildi.
- 2026-10-17 18:45:54–18:46:05 (+03:00), model gpt-4o-mini, istem `support-v1`, 9 çağrı.
- Kod commit'i `996f653`. İstem dosyalarının SHA256 özetleri 1. denemedekiyle aynı (`support-v1` değişmedi). Kaynak kayıtların özetleri JSON'da.

**Eşleşme (bu deneme, 9 soru):** tam eşleşme 7, farklı 2.

| Farklı olan soru | Elle etiket | Model etiketi |
|---|---|---|
| kemosentez S2 | kısmen | destekliyor |
| tarih S2 | kısmen | desteklemiyor |

| # | Elle etiket | Model etiketi | Model gerekçesi |
|---|---|---|---|
| kemosentez S1 | destekliyor | destekliyor | Alıntıda kimyasal enerji kullanıldığı ve besin üretimi gerçekleştiği belirtiliyor. |
| kemosentez S2 | kısmen | destekliyor | Alıntıda kemosentez yapan bakterilerle beslenen canlıların varlığı belirtiliyor. |
| kemosentez S3 | destekliyor | destekliyor | Alıntıda oksijenin üretilmediği belirtiliyor. |
| kemosentez S4 | destekliyor | destekliyor | Alıntı, kemosentetik canlıların prokaryot olduğunu açıkça belirtiyor. |
| tarih S1 | destekliyor | destekliyor | Alıntıda savaşın 1071'de gerçekleştiği belirtiliyor. |
| tarih S2 | kısmen | desteklemiyor | Alıntıda İzmir ile ilgili bir bilgi bulunmamaktadır. |
| tarih S3 | destekliyor | destekliyor | Alıntıda Türkiye Selçuklu Devleti ile Moğollar arasında savaş yapıldığı belirtiliyor. |
| tarih S4 | destekliyor | destekliyor | Alıntıda Anadolu'dan Türklerin atılamayacağı kesinleştiği belirtiliyor. |
| tarih S5 | destekliyor | destekliyor | Alıntıda Kudüs'ü ele geçirmenin temel dini amacı olduğu belirtiliyor. |

## Deneme 1 ve 2 birleşik (14 soru)

Deneme 1: [asama-9-destek-kontrolu-1.md](asama-9-destek-kontrolu-1.md) (Aşama 12d testinin 5 sorusu). Deneme 2: bu dosya (Test 2'nin 9 sorusu). İki deneme aynı istemle (`support-v1`) ve aynı ölçütle yapıldı.

**Eşleşme (14 soru):** tam eşleşme 10, farklı 4.

| Elle etiket | Model etiketi | Sayı | Sorular |
|---|---|---|---|
| kısmen | desteklemiyor | 2 | Deneme 1 · 12d S2; Deneme 2 · tarih S2 |
| destekliyor | desteklemiyor | 1 | Deneme 1 · 12d S5 |
| kısmen | destekliyor | 1 | Deneme 2 · kemosentez S2 |

| Deneme | # | Soru | Elle etiket | Model etiketi | Eşleşme |
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

## Sınırlar

- 9 etiketin 7'si aynı etiket (destekliyor) olduğundan bu denemeyle modelin zayıf desteği yakalayıp yakalamadığı sınırlı ölçülebilir.
- Test 2 kayıtlarında modelin özgün alıntısı olmadığı için üç kırpılmış soruda (kemosentez S3, tarih S2, tarih S3) yalnızca transkriptteki hâli değerlendirildi.
- Birleşik tablodaki 14 sorudan 9'u aynı kemosentez videosundan (`109kCbVtU1U`) ve farklı çalıştırmalardan geliyor; bazı sorular aynı konuyu ya da aynı soru metnini tekrarlıyor (ör. "Kemosentez sırasında hangi madde açığa çıkmaz?" iki denemede de var, alıntıları farklı). Sorular birbirinden bağımsız değildir.
- Modelin sıcaklığı 0,2; aynı istemle yeniden çalıştırma farklı etiket verebilir. Her deneme için yalnızca ilk çalıştırma kaydedildi.
