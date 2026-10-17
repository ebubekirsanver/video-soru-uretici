# Aşama 9 · Destek kontrolü denemesi 2

**Amaç:** Alıntı-cevap destek kontrolünün (`services/support_check.py`, istem `support-v1`) verdiği etiketleri, aynı sorular için verilen elle etiketlerle karşılaştırmak.
**Sorular:** Test 2 kayıtlarındaki 9 soru: [asama-6-test-2-kemosentez.json](asama-6-test-2-kemosentez.json) (video `109kCbVtU1U`, 4 soru) ve [asama-6-test-2-tarih.json](asama-6-test-2-tarih.json) (video `aaCHLYO3Fzg`, 5 soru); istem `questions-v1`. Sorular yeniden üretilmez.
**Etiketler:** destekliyor (alıntı doğru cevabı doğrudan söylüyor) / kısmen (ilgili ama cevabı doğrudan vermiyor ya da dolaylı) / desteklemiyor (alıntıdan cevap çıkarılamıyor).

> Durum: elle etiketler verildi; model etiketleri henüz alınmadı (model çağrısı yapılmadı).

**Elle etiketleme yöntemi:**
- Etiketler kullanıcı tarafından, yalnızca doğrulanmış kaynak alıntısına bakılarak verildi.
- Ölçüt: "Yalnızca doğrulanmış alıntıyı okuyan biri doğru cevabı çıkarabilir mi?"
- Videoya bakılmadı.
- Etiketleyen tek kişi (kullanıcı); etiketler model sonuçları görülmeden verildi ve model çağrısından önce commit'lendi.

**Dürüstlük notu:** Kullanıcı önce 9 sorunun hepsini "destekliyor" olarak etiketledi. Ardından asistan, kemosentez S2 ve tarih S2 için önceki bulgu notlarında ([asama-6-test-2.md](asama-6-test-2.md), C.3 (e) ve (d)) zaten bir sınır kaydedildiğine dikkat çekti: kemosentez S2'de alıntı ile cevap arasında tam örtüşme yok; tarih S2'de alıntı İzmir'i saymıyor, cevap bir çıkarımla bulunuyor. Kullanıcı bu iki etiketi, model sonucu görülmeden, "kısmen" olarak değiştirdi.

**Kayıt biçimi notu:** Test 2 kayıtları eski biçimdedir (`record_version` ve `quote_audit` yok). `trimmed` sorularda modelin yazdığı özgün alıntı ve kırpılan sözcükler bu kayıtlardan görülemez; tablodaki alıntı transkriptteki hâlidir.

| # | Soru | Doğru cevap | Kaynak alıntısı | Kaynak süresi | Eşleşme türü | Elle etiket (destekliyor/kısmen/desteklemiyor) | Model etiketi |
|---|---|---|---|---|---|---|---|
| kemosentez S1 | Kemosentetik canlılar hangi enerji kaynağını kullanarak besin üretimi gerçekleştirir? | Kimyasal enerji | kemosentez yapan canlılar için ne diyoruz? Kimyasal bir enerji kullanılıyor ve buna bağlı olarak da besin üretimi gerçekleşiyor. | 9:28 (568,959 sn) | exact | destekliyor |  |
| kemosentez S2 | Hidrotermal bacaların bulunduğu ortamda hangi canlılar yaşayabilir? | Kemosentetik canlılar | Bu nedenle okyanus derinliklerinde özellikle bu bacaların etrafında kemosentez yapan bakterilerle beslenen farklı biyolojik canlılara rastlanabilir. | 4:07 (247,64 sn) | exact | kısmen |  |
| kemosentez S3 | Kemosentez sırasında hangi madde açığa çıkmaz? | Oksijen | oksijen üretilmez demiştim. | 19:35 (1175,919 sn) | trimmed | destekliyor |  |
| kemosentez S4 | Kemosentetik canlıların hücre yapısı nedir? | Prokaryot | Kemosentetik canlıların tamamının prokaryot olduğunu unutma. | 7:22 (442,72 sn) | exact | destekliyor |  |
| tarih S1 | Malazgirt Savaşı hangi yıllarda gerçekleşmiştir? | 1071 | Bu savaş 1071'de gerçekleşti | 1:19 (79,52 sn) | exact | destekliyor |  |
| tarih S2 | Danışmentlilerin kurulduğu bölgeler arasında hangisi yer almaz? | İzmir | Tokat, Amasya, Kayseri, Sivas, Malatya bu bölgelere yayılmış bir beylik. | 4:04 (244,319 sn) | trimmed | kısmen |  |
| tarih S3 | Kösedağ Savaşı'nda Türkiye Selçuklu Devleti kime karşı savaşmıştır? | Moğollar | Türkiye Selçuklu Devleti ile Moğollar arasında yapıldı. | 29:46 (1786,96 sn) | trimmed | destekliyor |  |
| tarih S4 | Mir Kefalon Savaşı'nın önemi nedir? | Anadolu'dan Türklerin atılma ihtimalini ortadan kaldırması | Bu savaşta Türkiye Selçuklu Devleti Bizans'ı yenince Anadolu'dan Türklerin atılamayacağı kesinleşmişti. | 29:00 (1740,36 sn) | exact | destekliyor |  |
| tarih S5 | 1. Haçlı Seferi'nin temel amacı nedir? | Kudüs'ü ele geçirmek | Temel dini amaçları neymiş? Kudüs'ü ele geçirmekmiş. | 10:07 (607,279 sn) | exact | destekliyor |  |

## Sınırlar

- 9 etiketin 7'si aynı etiket (destekliyor) olduğundan bu denemeyle modelin zayıf desteği yakalayıp yakalamadığı sınırlı ölçülebilir.
- Test 2 kayıtlarında modelin özgün alıntısı olmadığı için üç kırpılmış soruda (kemosentez S3, tarih S2, tarih S3) yalnızca transkriptteki hâli değerlendirildi.
