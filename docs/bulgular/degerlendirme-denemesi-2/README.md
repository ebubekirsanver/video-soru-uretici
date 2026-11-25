# Değerlendirme denemesi 2

Deneme etiketlemesi (1–16 Aralık 2026) için üretilen değerlendirici dosyaları. Pilot 2'nin `questions-v3` sonuçlarından (6 video × 2 koşul) "anahtar yanlış" (A) kuralıyla ve değerlendirme yönergesinin metniyle yeniden üretildi (2026-11-25).

- Soru: 69. Üretilemeyen konu: 3. Eksik çift: 0.
- Tohum: 20261125.
- İstem sürümü: questions-v3.
- Yönerge: `docs/degerlendirme-yonergesi-v1.md`, SHA-256 `5dad86252b148682840cbfce7e93240655c07c266ac39df0f571c4bb3c8eff74`. Bu değer değerlendirici dosyalarının "Yönerge" sayfasının başında (ilk 12 karakter) ve anahtarda (`guide`) yazılıdır.
- Video bilgisi: `docs/bulgular/degerlendirme-denemesi-1/video-bilgisi.json` (altısı otomatik altyazı, İngilizce iki dilli).

Kullanılan komut (`backend` klasöründen):

```
python -m evaluation.export --girdi "../docs/bulgular/pilot-2/pilot-2-*.json" --video-bilgisi ../docs/bulgular/degerlendirme-denemesi-1/video-bilgisi.json --tohum 20261125 --istem-surumu questions-v3 --cikti <depo-dışı-klasör>/degerlendirme-denemesi-2 --anahtar-cikti <depo-dışı-klasör>/degerlendirme-denemesi-2/anahtar
```

Transkriptler yerel önbellekten okundu; YouTube'a istek atılmadı.

Çıktılar: `degerlendirici-A.xlsx`, `degerlendirici-B.xlsx` (içerik ve sıra aynı) ve `anahtar/anahtar.json`. **Değerlendirici dosyaları ve anahtar depoya girmez:** anahtar koşul bilgisi taşır, değerlendirici dosyaları tam transkript içerir. Dosyalar depo dışındaki bir klasördedir; export depo içine yazmayı reddeder. Kullanım adımları: [backend/evaluation/README.md](../../../backend/evaluation/README.md).
