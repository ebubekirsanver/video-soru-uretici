# Pilot 2: questions-v3 ile questions-v4

## Plan (betik çalıştırılmadan önce yazıldı)

- **Amaç:** Pilot 1'de görülen dört soruna karşı açılan `questions-v4` istemini, aynı konu ve düzeylerle `questions-v3` ile yan yana görmek. Ana deney tek istem sürümüyle yapılacak; hangisinin dondurulacağına bu çalıştırmadan sonra kullanıcı karar verecek.
- **Bu bir ÖN GÖZLEM çalışmasıdır:** Kalite ve Bloom uyumu ölçülmez. Rapor yorum içermez; yalnızca sayılar ve sorular yazılır.
- **Tek fark:** İstem sürümü. Konu çıkarma yeniden çalıştırılmaz.

### Videolar (temiz transkript)

Pilot 1'de tamamlanan dört video ve pilot 1 ekinde tamamlanırsa edebiyat ile Python:

| Alan | video_id |
|---|---|
| biyoloji | `109kCbVtU1U` |
| tarih | `aaCHLYO3Fzg` |
| matematik | `edSvMQ77TmU` |
| ingilizce | `FetnCoTS9qY` |
| edebiyat | `fgOxbhEMnQQ` |
| python | `CEr_UiR4Gvk` |

Plan güncellemesi (betik çalıştırılmadan önce, kullanıcı kararı): İlk planda edebiyat ve Python yoktu, çünkü 4 Kasım 2026'da YouTube engeli sürüyordu. Kullanıcı telefonun internetine geçme kararı verdi. Önce pilot 1 eki çalışır; edebiyat ve Python'un konu ve düzeyleri ekteki JSON dosyalarından alınır. Pilot 1 ekinde tamamlanmayan video atlanır ve raporlanır.

### Transkript

- Transkript önbellekten gelir. Önbellekte olmayan video için YouTube'a tek istek atılır; engellenirse ya da alınamazsa video atlanır, raporlanır ve o video için hiç OpenAI çağrısı yapılmaz.
- **Plan yazıldığındaki durum:** `backend/transcripts/` boştu; pilot 1 önbellek eklenmeden önce çalıştı. Engel sürerken betik çalıştırılırsa videolar atlanır.
- Betik önce bütün transkriptleri dener, sonra BGE-M3'ü yükler. Hiçbiri alınamazsa model yüklenmez, OpenAI'a gidilmez.

### Her video için adımlar

1. Konu metinleri (`topics.items[].text`) ve `bloom_levels`, `pilot-1-<alan>.json` dosyasından AYNEN alınır.
2. Sırayla 4 çalıştırma: `v3-full`, `v3-rag`, `v4-full`, `v4-rag`. Her biri bir kez, yeniden deneme yok.
3. `v3` çalıştırmalarının tekrarlanması, aynı istemle sonuçların ne kadar değiştiğini de gösterir.

### Ayarlar

- gpt-4o-mini, sıcaklık 0,2, temiz transkript, `k=5`, `fixed-150-30`, `BAAI/bge-m3`, `similarity-v1` (eşik 0,80), `check_support` kapalı. Pilot 1 ile aynı.
- **Model çağrısı:** Video başına 24 (4 çalıştırma × 6 konu); 6 videoda toplam 144 OpenAI çağrısı.
- **Tahmini maliyet:** Yaklaşık 0,14 USD. Pilot 1'in dört videodaki `full` ve `rag` harcaması (0,046469 USD) iki katı alındı, v4'ün daha uzun sistem istemi eklendi; edebiyat ve Python için video başına yaklaşık 0,02 USD varsayıldı.
- **Maliyet hesabı için sabit fiyat:** Girdi 0,15 USD / 1M token, çıktı 0,60 USD / 1M token (pilot 1 ile aynı). Hesap yalnızca betikte yapılır.

### Her çalıştırma için otomatik hesaplananlar

- **Konu başına sonuç:** `ok` / `empty` / `invalid` / `duplicate`. Boş olanlarda v4'ün `skip_reason` metni.
- **Alıntısı transkriptte bulunan soru sayısı.**
- **Olası cevap kökte (kaba işaret):** Metinler küçük harfe çevrilir, noktalama atılır. Doğru seçenek soru kökünde geçiyorsa ya da doğru seçenekteki 4 harften uzun kelimelerin yarısından fazlası kökte geçiyorsa işaretlenir. Geçme, metin içinde aramadır: "savaşı", "savaşından" içinde bulunur. Durak kelime listesi yoktur.
- **Örnek sızıntısı:** Soru kökü ya da seçeneklerde şu sözcükler geçiyorsa işaretlenir: "Ali", "Ayşe", "iki öğrenci", "basınç", "rüzgâr", "fırıldak", "mum", "termometre", "balon". Liste betik başında sabittir. Ali ve Ayşe büyük harfle, tam kelime olarak aranır. Diğerleri büyük-küçük harf gözetmeden kelime başından aranır, ek alabilir ("balonun"). Konu gerçekten bunlarla ilgiliyse yanlış işaret olabilir.
- **Yazım kuralı işaret sayısı** (`writing-rules-v1`) ve **benzerlik işaretli çift sayısı** (`similarity-v1`).
- **Süre, token ve maliyet.**

### Rapor (bu dosyaya, aşağıdaki işaretin altına)

1. Video × sürüm × koşul özet tablosu.
2. Yaratma düzeyindeki konuların dört çalıştırmadaki sonucu, ayrı tabloda.
3. Üretilen bütün sorular, video ve konu sırasıyla, her koşul için v3 ve v4 yan yana: hedef düzey, soru, seçenekler, doğru cevap, kaynak alıntısı ve zaman, işaretler.
4. Gizli bilgi taraması sonucu.

### Plan güncellemesi: token sınırı ve matematik v4 (yeniden çalıştırmadan önce yazıldı, kullanıcı kararı)

- **Neden:** İlk çalıştırmada matematik `v4-full`, 5. konuda 16384 çıktı token üretti, yanıt geçerli JSON olmadı ve istek 502 verdi; `v4-rag` çalışmadı.
- **Token sınırı:** Konu tabanlı soru üretiminde (v3 ve v4) `max_tokens` 1000 oldu (`QUESTION_MAX_TOKENS`). Yanıt sınıra takılırsa o konu `invalid` sayılır, kayda `truncated: true` yazılır, diğer konular sürer. Konu çıkarma, destek kontrolü ve `questions-v1` çağrılarında sınır yok.
- **Yeniden çalıştırma:** Yalnızca matematik `v4-full` ve `v4-rag`, birer kez; 12 çağrı, tahmini 0,013 USD. Transkript önbellekten gelir.
- **Fark:** Matematiğin v4 çalıştırmaları sınırla, diğer bütün çalıştırmalar sınırsız yapıldı. Sınırsız çalıştırmalarda tamamlanan en uzun yanıt 339 çıktı token idi.
- **Veri:** `pilot-2-matematik.json` içinde v3 sonuçları değişmez. Hatalı ilk `v4-full` çalıştırması ve harcaması `failed_runs` alanında durur; harcamaya dahil, tablolara dahil değildir.

### Betik

- **Dosya:** [pilot-2.py](pilot-2.py). Pilot 1 gibi FastAPI TestClient ile; çalıştırma kayıtları `backend/runs` altına yazılır.
- **Hata:** Bir çalıştırma hata verirse o ana kadar biten çalıştırmalar ve hata video dosyasına yazılır, sonraki videoya geçilir.
- **Çıktılar:** Video başına `pilot-2-<alan>.json`. Dosya varsa o video atlanır, üzerine yazılmaz. Atlanan videonun dosyası da yazılır; o video sonra çalıştırılacaksa dosyası elle kaldırılmalıdır.
- **Gizli bilgi:** Video dosyaları ve rapor CLAUDE.md kural 5'teki kalemler için taranır.

<!-- RAPOR_ISARETI: bu satırın altını pilot-2.py yazar -->

## Çalıştırma

- BGE-M3 yüklenme süresi: 27,2 sn.
- biyoloji: 4 / 4 çalıştırma · transkript kaynağı cache · model gpt-4o-mini.
- tarih: 4 / 4 çalıştırma · transkript kaynağı cache · model gpt-4o-mini.
- matematik: 4 / 4 çalıştırma · transkript kaynağı cache · model gpt-4o-mini.
- ingilizce: 4 / 4 çalıştırma · transkript kaynağı cache · model gpt-4o-mini.
- edebiyat: 4 / 4 çalıştırma · transkript kaynağı cache · model gpt-4o-mini.
- python: 4 / 4 çalıştırma · transkript kaynağı cache · model gpt-4o-mini.

## Video × sürüm × koşul özeti

| Video | Sürüm | Koşul | ok | empty | invalid | duplicate | Alıntısı bulunan | Olası cevap kökte | Örnek sızıntısı | Yazım işareti | Benzer çift | Süre (sn) | Girdi token | Çıktı token | Maliyet (USD) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| biyoloji | v3 | full | 6 | 0 | 0 | 0 | 6 | 0 | 0 | 2 | 1 | 30,0 | 51979 | 1424 | 0,008651 |
| biyoloji | v3 | rag | 6 | 0 | 0 | 0 | 5 | 0 | 0 | 2 | 0 | 22,2 | 18562 | 1384 | 0,003615 |
| biyoloji | v4 | full | 6 | 0 | 0 | 0 | 6 | 1 | 0 | 2 | 0 | 26,9 | 53647 | 1473 | 0,008931 |
| biyoloji | v4 | rag | 6 | 0 | 0 | 0 | 5 | 0 | 0 | 1 | 0 | 22,1 | 20230 | 1408 | 0,003879 |
| tarih | v3 | full | 6 | 0 | 0 | 0 | 4 | 0 | 0 | 3 | 0 | 26,1 | 67680 | 1361 | 0,010969 |
| tarih | v3 | rag | 5 | 1 | 0 | 0 | 4 | 0 | 1 | 0 | 0 | 20,4 | 19561 | 1198 | 0,003653 |
| tarih | v4 | full | 6 | 0 | 0 | 0 | 4 | 0 | 0 | 5 | 0 | 22,0 | 69348 | 1382 | 0,011231 |
| tarih | v4 | rag | 5 | 1 | 0 | 0 | 4 | 1 | 0 | 2 | 0 | 21,3 | 21229 | 1265 | 0,003943 |
| matematik | v3 | full | 5 | 1 | 0 | 0 | 4 | 1 | 0 | 0 | 0 | 27,2 | 51593 | 1131 | 0,008418 |
| matematik | v3 | rag | 5 | 1 | 0 | 0 | 4 | 0 | 0 | 1 | 1 | 20,9 | 18491 | 1200 | 0,003494 |
| matematik | v4 | full | 5 | 1 | 0 | 0 | 3 | 0 | 1 | 2 | 0 | 26,6 | 53261 | 1192 | 0,008704 |
| matematik | v4 | rag | 6 | 0 | 0 | 0 | 5 | 0 | 1 | 3 | 2 | 31,8 | 20159 | 1484 | 0,003914 |
| ingilizce | v3 | full | 6 | 0 | 0 | 0 | 5 | 0 | 0 | 1 | 1 | 21,8 | 23617 | 1344 | 0,004349 |
| ingilizce | v3 | rag | 6 | 0 | 0 | 0 | 6 | 0 | 0 | 1 | 1 | 19,5 | 16961 | 1208 | 0,003269 |
| ingilizce | v4 | full | 5 | 0 | 0 | 1 | 5 | 1 | 0 | 1 | 0 | 20,8 | 25285 | 1378 | 0,004620 |
| ingilizce | v4 | rag | 6 | 0 | 0 | 0 | 5 | 0 | 0 | 1 | 0 | 21,2 | 18629 | 1367 | 0,003615 |
| edebiyat | v3 | full | 6 | 0 | 0 | 0 | 3 | 0 | 0 | 4 | 0 | 21,5 | 35336 | 1386 | 0,006132 |
| edebiyat | v3 | rag | 6 | 0 | 0 | 0 | 4 | 0 | 0 | 3 | 0 | 21,4 | 19333 | 1452 | 0,003771 |
| edebiyat | v4 | full | 6 | 0 | 0 | 0 | 5 | 1 | 0 | 3 | 0 | 22,2 | 37004 | 1476 | 0,006436 |
| edebiyat | v4 | rag | 6 | 0 | 0 | 0 | 4 | 0 | 0 | 3 | 0 | 23,8 | 21001 | 1488 | 0,004043 |
| python | v3 | full | 6 | 0 | 0 | 0 | 5 | 0 | 0 | 3 | 0 | 27,6 | 22884 | 1339 | 0,004236 |
| python | v3 | rag | 6 | 0 | 0 | 0 | 6 | 0 | 0 | 2 | 0 | 19,5 | 17171 | 1086 | 0,003227 |
| python | v4 | full | 6 | 0 | 0 | 0 | 5 | 1 | 0 | 3 | 0 | 18,2 | 24552 | 1134 | 0,004363 |
| python | v4 | rag | 5 | 0 | 1 | 0 | 4 | 0 | 0 | 0 | 0 | 20,4 | 18839 | 1239 | 0,003569 |
| **Toplam (6 video)** | v3 | full | 35 | 1 | 0 | 0 | 27 | 1 | 0 | 13 | 2 | 154,2 | 253089 | 7985 | 0,042755 |
| **Toplam (6 video)** | v3 | rag | 34 | 2 | 0 | 0 | 29 | 0 | 1 | 9 | 2 | 123,9 | 110079 | 7528 | 0,021029 |
| **Toplam (6 video)** | v4 | full | 34 | 1 | 0 | 1 | 28 | 4 | 1 | 16 | 0 | 136,7 | 263097 | 8035 | 0,044285 |
| **Toplam (6 video)** | v4 | rag | 34 | 1 | 1 | 0 | 27 | 1 | 1 | 10 | 2 | 140,6 | 120087 | 8251 | 0,022963 |

Toplam satırları dört çalıştırması da tamam olan videolardan hesaplandı: biyoloji, tarih, matematik, ingilizce, edebiyat, python.

Harcama, hatalı çalıştırmalar dahil: 149 OpenAI çağrısı, 0,148122 USD (liste fiyatıyla tahmin).

"Olası cevap kökte" kaba bir işarettir. "Örnek sızıntısı" sayısı, konu gerçekten bu sözcüklerle ilgiliyse yanlış işaret olabilir.

**Hatalı çalıştırmalar** (harcamaya dahil, tablolara dahil değil)

- matematik v4-full: /api/questions: 502 LLM yanıtı geçerli JSON değil. 5 çağrı, 44355 girdi + 17395 çıktı token, 0,017090 USD. En uzun çağrı: 16384 çıktı token, 167,2 sn.

## Yaratma düzeyindeki konular

