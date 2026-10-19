# Doğrulama yanlış red 2 · Genelleme denemesindeki iki doğrulanamayan soru

**Tarih:** 19 Ekim 2026 (inceleme). Çalıştırma: 17 Ekim 2026, [genelleme denemesi 1](genelleme-denemesi-1.md).
**Kayıtlar:** [genelleme-1-matematik.json](genelleme-1-matematik.json) (Soru 3), [genelleme-1-ingilizce.json](genelleme-1-ingilizce.json) (Soru 5); kayıt sürümü 3, modelin özgün alıntısı `quote_audit` içinde.
**Yöntem:** [dogrulama-yanlis-red-1.md](dogrulama-yanlis-red-1.md) ile aynı. Kayıtlarda transkript olmadığı için transkript aynı kodla (`fetch_transcript` + `clean_transcript`) yeniden indirildi, yalnızca bellekte tutuldu. Uygulamanın `QuoteLocator.match` fonksiyonu yeniden çalıştırıldı; normalleştirilmiş alıntı, transkriptteki en benzer yerle kelime kelime karşılaştırıldı. Model çağrısı yapılmadı, kod değiştirilmedi.

> Bu dosya yalnızca incelemede görülenleri içerir.

**Sınıflar:** (a) doğrulayıcı transkriptte bulunan alıntıyı yanlış reddetti · (b) model alıntıyı transkripte göre değiştirdi ya da uydurdu · (c) belirsiz.

## Sonuç

| Soru | Sınıf | Fark |
|---|---|---|
| matematik S3 | **(b)** | Model transkriptte ayrı yerlerde geçen iki parçayı tek cümlede birleştirmiş; sıra sayılarını yazıyla yazmış (transkript rakamla yazıyor) |
| ingilizce S5 | **(b)** | Ortada tek kelime farklı: model "negatifi", transkript "negatif" |

**Sayılar:** 2 soru incelendi. (a) 0, (b) 2, (c) 0.

## matematik S3 (`edSvMQ77TmU`)

- **Soru:** *"Açıortay teoremi ile ilgili oranlar nasıl yazılır?"* · doğru cevap: `Kenar uzunlukları ile`
- **source_quote / model_quote (aynı):** `Birinci kolun birinci parçaya oranı, ikinci kolun ikinci parçaya oranı.`
- **quote_match:** `null` · **verified:** `false`
- Yeniden çalıştırılan `QuoteLocator.match`: `None`.

**Transkriptte o bölüm (ham segmentler):**

| Başlangıç (sn) | Metin |
|---|---|
| 352,88 | `Anlaştık mı? Peki neydi açıortay` |
| 354,88 | `teoremi? İşte 1inci kolun 1inci parçaya` |
| 359,36 | `oranı hemen yazalım. Ne? Nereye yazalım?` |
| 361,92 | `Tabii güzel bir soru. Şuraya. Evet.` |
| 364,40 | `2x'in 4'e oranı neydi? 2inci parçanın` |
| 370,04 | `özür dilerim 2inci kolun 2inci parçaya` |
| 372,12 | `oranı.` |

**Görülen farklar:**
1. **Sıra sayılarının yazımı:** Alıntıda `birinci` / `ikinci`, transkriptte `1inci` / `2inci`. `normalize` bu iki yazımı eşlemiyor. Normalleştirilmiş temiz transkriptte "birinci kolun", "ikinci kolun", "birinci parçaya", "ikinci parçaya" 0 kez; "1inci kolun 1inci parçaya oranı" 1 kez, "2inci kolun 2inci parçaya" 1 kez geçiyor.
2. **Birleştirme:** Alıntının iki yarısı transkriptte yan yana değil. İlk yarı 354,88 sn'de, ikinci yarı 370,04 sn'de başlıyor; arada `hemen yazalım. Ne? Nereye yazalım? Tabii güzel bir soru. Şuraya. Evet. 2x'in 4'e oranı neydi? 2inci parçanın özür dilerim` var. Model bu araları atıp iki parçayı tek cümle yapmış.
- Kontrol: ilk yarı transkriptteki rakamlı yazımla (`1inci kolun 1inci parçaya oranı`) verildiğinde `QuoteLocator.match` 354,88 sn'de `exact` eşleşme buluyor.

**Sınıflandırma: (b).** Model alıntıyı transkripte göre değiştirmiş: iki ayrı yeri birleştirmiş. Bu birleştirme yüzünden alıntı rakamlı yazımla verilse bile transkriptte kesintisiz geçmezdi. Sıra sayılarının yazım farkı (yazı / rakam) ayrıca doğrulayıcının eşleyemediği bir fark; tek başına görülseydi red-1'e benzer bir (a) durumu olabilirdi, ama bu soruda belirleyici olan birleştirme.

## ingilizce S5 (`FetnCoTS9qY`)

- **Soru:** *"Yüz kalıbı ile olumsuz cümle kurarken hangi kelime kullanılmaz?"* · doğru cevap: `Didn't`
- **source_quote:** `Burada dikkat etmemiz gereken en önemli nokta şudur negatifi belirtmek için did kelimesini kullanırız ama Özellikle belirtmek istediğim bir nokta vardır`
- **model_quote:** aynı metin, başında `[520]` etiketiyle.
- **quote_match:** `null` · **verified:** `false`
- Yeniden çalıştırılan `QuoteLocator.match`: `None`.

**Transkriptte o bölüm (ham segmentler):**

| Başlangıç (sn) | Metin |
|---|---|
| 497,31 | `Yalın haliyle yazarız Burada dikkat` |
| 499,98 | `etmemiz gereken en önemli nokta şudur` |
| **501,96** | **`negatif belirtmek için did kelimesini`** |
| 504,75 | `kullanırız ama Özellikle belirtmek` |
| 507,12 | `istediğim bir nokta vardır Burası` |

**Kelime kelime karşılaştırma (normalleştirilmiş, 21 kelime):**

| Alıntı | Transkript | Durum |
|---|---|---|
| burada dikkat etmemiz gereken en önemli nokta şudur | aynısı | aynı |
| **negatifi** | **negatif** | farklı |
| belirtmek için did kelimesini kullanırız ama özellikle belirtmek istediğim bir nokta vardır | aynısı | aynı |

- Fark alıntının ortasında (9. kelime). `MAX_TRIM_WORDS=2` kenar kırpması yalnızca kenarlarda çalıştığı için bu farkı kapatmıyor. Normalleştirilmiş temiz transkriptte "negatifi belirtmek" 0 kez geçiyor.

**Sınıflandırma: (b).** Transkripte göre model bir kelimeyi değiştirmiş ("negatif" → "negatifi"). Videoyu dinlemedim; konuşmacının hangi biçimi söylediğini ve transkriptin bu noktada doğru olup olmadığını bilmiyorum (**emin değilim**). Sınıflandırma, transkriptin yazdığına göredir.

## Sınırlar

- 2 soru; tek video başına tek çalıştırma.
- Transkriptler incelemede (19 Ekim) yeniden indirildi; soruların üretildiği andaki (17 Ekim) transkriptle birebir aynı olduğu doğrulanamadı (kayıtlarda transkript yok) — **emin değilim**.
- Videoya bakılmadı; transkriptin konuşmayı doğru yazıp yazmadığı değerlendirilmedi.
- Düzeltme önerisi yapılmadı, kod değiştirilmedi.
