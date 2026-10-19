# Aşama 12e · Tarayıcı gözlemi 1

**Tarih:** 19 Ekim 2026
**Deneme:** Kullanıcı, arayüzde kemosentez videosu (`109kCbVtU1U`) için "Alıntı-cevap destek kontrolünü de çalıştır" kutusu işaretliyken soru üretti (`count: 5`, `transcript_mode: clean`, istem `questions-v1`, destek kontrolü `support-v1`).
**Kayıt:** Çalıştırma kaydı yerelde (`backend/runs/20261019-173948-109kCbVtU1U-questions.json`); depoya kopyalanmadı. Aşağıdaki sayılar bu kayıtla karşılaştırıldı ve uyuşuyor.

> **Bu bir ölçüm değil, tarayıcı gözlemidir.** Etiketler model sonucu görülmeden önce kör olarak verilmedi; tek çalıştırmadır. Sayılar genel bir oran olarak kullanılmayacak.

## Arayüzde görülenler (kullanıcı)

- Onay kutusu ve açıklama metni doğru görünüyor; listenin üst satırında "Destek kontrolü: support-v1" yazıyor.
- İstek sürerken kutu kilitli (tıklanamıyor).
- Listenin altındaki not görünüyor.

## Sonuçlar

5 sorunun 5'inin kaynağı doğrulandı (alıntı transkriptte bulundu). Destek kontrolü:

| Soru | Doğru cevap | Kaynak alıntısı | Model etiketi |
|---|---|---|---|
| 1 | Kimyasal enerji | Yani inorganik maddeyi kullanarak organik besin sentezi yapan canlıya biz ototrof yani üretici canlı adını vermiştik. | desteklemiyor |
| 2 | Kemosentetik canlılar | Yani bu canlılarda nelermiş? Karides, yengeç, midye, deniz yıldızı gibi canlılarmış. | desteklemiyor |
| 3 | Oksijen | Demek ki kemosentezde oksijen açığa çıkmıyormuş. | destekliyor |
| 4 | Prokaryot | Kemosentez yapan canlılara da kemosentetik canlılar adını veriyoruz. Bu canlıların tamamı prokaryot hücre yapısına sahip olan canlılardır. | destekliyor |
| 5 | Gündüz ve gece | Yani besin üretimi için ışık şart değildir ifadesini kullanabiliriz. | desteklemiyor |

- **Sayılar:** 3 desteklemiyor (Soru 1, 2, 5), 2 destekliyor (Soru 3, 4).
- **Kullanıcının yorumu:**
  - Soru 1 ve 2'de alıntı metni cevabı içermiyor (okuyunca kendiliğinden görülüyor).
  - Soru 5'te alıntı "ışık şart değildir" diyor, cevap "gündüz ve gece": sınır vakası. Kullanıcı "kısmen" derdi, model "desteklemiyor" dedi.
- **Not (kayıttan):** Soru 2 ve Soru 5'in alıntısı, [destek kontrolü denemesi 1](asama-9-destek-kontrolu-1.md)'deki 12d S2 ve 12d S5 ile aynı metin; o denemede de model ikisine "desteklemiyor" demişti.

## Görülmeyenler

- "kısmen" etiketi
- "kontrol edilemedi" etiketi
- Dar ekran görünümü

## Sınırlar

- Ölçüm değil gözlem: etiketler kör verilmedi.
- Tek video, tek çalıştırma, 5 soru; genel oran olarak kullanılmayacak.
- Çalıştırma kaydı depoya kopyalanmadı (istekteki bağlantıda paylaşım kodu `si=` var).