| Video | Konu | v3-full | v3-rag | v4-full | v4-rag |
|---|---|---|---|---|---|
| biyoloji | Üretici Canlılar | ok | ok | ok | ok |
| tarih | Kösedağ Savaşı'nın Sonuçları | ok | empty | ok | empty: Kösedağ Savaşı'nın sonuçları bağlamda geçiyor ancak yaratma düzeyinde bir soru oluşturmak için yeterli bilgi yok. |
| matematik | Açıortay Teoremi Uygulamaları | empty | empty | empty: Açıortay Teoremi bağlamda geçiyor ancak yaratma düzeyinde bir soru oluşturmak için yeterli bilgi yok. | ok |
| ingilizce | Soru Cümlesi Oluşturma | ok | ok | duplicate | ok |
| edebiyat | Milli Edebiyat Dönemi Tanımı | ok | ok | ok | ok |
| python | Python Söz Dizimi | ok | ok | ok | invalid |

## Bütün sorular

### biyoloji

#### Konu 1 · hedef düzey Uygulama · Kemosentez Nedir?

| full | v3 | v4 |
|---|---|---|
| Sonuç | ok | ok |
| Soru | Okyanus derinliklerinde ışık enerjisi bulunmadığı için kemosentetik canlılar nasıl besin üretir? | Bir araştırmacı, okyanus derinliklerinde ışık olmayan bir ortamda kemosentetik canlıların besin üretim sürecini incelemektedir. Bu canlılar hangi maddeyi oksitleyerek enerji üretirler? |
| Seçenekler | Sadece su ve oksijen kullanarak besin üretirler.<br>Işık enerjisini kullanarak besin üretirler.<br>İnorganik maddeleri oksitlerler ve açığa çıkan enerjiyi kullanarak besin üretirler.<br>Besin üretimi için dışarıdan enerji alırlar. | İnorganik madde<br>Organik madde<br>Oksijen<br>Karbon dioksit |
| Doğru cevap | İnorganik maddeleri oksitlerler ve açığa çıkan enerjiyi kullanarak besin üretirler. | İnorganik madde |
| Kaynak alıntısı | Kemosentetik canlılar inorganik maddeleri oksitlerler ve bunun sonucunda enerji açığa çıkartırlar. | Kemosentetik canlılar inorganik maddeleri oksitlerler ve bunun sonucunda enerji açığa çıkartırlar. |
| Kaynak zamanı | 6:30 · alıntı bulundu | 6:30 · alıntı bulundu |
| İşaretler | yazım kuralı 4, 19 | yazım kuralı 19 |

| rag | v3 | v4 |
|---|---|---|
| Sonuç | ok | ok |
| Soru | Kemosentetik canlılar, okyanus derinliklerinde ışık olmadan besin üretimi yaparken hangi maddeyi kullanarak enerji üretirler? | Bir kemosentetik canlı, okyanus derinliklerinde besin üretmek için hangi maddeyi oksitler? |
| Seçenekler | Inorganik madde<br>Oksijen<br>Su<br>Organik madde | İnorganik madde<br>Organik madde<br>Su<br>Karbondioksit |
| Doğru cevap | Inorganik madde | İnorganik madde |
| Kaynak alıntısı | Kemosentetik canlılar da kimyasal enerjiyi kullanarak bir besin üretimini gerçekleştirdiği için o zaman kesinlikle biz şunu dememiz lazım. | Kemosentetik canlılar inorganik maddeleri oksitlerler ve bunun sonucunda enerji açığa çıkartırlar. |
| Kaynak zamanı | 5:40 · alıntı bulundu | 6:30 · alıntı bulundu |
| İşaretler | yok | yok |

#### Konu 2 · hedef düzey Hatırlama · Hidrotermal Bacalar

| full | v3 | v4 |
|---|---|---|
| Sonuç | ok | ok |
| Soru | Hidrotermal bacalar nerede bulunur? | Hidrotermal bacalar, hangi derinlikte bulunan sıcak su kaynaklarıdır? |
| Seçenekler | Kuru topraklarda<br>Göllerde<br>Dağların zirvelerinde<br>Okyanus tabanında | Nehir yatağı<br>Göl tabanı<br>Okyanus tabanı<br>Deniz yüzeyi |
| Doğru cevap | Okyanus tabanında | Okyanus tabanı |
| Kaynak alıntısı | Hidrotermal bacalar su ve gaz fışkırtan sıcak su kaynaklarının okyanus tabanında yer alan benzerleridir. | Hidrotermal bacalar su ve gaz fışkırtan sıcak su kaynaklarının okyanus tabanında yer alan benzerleridir. |
| Kaynak zamanı | 2:14 · alıntı bulundu | 2:14 · alıntı bulundu |
| İşaretler | yok | yok |

| rag | v3 | v4 |
|---|---|---|
| Sonuç | ok | ok |
| Soru | Hidrotermal bacalar nerede bulunur? | Hidrotermal bacalar nerede bulunur? |
| Seçenekler | Nehirlerde<br>Göllerde<br>Kıyılarda<br>Okyanus tabanında | Kıyılarda<br>Göllerde<br>Dağlık alanlarda<br>Okyanus tabanında |
| Doğru cevap | Okyanus tabanında | Okyanus tabanında |
| Kaynak alıntısı | Hidrotermal bacalar su ve gaz fışkırtan sıcak su kaynaklarının okyanus tabanında yer alan benzerleridir. | Hidrotermal bacalar su ve gaz fışkırtan sıcak su kaynaklarının okyanus tabanında yer alan benzerleridir. |
| Kaynak zamanı | 2:14 · alıntı bulundu | 2:14 · alıntı bulundu |
| İşaretler | yazım kuralı 4 | yok |

#### Konu 3 · hedef düzey Değerlendirme · Kemosentetik Canlılar

| full | v3 | v4 |
|---|---|---|
| Sonuç | ok | ok |
| Soru | Kemosentetik canlıların besin üretimi için hangi enerji kaynağını kullanması gerektiği konusunda aşağıdaki ifadelerden hangisi doğrudur? | Kemosentetik canlıların okyanus derinliklerinde besin üretimi yapabilmesi, bu canlıların ekosistem içindeki diğer canlılarla olan ilişkisini nasıl etkiler? |
| Seçenekler | Sadece organik maddeleri kullanarak besin üretirler.<br>Işık enerjisi kullanarak besin üretirler.<br>Kimyasal enerjiyi kullanarak besin üretirler.<br>Besin üretimi için enerjiye ihtiyaç duymazlar. | Kemosentetik canlılar, besin üretmediği için ekosistemdeki diğer canlıları olumsuz etkiler.<br>Kemosentetik canlılar, besin üreterek ekosistemdeki diğer canlıların yaşamını destekler.<br>Kemosentetik canlılar, sadece kendi türlerinin yaşamasına olanak tanır.<br>Kemosentetik canlılar, ekosistemdeki diğer canlılarla hiçbir ilişki kurmaz. |
| Doğru cevap | Kimyasal enerjiyi kullanarak besin üretirler. | Kemosentetik canlılar, besin üreterek ekosistemdeki diğer canlıların yaşamını destekler. |
| Kaynak alıntısı | Kemosentetik canlılar da kimyasal enerjiyi kullanarak bir besin üretimini gerçekleştirdiği için o zaman kesinlikle biz şunu dememiz lazım. | demek ki bu zorlu şartta canlı yaşayabiliyor ve bu canlı besin üretiyor. O zaman bu besini de başka tüketici organizmalar da yiyebilir. |
| Kaynak zamanı | 5:40 · alıntı bulundu | 3:51 · alıntı bulundu |
| İşaretler | benzer soru: konu 5 | olası cevap kökte; yazım kuralı 11 |

| rag | v3 | v4 |
|---|---|---|
| Sonuç | ok | ok |
| Soru | Kemosentetik canlıların besin üretimi ile ilgili aşağıdaki ifadelerden hangisi doğrudur? | Kemosentetik canlıların besin üretimi ile ilgili aşağıdaki ifadelerden hangisi doğrudur? |
| Seçenekler | Kemosentetik canlılar, yalnızca su ve oksijen ile besin üretir.<br>Kemosentetik canlılar, besin üretimi için ortamda ışık bulunmasını gerektirir.<br>Kemosentetik canlılar, yalnızca ışık enerjisi ile besin üretir.<br>Kemosentetik canlılar, inorganik maddeleri oksitleyerek enerji üretir. | Kemosentetik canlılar besin üretimi için klorofil pigmentine ihtiyaç duyar.<br>Kemosentetik canlılar sadece okyanus yüzeyinde yaşar.<br>Kemosentetik canlılar yalnızca ışık altında besin üretir.<br>Kemosentetik canlılar inorganik maddeleri oksitleyerek enerji üretir. |
| Doğru cevap | Kemosentetik canlılar, inorganik maddeleri oksitleyerek enerji üretir. | Kemosentetik canlılar inorganik maddeleri oksitleyerek enerji üretir. |
| Kaynak alıntısı | Kemosentetik canlılar da kimyasal enerjiyi kullanarak bir besin üretimini gerçekleştirdiği için o zaman kesinlikle biz şunu dememiz lazım. | Kemosentetik canlılar inorganik maddeleri oksitlerler ve bunun sonucunda enerji açığa çıkartırlar. |
| Kaynak zamanı | 5:40 · alıntı bulundu | 6:30 · alıntı bulundu |
| İşaretler | yok | yok |

#### Konu 4 · hedef düzey Yaratma · Üretici Canlılar

| full | v3 | v4 |
|---|---|---|
| Sonuç | ok | ok |
| Soru | Kemosentetik canlıların besin üretimi için hangi enerji kaynağını kullanarak bir düzenek tasarlamak en uygundur? | Kemosentez yapan bir canlı, besin üretimi için aşağıdaki hangi adımı gerçekleştirmelidir? |
| Seçenekler | Klorofil pigmenti kullanmak<br>Güneş ışığını kullanmak<br>Sıcak su kaynaklarından enerji almak<br>İnorganik maddeleri oksitlemek | C) Organik maddeleri parçalayarak enerji üretmek.<br>B) İnorganik maddeleri oksitleyerek enerji açığa çıkarmak.<br>D) Fotosentetik pigmentler kullanarak besin sentezlemek.<br>A) Işık enerjisini kullanarak su ve karbondioksiti birleştirmek. |
| Doğru cevap | İnorganik maddeleri oksitlemek | B) İnorganik maddeleri oksitleyerek enerji açığa çıkarmak. |
| Kaynak alıntısı | kemosentetik bakteriler için hemen bunun altını çizmek istiyorum. Uygun ortam oluştururlar. | Kemosentetik canlılar inorganik maddeleri oksitlerler ve bunun sonucunda enerji açığa çıkartırlar. |
| Kaynak zamanı | 3:07 · alıntı bulundu | 6:30 · alıntı bulundu |
| İşaretler | yok | yok |

| rag | v3 | v4 |
|---|---|---|
| Sonuç | ok | ok |
| Soru | Bir öğrenci, okyanus derinliklerinde ışık olmadan besin üretebilen bir ekosistem tasarlamak istiyor. Bu ekosistemde hangi canlı türü bu tasarıma en uygun olur? | Bir öğrenci, okyanus derinliklerinde ışık bulunmayan bir ortamda kemosentetik canlıların nasıl besin ürettiğini göstermek için bir deney düzenlemek istiyor. Aşağıdaki düzeneklerden hangisi bu amaca en uygundur? |
| Seçenekler | Fotosentetik canlılar<br>Hayvanlar<br>Kemosentetik canlılar<br>Bitkiler | C) Bir akvaryumda balıkların beslenmesini gözlemlemek.<br>B) Bir su tankında inorganik maddeleri oksitleyerek gaz açığa çıkmasını sağlamak.<br>D) Bir toprak örneğinde fotosentez yapan bitkilerin büyümesini izlemek.<br>A) Bir bitkiyi güneş ışığı altında büyütmek. |
| Doğru cevap | Kemosentetik canlılar | B) Bir su tankında inorganik maddeleri oksitleyerek gaz açığa çıkmasını sağlamak. |
| Kaynak alıntısı | Kemosentetik canlılar inorganik maddeleri oksitlerler ve bunun sonucunda enerji açığa çıkartırlar. | Kemosentetik canlılar inorganik maddeleri oksitlerler ve bunun sonucunda enerji açığa çıkartırlar. |
| Kaynak zamanı | 6:30 · alıntı bulundu | 6:30 · alıntı bulundu |
| İşaretler | yok | yazım kuralı 19 |

#### Konu 5 · hedef düzey Anlama · Kemosentez Ortamları

| full | v3 | v4 |
|---|---|---|
| Sonuç | ok | ok |
| Soru | Kemosentetik canlılar hangi enerji kaynağını kullanarak besin üretimini gerçekleştirirler? | Kemosentetik canlıların besin üretimi için hangi enerji kaynağını kullandığı en iyi şekilde aşağıdaki ifadelerden hangisiyle açıklanabilir? |
| Seçenekler | Işık enerjisi<br>Termal enerji<br>Mekanik enerji<br>Kimyasal enerji | Mekanik enerji<br>Termal enerji<br>Işık enerjisi<br>Kimyasal enerji |
| Doğru cevap | Kimyasal enerji | Kimyasal enerji |
| Kaynak alıntısı | Kemosentetiklerde kimyasal enerjiyi kullanarak besin üretimini gerçekleştiriyor. | Kemosentetik canlılar da kimyasal enerjiyi kullanarak bir besin üretimini gerçekleştirdiği için o zaman kesinlikle biz şunu dememiz lazım. |
| Kaynak zamanı | 11:33 · alıntı bulundu | 5:40 · alıntı bulundu |
| İşaretler | benzer soru: konu 3 | yok |

| rag | v3 | v4 |
|---|---|---|
| Sonuç | ok | ok |
| Soru | Kemosentetik canlıların yaşadığı ortamlar arasında hangisi bulunmamaktadır? | Kemosentetik canlıların yaşadığı ortamlar hakkında aşağıdakilerden hangisi doğrudur? |
| Seçenekler | Ormanlık alanlar<br>Okyanus derinlikleri<br>Lağım çamuru<br>Çöplükler | Kemosentetik canlılar sadece tatlı su kaynaklarında bulunur.<br>Kemosentetik canlılar yalnızca karasal ortamlarda yaşar.<br>Kemosentetik canlılar derin deniz diplerinde ve çöplüklerde yaşayabilir.<br>Kemosentetik canlılar yalnızca okyanus yüzeyinde yaşar. |
| Doğru cevap | Ormanlık alanlar | Kemosentetik canlılar derin deniz diplerinde ve çöplüklerde yaşayabilir. |
| Kaynak alıntısı | Kemosentetik canlılara da kemosentetik canlılar adını veriyoruz. Bu canlıların tamamı prokaryot hücre yapısına sahip olan canlılardır. Peki bu canlıların yaşadığı ortamları konuşacak olursak... Okyanus dibi ya da derin deniz dibi... Bunun dışında çöplükleri, lağım çamuru işleme kazanlarını... belirtebilirim. | Bu canlıların yaşadığı ortamları konuşacak olursak... okyanusların derinlikleri, derin deniz dipleri, çöplükler, lağımlar |
| Kaynak zamanı | yok · alıntı bulunamadı | yok · alıntı bulunamadı |
| İşaretler | yazım kuralı 19 | yok |

