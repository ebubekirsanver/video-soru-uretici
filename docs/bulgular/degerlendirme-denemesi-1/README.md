# Değerlendirme denemesi 1

Dışa aktarmanın deneme çalıştırması. Pilot 2'nin `questions-v3` sonuçlarından (6 video × 2 koşul) üretildi; 69 soru, 3 üretilemeyen konu, tohum 20261105. Etiket yok, analiz çalıştırılmadı.

Değerlendirici dosyaları ve anahtar bu klasörde üretilir ama depoya girmez (`.gitignore`). Transkriptler önbellekte varsa aynı komut aynı içeriği üretir:

```
cd backend
python -m evaluation.export --girdi "../docs/bulgular/pilot-2/pilot-2-*.json" --video-bilgisi ../docs/bulgular/degerlendirme-denemesi-1/video-bilgisi.json --tohum 20261105 --cikti ../docs/bulgular/degerlendirme-denemesi-1 --anahtar-cikti ../docs/bulgular/degerlendirme-denemesi-1/anahtar --istem-surumu questions-v3
```

Not (2026-11-18): Bu komut geçmiş kayıttır, değiştirilmedi. O tarihten beri `export` depo içindeki bir klasöre yazmıyor (anahtar dosyası koşul bilgisi taşır, değerlendirici dosyaları tam transkript içerir); komut bugün çalıştırılırsa hata verir. Yeniden üretmek için `--cikti` ve `--anahtar-cikti` depo dışındaki bir klasör olmalı. Bu klasörde daha önce üretilmiş dosyalar git dışında kaldı.

`video-bilgisi.json` pilot videolar için elle oluşturuldu (altısı otomatik altyazı, İngilizce iki dilli) ve depoya girer. 2026-11-10'da dosyalar "Tanıma hatası kaynaklı mı" sütunuyla yeniden üretildi.

Çıktılar: `degerlendirici-A.xlsx`, `degerlendirici-B.xlsx`, `anahtar/anahtar.json`. Kullanım adımları: [backend/evaluation/README.md](../../../backend/evaluation/README.md).
