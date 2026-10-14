# Aşama 12d · Tarayıcı testi 1 bulguları

**Tarih:** 14 Ekim 2026
**Test:** Arayüzdeki "Soruları üret" düğmesiyle `POST /api/questions` · video `109kCbVtU1U` (kemosentez) · `count: 5` · `transcript_mode: clean`
**Model / istem:** gpt-4o-mini · `questions-v1`
**Ham sonuç:** [asama-12d-test-1.json](asama-12d-test-1.json) (yerel çalıştırma kaydı `backend/runs/20261014-152923-109kCbVtU1U-questions.json` dosyasının birebir kopyası). 5 soru döndü, 5'inin alıntısı transkriptte bulundu (`verified=true`).

## Elle kontrol durumu

- 5 sorudan 2'sinin (Soru 1 ve Soru 2) kaynak süresi kullanıcı tarafından videoda açılıp kontrol edildi.
- Kalan 3 sorunun kaynak süresi kontrol edilmedi.
- Hiçbir sorunun saniyesi ölçülmedi.

## Bulgu · Soru 2'de alıntı konuyla ilgili ama doğru cevabı doğrudan söylemiyor

**Soru 2:** *"Hidrotermal bacaların etrafında hangi canlılar yaşayabilir?"*
- Doğru cevap (yanıta göre): **Kemosentetik canlılar**
- Kaynak alıntısı: *"Yani bu canlılarda nelermiş? Karides, yengeç, midye, deniz yıldızı gibi canlılarmış."*
- `verified=true`, `quote_match: exact`, kaynak süresi 257,639 sn (**4:17**)

**Kullanıcının gördüğü ve söylediği:** Kullanıcı bağlantıdaki 4:17'yi videoda açıp dinledi. O noktada canlılar sayılıyor (karides, yengeç, midye, deniz yıldızı gibi), ama bunların kemosentetik canlılar olduğu söylenmiyor. Kullanıcıya göre videonun devamında "kemosentetik canlılar" ifadesi geçiyor, fakat bağlantının açtığı noktada geçmiyor.

**Sonuç:**
- Alıntı transkriptte bulunuyor ve süresi o konuşmayla uyuşuyor.
- Alıntı konuyla ilgili ama doğru cevabı ("Kemosentetik canlılar") doğrudan söylemiyor (elle etiket: kısmen; bkz. [asama-9-destek-kontrolu-1.md](asama-9-destek-kontrolu-1.md)).
- Cevap videoda bir yerde geçiyor olabilir, ama soruya bağlı kaynak onu doğrudan göstermiyor.
- **"Kaynağı doğrulanmış" etiketi, kaynağın cevabı kanıtladığı anlamına gelmiyor.**

## Sınırlar

- Tek soru, tek video, tek elle kontrol.