#### Konu 6 · hedef düzey Çözümleme · Fotosentez ve Kemosentez Farkları

| full | v3 | v4 |
|---|---|---|
| Sonuç | ok | ok |
| Soru | Fotosentez ve kemosentez arasındaki temel fark nedir? | Fotosentez ve kemosentez arasındaki temel fark nedir? |
| Seçenekler | Kemosentez sadece bitkilerde gerçekleşir, fotosentez ise tüm canlılarda gerçekleşir.<br>Kemosentezde klorofil pigmenti bulunur, fotosentezde bulunmaz.<br>Fotosentezde oksijen açığa çıkar, kemosentezde ise her iki durumda da oksijen açığa çıkar.<br>Fotosentezde ışık enerjisi kullanılır, kemosentezde kimyasal enerji kullanılır. | Her iki süreçte de ışık enerjisi kullanılır.<br>Fotosentezde ışık enerjisi kullanılır, kemosentezde kimyasal enerji kullanılır.<br>Her iki süreçte de kimyasal enerji kullanılır.<br>Fotosentezde kimyasal enerji kullanılır, kemosentezde ışık enerjisi kullanılır. |
| Doğru cevap | Fotosentezde ışık enerjisi kullanılır, kemosentezde kimyasal enerji kullanılır. | Fotosentezde ışık enerjisi kullanılır, kemosentezde kimyasal enerji kullanılır. |
| Kaynak alıntısı | Üreticileri de biz ikiye ayırmıştık. Kullandığı enerji kaynağına göre. Eğer ışık enerjisini kullanarak besin üretiyorsa biz buna fotosentetik canlı demiştik. Kimyasal bir enerjiyi kullanarak besin üretimini gerçekleştiriyorsa o canlıya da kemosentetik canlı adını vermiştik. | Üreticileri de biz ikiye ayırmıştık. Kullandığı enerji kaynağına göre. Eğer ışık enerjisini kullanarak besin üretiyorsa biz buna fotosentetik canlı demiştik. Kimyasal bir enerjiyi kullanarak besin üretimini gerçekleştiriyorsa o canlıya da kemosentetik canlı adını vermiştik. |
| Kaynak zamanı | 3:27 · alıntı bulundu | 3:27 · alıntı bulundu |
| İşaretler | yok | yok |

| rag | v3 | v4 |
|---|---|---|
| Sonuç | ok | ok |
| Soru | Fotosentez ve kemosentez arasındaki temel fark nedir? | Fotosentez ve kemosentez arasındaki temel farklardan biri nedir? |
| Seçenekler | Fotosentezde kimyasal enerji kullanılır, kemosentezde ışık enerjisi kullanılır.<br>Kemosentezde oksijen üretilir, fotosentezde üretilmez.<br>Kemosentezde besin üretimi yoktur, fotosentezde vardır.<br>Fotosentezde klorofil kullanılır, kemosentezde kullanılmaz. | Kemosentezde besin üretimi yoktur, fotosentezde vardır.<br>Fotosentezde klorofil kullanılır, kemosentezde kullanılmaz.<br>Kemosentezde oksijen üretilir, fotosentezde üretilmez.<br>Fotosentezde enerji kaynağı kimyasal enerjidir, kemosentezde ışık enerjisi kullanılır. |
| Doğru cevap | Fotosentezde klorofil kullanılır, kemosentezde kullanılmaz. | Fotosentezde klorofil kullanılır, kemosentezde kullanılmaz. |
| Kaynak alıntısı | Fotosentezde klorofil pigmenti kullanılır ama kemosentezde kullanılmaz. | Fotosentezde klorofil pigmenti kullanılır ama kemosentezde kullanılmaz. |
| Kaynak zamanı | 18:14 · alıntı bulundu | 18:14 · alıntı bulundu |
| İşaretler | yok | yok |

### tarih

#### Konu 1 · hedef düzey Çözümleme · Malazgirt Savaşı'nın Önemi

| full | v3 | v4 |
|---|---|---|
| Sonuç | ok | ok |
| Soru | Malazgirt Savaşı'nın ardından Anadolu'da kurulan beyliklerin ortak özelliği nedir? | Malazgirt Savaşı'nın ardından Anadolu'da kurulan beyliklerin ortaya çıkışını etkileyen temel faktör hangisidir? |
| Seçenekler | Hepsi aynı yıl kurulmuştur.<br>Hepsi denizcilik faaliyetleriyle tanınmıştır.<br>Hepsi Bizans ile doğrudan savaşmamıştır.<br>Hepsi Anadolu'yu Türkleştiren ve İslamlaştıran beyliklerdir. | Bizans'ın zayıflaması<br>Haçlı seferlerinin başlaması<br>Gürcülerle yapılan savaşlar<br>Türklerin Anadolu'ya yerleşmesi |
| Doğru cevap | Hepsi Anadolu'yu Türkleştiren ve İslamlaştıran beyliklerdir. | Türklerin Anadolu'ya yerleşmesi |
| Kaynak alıntısı | Bu savaş bir dönüm noktasıydı. Bu savaşa yurt açan, yurt kuran savaşı da derler. Çünkü Anadolu'da Türklerin yerleşmesinde bu savaş dönüm noktası olmuş. | Bu savaş bir dönüm noktasıydı. Bu savaşa yurt açan, yurt kuran savaşı da derler. |
| Kaynak zamanı | yok · alıntı bulunamadı | yok · alıntı bulunamadı |
| İşaretler | yazım kuralı 4, 12 | yazım kuralı 12 |

| rag | v3 | v4 |
|---|---|---|
| Sonuç | ok | ok |
| Soru | Malazgirt Savaşı'nın Anadolu'nun Türk yurdu haline gelmesi üzerindeki etkileri arasında hangisi doğru bir ilişkiyi ifade etmektedir? | Malazgirt Savaşı'nın ardından Anadolu'da Türklerin yerleşmesi ile ilgili aşağıdaki ifadelerden hangisi doğrudur? |
| Seçenekler | Malazgirt Savaşı, Anadolu'da Türklerin yerleşmesini engelledi.<br>Malazgirt Savaşı sonrası Türkler Anadolu'dan atılma ihtimalini kaybetti.<br>Malazgirt Savaşı, Anadolu'daki ticaret yollarının denetimini Bizans'a bıraktı.<br>Malazgirt Savaşı, Anadolu'da sadece askeri bir zafer sağladı, kültürel etkisi yoktu. | Malazgirt Savaşı, Anadolu'da Türklerin yerleşmesini durdurmuştur.<br>Malazgirt Savaşı, Anadolu'da Türklerin yerleşmesini hızlandırmıştır.<br>Malazgirt Savaşı, Anadolu'da Türklerin yerleşmesini engellemiştir.<br>Malazgirt Savaşı, Anadolu'da Türklerin yerleşmesine etki etmemiştir. |
| Doğru cevap | Malazgirt Savaşı sonrası Türkler Anadolu'dan atılma ihtimalini kaybetti. | Malazgirt Savaşı, Anadolu'da Türklerin yerleşmesini hızlandırmıştır. |
| Kaynak alıntısı | Malazgirt Savaşı'ndan sonra ne olmuştu? Anadolu Türkleşmeye ve İslamlaşmaya başlamıştı. | Bu savaş bir dönüm noktasıydı. Bu savaşa zaten yurt açan, yurt kuran savaşı da derler. Çünkü Anadolu'da Türklerin yerleşmesinde bu savaş dönüm noktası olmuş. |
| Kaynak zamanı | 23:16 · alıntı bulundu | 1:28 · alıntı bulundu |
| İşaretler | yok | olası cevap kökte |

#### Konu 2 · hedef düzey Anlama · Birinci Beylikler Dönemi

| full | v3 | v4 |
|---|---|---|
| Sonuç | ok | ok |
| Soru | Malazgirt Savaşı'ndan sonra Anadolu'da kurulan beyliklerin ortak özellikleri arasında hangisi yer almaz? | Malazgirt Savaşı'nın ardından Anadolu'da kurulan beyliklerin en önemli işlevi nedir? |
| Seçenekler | Denizcilik faaliyetleri yürütmeleri<br>Ermenilerle ve Gürcülerle mücadele etmeleri<br>Anadolu'da imar faaliyetleri yapmaları<br>Anadolu'yu Türkleştirmeleri | Anadolu'yu Türkleştirmek<br>Haçlılarla ittifak kurmak<br>Bizans'ı yeniden güçlendirmek<br>Gürcülerle birleşmek |
| Doğru cevap | Denizcilik faaliyetleri yürütmeleri | Anadolu'yu Türkleştirmek |
| Kaynak alıntısı | Bu açıdan çok önemli. Hatta denizler de Bizanslılarla mücadele etmişler. | Bu savaştan sonra Anadolu'da 1. Beylikler dönemi başlamış. |
| Kaynak zamanı | 8:34 · alıntı bulundu | 1:39 · alıntı bulundu |
| İşaretler | yazım kuralı 19 | yazım kuralı 12 |

| rag | v3 | v4 |
|---|---|---|
| Sonuç | ok | ok |
| Soru | Malazgirt Savaşı'ndan sonra Anadolu'da kurulan beyliklerden hangisi doğru bir şekilde verilmiştir? | Malazgirt Savaşı'ndan sonra Anadolu'da kurulan beyliklerin ortak özellikleri arasında hangisi yer almaz? |
| Seçenekler | Karamanoğulları<br>Saltuklular<br>Aydınoğulları<br>Osmanoğulları | Denizcilik faaliyetleri ile tanınmışlardır.<br>İlk beylikler olarak kabul edilirler.<br>Kuruldukları bölgelerde sürekli mücadele etmişlerdir.<br>Anadolu'yu Türkleştirmişlerdir. |
| Doğru cevap | Saltuklular | Denizcilik faaliyetleri ile tanınmışlardır. |
| Kaynak alıntısı | Malazgirt Savaşı'nın ardından kurulan beylikler hangileri? Bakıyorum. Saltuklular. Renklendirelim şöyle. Saltuklular, Artuklular, Mengücekliler, Çakabeyli ve Danışmentliler. | Bunlar Anadolu'da kurulan ilk beylikler olduğu için Anadolu'yu Türkleştirenler, Anadolu'yu Müslümanlaştıranlar işte bu beylikler. |
| Kaynak zamanı | 1:44 · alıntı bulundu | 4:42 · alıntı bulundu |
| İşaretler | yok | yazım kuralı 19 |

#### Konu 3 · hedef düzey Değerlendirme · Haçlı Seferlerinin Nedenleri

| full | v3 | v4 |
|---|---|---|
| Sonuç | ok | ok |
| Soru | Haçlı seferlerinin başlıca nedeni olarak aşağıdakilerden hangisi en doğru şekilde ifade edilmiştir? | Haçlı seferlerinin temel nedenleri arasında aşağıdakilerden hangisi yer almamaktadır? |
| Seçenekler | Doğu-Batı ticaret yollarının kontrolünü sağlamak<br>Kudüs'ü ele geçirmek amacıyla Hristiyanların birleşmesi<br>Hristiyanlık ve İslam arasındaki mezhep çatışması<br>Türklerin Anadolu'dan atılması için yapılan bir savaş | Kudüs'ü ele geçirmek amacı<br>Müslümanların Avrupa'ya saldırması<br>Hristiyan mezhepleri arasındaki güç mücadelesi<br>Doğu-Batı ticaret yollarının kontrolü |
| Doğru cevap | Kudüs'ü ele geçirmek amacıyla Hristiyanların birleşmesi | Müslümanların Avrupa'ya saldırması |
| Kaynak alıntısı | Dolayısıyla Kudüs'ü Müslüman dünyasından almak amacıyla dini bir sebeple ne yapıyorlar? Saldırıyorlar. Temel dini amaçları neymiş? Kudüs'ü ele geçirmekmiş. | Dolayısıyla 1096 yılında 1. Haçlı Seferi adıyla bütün Hristiyanların böyle birleşip Müslümanların üzerine, Türklerin üzerine geldiğini görüyoruz. |
| Kaynak zamanı | 10:02 · alıntı bulundu | 9:07 · alıntı bulundu |
| İşaretler | yok | yazım kuralı 19 |

| rag | v3 | v4 |
|---|---|---|
| Sonuç | ok | ok |
| Soru | Ali, Haçlı Seferlerinin sadece dini sebeplerle yapıldığını savunuyor. Ayşe ise, bu seferlerin siyasi ve ekonomik nedenlerle de gerçekleştirildiğini düşünüyor. Hangi değerlendirme doğrudur? | Haçlı Seferleri'nin temel nedenleri arasında hangi seçenek yer almamaktadır? |
| Seçenekler | İki iddia da desteklenir.<br>İki iddia da anlatılanlarla çelişir.<br>Ali'nin iddiası desteklenir, Ayşe'ninki desteklenmez.<br>Ayşe'nin iddiası desteklenir, Ali'ninki desteklenmez. | Hristiyanların yeni topraklar kazanma isteği<br>Türkleri Anadolu'dan atmak amacıyla siyasi sebepler<br>Doğudan gelen ticaret yollarının hakimiyetini sağlamak<br>Kudüs'ü ele geçirmek amacıyla dini sebepler |
| Doğru cevap | Ayşe'nin iddiası desteklenir, Ali'ninki desteklenmez. | Hristiyanların yeni topraklar kazanma isteği |
| Kaynak alıntısı | Peki haçlılar seferlerini neden yapıyor? Bunları bir başlıklandıralım. Mesela dini sebepler diyelim... Siyasi olarak baktığımda tabii ki Türkleri Anadolu'dan atmak, Müslümanları Anadolu'dan atmak amacıyla hareket ediyorlar. | Peki haçlılar seferlerini neden yapıyor? Bunları bir başlıklandıralım. Mesela dini sebepler diyelim. |
| Kaynak zamanı | yok · alıntı bulunamadı | 9:36 · alıntı bulundu |
| İşaretler | örnek sızıntısı (Ali, Ayşe) | yazım kuralı 19 |

#### Konu 4 · hedef düzey Hatırlama · Miri Kefalon Savaşı

