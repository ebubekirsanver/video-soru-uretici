# Aşama 7b · Koşul denemesi 1

## Plan (betik çalıştırılmadan önce yazıldı)

- **Amaç:** İki koşulun (tam transkript `full` / RAG `rag`) gerçek bir videoda uçtan uca çalıştığını görmek.
- **Bu bir İŞLERLİK denemesidir, AS1 değerlendirmesi değildir:** Soru kalitesi hakkında yargı ve isabet iddiası yok. Kalite, değerlendirme yönergesi hazırlandıktan sonra (Güz 13–14) iki değerlendiriciyle ölçülecek.
- **Video:** Kemosentez (`109kCbVtU1U`), temiz transkript.
- **Konular:**
  - Önce özet servisi (`/api/summary`) bir kez çalıştırılır.
  - Dönen konuların ilk 6'sı (6'dan az ise hepsi) `asama-7b-kosul-denemesi-1-konular.json` dosyasına yazılır.
  - İki koşulda da aynı liste `topics` olarak verilir.
  - Konular kullanıcıya gösterilir; kullanıcı onaylamadan koşullar çalıştırılmaz.
- **Ayarlar:**
  - Model `gpt-4o-mini`, istem `questions-v2`.
  - RAG için `k=5`, parçalama `fixed-150-30`, gömme `BAAI/bge-m3`.
  - Her koşul bir kez çalıştırılır. `check_support` kapalı.
- **Betik:** [asama-7b-kosul-denemesi-1.py](asama-7b-kosul-denemesi-1.py).
  - İstekler API üzerinden FastAPI TestClient ile yapılır; çalışan bir sunucu gerekmez.
  - Çalıştırma kayıtları `backend/runs` altına yazılır (git dışında).
  - İki adım ayrı çalıştırılır: `ozet`, ardından onaydan sonra `kosullar`.

### Raporlanacaklar

- **Her koşul için:**
  - konu başına sonuç (`ok` / `empty` / `invalid` / `duplicate`)
  - dönen soru sayısı
  - alıntısı transkriptte bulunan soru sayısı
  - yazım kuralı işaretleri (sayı ve kural numarası)
  - toplam süre
  - model çağrısı sayısı
  - toplam token
- **RAG için ayrıca:** Her konuda gelen parçaların `chunk_index`, zaman aralığı ve skoru; bağlamın kelime sayısı.
- **Full için ayrıca:** Bağlamın kelime sayısı.
- **Yan yana tablo:** İki koşulun aynı konudaki soruları: konu, full sorusu ve doğru cevabı, rag sorusu ve doğru cevabı, iki kaynak zamanı. Yorum yazılmaz; değerlendirmeyi kullanıcı yapacak.
- **Maliyet:** Tahmin edilmez; yalnızca token sayıları yazılır.

## Çalıştırma (31 Ekim 2026)

- **Adımlar:** Önce `ozet` adımı çalıştırıldı ve konular kullanıcıya gösterildi. Kullanıcı onaylayınca `kosullar` adımı bir kez çalıştırıldı.
- **Konu sayısı:** Özet servisi 5 konu döndürdü. Plan "6'dan az ise hepsi" dediği için beşi de kullanıldı.
- **Model çağrıları:** Toplam 11 OpenAI çağrısı: özet 1, full 5, rag 5.
- **Çıktı dosyaları:**
  - Konular: [asama-7b-kosul-denemesi-1-konular.json](asama-7b-kosul-denemesi-1-konular.json)
  - Yanıtlar ve kayıttan seçilen alanlar: [asama-7b-kosul-denemesi-1.json](asama-7b-kosul-denemesi-1.json)
- **Gizli bilgi taraması:** Çalıştırma kayıtları `backend/runs` altında kaldı. Depoya giren iki JSON dosyası ve bu çıktı tarandı (yerel yol, anahtar, yetki başlığı, `si=`, e-posta); eşleşme yok.

### Konular (betiğin `ozet` çıktısı, olduğu gibi)

```
Özetten dönen konu sayısı: 5 · kullanılacak: 5
  1. Kemosentez Nedir?
  2. Hidrotermal Bacalar ve Canlılar
  3. Kemosentetik Canlıların Özellikleri
  4. Fotosentez ve Kemosentez Farkları
  5. Kemosentez ve Ekosistem
```

### Koşullar (betiğin `kosullar` çıktısı, olduğu gibi)

