# Doğrulama yanlış red 1 · Transkriptte bulunan alıntının reddedilmesi

**Tarih:** 17 Ekim 2026
**Çalıştırma:** Aşama 12e tarayıcı testi sırasında `POST /api/questions` · video `109kCbVtU1U` (kemosentez) · `count: 5` · `transcript_mode: clean` · `check_support: true` · istem `questions-v1`
**Ham sonuç:** [dogrulama-yanlis-red-1.json](dogrulama-yanlis-red-1.json) (`backend/runs/20261017-211257-109kCbVtU1U-questions.json` kaydının birebir kopyası, kayıt sürümü 3)

> Bu dosya yalnızca incelemede görülenleri içerir. İnceleme sırasında model çağrısı yapılmadı; transkript YouTube'dan yalnızca bellekte okundu.

## Soru (kayıttan, olduğu gibi)

- **Soru 2:** *"Hidrotermal bacaların iç kısımlarındaki sıcaklık aralığı nedir?"*
- **Seçenekler:** `200-300 °C` · `400-450 °C` · `350-400 °C` · `100-200 °C` (doğru cevap: `350-400 °C`)
- **source_quote:** `İç kısımlarında 350-400 S D, ağız kısımlarında ise yaklaşık 150 S D sıcaklığa sahip olan bu hidrotermal bacalar...`
- **quote_audit'teki modelin alıntısı (model_quote):** `[156] İç kısımlarında 350-400 S D, ağız kısımlarında ise yaklaşık 150 S D sıcaklığa sahip olan bu hidrotermal bacalar...`
- **quote_match:** `null` · **verified:** `false` · **source_start_seconds:** `null`
- Destek kontrolü bu soru için çağrı yapmadı (`kontrol edilmedi`).

## Transkriptteki yazım

Ham transkriptte "350" geçen segment ve komşuları:

| Başlangıç (sn) | Metin |
|---|---|
| 161,56 | `tabanında keşfedildi. İç kısımlarında` |
| **164,48** | **`350400 S D, ağız kısımlarında ise`** |
| 168,00 | `yaklaşık 150 S D sıcaklığa sahip olan bu` |

Transkriptte **"350400 S D"** yazıyor (tire yok, bitişik).

## Doğrulama neden başarısız oldu

- `quotes.normalize` noktalama işaretlerini boşluğa çeviriyor; tire de noktalama sayılıyor. Bu yüzden alıntıdaki `350-400` iki kelime oluyor: `350`, `400`. Transkriptteki `350400` ise tek kelime.
- Normalleştirilmiş alıntı (19 kelime) transkriptle kelime kelime karşılaştırıldığında tek fark bu: alıntının geri kalanı (`iç kısımlarında` ve `s d ağız kısımlarında ise yaklaşık 150 s d sıcaklığa sahip olan bu hidrotermal bacalar`) transkriptle aynı.
- Kodda kenar kırpma en fazla 2 kelime (`MAX_TRIM_WORDS=2`) ve yalnızca kenarlardan yapılıyor. Fark alıntının ortasında (3. ve 4. kelime) olduğu için kırpmayla kapanmıyor.
- Uygulamanın `QuoteLocator.match` fonksiyonu aynı transkriptle yeniden çalıştırıldığında yine `None` döndü.

**Dürüstlük notu:** İlk tahmin, başarısızlığın "°C" ile "S D" farkından kaynaklandığıydı. İnceleme bunu çürüttü: alıntıda ve transkriptte ikisi de "S D". "°C" yalnızca soru metninde ve seçeneklerde geçiyor; bunlar alıntı aramasına girmiyor.

## Sonuç

Bu, **güncel kurallarla** (Bulgu 6'daki kenar kırpma ve kısa alıntı kuralından sonra) doğrulama kodunun transkriptte bulunan bir alıntıyı reddettiği ilk gözlenen örnektir. Daha önceki bulgularda kuralların meşru alıntıyı haksız yere reddetmeme yönünün sınanmadığı yazılmıştı ([asama-6-test-2.md](asama-6-test-2.md), Sınırlar). Kurallar değişmeden önce, Test 1'de de iki meşru alıntı reddedilmişti ([asama-6-test-1.md](asama-6-test-1.md), Bulgu 2); güncel kurallar o iki örnek üzerine eklendi.

## Olası düzeltme (uygulanmadı)

Sayı aralıklarında tire / bitişik yazım farkını normalleştirmek bir aday. Tek örneğe göre kural eklemek riskli; daha fazla örnek toplanmadan karar verilmeyecek.

## Sınırlar

- Tek örnek; bu tür yanlış reddin sıklığı bilinmiyor.
- Bugünkü diğer doğrulanamayan iki sorunun (genelleme denemesi 1: matematik S3, ingilizce S5) nedeni henüz incelenmedi.
- Düzeltme uygulanmadı; kod (`quotes.py`) değiştirilmedi.
