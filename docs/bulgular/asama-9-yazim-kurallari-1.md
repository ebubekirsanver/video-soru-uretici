# Aşama 9 · Yazım kuralları değerlendirmesi 1

## Ölçüt (değerlendirme çalıştırılmadan önce yazıldı ve commit'lendi)

- **İşaret doğru:** Soru, ilgili kuralın Moore vd. (2023) Tablo 1'deki tanımını gerçekten ihlal ediyor.
- **İşaret yanlış:** Soru, ilgili kuralın tanımını ihlal etmiyor.
- **Neyi ölçer:** Bu değerlendirme yalnızca yanlış pozitifleri ölçer.
- **Neyi ölçmez:** İşaretlenmeyen sorular etiketlenmediği için kaçırılan hatalar ölçülmez.

## Deneme

- **Tarih:** 20 Ekim 2026.
- **Kural sürümü:** `writing-rules-v1`. Betik çalıştırıldığında kod commit'i `12a9a63` idi; betiğin kendisi henüz commit'lenmemişti.
- **Betik ve çıktı:** [asama-9-yazim-kurallari-1.py](asama-9-yazim-kurallari-1.py), [JSON](asama-9-yazim-kurallari-1.json). Betik bir kez çalıştırıldı, model çağrısı yok.
- **Hangi sorular:** `docs/bulgular` altındaki, soru listesi içeren commit'li JSON dosyalarındaki son sorular (kayıttaki seçenek sırası ve `correct_index` ile).
- **Tekrarlar:** Aynı soru metni (normalize sonrası) bir kez sayıldı; dosya adı sırasına göre ilk görülen tutuldu.
- **Atlanan dosyalar:** Destek kontrolü deney dosyaları (`asama-9-destek-kontrolu-1/2/3.json`) soru listesi içermediği için atlandı.
- **Kurallar:** Sonuçlara bakılarak değiştirilmedi.

## Taranan sorular

**36 benzersiz soru** tarandı. 6 soru başka bir dosyada aynı metinle geçtiği için atlandı.

| Dosya | Dosyadaki soru | Sayılan (benzersiz) |
|---|---|---|
| `asama-12d-test-1.json` | 5 | 5 |
| `asama-6-test-1-kemosentez.json` | 4 | 2 |
| `asama-6-test-2-kemosentez.json` | 4 | 2 |
| `asama-6-test-2-tarih.json` | 5 | 5 |
| `dogrulama-yanlis-red-1.json` | 4 | 2 |
| `genelleme-1-edebiyat.json` | 5 | 5 |
| `genelleme-1-ingilizce.json` | 5 | 5 |
| `genelleme-1-matematik.json` | 5 | 5 |
| `genelleme-1-python.json` | 5 | 5 |

## Kural başına işaret sayısı

İşaretlenen soru sayısı: **12**. Hiçbir soruda birden fazla işaret yok.

| Kural | Ad | İşaret |
|---|---|---|
| 3 | None of the above | 0 |
| 4 | Longest option correct | 3 |
| 6 | True/false question | 0 |
| 9 | All of the above | 0 |
| 10 | Fill-in-blank | 0 |
| 11 | Absolute terms | 0 |
| 12 | Word repeats | 0 |
| 14 | Complex or K-type | 0 |
| 16 | Lost sequence | 5 |
| 17 | Vague terms | 0 |
| 19 | Negative worded | 4 |

## 16. kural (Lost sequence) için not

- **Sorular eski:** Taranan sorular, sayısal seçeneklerin sıralanmasından (`shuffle_options` değişikliği, 20 Ekim 2026) önce üretildi. O zaman kod sayısal seçenekleri de rastgele karıştırıyordu.
- **Karıştırma kaynaklı olabilir:** Bu yüzden 16. kural işaretleri modelin değil, karıştırmanın sonucu olabilir. Bu deneme ikisini ayırt edemez; modelin özgün seçenek sırası kayıtlarda yok.
- **Bugünkü kodla:** Aynı sorular bugün üretilseydi, tamamı sayısal olan seçenekler küçükten büyüğe sıralanacaktı.
- **Sürüm numaraları:** "Python 2.7", "Python 3.11" gibi seçenekler kodda ondalık sayı olarak okunur (aynı ön ek "python", nokta ondalık).

## İşaretlenen sorular

Etiket sütununu kullanıcı dolduracak (yukarıdaki ölçüte göre: doğru / yanlış).