| full | v3 | v4 |
|---|---|---|
| Sonuç | ok | ok |
| Soru | Miri Kefalon Savaşı hangi yıllarda gerçekleşmiştir? | Mir Kefalon Savaşı hangi yıl gerçekleşmiştir? |
| Seçenekler | 1071<br>1096<br>1176<br>1243 | 1071<br>1096<br>1176<br>1243 |
| Doğru cevap | 1176 | 1176 |
| Kaynak alıntısı | Ne zaman? 1176 yılında. Bu açıdan önemlidir. | Ne zaman? 1176 yılında. Bu açıdan önemlidir. |
| Kaynak zamanı | 22:01 · alıntı bulundu | 22:01 · alıntı bulundu |
| İşaretler | yok | yok |

| rag | v3 | v4 |
|---|---|---|
| Sonuç | ok | ok |
| Soru | Mir Kefalon Savaşı hangi yıl gerçekleşmiştir? | Miri Kefalon Savaşı hangi yıl gerçekleşmiştir? |
| Seçenekler | 1165<br>1176<br>1180<br>1200 | 1165<br>1176<br>1180<br>1200 |
| Doğru cevap | 1176 | 1176 |
| Kaynak alıntısı | Ne zaman? 1176 yılında. | Miri Kefalon Savaşı Türkiye Selçuklu Devleti'nin yapmış olduğu bir savaştır... Ne zaman? 1176 yılında. |
| Kaynak zamanı | 22:01 · alıntı bulundu | yok · alıntı bulunamadı |
| İşaretler | yok | yok |

#### Konu 5 · hedef düzey Yaratma · Kösedağ Savaşı'nın Sonuçları

| full | v3 | v4 |
|---|---|---|
| Sonuç | ok | ok |
| Soru | Kösedağ Savaşı'nın ardından Türkiye Selçuklu Devleti'nin karşılaştığı en önemli sonuçlardan hangisi, Anadolu'daki beyliklerin ortaya çıkmasına zemin hazırlamıştır? | Kösedağ Savaşı'nın ardından Türkiye Selçuklu Devleti'nin karşılaştığı durumlar göz önüne alındığında, aşağıdaki sonuçlardan hangisi bu savaştan sonra ortaya çıkan yeni bir durumu en iyi ifade eder? |
| Seçenekler | Moğol egemenliğinin artması<br>Anadolu'da tarımsal üretimin artması<br>Türklerin Anadolu'dan atılması<br>Ticaret yollarının güvenliğinin sağlanması | Moğol egemenliği altında Anadolu'da yeni beylikler ortaya çıkmıştır.<br>Ticaret yolları güvenli hale gelmiştir.<br>Anadolu'da Türklerin merkezi otoritesi güçlenmiştir.<br>Anadolu'da tarımsal üretim artmıştır. |
| Doğru cevap | Moğol egemenliğinin artması | Moğol egemenliği altında Anadolu'da yeni beylikler ortaya çıkmıştır. |
| Kaynak alıntısı | Kösedağ Savaşı'ndan sonra Türkiye Selçuklu Devleti Anadolu'nun büyük bir bölümünü Moğol egemenliğine bırakmak zorunda kaldı. | Kösedağ Savaşı'ndan sonra Türkiye Selçuklu Devleti Anadolu'nun büyük bir bölümünü Moğol egemenliğine bırakmak zorunda kaldı. |
| Kaynak zamanı | yok · alıntı bulunamadı | yok · alıntı bulunamadı |
| İşaretler | yok | yazım kuralı 4, 12 |

| rag | v3 | v4 |
|---|---|---|
| Sonuç | empty | empty: Kösedağ Savaşı'nın sonuçları bağlamda geçiyor ancak yaratma düzeyinde bir soru oluşturmak için yeterli bilgi yok. |

#### Konu 6 · hedef düzey Uygulama · İkinci Beylikler Dönemi

| full | v3 | v4 |
|---|---|---|
| Sonuç | ok | ok |
| Soru | Kösedağ Savaşı'ndan sonra Anadolu'da hangi durum meydana gelmiştir? | Kösedağ Savaşı'ndan sonra Anadolu'da hangi durum meydana gelmiştir? |
| Seçenekler | Türkiye Selçuklu Devleti güçlenmiştir.<br>Moğol istilası sona ermiştir.<br>Anadolu'da ikinci beylikler dönemi başlamıştır.<br>Türklerin Anadolu'dan atılması kesinleşmiştir. | Moğol baskısı Anadolu'da sona ermiştir.<br>Anadolu'da tarımsal üretim artmıştır.<br>Anadolu'da ikinci beylikler dönemi başlamıştır.<br>Anadolu'da Türklerin merkezi otoritesi güçlenmiştir. |
| Doğru cevap | Anadolu'da ikinci beylikler dönemi başlamıştır. | Anadolu'da ikinci beylikler dönemi başlamıştır. |
| Kaynak alıntısı | Anadolu'da ikinci beylikler ortaya çıkıyor. | Anadolu'da ikinci beylikler ortaya çıkıyor. |
| Kaynak zamanı | 26:05 · alıntı bulundu | 26:05 · alıntı bulundu |
| İşaretler | yok | yok |

| rag | v3 | v4 |
|---|---|---|
| Sonuç | ok | ok |
| Soru | Kösedağ Savaşı'ndan sonra Anadolu'da kurulan ikinci beylikler hangi bölgede yoğunlaşmıştır? | Kösedağ Savaşı'ndan sonra Anadolu'da kurulan ikinci beylikler genellikle hangi bölgelerde yoğunlaşmıştır? |
| Seçenekler | Doğusunda<br>Güneyinde<br>Kuzeyinde<br>Batısında | Kuzeyinde<br>Güneyinde<br>Doğusunda<br>Batısında |
| Doğru cevap | Batısında | Batısında |
| Kaynak alıntısı | O zaman ik beylikler nerede yoğunlaşır? Bu bölgelerde. | Kösedağ Savaşı'ndan sonra Türkiye Selçuklu Devleti yenilirse ne olur? O ele geçirmiş olduğu beylikler, Anadolu'daki hakimiyet bozulur. Türkiye Selçuklu Devleti'nin merkezi otoritesi zayıflar. Anadolu toprakları Moğollar tarafından yağmalanır ve bu Moğol baskısı, Moğol istilası Anadolu'da kan, kaos, gözyaşı getirecek. |
| Kaynak zamanı | 26:54 · alıntı bulundu | 24:36 · alıntı bulundu |
| İşaretler | yok | yok |

### matematik

#### Konu 1 · hedef düzey Hatırlama · Açıortay Teoremi

| full | v3 | v4 |
|---|---|---|
| Sonuç | ok | ok |
| Soru | İç açıortay teoremi, bir üçgende hangi oranı belirler? | İç açıortay teoremi, bir üçgende hangi oranların eşit olduğunu belirtir? |
| Seçenekler | Birinci kolun birinci parçaya oranı ile ikinci kolun ikinci parçaya oranı<br>Üçgenin çevresinin alanına oranı<br>Üçgenin iç açıları toplamına oranı<br>Birinci kolun ikinci parçaya oranı ile ikinci kolun birinci parçaya oranı | Üçgenin çevresinin yarısı, üçgenin alanına eşittir.<br>Birinci kolun birinci parçaya oranı, ikinci kolun ikinci parçaya oranına eşittir.<br>Bir kenarın uzunluğu, diğer kenarların toplamına eşittir.<br>Üçgenin iç açılarının toplamı 180 derecedir. |
| Doğru cevap | Birinci kolun birinci parçaya oranı ile ikinci kolun ikinci parçaya oranı | Birinci kolun birinci parçaya oranı, ikinci kolun ikinci parçaya oranına eşittir. |
| Kaynak alıntısı | İç açıortay teoremi diyor. O zaman hadi bir de bunun ispatını yapalım. | Dolayısıyla hadi gel iç açıortaylar için, yani üçgenin içerisinde bulunan açıortaylar için teoremimize hemen bir bakalım. |
| Kaynak zamanı | 2:07 · alıntı bulundu | 1:08 · alıntı bulundu |
| İşaretler | yok | yazım kuralı 4 |

| rag | v3 | v4 |
|---|---|---|
| Sonuç | ok | ok |
| Soru | İç açıortay teoremi, hangi oranların eşit olduğunu belirtir? | İç açıortay teoremi, üçgenin kenar uzunlukları arasındaki oranları nasıl belirler? |
| Seçenekler | C'nin Y'ye oranı ile B'nin X'e oranı<br>C'nin X'e oranı ile A'nın B'ye oranı<br>C'nin X'e oranı ile B'nin Y'ye oranı<br>B'nin X'e oranı ile A'nın Y'ye oranı | Kenar uzunlukları toplamı, açıortay ile ilgili değildir.<br>Açıortay, yalnızca açının büyüklüğüne bağlıdır.<br>Birinci kolun birinci parçaya oranı, ikinci kolun ikinci parçaya oranına eşittir.<br>Üçgenin tüm kenar uzunlukları eşit olmalıdır. |
| Doğru cevap | C'nin X'e oranı ile B'nin Y'ye oranı | Birinci kolun birinci parçaya oranı, ikinci kolun ikinci parçaya oranına eşittir. |
| Kaynak alıntısı | C'nin X'e oranı, yani sağ bölü sağ parça B'nin Y'ye oranına eşit, yani sol bölü sol parça gibi düşünebilirsin. | İşte burada C'nin X'e oranı, yani sağ bölü sağ parça B'nin Y'ye oranına eşit, yani sol bölü sol parça gibi düşünebilirsin. |
| Kaynak zamanı | 1:47 · alıntı bulundu | 1:47 · alıntı bulundu |
| İşaretler | benzer soru: konu 3 | yazım kuralı 4; benzer soru: konu 6 |

#### Konu 2 · hedef düzey Uygulama · Açıortayın Tanımı

| full | v3 | v4 |
|---|---|---|
| Sonuç | ok | ok |
| Soru | Bir üçgende açıortay çizildiğinde, birinci kol 10 cm ve bu kolun ayırdığı parça 5 cm ise, ikinci kolun uzunluğu 15 cm olduğuna göre, bu kolun ayırdığı parça kaç cm'dir? | Bir üçgende açıortay çizildiğinde, bu açıortayın bir kolu 12 cm, ayırdığı parça ise 8 cm ise, diğer kolun uzunluğu nedir? |
| Seçenekler | 7.5 cm<br>10 cm<br>12.5 cm<br>15 cm | 16 cm<br>18 cm<br>20 cm<br>24 cm |
| Doğru cevap | 12.5 cm | 20 cm |
| Kaynak alıntısı | madem kenar uzunluklarıyla çalışacağız, o zaman sana bir teorem vermem lazım. | Açıortayın işte sağ kolu bölü sağ parçası, sol kolu bölü sol parça gibi düşünebilirsin. |
| Kaynak zamanı | 1:03 · alıntı bulundu | yok · alıntı bulunamadı |
| İşaretler | yok | yok |

| rag | v3 | v4 |
|---|---|---|
| Sonuç | ok | ok |
| Soru | Bir üçgende A açısının açıortayı, B ve C kenarlarını X ve Y parçalarına ayırıyor. Eğer A açısının kolu B kenarını 12 birim, C kenarını ise 8 birim ayırıyorsa, X ve Y parçalarının oranı nedir? | Bir üçgende açıortay çizildiğinde, bir kolun uzunluğu 10 cm ve bu kolun ayırdığı parça 5 cm ise, diğer kolun uzunluğu 15 cm olan bir açının ayırdığı parçanın uzunluğu nedir? |
| Seçenekler | 4/3<br>2/3<br>3/2<br>3/4 | 5 cm<br>7.5 cm<br>10 cm<br>12 cm |
| Doğru cevap | 3/2 | 7.5 cm |
| Kaynak alıntısı | C'nin X'e oranı, yani sağ bölü sağ parça B'nin Y'ye oranına eşit, | C'nin X'e oranı, yani sağ bölü sağ parça B'nin Y'ye oranına eşit, |
| Kaynak zamanı | 1:47 · alıntı bulundu | 1:47 · alıntı bulundu |
| İşaretler | yok | yok |

#### Konu 3 · hedef düzey Değerlendirme · İç Açıortay Teoremi İspatı

| full | v3 | v4 |
|---|---|---|
| Sonuç | ok | ok |
| Soru | İç açıortay teoreminin ispatında hangi yöntem daha net bir sonuç verir? | İki öğrenci tartışıyor. Ali: "İç açıortay teoremi, açıortayın ayırdığı parçaların oranlarının eşit olduğunu söyler." Ayşe: "İç açıortay teoremi, yalnızca açıların eşitliğini ifade eder." Anlatılanlara göre hangi değerlendirme doğrudur? |
| Seçenekler | Dik üçgen yöntemi<br>Eşlik benzerlik yöntemi<br>Çizgi yöntemi<br>Kenarortay teoremi | İki iddia da desteklenir.<br>İki iddia da anlatılanlarla çelişir.<br>Ayşe'nin iddiası desteklenir, Ali'ninki desteklenmez.<br>Ali'nin iddiası desteklenir, Ayşe'ninki desteklenmez. |
| Doğru cevap | Eşlik benzerlik yöntemi | Ali'nin iddiası desteklenir, Ayşe'ninki desteklenmez. |
| Kaynak alıntısı | madem kenar uzunluklarıyla çalışacağız, o zaman sana bir teorem vermem lazım. Dolayısıyla hadi gel iç açıortaylar için, yani üçgenin içerisinde bulunan açıortaylar için teoremimize hemen bir bakalım. | C'nin X'e oranı, yani sağ bölü sağ parça B'nin Y'ye oranına eşit, yani sol bölü sol parça gibi düşünebilirsin. |
| Kaynak zamanı | 1:03 · alıntı bulundu | 1:47 · alıntı bulundu |
| İşaretler | yok | örnek sızıntısı (Ali, Ayşe, iki öğrenci) |

