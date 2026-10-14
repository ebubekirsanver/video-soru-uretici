# Aşama 9 · Destek kontrolü denemesi 1

**Amaç:** Alıntı-cevap destek kontrolünün (`services/support_check.py`, istem `support-v1`) verdiği etiketleri, aynı sorular için verilen elle etiketlerle karşılaştırmak.
**Sorular:** [asama-12d-test-1.json](asama-12d-test-1.json) kaydındaki 5 soru (video `109kCbVtU1U`, `questions-v1`). Sorular yeniden üretilmez.
**Etiketler:** destekliyor (alıntı doğru cevabı doğrudan söylüyor) / kısmen (ilgili ama cevabı doğrudan vermiyor ya da dolaylı) / desteklemiyor (alıntıdan cevap çıkarılamıyor).

> Durum: elle etiketler model çağrısından önce verildi ve commit'lendi (`05196c3`). Model etiketleri sonra, tek çalıştırmayla alındı; sonuç değiştirilmeden kaydedildi.

**Elle etiketleme yöntemi:**
- Etiketler kullanıcı tarafından, yalnızca doğrulanmış kaynak alıntısına bakılarak verildi.
- Ölçüt: "Yalnızca alıntıyı okuyan biri doğru cevabı çıkarabilir mi?"
- Videoya bakılmadı.
- Etiketleyen tek kişi (kullanıcı); etiketler model etiketleri görülmeden verildi ve model çağrısından önce commit'lendi.

| # | Soru | Doğru cevap | Kaynak alıntısı | Kaynak süresi | Elle etiket (destekliyor/kısmen/desteklemiyor) | Model etiketi | Eşleşme |
|---|---|---|---|---|---|---|---|
| 1 | Kemosentetik canlılar hangi enerji kaynağını kullanarak besin üretirler? | Kimyasal enerji | Kimyasal bir enerjiyi kullanarak besin üretimini gerçekleştiriyorsa o canlıya da kemosentetik canlı adını vermiştik. | 3:36 (216,84 sn) | destekliyor | destekliyor | aynı |
| 2 | Hidrotermal bacaların etrafında hangi canlılar yaşayabilir? | Kemosentetik canlılar | Yani bu canlılarda nelermiş? Karides, yengeç, midye, deniz yıldızı gibi canlılarmış. | 4:17 (257,639 sn) | kısmen | desteklemiyor | farklı |
| 3 | Kemosentez sırasında hangi madde açığa çıkmaz? | Oksijen | Demek ki kemosentezde oksijen açığa çıkmıyormuş. | 13:33 (813,279 sn) | destekliyor | destekliyor | aynı |
| 4 | Kemosentetik canlıların hücre yapısı nedir? | Prokaryot | Kemosentez yapan canlılara da kemosentetik canlılar adını veriyoruz. Bu canlıların tamamı prokaryot hücre yapısına sahip olan canlılardır. | 9:38 (578,32 sn) | destekliyor | destekliyor | aynı |
| 5 | Kemosentez hangi koşullarda gerçekleşebilir? | Gündüz ve gece | Yani besin üretimi için ışık şart değildir ifadesini kullanabiliriz. | 6:11 (371,56 sn) | destekliyor | desteklemiyor | farklı |

## Model çalıştırması

- **Ham sonuç:** [asama-9-destek-kontrolu-1.json](asama-9-destek-kontrolu-1.json) (ilk ve tek çalıştırma, değiştirilmeden).
- **Betik:** [asama-9-destek-kontrolu-1.py](asama-9-destek-kontrolu-1.py). Sorular yeniden üretilmeden doğrudan `check_support` fonksiyonuna verildi.
- 2026-10-14 16:07:09–16:07:16 (+03:00), model gpt-4o-mini, istem `support-v1`, 5 çağrı.
- Kod commit'i `05196c3`. İstem dosyalarının ve kaynak kaydın SHA256 özetleri JSON'da.

**Eşleşme:** 5 sorunun 3'ünde elle etiket ile model etiketi aynı (Soru 1, 3, 4), 2'sinde farklı (Soru 2, 5).

Not: Soru 5 için etiket model sonucu görülmeden verildi ve değiştirilmedi; alıntıdan cevaba bir çıkarım gerekiyor.

| # | Elle etiket | Model etiketi | Model gerekçesi |
|---|---|---|---|
| 1 | destekliyor | destekliyor | Alıntıda kemosentetik canlıların kimyasal enerji kullanarak besin ürettiği belirtiliyor. |
| 2 | kısmen | desteklemiyor | Alıntıda kemosentetik canlılar hakkında bilgi verilmemiş. |
| 3 | destekliyor | destekliyor | Alıntıda kemosentezde oksijenin açığa çıkmadığı belirtiliyor. |
| 4 | destekliyor | destekliyor | Alıntıda kemosentetik canlıların prokaryot hücre yapısına sahip olduğu belirtiliyor. |
| 5 | destekliyor | desteklemiyor | Alıntıda kemosentezin hangi koşullarda gerçekleştiğine dair bir bilgi yok. |

## Sınırlar

- 5 soru, tek video, tek etiketleyen, modelin tek çalıştırması.
- Modelin sıcaklığı 0,2; aynı istemle yeniden çalıştırma farklı etiket verebilir. Yalnızca ilk çalıştırma kaydedildi.
- Bu 5 soruluk karşılaştırma, model değerlendirmesinin isabetini ölçmek için yeterli bir örneklem değildir.