```
Video: 109kCbVtU1U · konular (5): Kemosentez Nedir?; Hidrotermal Bacalar ve Canlılar; Kemosentetik Canlıların Özellikleri; Fotosentez ve Kemosentez Farkları; Kemosentez ve Ekosistem

=== Koşul: full ===
İstem: questions-v2 · model: gpt-4o-mini · k: None · parçalama: None · gömme: None
Konu başına sonuç:
  - Kemosentez Nedir?: ok · bağlam 3287 kelime
  - Hidrotermal Bacalar ve Canlılar: ok · bağlam 3287 kelime
  - Kemosentetik Canlıların Özellikleri: ok · bağlam 3287 kelime
  - Fotosentez ve Kemosentez Farkları: ok · bağlam 3287 kelime
  - Kemosentez ve Ekosistem: duplicate · bağlam 3287 kelime
Sonuç sayıları: {'ok': 4, 'empty': 0, 'invalid': 0, 'duplicate': 1}
Dönen soru: 4 / 5 · alıntısı transkriptte bulunan: 4
Yazım kuralı işaretleri: 0 · yok
Toplam süre: 14384.2 ms · model çağrısı: 5 · token: 39995 giriş + 698 çıkış = 40693
Aşama süreleri (ms): transcript_fetch_ms=1827.9, clean_ms=9.4, llm_questions_ms=12508.8, quote_verify_ms=36.5, writing_check_ms=1.4, total_ms=14384.2

=== Koşul: rag ===
İstem: questions-v2 · model: gpt-4o-mini · k: 5 · parçalama: fixed-150-30 · gömme: BAAI/bge-m3
Konu başına sonuç:
  - Kemosentez Nedir?: ok · bağlam 759 kelime
      chunk 10 · 547.64–614.52 sn (9:07–10:14) · skor 0.6110
      chunk 13 · 712.44–786.84 sn (11:52–13:06) · skor 0.6089
      chunk 21 · 1152.96–1229.04 sn (19:12–20:29) · skor 0.5954
      chunk 14 · 769.40–839.20 sn (12:49–13:59) · skor 0.5946
      chunk 26 · 1426.40–1492.00 sn (23:46–24:52) · skor 0.5764
  - Hidrotermal Bacalar ve Canlılar: ok · bağlam 759 kelime
      chunk 2 · 101.52–176.88 sn (1:41–2:56) · skor 0.5931
      chunk 8 · 444.92–511.88 sn (7:24–8:31) · skor 0.5541
      chunk 4 · 216.84–289.48 sn (3:36–4:49) · skor 0.5461
      chunk 3 · 156.20–234.16 sn (2:36–3:54) · skor 0.5439
      chunk 5 · 271.60–349.04 sn (4:31–5:49) · skor 0.5150
  - Kemosentetik Canlıların Özellikleri: ok · bağlam 755 kelime
      chunk 4 · 216.84–289.48 sn (3:36–4:49) · skor 0.6295
      chunk 26 · 1426.40–1492.00 sn (23:46–24:52) · skor 0.6208
      chunk 10 · 547.64–614.52 sn (9:07–10:14) · skor 0.6203
      chunk 13 · 712.44–786.84 sn (11:52–13:06) · skor 0.6179
      chunk 16 · 881.72–947.84 sn (14:41–15:47) · skor 0.6129
  - Fotosentez ve Kemosentez Farkları: ok · bağlam 764 kelime
      chunk 21 · 1152.96–1229.04 sn (19:12–20:29) · skor 0.7176
      chunk 18 · 983.88–1054.84 sn (16:23–17:34) · skor 0.7072
      chunk 19 · 1039.36–1111.44 sn (17:19–18:31) · skor 0.6762
      chunk 26 · 1426.40–1492.00 sn (23:46–24:52) · skor 0.6533
      chunk 13 · 712.44–786.84 sn (11:52–13:06) · skor 0.6475
  - Kemosentez ve Ekosistem: ok · bağlam 760 kelime
      chunk 10 · 547.64–614.52 sn (9:07–10:14) · skor 0.5573
      chunk 13 · 712.44–786.84 sn (11:52–13:06) · skor 0.5464
      chunk 26 · 1426.40–1492.00 sn (23:46–24:52) · skor 0.5361
      chunk 18 · 983.88–1054.84 sn (16:23–17:34) · skor 0.5350
      chunk 5 · 271.60–349.04 sn (4:31–5:49) · skor 0.5326
Sonuç sayıları: {'ok': 5, 'empty': 0, 'invalid': 0, 'duplicate': 0}
Dönen soru: 5 / 5 · alıntısı transkriptte bulunan: 5
Yazım kuralı işaretleri: 0 · yok
Toplam süre: 95346.0 ms · model çağrısı: 5 · token: 12143 giriş + 872 çıkış = 13015
Aşama süreleri (ms): transcript_fetch_ms=11840.6, clean_ms=10.5, index_ms=88.7, retrieval_ms=71818.9, llm_questions_ms=11348.8, quote_verify_ms=25.4, writing_check_ms=2.6, total_ms=95346.0

=== Aynı konuda iki koşulun soruları ===
| Konu | full sorusu | full doğru cevap | rag sorusu | rag doğru cevap | full kaynak | rag kaynak |
|---|---|---|---|---|---|---|
| Kemosentez Nedir? | Kemosentez yapan canlılar hangi tür enerji kaynağını kullanarak besin üretirler? | Kimyasal enerji | Kemosentez yapan canlılar hangi hücre yapısına sahiptir? | Prokaryot hücre yapısına | 11:33 | 9:38 |
| Hidrotermal Bacalar ve Canlılar | Hidrotermal bacaların etrafında hangi canlılar kemosentez yaparak besin üretir? | Yengeçler | Hidrotermal bacaların etrafında hangi tür canlılar yaşayabilir? | Kemosentetik canlılar | 4:07 | 3:44 |
| Kemosentetik Canlıların Özellikleri | Kemosentetik canlılar hangi enerji kaynağını kullanarak besin üretimi gerçekleştirir? | Kimyasal enerji | Kemosentetik canlılar hangi tür hücre yapısına sahiptir? | Prokaryot | 11:33 | 9:38 |
| Fotosentez ve Kemosentez Farkları | Kemosentetik canlılar hangi enerji kaynağını kullanarak besin üretirler? | Kimyasal enerji | Fotosentez ile kemosentez arasındaki temel fark nedir? | Fotosentezde güneş ışığı kullanılır, kemosentezde kimyasal enerji kullanılır. | 11:33 | 18:00 |
| Kemosentez ve Ekosistem | — | — | Kemosentez yapan canlıların hücre yapısı nedir? | Prokaryot hücre yapısına sahiptirler | — | 9:38 |
```