| rag | v3 | v4 |
|---|---|---|
| Sonuç | ok | ok |
| Soru | İç açıortay teoremi ile ilgili olarak, C'nin X'e oranı ile B'nin Y'ye oranı arasındaki ilişkiyi değerlendirdiğimizde hangi ifade doğrudur? | İki öğrenci tartışıyor. Ali: "Açıortay teoremi, bir kenarın uzunluğunun, o kenarı ayıran parçaların oranına eşit olduğunu söyler." Ayşe: "Açıortay teoremi, sadece açıların oranları ile ilgilidir." Anlatılanlara göre hangi değerlendirme doğrudur? |
| Seçenekler | C'nin X'e oranı B'nin Y'ye oranından büyüktür.<br>C'nin X'e oranı B'nin Y'ye oranı ile ilgisizdir.<br>C'nin X'e oranı B'nin Y'ye oranından küçüktür.<br>C'nin X'e oranı B'nin Y'ye oranına eşittir. | Ayşe'nin iddiası desteklenir, Ali'ninki desteklenmez.<br>Ali'nin iddiası desteklenir, Ayşe'ninki desteklenmez.<br>İki iddia da anlatılanlarla çelişir.<br>İki iddia da desteklenir. |
| Doğru cevap | C'nin X'e oranı B'nin Y'ye oranına eşittir. | Ali'nin iddiası desteklenir, Ayşe'ninki desteklenmez. |
| Kaynak alıntısı | C'nin X'e oranı, yani sağ bölü sağ parça B'nin Y'ye oranına eşit, yani sol bölü sol parça gibi düşünebilirsin. | C'nin X'e oranı B'nin Y'ye oranına eşittir. |
| Kaynak zamanı | 1:47 · alıntı bulundu | 5:17 · alıntı bulundu |
| İşaretler | benzer soru: konu 1 | örnek sızıntısı (Ali, Ayşe, iki öğrenci) |

#### Konu 4 · hedef düzey Yaratma · Açıortay Teoremi Uygulamaları

| full | v3 | v4 |
|---|---|---|
| Sonuç | empty | empty: Açıortay Teoremi bağlamda geçiyor ancak yaratma düzeyinde bir soru oluşturmak için yeterli bilgi yok. |

| rag | v3 | v4 |
|---|---|---|
| Sonuç | empty | ok |
| Soru | — | Bir öğrenci, açıortay teoremini kullanarak bir üçgenin kenar uzunluklarını oranlamak istiyor. Aşağıdaki düzeneklerden hangisi bu amaca en uygundur? |
| Seçenekler | — | Üçgenin iç açılarının toplamını hesaplamak.<br>Açıortay çizimi yaparak kenar uzunluklarını ölçmek.<br>Üçgenin çevresini hesaplamak için kenar uzunluklarını toplamak.<br>Açıortayı kullanarak kenar uzunluklarının oranını belirlemek. |
| Doğru cevap | — | Açıortayı kullanarak kenar uzunluklarının oranını belirlemek. |
| Kaynak alıntısı | — | Yani benzerlik üzerinden eee bunları ispatlayabiliyoruz. |
| Kaynak zamanı | — | 5:26 · alıntı bulundu |
| İşaretler | — | yazım kuralı 12; benzer soru: konu 6 |

#### Konu 5 · hedef düzey Anlama · Dik Açıortay ve Kenarortay

| full | v3 | v4 |
|---|---|---|
| Sonuç | ok | ok |
| Soru | Dik açıortay ve kenarortay özelliği taşıyan bir üçgenin hangi özelliği vardır? | Dik açıortay özelliği taşıyan bir üçgenin kenar uzunlukları arasında hangi ilişki vardır? |
| Seçenekler | Eşkenar üçgen oluşturur.<br>İkizkenar üçgen oluşturur.<br>Dörtgen oluşturur.<br>Dik üçgen oluşturur. | Kenar uzunlukları toplamı her zaman 90'dır.<br>Kenar uzunlukları her zaman farklıdır.<br>Kenar uzunlukları eşit olmalıdır.<br>Kenar uzunlukları birbirine orantılıdır. |
| Doğru cevap | İkizkenar üçgen oluşturur. | Kenar uzunlukları birbirine orantılıdır. |
| Kaynak alıntısı | demek ki bu açıortay dik gidiyorsa demek ki bu açıortay dik gidiyorsa demek ki bu gittiği yerde de kenarortaylık sağlatacak. | Dik açıortay, aynı zamanda kenarortay özelliği taşır ve ikizkenar üçgen oluşturur. |
| Kaynak zamanı | yok · alıntı bulunamadı | yok · alıntı bulunamadı |
| İşaretler | yok | yazım kuralı 11 |

| rag | v3 | v4 |
|---|---|---|
| Sonuç | ok | ok |
| Soru | Dik açıortay ve kenarortay özelliği taşıyan bir üçgenin hangi tür üçgen olduğu söylenmektedir? | Dik açıortay özelliği taşımak, aynı zamanda hangi özelliği de taşır? |
| Seçenekler | İkizkenar Üçgen<br>Dar Açılı Üçgen<br>Dik Üçgen<br>Eşkenar Üçgen | İkizkenar üçgen<br>Kenarortay<br>Dik kenar<br>Açıortay |
| Doğru cevap | İkizkenar Üçgen | İkizkenar üçgen |
| Kaynak alıntısı | Dik açıortay, aynı zamanda kenarortay özelliği taşır ve ikizkenar üçgen oluşturur. | Dik açıortay, aynı zamanda kenarortay özelliği taşır ve ikizkenar üçgen oluşturur. |
| Kaynak zamanı | yok · alıntı bulunamadı | yok · alıntı bulunamadı |
| İşaretler | yok | yazım kuralı 4 |

#### Konu 6 · hedef düzey Çözümleme · Açıortay Teoremi ile Oranlama

| full | v3 | v4 |
|---|---|---|
| Sonuç | ok | ok |
| Soru | Açıortay teoremi kullanılarak, bir üçgende C kenarının uzunluğu 10 birim, X parçasının uzunluğu 5 birim olduğunda, B kenarının uzunluğu ne olmalıdır? | Açıortay teoremi ile ilgili verilen bilgilere göre, C'nin X'e oranı ile B'nin Y'ye oranı arasındaki ilişki nedir? |
| Seçenekler | 10 birim<br>15 birim<br>20 birim<br>25 birim | C/X = B/Y<br>C/Y = X/B<br>C/X = Y/B<br>C/Y = B/X |
| Doğru cevap | 15 birim | C/X = B/Y |
| Kaynak alıntısı | C'nin X'e oranı, yani sağ bölü sağ parça B'nin Y'ye oranına eşit, yani sol bölü sol parça gibi düşünebilirsin. | C'nin X'e oranı, yani sağ bölü sağ parça B'nin Y'ye oranına eşit, yani sol bölü sol parça gibi düşünebilirsin. |
| Kaynak zamanı | 1:47 · alıntı bulundu | 1:47 · alıntı bulundu |
| İşaretler | olası cevap kökte | yok |

| rag | v3 | v4 |
|---|---|---|
| Sonuç | ok | ok |
| Soru | Açıortay teoremi kullanılarak, üçgenin kenar uzunlukları arasındaki oranlar nasıl belirlenir? | Açıortay teoremi kullanılarak, üçgenin kenar uzunlukları arasındaki oranlar nasıl belirlenir? |
| Seçenekler | Üçgenin iç açıları toplamı 180 derecedir.<br>Birinci kolun uzunluğu, ikinci kolun uzunluğuna eşittir.<br>Birinci kolun birinci parçaya oranı, ikinci kolun ikinci parçaya oranına eşittir.<br>Açıortay, üçgenin alanını iki eşit parçaya böler. | Birinci kolun birinci parçaya oranı, ikinci kolun birinci parçaya oranına eşittir.<br>Birinci kolun ikinci parçaya oranı, ikinci kolun birinci parçaya oranına eşittir.<br>Birinci kolun birinci parçaya oranı, ikinci kolun ikinci parçaya oranına eşittir.<br>Birinci kolun ikinci parçaya oranı, ikinci kolun ikinci parçaya oranına eşittir. |
| Doğru cevap | Birinci kolun birinci parçaya oranı, ikinci kolun ikinci parçaya oranına eşittir. | Birinci kolun birinci parçaya oranı, ikinci kolun ikinci parçaya oranına eşittir. |
| Kaynak alıntısı | C'nin X'e oranı, yani sağ bölü sağ parça B'nin Y'ye oranına eşit, | C'nin X'e oranı, yani sağ bölü sağ parça B'nin Y'ye oranına eşit, |
| Kaynak zamanı | 1:47 · alıntı bulundu | 1:47 · alıntı bulundu |
| İşaretler | yazım kuralı 4 | benzer soru: konu 1, 4 |

### ingilizce

#### Konu 1 · hedef düzey Hatırlama · Gelenekler ve Önemli Kelimeler

| full | v3 | v4 |
|---|---|---|
| Sonuç | ok | ok |
| Soru | Dersin başlangıcında hangi konular tanıtılmaktadır? | Dersin başlangıcında hangi konular tanıtılmaktadır? |
| Seçenekler | Teknoloji ve ulaşım<br>Gelenekler ve önemli kelimeler<br>Sosyal hayat ve çiftçilik<br>Duygular ve alışkanlıklar | Savaş teknolojileri<br>Gelenekler ve önemli kelimeler<br>Tarım ve çiftçilik<br>Sosyal hayat ve giyim |
| Doğru cevap | Gelenekler ve önemli kelimeler | Gelenekler ve önemli kelimeler |
| Kaynak alıntısı | Bu dersimizde on sınıfın dördüncü ünitesi olan gördüğü tions yani gelenekler Az önce hep birlikte işleyeceğiz dersimize bunu da içerisinde bulunan bilmeniz gereken önemli kelimelerle başlayacağız | Bu dersimizde on sınıfın dördüncü ünitesi olan gördüğü tions yani gelenekler Az önce hep birlikte işleyeceğiz dersimize bunu da içerisinde bulunan bilmeniz gereken önemli kelimelerle başlayacağız |
| Kaynak zamanı | 0:02 · alıntı bulundu | 0:02 · alıntı bulundu |
| İşaretler | yok | yazım kuralı 4 |

| rag | v3 | v4 |
|---|---|---|
| Sonuç | ok | ok |
| Soru | Dersin başlangıcında hangi konu tanıtılmaktadır? | Dersin başlangıcında hangi konu tanıtılmaktadır? |
| Seçenekler | Eğitim ve alışkanlıklar<br>Gelenekler ve önemli kelimeler<br>Teknoloji ve ulaşım<br>Savaş ve sosyal hayat | Eğitim ve alışkanlıklar<br>Gelenekler ve önemli kelimeler<br>Teknoloji ve savaş<br>Sosyal hayat ve çiftçilik |
| Doğru cevap | Gelenekler ve önemli kelimeler | Gelenekler ve önemli kelimeler |
| Kaynak alıntısı | Bu dersimizde on sınıfın dördüncü ünitesi olan gördüğü tions yani gelenekler Az önce hep birlikte işleyeceğiz dersimize bunu da içerisinde bulunan bilmeniz gereken önemli kelimelerle başlayacağız | Bu dersimizde on sınıfın dördüncü ünitesi olan gördüğü tions yani gelenekler Az önce hep birlikte işleyeceğiz dersimize bunu da içerisinde bulunan bilmeniz gereken önemli kelimelerle başlayacağız |
| Kaynak zamanı | 0:02 · alıntı bulundu | 0:02 · alıntı bulundu |
| İşaretler | yazım kuralı 4 | yok |

#### Konu 2 · hedef düzey Değerlendirme · Yüz Kalıbının Kullanımı

| full | v3 | v4 |
|---|---|---|
| Sonuç | ok | ok |
| Soru | Aşağıdaki cümlelerden hangisi yüz kalıbının kullanımına uygun bir örnek değildir? | Aşağıdaki cümlelerden hangisi yüz kalıbının kullanımını doğru bir şekilde ifade etmektedir? |
| Seçenekler | O, gençken futbol oynardı.<br>Onlar, geçen yaz sinemaya gitmezdi.<br>Ben çocukken yüzerdim.<br>Biz, geçen yıl tatile gitmedik. | Ben çocukken yüzme dersi almıyordum.<br>Ben çocukken her gün yüzme dersi alıyordum.<br>Ben çocukken yüzme dersi almazdım.<br>Ben çocukken yüzme dersi almadım. |
| Doğru cevap | Onlar, geçen yaz sinemaya gitmezdi. | Ben çocukken yüzme dersi almazdım. |
| Kaynak alıntısı | yüz kalıbı şu amaçlarla kullanılır geçmişte sürekli olarak yapılan Ama artık yapılmayan eylemleriniz den yada alışkanlıklarınızdan bahsedecek siniz | yüz kalıbı şu amaçlarla kullanılır geçmişte sürekli olarak yapılan Ama artık yapılmayan eylemleriniz den yada alışkanlıklarınızdan bahsedecek siniz |
| Kaynak zamanı | 5:04 · alıntı bulundu | 5:04 · alıntı bulundu |
| İşaretler | yazım kuralı 19 | yok |

| rag | v3 | v4 |
|---|---|---|
| Sonuç | ok | ok |
| Soru | Aşağıdaki cümlelerden hangisi yüz kalıbının kullanımını doğru bir şekilde yargılamaktadır? | Aşağıdaki cümlelerden hangisi yüz kalıbının doğru kullanımını gösterir? |
| Seçenekler | Ben çocukken yüzmeyi sevmezdim.<br>Ben çocukken yüzerdim.<br>Ben çocukken yüzmeyi öğrenmedim.<br>Ben çocukken yüzmüyordum. | Ben çocukken futbol oynardım.<br>Ben çocukken futbol oynamıyorum.<br>Ben çocukken futbol oynuyorum.<br>Ben çocukken futbol oynamadım. |
| Doğru cevap | Ben çocukken yüzerdim. | Ben çocukken futbol oynardım. |
| Kaynak alıntısı | yüz kalıbı şu amaçlarla kullanılır geçmişte sürekli olarak yapılan Ama artık yapılmayan eylemleriniz den yada alışkanlıklarınızdan bahsedecek siniz | yüz kalıbı şu amaçlarla kullanılır geçmişte sürekli olarak yapılan Ama artık yapılmayan eylemleriniz den yada alışkanlıklarınızdan bahsedecek siniz |
| Kaynak zamanı | 5:04 · alıntı bulundu | 5:04 · alıntı bulundu |
| İşaretler | yok | yok |

#### Konu 3 · hedef düzey Uygulama · Olumlu Cümle Yapısı

| full | v3 | v4 |
|---|---|---|
| Sonuç | ok | ok |
| Soru | Aşağıdaki cümlelerden hangisi yüz kalıbı kullanılarak doğru bir şekilde oluşturulmuştur? | Aşağıdaki cümlelerden hangisi yüz kalıbı kullanılarak doğru bir şekilde oluşturulmuştur? |
| Seçenekler | Ben çocukken yüzmeyi severdim.<br>Ben çocukken yüzmeyi sevmem.<br>Ben çocukken yüzmeyi sevmedim.<br>Ben çocukken yüzmeyi sevmiyorum. | Ben çocukken yüzmeyi severdim.<br>Ben çocukken yüzmeyi sevmem.<br>Ben çocukken yüzmeyi sevmedim.<br>Ben çocukken yüzmeyi sevmiyordum. |
| Doğru cevap | Ben çocukken yüzmeyi severdim. | Ben çocukken yüzmeyi severdim. |
| Kaynak alıntısı | kalıbını kullanarak Eğer olumlu bir cümle kurmak istiyorsanız şu kurallara dikkat etmemiz gerekir | kalıbını kullanarak Eğer olumlu bir cümle kurmak istiyorsanız şu kurallara dikkat etmemiz gerekir |
| Kaynak zamanı | 5:33 · alıntı bulundu | 5:33 · alıntı bulundu |
| İşaretler | yok | yok |

