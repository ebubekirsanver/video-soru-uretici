# Bulgular

Bu klasör, sistemin gerçek ders videolarıyla yapılan denemelerinin kaydıdır. Her test turunun bir bulgu dosyası (`.md`) ve `POST /api/questions` çağrısının değiştirilmemiş ham yanıtları (`.json`) vardır. Bulgu dosyaları ne ölçüldüğünü, nasıl ölçüldüğünü ve sonuçların sınırlarını anlatır. Bunlar ön denemelerdir; ölçülü karşılaştırmalar Aşama 15'te yapılacaktır.

Tüm testler Aşama 6'nın RAG'siz taban çizgisiyle yapıldı: gpt-4o-mini, istem `questions-v1`, `count: 5`, `transcript_mode: clean`.

## Test turları

| Test | Video | Kod durumu | Sonuç | Elle zaman kontrolü | Dosyalar |
|---|---|---|---|---|---|
| Test 1 (A) · ilk çalıştırma | Kemosentez (`109kCbVtU1U`) | İlk Aşama 6 kodu: zaman 30 sn'lik blok başlangıcından, 5 kelimeden kısa alıntı reddediliyor, kenar kırpma yok | 4 soru, **2/4 doğrulandı** | Soru 3'ün cümlesi elle kontrol edildi (model `[591]` dedi, cümle 7:15'te başlayan bölümde) | [asama-6-test-1.md](asama-6-test-1.md) (A bölümü), [JSON](asama-6-test-1-kemosentez.json) |
| Test 1 (B) · yeniden ölçüm | Kemosentez (`109kCbVtU1U`) | Tanıdan sonraki kurallar: segment tabanlı zaman, 3-4 kelimede tek geçiş, en fazla 2 kelimelik kenar kırpma | Aynı 4 sorunun yeni kurallarla yeniden ölçümü: **4/4**. **Model yeniden çalıştırılmadı.** | Yeni ölçüm yok | [asama-6-test-1.md](asama-6-test-1.md) (B bölümü) |
| Test 2 | Kemosentez (`109kCbVtU1U`) ve tarih (`aaCHLYO3Fzg`) | Kural değişikliklerinden sonraki ilk gerçek çalıştırmalar | Kemosentez 4 soru + tarih 5 soru: **9/9 doğrulandı** | 6 sorunun zamanı elle kontrol edildi, 6'sı doğru; saniyesi ölçülen 4'ünde kod cümleden 1,5-5,4 sn önce başlatıyor (ortalama ~2,6 sn) | [asama-6-test-2.md](asama-6-test-2.md), [kemosentez JSON](asama-6-test-2-kemosentez.json), [tarih JSON](asama-6-test-2-tarih.json) |
| Aşama 12d · tarayıcı testi 1 | Kemosentez (`109kCbVtU1U`) | 12d arayüzünden ("Soruları üret"), istem `questions-v1` | 5 soru, 5'inin alıntısı transkriptte bulundu. **Soru 2'de alıntı konuyla ilgili ama doğru cevabı doğrudan söylemiyor (elle etiket: kısmen).** | 2 sorunun (Soru 1, 2) kaynak süresi videoda açılıp kontrol edildi; kalan 3'ü kontrol edilmedi; saniye ölçülmedi | [asama-12d-test-1.md](asama-12d-test-1.md), [JSON](asama-12d-test-1.json) |
| Aşama 9 · destek kontrolü denemesi 1 | Kemosentez (`109kCbVtU1U`), Aşama 12d testinin 5 sorusu (yeniden üretilmeden) | Alıntı-cevap destek kontrolü, istem `support-v1` | Elle etiketler (kullanıcı, yalnızca alıntıya bakarak, model etiketlerini görmeden): 4 destekliyor, 1 kısmen. Model etiketleri (tek çalıştırma): 3 destekliyor, 2 desteklemiyor. Eşleşme: 5 sorunun 3'ünde aynı, 2'sinde farklı. | Yok (bu deneme zamanı değil, alıntı-cevap desteğini inceliyor) | [asama-9-destek-kontrolu-1.md](asama-9-destek-kontrolu-1.md), [JSON](asama-9-destek-kontrolu-1.json), [betik](asama-9-destek-kontrolu-1.py) |
| Aşama 9 · destek kontrolü denemesi 2 | Kemosentez (`109kCbVtU1U`) ve tarih (`aaCHLYO3Fzg`), Test 2'nin 9 sorusu (yeniden üretilmeden) | Alıntı-cevap destek kontrolü, istem `support-v1` | Elle etiketler (kullanıcı, yalnızca alıntıya bakarak, model sonuçlarını görmeden): 7 destekliyor, 2 kısmen; iki etiket asistanın önceki bulgu notlarına dikkat çekmesiyle "destekliyor"dan "kısmen"e değiştirildi (dürüstlük notu dosyada). Model etiketleri (tek çalıştırma): 8 destekliyor, 1 desteklemiyor. Eşleşme: 9 sorunun 7'sinde aynı, 2'sinde farklı. Deneme 1 ile birleşik 14 soruda: 10 aynı, 4 farklı. | Yok (bu deneme zamanı değil, alıntı-cevap desteğini inceliyor) | [asama-9-destek-kontrolu-2.md](asama-9-destek-kontrolu-2.md), [JSON](asama-9-destek-kontrolu-2.json), [betik](asama-9-destek-kontrolu-2.py) |
| Genelleme denemesi 1 | Matematik (`edSvMQ77TmU`), edebiyat (`fgOxbhEMnQQ`), python (`CEr_UiR4Gvk`), ingilizce (`FetnCoTS9qY`) | `questions-v1`, `check_support: false`; video başına tek çalıştırma | Alıntısı transkriptte bulunan: matematik 4/5, edebiyat 5/5, python 5/5, ingilizce 4/5. İngilizce transkriptte "used to" 0, "yüz" 25 kez geçiyor. Soru kalitesi ve özet doğruluğu ölçülmedi. | Yok | [genelleme-denemesi-1.md](genelleme-denemesi-1.md), JSON: [matematik](genelleme-1-matematik.json), [edebiyat](genelleme-1-edebiyat.json), [python](genelleme-1-python.json), [ingilizce](genelleme-1-ingilizce.json) |
| Aşama 9 · destek kontrolü denemesi 3 | Genelleme denemesi 1'in 4 videosu, alıntısı doğrulanmış 18 soru (yeniden üretilmeden) | Alıntı-cevap destek kontrolü, istem `support-v1` | Elle etiketler (kullanıcı, yalnızca alıntıya bakarak, model sonuçlarını görmeden): 14 destekliyor, 3 desteklemiyor, 1 belirsiz (ingilizce S3, eşleşme sayımı dışı). Model etiketleri (tek çalıştırma, 18 çağrı): sayıma giren 17 soruda 11 aynı, 6 farklı. Deneme 1+2+3 birleşik: sayıma giren 31 soruda 21 aynı, 10 farklı. | Yok (bu deneme zamanı değil, alıntı-cevap desteğini inceliyor) | [asama-9-destek-kontrolu-3.md](asama-9-destek-kontrolu-3.md), [JSON](asama-9-destek-kontrolu-3.json), [betik](asama-9-destek-kontrolu-3.py) |
| Doğrulama yanlış red 1 | Kemosentez (`109kCbVtU1U`), Aşama 12e tarayıcı testindeki bir çalıştırma | Güncel alıntı doğrulama kuralları (`quotes.py`), `questions-v1` | Transkriptte bulunan bir alıntı reddedildi: alıntıda "350-400 S D", transkriptte "350400 S D"; normalleştirmede tire kelimeyi ikiye bölüyor, fark ortada olduğu için kırpmayla kapanmıyor. Tek örnek; düzeltme uygulanmadı. | Yok | [dogrulama-yanlis-red-1.md](dogrulama-yanlis-red-1.md), [JSON](dogrulama-yanlis-red-1.json) |
| Doğrulama yanlış red 2 | Genelleme denemesi 1'deki iki doğrulanamayan soru: matematik S3 (`edSvMQ77TmU`), ingilizce S5 (`FetnCoTS9qY`) | Güncel alıntı doğrulama kuralları (`quotes.py`); inceleme, model çağrısı yok | 2 soru incelendi: (a) doğrulayıcı yanlış reddetti 0, (b) model alıntıyı değiştirdi 2, (c) belirsiz 0. Matematik S3: iki ayrı yer birleştirilmiş, sıra sayıları yazıyla (transkript rakamla). İngilizce S5: tek kelime farkı ("negatifi" / "negatif"). | Yok | [dogrulama-yanlis-red-2.md](dogrulama-yanlis-red-2.md) |
| Aşama 12e · tarayıcı gözlemi 1 | Kemosentez (`109kCbVtU1U`), 19 Ekim 2026 | 12e arayüzü, destek kontrolü açık (`support-v1`), `questions-v1` | Ölçüm değil gözlem (kör etiket yok, tek çalıştırma). 5 sorunun 5'i doğrulandı; destek kontrolü 3 desteklemiyor, 2 destekliyor. Kutu, kilit ve alt not görüldü; "kısmen", "kontrol edilemedi" ve dar ekran görülmedi. | Yok | [asama-12e-tarayici-gozlemi-1.md](asama-12e-tarayici-gozlemi-1.md) |

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
