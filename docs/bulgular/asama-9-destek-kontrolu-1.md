# Aşama 9 · Destek kontrolü denemesi 1

**Amaç:** Alıntı-cevap destek kontrolünün (`services/support_check.py`, istem `support-v1`) verdiği etiketleri, aynı sorular için verilen elle etiketlerle karşılaştırmak.
**Sorular:** [asama-12d-test-1.json](asama-12d-test-1.json) kaydındaki 5 soru (video `109kCbVtU1U`, `questions-v1`). Sorular yeniden üretilmez.
**Etiketler:** destekliyor (alıntı doğru cevabı doğrudan söylüyor) / kısmen (ilgili ama cevabı doğrudan vermiyor ya da dolaylı) / desteklemiyor (alıntıdan cevap çıkarılamıyor).

> Durum: elle etiketler verildi; model etiketleri henüz alınmadı (model çağrısı yapılmadı).

**Elle etiketleme yöntemi:**
- Etiketler kullanıcı tarafından, yalnızca doğrulanmış kaynak alıntısına bakılarak verildi.
- Ölçüt: "Yalnızca alıntıyı okuyan biri doğru cevabı çıkarabilir mi?"
- Videoya bakılmadı.
- Etiketleyen tek kişi (kullanıcı); etiketler model etiketleri görülmeden verildi ve model çağrısından önce commit'lendi.

| # | Soru | Doğru cevap | Kaynak alıntısı | Kaynak süresi | Elle etiket (destekliyor/kısmen/desteklemiyor) | Model etiketi |
|---|---|---|---|---|---|---|
| 1 | Kemosentetik canlılar hangi enerji kaynağını kullanarak besin üretirler? | Kimyasal enerji | Kimyasal bir enerjiyi kullanarak besin üretimini gerçekleştiriyorsa o canlıya da kemosentetik canlı adını vermiştik. | 3:36 (216,84 sn) | destekliyor | |
| 2 | Hidrotermal bacaların etrafında hangi canlılar yaşayabilir? | Kemosentetik canlılar | Yani bu canlılarda nelermiş? Karides, yengeç, midye, deniz yıldızı gibi canlılarmış. | 4:17 (257,639 sn) | kısmen | |
| 3 | Kemosentez sırasında hangi madde açığa çıkmaz? | Oksijen | Demek ki kemosentezde oksijen açığa çıkmıyormuş. | 13:33 (813,279 sn) | destekliyor | |
| 4 | Kemosentetik canlıların hücre yapısı nedir? | Prokaryot | Kemosentez yapan canlılara da kemosentetik canlılar adını veriyoruz. Bu canlıların tamamı prokaryot hücre yapısına sahip olan canlılardır. | 9:38 (578,32 sn) | destekliyor | |
| 5 | Kemosentez hangi koşullarda gerçekleşebilir? | Gündüz ve gece | Yani besin üretimi için ışık şart değildir ifadesini kullanabiliriz. | 6:11 (371,56 sn) | destekliyor | |