| rag | v3 | v4 |
|---|---|---|
| Sonuç | ok | ok |
| Soru | Aşağıdaki cümlelerden hangisi yüz kalıbı kullanılarak olumlu bir şekilde ifade edilmiştir? | Aşağıdaki cümlelerden hangisi yüz kalıbıyla olumlu bir cümle kurma kuralına uygundur? |
| Seçenekler | They did not go to the park.<br>She did not eat dinner.<br>I did not play football.<br>He did play football. | I did not play football.<br>He did play football.<br>She did plays football.<br>They did not play football. |
| Doğru cevap | He did play football. | He did play football. |
| Kaynak alıntısı | Eğer olumlu bir cümle kurmak istiyorsanız şu kurallara dikkat etmemiz gerekir | Eğer olumlu bir cümle kurmak istiyorsanız şu kurallara dikkat etmemiz gerekir bir cümle Öncelikle biraz ne ile başlarız |
| Kaynak zamanı | 5:33 · alıntı bulundu | 5:33 · alıntı bulundu |
| İşaretler | yok | yok |

#### Konu 4 · hedef düzey Anlama · Olumsuz Cümle Yapısı

| full | v3 | v4 |
|---|---|---|
| Sonuç | ok | ok |
| Soru | Yüz kalıbıyla olumsuz bir cümle kurmak için hangi kelime kullanılmalıdır? | Yüz kalıbıyla olumsuz bir cümle kurmak için hangi kelime kullanılmalıdır? |
| Seçenekler | does<br>did<br>do<br>had | do<br>did<br>does<br>had |
| Doğru cevap | did | did |
| Kaynak alıntısı | negatif form olumsuz hal demektir Eğer yüz kalıbını kullanarak olumsuz bir cümle bu istiyorsak şu kalıplara dikkat etmeliyiz Biz cümleyi bir özne ile başlarız ay ve Yuh Bey he she it özel lerinden biri Tabletimi yazdıktan sonra negatifi geçiyor lan did kelimesini kullanırız | negatif form olumsuz hal demektir Eğer yüz kalıbını kullanarak olumsuz bir cümle bu istiyorsak şu kalıplara dikkat etmeliyiz |
| Kaynak zamanı | 7:47 · alıntı bulundu | 7:47 · alıntı bulundu |
| İşaretler | benzer soru: konu 6 | yok |

| rag | v3 | v4 |
|---|---|---|
| Sonuç | ok | ok |
| Soru | Yüz kalıbı ile olumsuz bir cümle kurmak için hangi ifadeyi kullanmalıyız? | Yüz kalıbı ile olumsuz bir cümle kurmak için hangi ifadeyi kullanmalıyız? |
| Seçenekler | Did yüzü<br>Did yüz<br>Did not yüz<br>Didn't yüz | Doesn't yüz<br>Did yüz<br>Did not yüz<br>Didn't yüz |
| Doğru cevap | Didn't yüz | Didn't yüz |
| Kaynak alıntısı | negatif belirtmek için did kelimesini kullanırız ama Özellikle belirtmek istediğim bir nokta vardır Burası sorularda en çok sorular noktadır dedim kelimesini kullandıktan sonra yüzüstü kelimesinde ufak bir değişiklik olacaktır yani din 102 olarak kullanmanızı yanlıştır | negatif yapar Kendini yüz ifadesini kullanırız daha sonra yanındaki zil ekleriz |
| Kaynak zamanı | 8:21 · alıntı bulundu | 12:54 · alıntı bulundu |
| İşaretler | benzer soru: konu 6 | yok |

#### Konu 5 · hedef düzey Yaratma · Soru Cümlesi Oluşturma

| full | v3 | v4 |
|---|---|---|
| Sonuç | ok | duplicate |
| Soru | Aşağıdaki cümlelerden hangisi yüz kalıbı kullanılarak doğru bir soru cümlesi oluşturulmuştur? | — |
| Seçenekler | Did you playing football when you were a child?<br>Do you play football when you were a child?<br>Did you played football when you were a child?<br>Did you play football when you were a child? | — |
| Doğru cevap | Did you play football when you were a child? | — |
| Kaynak alıntısı | Eğer yüz ifadesini soru yapacaksak şu kurallara dikkat etmeliyiz Biz sürekli olarak cümlenin başında da ifadesini kullanırız ardından İngilizce'de bulunan yedi tane Özen'in bir tanesini yazarız ve daha sonra yüz kalıbının kendisini yazdıktan sonra fiilin birinci haline ek almamış halinde kullanırız | — |
| Kaynak zamanı | 10:12 · alıntı bulundu | — |
| İşaretler | yok | — |

| rag | v3 | v4 |
|---|---|---|
| Sonuç | ok | ok |
| Soru | Aşağıdaki cümlelerden hangisi, 'yüz kalıbı' kullanılarak doğru bir soru cümlesi oluşturulmuştur? | Aşağıdaki cümlelerden hangisi, yüz kalıbını kullanarak geçmişte sürekli yapılan ama artık yapılmayan bir eylemi ifade etmek için doğru bir soru cümlesi oluşturur? |
| Seçenekler | Do you played football yesterday?<br>Did you playeds football yesterday?<br>Did you plays football yesterday?<br>Did you play football yesterday? | Did you play football?<br>Did you played football?<br>Did you plays football?<br>Did you not play football? |
| Doğru cevap | Did you play football yesterday? | Did you play football? |
| Kaynak alıntısı | Eğer yüz ifadesini soru yapacaksak şu kurallara dikkat etmeliyiz | Eğer yüz ifadesini soru yapacaksak şu kurallara dikkat etmeliyiz Biz sürekli olarak cümlenin başında da ifadesini kullanırız ardından İngilizce'de bulunan yedi tane Özen'in bir tanesini yazarız ve daha sonra yüz kalıbının kendisini yazdıktan sonra fiilin birinci haline ek almamış halinde kullanırız |
| Kaynak zamanı | 10:12 · alıntı bulundu | 10:12 · alıntı bulundu |
| İşaretler | yok | yazım kuralı 19 |

#### Konu 6 · hedef düzey Çözümleme · Alıştırma Soruları

| full | v3 | v4 |
|---|---|---|
| Sonuç | ok | ok |
| Soru | Yüz kalıbını kullanarak olumsuz bir cümle oluşturmak için hangi ifadeyi kullanmalıyız? | Yüz kalıbının olumsuz haliyle cümle kurmak için hangi sırayı izlemeliyiz? |
| Seçenekler | Does<br>Had<br>Did<br>Do | Özne → fiil → yüz kalıbı → did<br>Özne → yüz kalıbı → did → fiil<br>Özne → did → yüz kalıbı → fiil<br>Did → özne → yüz kalıbı → fiil |
| Doğru cevap | Did | Özne → did → yüz kalıbı → fiil |
| Kaynak alıntısı | Eğer yüz kalıbını kullanarak olumsuz bir cümle bu istiyorsak şu kalıplara dikkat etmeliyiz Biz cümleyi bir özne ile başlarız ay ve Yuh Bey he she it özel lerinden biri Tabletimi yazdıktan sonra negatif anlam katmak için did kelimesini kullanırız. | Eğer yüz kalıbını kullanarak olumsuz bir cümle bu istiyorsak şu kalıplara dikkat etmeliyiz Biz cümleyi bir özne ile başlarız ay ve Yuh Bey he she it özel lerinden biri Tabletimi yazdıktan sonra negatifi geçiyor lan did kelimesini kullanırız ardından yüz ifadesini yazarız |
| Kaynak zamanı | yok · alıntı bulunamadı | 7:47 · alıntı bulundu |
| İşaretler | benzer soru: konu 4 | olası cevap kökte |

| rag | v3 | v4 |
|---|---|---|
| Sonuç | ok | ok |
| Soru | Yüz kalıbının olumsuz cümle yapısında hangi kelime kullanılmalıdır? | Yüz kalıbının olumlu bir cümlede nasıl kullanıldığını açıklayan doğru sıra hangisidir? |
| Seçenekler | Do<br>Was<br>Does<br>Did | A) Özne yazılır → yüz kalıbı eklenir → fiil yalın haliyle yazılır.<br>B) Yüz kalıbı yazılır → özne eklenir → fiil geçmiş zaman eki alır.<br>D) Fiil geçmiş zaman eki alır → özne yazılır → yüz kalıbı eklenir.<br>C) Did kelimesi yazılır → özne eklenir → yüz kalıbı eklenir. |
| Doğru cevap | Did | A) Özne yazılır → yüz kalıbı eklenir → fiil yalın haliyle yazılır. |
| Kaynak alıntısı | negatif anlamda Dandini kelimesini yazar Daha sonra yüz ifadesini kullanırız | Eğer olumlu bir cümle kurmak istiyorsanız şu kurallara dikkat etmemiz gerekir bir cümle Öncelikle biraz ne ile başlarız... ardından yüz ifadesini yazarız. |
| Kaynak zamanı | 10:03 · alıntı bulundu | yok · alıntı bulunamadı |
| İşaretler | benzer soru: konu 4 | yok |

### edebiyat

#### Konu 1 · hedef düzey Yaratma · Milli Edebiyat Dönemi Tanımı

| full | v3 | v4 |
|---|---|---|
| Sonuç | ok | ok |
| Soru | Milli Edebiyat Dönemi'nde eserlerin konuları ve temaları arasında hangisi en belirgin olanıdır? | Milli Edebiyat Dönemi'nde eserlerin hangi unsurları bir araya getirerek yazılması amaçlanmıştır? |
| Seçenekler | Süslü dil kullanımı<br>Anadolu insanının yaşamı<br>Batı edebiyatı etkileri<br>Arap ve Fars edebiyatı | Sadece bireysel duygular ve soyut temalar<br>Arapça ve Farsça tamlamalar<br>Batı edebiyatı ve Fransızca kelimeler<br>Halkın günlük yaşamı ve Anadolu insanının hikayeleri |
| Doğru cevap | Anadolu insanının yaşamı | Halkın günlük yaşamı ve Anadolu insanının hikayeleri |
| Kaynak alıntısı | Edebiyatçılar Anadolu'yu ve Anadolu insanını eserlerine taşımıştır. | Milli Edebiyat Döneminde de yine eserlerin konusu olacak. Sade Türkçe, ağır ve süslü dilden kaçınılmış, halka yakın, anlaşılır bir dil kullanılacak. |
| Kaynak zamanı | 1:14 · alıntı bulundu | 1:21 · alıntı bulundu |
| İşaretler | yok | yok |

| rag | v3 | v4 |
|---|---|---|
| Sonuç | ok | ok |
| Soru | Milli Edebiyat Dönemi'nde hangi özellikler bir araya getirilerek edebi eserler oluşturulmuştur? | Bir grup öğrenci, Milli Edebiyat Dönemi'nin etkilerini anlamak için bir proje hazırlamaktadır. Aşağıdaki projelerden hangisi, bu dönemin milliyetçi ve yerel unsurlarını en iyi şekilde yansıtır? |
| Seçenekler | Toplum için sanat anlayışı ve Anadolu insanının hayatı<br>Sadece bireysel duyguların ön planda tutulması<br>Sadece Batı edebiyatından esinlenme<br>Arapça ve Farsça kelimelerin yoğun kullanımı | D) Farklı milletlerin edebiyatlarını karşılaştırmak.<br>A) Yabancı edebiyat eserlerini inceleyip sunmak.<br>B) Anadolu insanının günlük yaşamını ve kültürel değerlerini belgelemek.<br>C) Batı edebiyatındaki akımları analiz etmek. |
| Doğru cevap | Toplum için sanat anlayışı ve Anadolu insanının hayatı | B) Anadolu insanının günlük yaşamını ve kültürel değerlerini belgelemek. |
| Kaynak alıntısı | Milli Edebiyat Döneminde 1911 yılında Selanik'te Genç Kalemler dergisi etrafında toplanan... Anadolu coğrafyası, Anadolu insanı edebiyata taşınmıştır. | Milli Edebiyat Döneminde... Anadolu coğrafyası, Anadolu insanı edebiyata taşınmıştır. |
| Kaynak zamanı | yok · alıntı bulunamadı | yok · alıntı bulunamadı |
| İşaretler | yok | yazım kuralı 4 |

#### Konu 2 · hedef düzey Anlama · Yeni Lisan Hareketi

| full | v3 | v4 |
|---|---|---|
| Sonuç | ok | ok |
| Soru | Yeni Lisan Hareketi'nin amacı nedir? | Yeni Lisan Hareketi'nin amacı nedir? |
| Seçenekler | Sadece İstanbul Türkçesini kullanmak<br>Halk edebiyatına dönüş yapmak<br>Batı edebiyatını benimsemek<br>Arapça ve Farsça kelimeleri artırmak | Sadece İstanbul Türkçesini kullanmak<br>Halk edebiyatına dönüş yapmak<br>Arapça ve Farsça kelimeleri artırmak<br>Batı edebiyatını taklit etmek |
| Doğru cevap | Halk edebiyatına dönüş yapmak | Halk edebiyatına dönüş yapmak |
| Kaynak alıntısı | Yeni Lisan yani yeni dil hareketini başlatacaklar ve dilimizdeki Arapça, Farsça, işte farklı dillerden gelmiş Fransızca sözcükleri atıp pırıl pırıl ta Halk Edebiyatı Dönemindeki öz Türkçeye dönecekler. | 'Yeni Lisan yani yeni dil hareketini başlatacaklar ve dilimizdeki Arapça, Farsça, işte farklı dillerden gelmiş Fransızca sözcükleri atıp pırıl pırıl ta Halk Edebiyatı Dönemindeki öz Türkçeye dönecekler.' |
| Kaynak zamanı | yok · alıntı bulunamadı | yok · alıntı bulunamadı |
| İşaretler | yok | yok |