| # | Video | Soru | Seçenekler | Doğru seçenek | Kural | Detail | Etiket (doğru/yanlış) |
|---|---|---|---|---|---|---|---|
| 1 | kemosentez (`109kCbVtU1U`), `asama-12d-test-1.json` S3 | Kemosentez sırasında hangi madde açığa çıkmaz? | Su / Oksijen / Enerji / Karbondioksit | Oksijen | 19 · Negative worded | Olumsuz ifade: çıkmaz |  |
| 2 | kemosentez (`109kCbVtU1U`), `asama-6-test-1-kemosentez.json` S2 | Hidrotermal bacaların bulunduğu yerler hakkında hangi ifade doğrudur? | Işık vardır / Yüzeyde bulunur / Sıcaklık 0°C'dir / Okyanus tabanında yer alır | Okyanus tabanında yer alır | 4 · Longest option correct | Doğru seçenek 26 karakter, en uzun çeldirici 16 karakter |  |
| 3 | tarih (`aaCHLYO3Fzg`), `asama-6-test-2-tarih.json` S1 | Malazgirt Savaşı hangi yıllarda gerçekleşmiştir? | 1081 / 1066 / 1096 / 1071 | 1071 | 16 · Lost sequence | Sayısal seçenekler sıralı değil: 1081, 1066, 1096, 1071 |  |
| 4 | tarih (`aaCHLYO3Fzg`), `asama-6-test-2-tarih.json` S2 | Danışmentlilerin kurulduğu bölgeler arasında hangisi yer almaz? | Amasya / İzmir / Kayseri / Tokat | İzmir | 19 · Negative worded | Olumsuz ifade: almaz |  |
| 5 | ingilizce (`FetnCoTS9qY`), `genelleme-1-ingilizce.json` S1 | Yüz kalıbı hangi durumlarda kullanılır? | Sadece olumlu cümlelerde / Gelecek zaman için / Geçmişte sürekli yapılan ama artık yapılmayan eylemler için / Sadece olumsuz cümlelerde | Geçmişte sürekli yapılan ama artık yapılmayan eylemler için | 4 · Longest option correct | Doğru seçenek 59 karakter, en uzun çeldirici 25 karakter |  |
| 6 | ingilizce (`FetnCoTS9qY`), `genelleme-1-ingilizce.json` S4 | Yüz kalıbı ile olumlu bir cümle kurmak için hangi özne kullanılmaz? | It / She / He / I | It | 19 · Negative worded | Olumsuz ifade: kullanılmaz |  |
| 7 | ingilizce (`FetnCoTS9qY`), `genelleme-1-ingilizce.json` S5 | Yüz kalıbı ile olumsuz cümle kurarken hangi kelime kullanılmaz? | Aren't / Did / Didn't / Wasn't | Didn't | 19 · Negative worded | Olumsuz ifade: kullanılmaz |  |
| 8 | matematik (`edSvMQ77TmU`), `genelleme-1-matematik.json` S3 | Açıortay teoremi ile ilgili oranlar nasıl yazılır? | Kenarortay ile / Kenar uzunlukları ile / Açı ölçüleri ile / Dış açı ile | Kenar uzunlukları ile | 4 · Longest option correct | Doğru seçenek 21 karakter, en uzun çeldirici 16 karakter |  |
| 9 | python (`CEr_UiR4Gvk`), `genelleme-1-python.json` S1 | Python hangi yıl yayınlanmıştır? | 1991 / 1994 / 2000 / 1989 | 1991 | 16 · Lost sequence | Sayısal seçenekler sıralı değil: 1991, 1994, 2000, 1989 |  |
| 10 | python (`CEr_UiR4Gvk`), `genelleme-1-python.json` S2 | Python hangi sürümünü bu eğitimde kullanacağını belirtmiştir? | Python 2.7 / Python 3.11 / Python 3.13 / Python 3.12 | Python 3.13 | 16 · Lost sequence | Sayısal seçenekler sıralı değil: Python 2.7, Python 3.11, Python 3.13, Python 3.12 |  |
| 11 | python (`CEr_UiR4Gvk`), `genelleme-1-python.json` S4 | Python'un ilk resmi sürümü ne zaman çıkmıştır? | 2000 / 2008 / 1994 / 1991 | 1994 | 16 · Lost sequence | Sayısal seçenekler sıralı değil: 2000, 2008, 1994, 1991 |  |
| 12 | python (`CEr_UiR4Gvk`), `genelleme-1-python.json` S5 | Python 2'nin son sürümü ne zaman çıkmıştır? | 2020 / 2015 / 2008 / 2010 | 2010 | 16 · Lost sequence | Sayısal seçenekler sıralı değil: 2020, 2015, 2008, 2010 |  |

## Sınırlar

- **Ölçülen:** Yalnızca yanlış pozitifler. İşaretlenmeyen 24 soru etiketlenmedi; kaçırılan hatalar ölçülmez.
- **Örneklem:**
  - 5 video, 36 soru.
  - Sorular bağımsız değil: aynı videodan birden çok soru var, kemosentez videosu birden çok çalıştırmada geçiyor.
  - Kural başına işaret sayısı küçük.
- **Tek etiketleyen:** Etiketleri yalnızca kullanıcı verecek.
- **İsabet iddiası yok:** Sonuçlar oran olarak verilmeyecek.