## Özet tablo

| | full | rag |
|---|---|---|
| Konu başına sonuç | ok 4, duplicate 1 ("Kemosentez ve Ekosistem") | ok 5 |
| Dönen soru / alıntısı transkriptte bulunan | 4 / 4 | 5 / 5 |
| Yazım kuralı işaretleri | 0 | 0 |
| Model çağrısı | 5 | 5 |
| Token (giriş + çıkış) | 39995 + 698 = 40693 | 12143 + 872 = 13015 |
| Bağlamın kelime sayısı (konu başına) | 3287 | 755–764 |
| Toplam süre | 14384,2 ms | 95346,0 ms |

**RAG süresi hakkında not:**
- **Model ilk erişimde yüklendi:** Dizin 7a denemesinden önbellekteydi (`index_ms` 88,7 ms, yeniden gömme yok). Bu yüzden BGE-M3 modeli ilk erişim sorgusunda yüklendi; `retrieval_ms` (71818,9 ms) bu yüklemeyi de içeriyor.
- **Transkript çekme süreleri farklı:** İki koşulda transkript çekme süresi de farklı (1827,9 ms / 11840,6 ms). Bu süre YouTube isteğine ait.

## Aynı konuda iki koşulun soruları

Yorum yazılmadı; değerlendirmeyi kullanıcı yapacak.

| Konu | full sorusu | full doğru cevap | rag sorusu | rag doğru cevap | full kaynak | rag kaynak |
|---|---|---|---|---|---|---|
| Kemosentez Nedir? | Kemosentez yapan canlılar hangi tür enerji kaynağını kullanarak besin üretirler? | Kimyasal enerji | Kemosentez yapan canlılar hangi hücre yapısına sahiptir? | Prokaryot hücre yapısına | 11:33 | 9:38 |
| Hidrotermal Bacalar ve Canlılar | Hidrotermal bacaların etrafında hangi canlılar kemosentez yaparak besin üretir? | Yengeçler | Hidrotermal bacaların etrafında hangi tür canlılar yaşayabilir? | Kemosentetik canlılar | 4:07 | 3:44 |
| Kemosentetik Canlıların Özellikleri | Kemosentetik canlılar hangi enerji kaynağını kullanarak besin üretimi gerçekleştirir? | Kimyasal enerji | Kemosentetik canlılar hangi tür hücre yapısına sahiptir? | Prokaryot | 11:33 | 9:38 |
| Fotosentez ve Kemosentez Farkları | Kemosentetik canlılar hangi enerji kaynağını kullanarak besin üretirler? | Kimyasal enerji | Fotosentez ile kemosentez arasındaki temel fark nedir? | Fotosentezde güneş ışığı kullanılır, kemosentezde kimyasal enerji kullanılır. | 11:33 | 18:00 |
| Kemosentez ve Ekosistem | — | — | Kemosentez yapan canlıların hücre yapısı nedir? | Prokaryot hücre yapısına sahiptirler | — | 9:38 |

## Kullanıcı kontrolü

- **Kontrol edilen soru:** Full koşulundaki "Hidrotermal bacaların etrafında hangi canlılar kemosentez yaparak besin üretir?" sorusu. Doğru cevap "Yengeçler" verilmiş.
- **Videodaki metin:** Kullanıcı videoyu 4:07'den kontrol etti. Videoda şöyle deniyor: "kemosentez yapan bakterilerle beslenen farklı biyolojik canlılara (karides, yengeç, midye, denizyıldızı vb.)".
- **Sonuç: sorunun doğru cevabı hatalı.** Kemosentezi bakteriler yapıyor, yengeçler onlarla besleniyor.
- **Neden doğrulanmış görünüyor:** Alıntı transkriptte bulunduğu için soru doğrulanmış görünüyor. Bu, alıntının transkriptte bulunmasının cevabın doğruluğunu göstermediğine bir örnek.
- **Kapsam:** Tek soru, tek kullanıcı kontrolü; başka soru kontrol edilmedi.

## Sınırlar

- Tek video, tek çalıştırma, 5 konu (özet servisi 5 konu döndürdü; plan en çok 6 diyordu).
- Kalite ölçülmedi.
- Konular özet servisinden geldi.