| rag | v3 | v4 |
|---|---|---|
| Sonuç | ok | ok |
| Soru | Yeni Lisan Hareketi'nin amacı nedir? | Yeni Lisan hareketinin amacı nedir? |
| Seçenekler | Sadece İstanbul Türkçesini kullanmak<br>Halk edebiyatına dönüş yapmak<br>Arapça ve Farsça kelimeleri artırmak<br>Edebiyatı Batı'ya yönlendirmek | Sanat için sanat anlayışını benimsemek<br>Halk edebiyatına dönüş yapmak<br>Arapça ve Farsça kelimeleri artırmak<br>Sadece İstanbul Türkçesini kullanmak |
| Doğru cevap | Halk edebiyatına dönüş yapmak | Halk edebiyatına dönüş yapmak |
| Kaynak alıntısı | Yeni Lisan yani yeni dil hareketini başlatacaklar ve dilimizdeki Arapça, Farsça, işte farklı farklı dillerden gelmiş Fransızca sözcükleri atıp pırıl pırıl ta Halk Edebiyatı Dönemindeki öz Türkçeye dönecekler | Yeni Lisan yani yeni dil hareketini başlatacaklar ve dilimizdeki Arapça, Farsça, işte farklı farklı dillerden gelmiş Fransızca sözcükleri atıp pırıl pırıl ta Halk Edebiyatı Dönemindeki öz Türkçeye dönecekler |
| Kaynak zamanı | 0:54 · alıntı bulundu | 0:54 · alıntı bulundu |
| İşaretler | yok | yok |

#### Konu 3 · hedef düzey Değerlendirme · Edebiyatın Temaları

| full | v3 | v4 |
|---|---|---|
| Sonuç | ok | ok |
| Soru | Milli Edebiyat Dönemi'nde vatan sevgisi, bağımsızlık ve kahramanlık temalarının ön plana çıkmasının sebebi nedir? | Milli Edebiyat Dönemi'nde vatan sevgisi, bağımsızlık ve kahramanlık temalarının önemi nedir? |
| Seçenekler | Bu temalar, yalnızca bireysel duyguları ifade etmek için önemlidir.<br>Bu temalar yalnızca edebi eserlerde yer alır.<br>Bu temalar, sadece tarihsel olayları anlatmak için kullanılır.<br>Bu temalar, toplumun bilinçlenmesi ve milli kimliğin güçlenmesi için önemlidir. | Bu temalar, milli kimliği ve bağımsızlık bilincini güçlendirmek amacıyla önemlidir.<br>Bu temalar yalnızca edebi eserlerde yer alır, toplumsal bir etkisi yoktur.<br>Bu temalar, yalnızca halk edebiyatı ile sınırlıdır.<br>Bu temalar, sadece tarihsel olayları anlatmak için kullanılır. |
| Doğru cevap | Bu temalar, toplumun bilinçlenmesi ve milli kimliğin güçlenmesi için önemlidir. | Bu temalar, milli kimliği ve bağımsızlık bilincini güçlendirmek amacıyla önemlidir. |
| Kaynak alıntısı | Vatan sevgisi, bağımsızlık, aynı zamanda kahramanlık, doğa ve tarih önemli konular, temalar olacak. | Vatan sevgisi, bağımsızlık, aynı zamanda kahramanlık, doğa ve tarih önemli konular, temalar olacak. |
| Kaynak zamanı | 2:01 · alıntı bulundu | 2:01 · alıntı bulundu |
| İşaretler | yazım kuralı 12 | yazım kuralı 12 |

| rag | v3 | v4 |
|---|---|---|
| Sonuç | ok | ok |
| Soru | Aşağıdaki ifadelerden hangisi vatan sevgisi, bağımsızlık ve kahramanlık temalarının edebiyat üzerindeki etkisini en iyi şekilde yansıtır? | Milli Edebiyat Dönemi'nde vatan sevgisi, bağımsızlık ve kahramanlık temalarının önemi nedir? Aşağıdaki değerlendirmelerden hangisi doğrudur? |
| Seçenekler | Bu temalar, edebiyat eserlerinde sadece bireysel duyguları ifade etmek için yer alır.<br>Bu temalar, edebiyat eserlerinde yalnızca tarihi olayları anlatmak için kullanılır.<br>Vatan sevgisi, bağımsızlık ve kahramanlık, edebiyatın milli kimliği güçlendirmede önemli rol oynar.<br>Kahramanlık teması, edebiyatın yalnızca savaş hikayelerinde geçerli bir konusudur. | Bu temalar, edebiyatın sadece estetik yönünü güçlendirir.<br>Bu temalar, edebiyatın evrensel değerlerini göz ardı eder.<br>Bu temalar, milli kimliği ve bağımsızlık bilincini güçlendirmek için önemlidir.<br>Bu temalar, yalnızca tarihsel olayları anlatmak için kullanılır. |
| Doğru cevap | Vatan sevgisi, bağımsızlık ve kahramanlık, edebiyatın milli kimliği güçlendirmede önemli rol oynar. | Bu temalar, milli kimliği ve bağımsızlık bilincini güçlendirmek için önemlidir. |
| Kaynak alıntısı | Vatan sevgisi, bağımsızlık, aynı zamanda kahramanlık, doğa ve tarih önemli konular, temalar olacak. | Vatan sevgisi, bağımsızlık, aynı zamanda kahramanlık, doğa ve tarih önemli konular, temalar olacak. |
| Kaynak zamanı | 2:01 · alıntı bulundu | 2:01 · alıntı bulundu |
| İşaretler | yazım kuralı 12 | yazım kuralı 12 |

#### Konu 4 · hedef düzey Uygulama · Osmanlıcılık Akımı

| full | v3 | v4 |
|---|---|---|
| Sonuç | ok | ok |
| Soru | Osmanlıcılık akımının temel amacı nedir? | Osmanlıcılık akımının uygulanması durumunda, Osmanlı Devleti'nde farklı etnik grupların bir arada yaşaması için hangi yaklaşım benimsenmiştir? |
| Seçenekler | Sadece Türklerin haklarını savunmak<br>Balkan uluslarını Osmanlı Devleti'nden ayırmak<br>Batı kültürünü benimsemek<br>Osmanlı vatandaşlığı temelinde devletin bütünlüğünü korumak | Osmanlı vatandaşlığı temelinde bir arada yaşama<br>Halkın farklılıklarını vurgulamak<br>Her etnik grubun bağımsızlık talep etmesi<br>Sadece Türk kimliğini ön plana çıkarmak |
| Doğru cevap | Osmanlı vatandaşlığı temelinde devletin bütünlüğünü korumak | Osmanlı vatandaşlığı temelinde bir arada yaşama |
| Kaynak alıntısı | Osmanlıcılık akımı Osmanlı vatandaşlığı temelinde devletin bütünlüğünü korumaya çalışıyor. | Osmanlıcılık akımı Osmanlı vatandaşlığı temelinde devletin bütünlüğünü korumaya çalışıyor. |
| Kaynak zamanı | 5:15 · alıntı bulundu | 5:15 · alıntı bulundu |
| İşaretler | yazım kuralı 12 | olası cevap kökte; yazım kuralı 12 |

| rag | v3 | v4 |
|---|---|---|
| Sonuç | ok | ok |
| Soru | Osmanlıcılık akımının uygulanması durumunda, Osmanlı Devleti'nde farklı etnik grupların bir arada nasıl yaşaması bekleniyordu? | Osmanlıcılık akımının başarılı olabilmesi için hangi stratejinin uygulanması gerekiyordu? |
| Seçenekler | Herkes kendi etnik kimliğini ön plana çıkaracak.<br>Tüm etnik gruplar Osmanlı vatandaşlığı altında birleşecek.<br>Farklı etnik gruplar birbirleriyle çatışacak.<br>Her etnik grup kendi bağımsız devletini kuracak. | Batı ile tamamen entegre olmak<br>Balkan uluslarının bağımsızlık taleplerini desteklemek<br>Farklı din ve kültürleri yok saymak<br>Osmanlı vatandaşlığı temelinde bir birlik oluşturmak |
| Doğru cevap | Tüm etnik gruplar Osmanlı vatandaşlığı altında birleşecek. | Osmanlı vatandaşlığı temelinde bir birlik oluşturmak |
| Kaynak alıntısı | Osmanlıcılık akımı Osmanlı vatandaşlığı temelinde devletin bütünlüğünü korumaya çalışıyor. | Osmanlıcılık akımı Osmanlı vatandaşlığı temelinde devletin bütünlüğünü korumaya çalışıyor. |
| Kaynak zamanı | 5:15 · alıntı bulundu | 5:15 · alıntı bulundu |
| İşaretler | yazım kuralı 12 | yazım kuralı 12 |

#### Konu 5 · hedef düzey Çözümleme · Olay ve Durum Hikayeleri

| full | v3 | v4 |
|---|---|---|
| Sonuç | ok | ok |
| Soru | Olay hikayeleri ile durum hikayeleri arasındaki temel fark nedir? | Olay hikayesi ile durum hikayesinin temel farkı nedir? |
| Seçenekler | Olay hikayeleri beklenmedik sonlarla biterken, durum hikayeleri hayatın kesitlerini anlatır.<br>Olay hikayeleri yalnızca Anadolu insanını anlatır, durum hikayeleri ise her türlü karakteri.<br>Durum hikayeleri genellikle kısa ve özken, olay hikayeleri uzun ve detaylıdır.<br>Durum hikayeleri her zaman bir olay içerirken, olay hikayeleri içermez. | Olay hikayesi, beklenmedik sonlarla biterken durum hikayesi her zaman sürpriz bir sonla biter.<br>Olay hikayesi, yalnızca Anadolu insanını anlatırken durum hikayesi evrensel temalar içerir.<br>Olay hikayesi, hayatın kesitlerini anlatırken durum hikayesi belirli bir olay içerir.<br>Olay hikayesi, giriş, gelişme ve sonuç bölümlerine sahiptir; durum hikayesi ise bu bölümleri içermez. |
| Doğru cevap | Olay hikayeleri beklenmedik sonlarla biterken, durum hikayeleri hayatın kesitlerini anlatır. | Olay hikayesi, giriş, gelişme ve sonuç bölümlerine sahiptir; durum hikayesi ise bu bölümleri içermez. |
| Kaynak alıntısı | Olay hikayesi şu: Hikayede eğer bir olay varsa, giriş, sonuçta acaba ne oldu, eyvah ne olacak diyorsanız bu olay hikayesidir... Durum hikayelerinde ise hayatın bir kesiti, yani kesit hikayeleri de denir buna, bir durum anlatılır. | Olay hikayesi şu: Hikayede eğer bir olay varsa, giriş, sonuçta acaba ne oldu, eyvah ne olacak diyorsanız bu olay hikayesidir, |
| Kaynak zamanı | yok · alıntı bulunamadı | 10:31 · alıntı bulundu |
| İşaretler | yazım kuralı 11, 17 | yazım kuralı 11 |

| rag | v3 | v4 |
|---|---|---|
| Sonuç | ok | ok |
| Soru | Aşağıdakilerden hangisi durum hikayelerinin özelliklerinden biri değildir? | Olay hikayeleri ile durum hikayeleri arasındaki temel fark nedir? |
| Seçenekler | Beklenmedik bir sonla biter.<br>Kesit hikayeleri olarak da bilinir.<br>Hayatın belli bir kesitini anlatır.<br>Giriş, gelişme ve sonuç bölümleri yoktur. | Olay hikayeleri, hayatın kesitlerini anlatırken durum hikayeleri beklenmedik sonlarla biter.<br>Durum hikayeleri, klasik hikaye tarzında yazılırken olay hikayeleri modern tarzda yazılır.<br>Olay hikayeleri, sadece Türk tarihinden alınan konuları işlerken durum hikayeleri evrensel temalar içerir.<br>Olay hikayeleri, giriş, gelişme ve sonuç bölümlerine sahipken durum hikayeleri bu bölümlere sahip değildir. |
| Doğru cevap | Beklenmedik bir sonla biter. | Olay hikayeleri, giriş, gelişme ve sonuç bölümlerine sahipken durum hikayeleri bu bölümlere sahip değildir. |
| Kaynak alıntısı | Durum hikayelerinde ise hayatın bir kesiti, yani kesit hikayeleri de denir buna, bir durum anlatılır. | bir durum hikayesini gördüğünüzde giriş, gelişme, sonuç bölümü olmadığını, hayatın belli bir kesitini, belli bir bölümünü aktarıldığını anlatırsınız. |
| Kaynak zamanı | 10:45 · alıntı bulundu | 12:08 · alıntı bulundu |
| İşaretler | yazım kuralı 19 | yok |

#### Konu 6 · hedef düzey Hatırlama · Milli Edebiyat Dönemi Yazarları

| full | v3 | v4 |
|---|---|---|
| Sonuç | ok | ok |
| Soru | Milli Edebiyat Dönemi'nin önde gelen yazarlarından biri kimdir? | Milli Edebiyat Dönemi'nin önde gelen yazarlarından biri kimdir? |
| Seçenekler | Ziya Gökalp<br>Ahmet Mithat Efendi<br>Halit Ziya Uşaklıgil<br>Tevfik Fikret | Ziya Gökalp<br>Ahmet Mithat Efendi<br>Halit Ziya Uşaklıgil<br>Tevfik Fikret |
| Doğru cevap | Ziya Gökalp | Ziya Gökalp |
| Kaynak alıntısı | Milli Edebiyat Dönemi yazarları: Ziya Gökalp, Ömer Seyfettin ve Halide Edip Adıvar gibi yazarlar bu dönemin önde gelen isimleridir. | Ziya Gökalp, Ömer Seyfettin, Ali Canip Yöntem, Mehmet Emin Yurdakul, bak Yurdakul olmuş. Sonradan alıyorlar bunlar soyismini. |
| Kaynak zamanı | yok · alıntı bulunamadı | 9:24 · alıntı bulundu |
| İşaretler | yok | yok |

| rag | v3 | v4 |
|---|---|---|
| Sonuç | ok | ok |
| Soru | Milli Edebiyat Dönemi'nin önde gelen yazarlarından biri kimdir? | Milli Edebiyat Dönemi'nin önde gelen yazarlarından biri kimdir? |
| Seçenekler | Ziya Gökalp<br>Ahmet Hamdi Tanpınar<br>Cevat Şakir Kabaağaçlı<br>Orhan Kemal | Ziya Gökalp<br>Ahmet Hamdi Tanpınar<br>Halit Ziya Uşaklıgil<br>Orhan Kemal |
| Doğru cevap | Ziya Gökalp | Ziya Gökalp |
| Kaynak alıntısı | Milli Edebiyat Dönemi yazarları: Ziya Gökalp, Ömer Seyfettin ve Halide Edip Adıvar gibi yazarlar bu dönemin önde gelen isimleridir. | Milli Edebiyat Dönemi yazarları: Ziya Gökalp, Ömer Seyfettin ve Halide Edip Adıvar gibi yazarlar bu dönemin önde gelen isimleridir. |
| Kaynak zamanı | yok · alıntı bulunamadı | yok · alıntı bulunamadı |
| İşaretler | yok | yok |

### python

#### Konu 1 · hedef düzey Değerlendirme · Python Nedir?

