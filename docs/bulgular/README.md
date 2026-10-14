# Bulgular

Bu klasör, sistemin gerçek ders videolarıyla yapılan denemelerinin kaydıdır. Her test turunun bir bulgu dosyası (`.md`) ve `POST /api/questions` çağrısının değiştirilmemiş ham yanıtları (`.json`) vardır. Bulgu dosyaları ne ölçüldüğünü, nasıl ölçüldüğünü ve sonuçların sınırlarını anlatır. Bunlar ön denemelerdir; ölçülü karşılaştırmalar Aşama 15'te yapılacaktır.

Tüm testler Aşama 6'nın RAG'siz taban çizgisiyle yapıldı: gpt-4o-mini, istem `questions-v1`, `count: 5`, `transcript_mode: clean`.

## Test turları

| Test | Video | Kod durumu | Sonuç | Elle zaman kontrolü | Dosyalar |
|---|---|---|---|---|---|
| Test 1 (A) · ilk çalıştırma | Kemosentez (`109kCbVtU1U`) | İlk Aşama 6 kodu: zaman 30 sn'lik blok başlangıcından, 5 kelimeden kısa alıntı reddediliyor, kenar kırpma yok | 4 soru, **2/4 doğrulandı** | Soru 3'ün cümlesi elle kontrol edildi (model `[591]` dedi, cümle 7:15'te başlayan bölümde) | [asama-6-test-1.md](asama-6-test-1.md) (A bölümü), [JSON](asama-6-test-1-kemosentez.json) |
| Test 1 (B) · yeniden ölçüm | Kemosentez (`109kCbVtU1U`) | Tanıdan sonraki kurallar: segment tabanlı zaman, 3-4 kelimede tek geçiş, en fazla 2 kelimelik kenar kırpma | Aynı 4 sorunun yeni kurallarla yeniden ölçümü: **4/4**. **Model yeniden çalıştırılmadı.** | Yeni ölçüm yok | [asama-6-test-1.md](asama-6-test-1.md) (B bölümü) |
| Test 2 | Kemosentez (`109kCbVtU1U`) ve tarih (`aaCHLYO3Fzg`) | Kural değişikliklerinden sonraki ilk gerçek çalıştırmalar | Kemosentez 4 soru + tarih 5 soru: **9/9 doğrulandı** | 6 sorunun zamanı elle kontrol edildi, 6'sı doğru; saniyesi ölçülen 4'ünde kod cümleden 1,5-5,4 sn önce başlatıyor (ortalama ~2,6 sn) | [asama-6-test-2.md](asama-6-test-2.md), [kemosentez JSON](asama-6-test-2-kemosentez.json), [tarih JSON](asama-6-test-2-tarih.json) |
| Aşama 12d · tarayıcı testi 1 | Kemosentez (`109kCbVtU1U`) | 12d arayüzünden ("Soruları üret"), istem `questions-v1` | 5 soru, 5'inin alıntısı transkriptte bulundu. **Soru 2'de kaynak, doğru cevabı desteklemiyor.** | 2 sorunun (Soru 1, 2) kaynak süresi videoda açılıp kontrol edildi; kalan 3'ü kontrol edilmedi; saniye ölçülmedi | [asama-12d-test-1.md](asama-12d-test-1.md), [JSON](asama-12d-test-1.json) |

## Okuma sırası

1. **Bu dosya:** hangi testin neyi ölçtüğü.
2. **[asama-6-test-1.md](asama-6-test-1.md):**
   - A: ilk çalıştırma
   - B: aynı soruların yeniden ölçümü
   - Bulgu 1-6: tanı ve bu tanıdan çıkan kural değişiklikleri
   - Sınırlar
3. **[asama-6-test-2.md](asama-6-test-2.md):**
   - C.1 ve C.2: iki videonun soru tabloları
   - C.3: ikinci test bulguları
   - Sınırlar

   Test 2, kuralların Test 1'de ayarlanmasından sonraki ilk denemedir; Test 1 ile karşılaştırılarak okunmalıdır.

## Genel sınırlar

- **Örneklem küçük:** Test 1'de tek video ve 4 soru, Test 2'de 2 video ve 9 soru var. Her video için tek çalıştırma yapıldı. Sonuçlar istatistiksel değildir.
- **Kurallar Test 1'in 4 sorusuna bakılarak ayarlandı.** Test 1 (B)'deki 4/4 sonucu kuralların başarısını göstermez. Test 2'de hiç ret olmadığı için kuralların meşru alıntıyı haksız yere reddetmeme yönü henüz sınanmadı.
- **`verified=true` doğruluk kanıtı değildir:** yalnızca sorunun dayandığı alıntının videoda geçtiğini gösterir. Sorunun ya da cevabın doğruluğunu göstermez.
- **Elle zaman ölçümü yaklaşık ±1 sn hassasiyetlidir.** Her sorunun zamanı kontrol edilmedi.
- **Test 2 kayıtları eski biçimdedir:** modelin özgün alıntısını (`model_quote`) içermez, bu yüzden kırpılan sözcükler görülemez. Bu bilgi sonraki çalıştırmaların kayıtlarına eklendi.
- **Soru kalitesini yalnızca geliştirici inceledi;** öğretmen değerlendirmesi Aşama 15'e bırakıldı.