| full | v3 | v4 |
|---|---|---|
| Sonuç | ok | ok |
| Soru | Python'un hangi özelliği, yazılımcıların diğer programlama dillerine göre daha az satırla program yazmalarına olanak tanır? | Python programlama dilinin hangi alanda kullanılmadığı söylenebilir? |
| Seçenekler | Python'un zengin kütüphaneye sahip olması<br>Python'un İngilizceye benzer basit bir söz dizimine sahip olması<br>Python'un yorumlayıcı sistemde çalışması<br>Python'un web geliştirme için kullanılabilmesi | Oyun geliştirme<br>Veri analizi<br>Web geliştirme<br>Ses düzenleme |
| Doğru cevap | Python'un İngilizceye benzer basit bir söz dizimine sahip olması | Ses düzenleme |
| Kaynak alıntısı | python' İngilizceye benzer basit bir söz dizimi vardır... python geliştiricilerinin diğer bazı programlama dillerine göre daha az satırla program yazmalarına olanak tanıyan bir söz dizimine sahiptir. | python web uygulamaları oluşturmak için sunucuda kullanılabiliyor... veri analizi yapılabiliyor... python'da oyun geliştirebilirsiniz... |
| Kaynak zamanı | yok · alıntı bulunamadı | yok · alıntı bulunamadı |
| İşaretler | yazım kuralı 4 | yazım kuralı 19 |

| rag | v3 | v4 |
|---|---|---|
| Sonuç | ok | ok |
| Soru | Python'un hangi özelliği, onu diğer programlama dillerine göre daha fazla tercih edilmesine neden olmaktadır? | Python'un kullanım alanları hakkında yapılan aşağıdaki değerlendirmelerden hangisi doğrudur? 1) Python yalnızca web geliştirme için kullanılır. 2) Python, veri analizi ve makine öğrenimi gibi alanlarda da yaygın olarak kullanılmaktadır. 3) Python, sadece masaüstü uygulamaları geliştirmek için uygundur. 4) Python, yalnızca oyun geliştirme için tercih edilen bir dildir. |
| Seçenekler | Daha fazla kütüphane desteği sunması<br>Yalnızca web geliştirme için kullanılması<br>Sadece masaüstü uygulamaları için uygun olması<br>Kodun yalnızca bir kez çalıştırılabilmesi | 2 ve 4<br>2 ve 3<br>1 ve 2<br>3 ve 4 |
| Doğru cevap | Daha fazla kütüphane desteği sunması | 1 ve 2 |
| Kaynak alıntısı | python' zengin bir Kütüphanesi vardır yani bur burada insanlar yazılımcılar kütüphaneler oluşturmuşlar demişler ki kardeşim python'da şu işlemi mi yapacaksın Al sana hazır bir kütüphane | python popüler bir programlama dilidir ve guido One rossum tarafından yaratılmış ve 1991'de yayınlanmıştır... python web uygulamaları oluşturmak için sunucuda kullanılabiliyor... python büyük verileri işlemek ve karmaşık matematik işlemleri gerçekleştirmek için de zaten kullanılıyor. |
| Kaynak zamanı | 2:55 · alıntı bulundu | yok · alıntı bulunamadı |
| İşaretler | yazım kuralı 12 | yok |

#### Konu 2 · hedef düzey Uygulama · Python'un Kullanım Alanları

| full | v3 | v4 |
|---|---|---|
| Sonuç | ok | ok |
| Soru | Bir veri analisti, büyük veri setlerini analiz etmek için Python kullanmak istiyor. Python'un bu amaçla hangi kütüphanesini tercih etmesi uygun olur? | Bir veri analisti, büyük veri setlerini analiz etmek için Python kullanmak istiyor. Python'un bu amaçla hangi kütüphanelerini kullanması önerilir? |
| Seçenekler | Pandas<br>Django<br>Flask<br>TensorFlow | Django ve Flask<br>OpenCV ve Pygame<br>Pandas ve Matplotlib<br>TensorFlow ve Keras |
| Doğru cevap | Pandas | Pandas ve Matplotlib |
| Kaynak alıntısı | veri analizi yapılabiliyor ki veri analizleri python' kullanır bakın pandas non python mat plot lip gibi kütüphaneler sayesinde veri setleri üzerinde kolaylıkla analiz yapılabiliyor | python' kullanır bakın pandas non python mat plot lip gibi kütüphaneler sayesinde veri setleri üzerinde kolaylıkla analiz yapılabiliyor |
| Kaynak zamanı | 5:56 · alıntı bulundu | 5:58 · alıntı bulundu |
| İşaretler | yok | yok |

| rag | v3 | v4 |
|---|---|---|
| Sonuç | ok | ok |
| Soru | Python ile veri analizi yapmak için hangi kütüphaneler kullanılabilir? | Bir yazılım geliştirici, bir web uygulaması oluşturmak için Python kullanmak istiyor. Bu durumda hangi Python framework'ü onun için uygun bir seçim olacaktır? |
| Seçenekler | Keras ve PyTorch<br>Pandas ve Matplotlib<br>OpenCV ve Pygame<br>Django ve Flask | Pandas<br>Django<br>NumPy<br>Keras |
| Doğru cevap | Pandas ve Matplotlib | Django |
| Kaynak alıntısı | veri analizi yapılabiliyor ki veri analizleri python' kullanır bakın pandas non python mat plot lip gibi kütüphaneler sayesinde veri setleri üzerinde kolaylıkla analiz yapılabiliyor | python bakın jango ve flash gibi popüler web frameworkleri ile Web siteleri geliştirmek için kullanılabilir |
| Kaynak zamanı | 5:56 · alıntı bulundu | 6:17 · alıntı bulundu |
| İşaretler | yok | yok |

#### Konu 3 · hedef düzey Yaratma · Python Söz Dizimi

| full | v3 | v4 |
|---|---|---|
| Sonuç | ok | ok |
| Soru | Python'da basit bir hesap makinesi uygulaması oluşturmak için aşağıdaki kod parçalarından hangisi en uygun şekilde bir araya getirilmiştir? | Python dilinde, bir değişken tanımlamak ve ona bir değer atamak için hangi ifadeyi kullanmalısınız? |
| Seçenekler | def hesap_makinesi(x, y): print(x + y)<br>def hesap_makinesi(x, y): return x - y<br>def hesap_makinesi(x, y): print(x - y)<br>def hesap_makinesi(x, y): return x + y | 10 = değişken<br>değişken: 10<br>değişken = 10<br>değişken -> 10 |
| Doğru cevap | def hesap_makinesi(x, y): return x + y | değişken = 10 |
| Kaynak alıntısı | python' İngilizceye benzer basit bir söz | python' İngilizceye benzer basit bir söz |
| Kaynak zamanı | 2:12 · alıntı bulundu | 2:12 · alıntı bulundu |
| İşaretler | yok | olası cevap kökte |

| rag | v3 | v4 |
|---|---|---|
| Sonuç | ok | invalid |
| Soru | Python programlama dilinin söz dizimini kullanarak basit bir hesap makinesi oluşturmak isteyen bir öğrenci, aşağıdaki kod parçalarından hangisini kullanmalıdır? | — |
| Seçenekler | print(a + b) toplam =<br>toplam = a + b; print(toplam)<br>toplam = a + b; toplam.print()<br>toplam = a + b; toplam.show() | — |
| Doğru cevap | toplam = a + b; print(toplam) | — |
| Kaynak alıntısı | python' İngilizceye benzer basit bir söz dizimi vardır | — |
| Kaynak zamanı | 2:12 · alıntı bulundu | — |
| İşaretler | yok | — |

#### Konu 4 · hedef düzey Hatırlama · Python 2 ve 3 Arasındaki Farklar

| full | v3 | v4 |
|---|---|---|
| Sonuç | ok | ok |
| Soru | Python 2 ve Python 3 arasında hangi önemli uyumsuzluk bulunmaktadır? | Python'un ilk sürümü ne zaman yayınlanmıştır? |
| Seçenekler | Python 2, Python 3'ten daha fazla kütüphane içerir<br>Python 3, Python 2'den daha az popülerdir<br>Python 3, Python 2'den daha fazla satırla program yazmayı gerektirir<br>Python 2 kodları Python 3'te çalışmayabilir | 1991<br>1994<br>2000<br>2008 |
| Doğru cevap | Python 2 kodları Python 3'te çalışmayabilir | 1991 |
| Kaynak alıntısı | python 3 dikkatli dinleyin önceki python sürümlerine tam uyumlu değil maalesef yani python 2 kodları python 3'te çalışmayabilir | python popüler bir programlama dilidir ve guido One rossum tarafından yaratılmış ve 1991'de yayınlanmıştır |
| Kaynak zamanı | 4:39 · alıntı bulundu | 1:05 · alıntı bulundu |
| İşaretler | yok | yok |

| rag | v3 | v4 |
|---|---|---|
| Sonuç | ok | ok |
| Soru | Python 3'ün çıkış yılı nedir? | Python 3'ün çıkış tarihi nedir? |
| Seçenekler | 1994<br>2000<br>2008<br>2010 | 1994<br>2000<br>2008<br>2010 |
| Doğru cevap | 2008 | 2008 |
| Kaynak alıntısı | 2008'de zaten python 3 çıkmıştı | 2010'da python 3 serisine geçiş kolay paylaşılabilecek bazı değişiklikler yapıldı ki 2008'de zaten python 3 çıkmıştı |
| Kaynak zamanı | 4:31 · alıntı bulundu | 4:25 · alıntı bulundu |
| İşaretler | yok | yok |

#### Konu 5 · hedef düzey Çözümleme · Python Kütüphaneleri

| full | v3 | v4 |
|---|---|---|
| Sonuç | ok | ok |
| Soru | Python'un zengin kütüphane ekosisteminin sağladığı avantajlar arasında hangisi doğru bir ilişkiyi ifade etmektedir? | Python'un hangi kullanım alanı, veri analizi ile doğrudan ilişkilidir? |
| Seçenekler | Python, sadece oyun geliştirmek için kullanılan bir programlama dilidir.<br>Python, yalnızca bilimsel hesaplamalar için kullanılmaktadır.<br>Python, veri analizi için pandas ve matplotlib gibi kütüphanelerle çalışır.<br>Python, yalnızca web geliştirme için kullanılan bir dildir. | Bilimsel hesaplamalar<br>Oyun geliştirme<br>Görsel işleme<br>Web geliştirme |
| Doğru cevap | Python, veri analizi için pandas ve matplotlib gibi kütüphanelerle çalışır. | Bilimsel hesaplamalar |
| Kaynak alıntısı | python' kullanır bakın pandas non python mat plot lip gibi kütüphaneler sayesinde veri setleri üzerinde kolaylıkla analiz yapılabiliyor | python' La birlikte bazı hesaplamaları kolay bir şekilde yapabiliyor veri analizi yapılabiliyor ki veri analizleri python' kullanır |
| Kaynak zamanı | 5:58 · alıntı bulundu | 5:52 · alıntı bulundu |
| İşaretler | yazım kuralı 12 | yazım kuralı 4 |

| rag | v3 | v4 |
|---|---|---|
| Sonuç | ok | ok |
| Soru | Python'un hangi alanda kullanılmadığı söylenebilir? | Python'un hangi alanda kullanımı, diğer alanlarla doğrudan ilişkilidir? |
| Seçenekler | Oyun geliştirme<br>Veri analizi<br>Ses düzenleme<br>Görsel işleme | Veri analizi<br>Web geliştirme<br>Görsel işleme<br>Oyun geliştirme |
| Doğru cevap | Ses düzenleme | Veri analizi |
| Kaynak alıntısı | python' hemen hemen birçok alanda kullanıyorlar | veri analizi yapılabiliyor ki veri analizleri python' kullanır bakın pandas non python mat plot lip gibi kütüphaneler sayesinde veri setleri üzerinde kolaylıkla analiz yapılabiliyor |
| Kaynak zamanı | 7:43 · alıntı bulundu | 5:56 · alıntı bulundu |
| İşaretler | yazım kuralı 19 | yok |

#### Konu 6 · hedef düzey Anlama · Python ile Oyun Geliştirme

| full | v3 | v4 |
|---|---|---|
| Sonuç | ok | ok |
| Soru | Python ile hangi alanda uygulama geliştirmek mümkün değildir? | Python'un hangi alanda kullanılabileceği ile ilgili verilen bilgilerden hangisi doğrudur? |
| Seçenekler | Web geliştirme<br>Oyun geliştirme<br>Ses kaydı yapma<br>Veri analizi | Python, veri analizi ve makine öğrenimi gibi birçok alanda kullanılabilir.<br>Python, yalnızca oyun geliştirme için uygundur.<br>Python yalnızca web geliştirme için kullanılır.<br>Python, sadece masaüstü uygulamaları için geliştirilmiştir. |
| Doğru cevap | Ses kaydı yapma | Python, veri analizi ve makine öğrenimi gibi birçok alanda kullanılabilir. |
| Kaynak alıntısı | oyun geliştirebilirsiniz ama tabii ki pay Game gibi kütüphanelerle basit oyunlar geliş geliştirebilirsiniz | Neler yapabilirsin şimdi python'da neler yapabilirsin sorusuna cevaplamam lazım yani ben bunu niye öğreniyorum da bir cevabıdır Aslında bu matematiksel hesaplamalar yapabiliyoruz |
| Kaynak zamanı | 7:24 · alıntı bulundu | 5:34 · alıntı bulundu |
| İşaretler | yazım kuralı 19 | yazım kuralı 12 |

| rag | v3 | v4 |
|---|---|---|
| Sonuç | ok | ok |
| Soru | Python ile oyun geliştirmek için hangi kütüphane kullanılabilir? | Python ile oyun geliştirme konusunda hangi ifade doğrudur? |
| Seçenekler | Flask<br>NumPy<br>Pygame<br>Pandas | Python, sadece veri analizi için kullanılır.<br>Python, yalnızca web geliştirme için kullanılır.<br>Pygame kütüphanesi ile basit oyunlar geliştirilebilir.<br>Python, oyun geliştirme için uygun bir dil değildir. |
| Doğru cevap | Pygame | Pygame kütüphanesi ile basit oyunlar geliştirilebilir. |
| Kaynak alıntısı | python'da oyun geliştirebilirsiniz ama tabii ki pay Game gibi kütüphanelerle basit oyunlar geliş geliştirebilirsiniz | python'da oyun geliştirebilirsiniz ama tabii ki pay Game gibi kütüphanelerle basit oyunlar geliş geliştirebilirsiniz |
| Kaynak zamanı | 7:24 · alıntı bulundu | 7:24 · alıntı bulundu |
| İşaretler | yok | yok |

## Gizli bilgi taraması

Video JSON dosyaları ve bu rapor tarandı (API anahtarı, yetki başlığı, parola/token, `.env`, e-posta, yerel yol, paylaşım kodu); eşleşme yok.
