# Aşama 8 · questions-v3 denemesi 1

## Plan (betik çalıştırılmadan önce yazıldı)

- **Amaç:** Konu çıkarma (`topics-v1`), Bloom eşlemesi (`questions-v3`) ve benzerlik işaretinin (`similarity-v1`, eşik 0,80) gerçek videoda birlikte çalıştığını görmek.
- **Bu bir İŞLERLİK denemesidir:** Soru kalitesi ve Bloom uyumu hakkında yargı ve isabet iddiası yok. Düzey uyumu iki değerlendiriciyle ölçülecek.
- **Video:** Kemosentez (`109kCbVtU1U`), temiz transkript.
- **Adım 1:**
  - `/api/topics` bir kez çağrılır (`count` 6).
  - Konular ve tohumlu düzey eşlemesi `asama-8-v3-denemesi-1-konular.json` dosyasına yazılır.
  - Konular kullanıcıya gösterilir; kullanıcı onaylamadan devam edilmez.
- **Adım 2:**
  - Aynı 6 konu (`text` alanları) ve aynı `bloom_levels` ile önce `context_mode=full`, sonra `context_mode=rag` çağrılır.
  - `k=5`. Her koşul bir kez. `check_support` kapalı.
- **Ayarlar:** gpt-4o-mini, `questions-v3`, `topics-v1`, `fixed-150-30`, `BAAI/bge-m3`, `similarity-v1` (eşik 0,80).
- **Betik:** [asama-8-v3-denemesi-1.py](asama-8-v3-denemesi-1.py).
  - İstekler API üzerinden FastAPI TestClient ile yapılır; çalışan bir sunucu gerekmez.
  - Çalıştırma kayıtları `backend/runs` altına yazılır (git dışında).
  - Çıktı dosyalarının üzerine yazılmaz.

### Önceki denemeyle tek karşılaştırma (önceden yazıldı)

- **Karşılaştırılacak sayı:** Her koşulda benzerlik işaretli çift sayısı. Başka bir karşılaştırma iddiası yok.
- **Önceki değer:** 7b koşul denemesinde ([asama-7b-kosul-denemesi-1.md](asama-7b-kosul-denemesi-1.md)) çalışma sırasında benzerlik işareti yoktu. Aynı soruların sonradan ölçülen (a) "soru + doğru cevap" skorlarına ([asama-9-benzer-sorular-1.md](asama-9-benzer-sorular-1.md)) eşik 0,80 uygulanınca:
  - **full:** 3 çift (çift 2, 3, 6)
  - **rag:** 3 çift (çift 8, 10, 15)
- **Sınır:** 7b'de full 4, rag 5 soru döndürmüştü; bu denemede koşul başına 6 soru bekleniyor. Soru sayısı farklı olduğu için çift sayıları da farklı sayıda çift üzerinden hesaplanıyor (7b: full 6, rag 10 çift; bu deneme: 6 soruda 15 çift).

### Raporlanacaklar

- **Her koşul için, konu başına:**
  - hedef düzey
  - sonuç (`ok` / `empty` / `invalid` / `duplicate`)
  - soru ve doğru cevap
  - kaynak zamanı ve alıntının bulunup bulunmadığı
  - modelin `reasoning` metni
- **Her koşul için, toplam:**
  - benzerlik işaretli çiftler ve skorları
  - yazım kuralı işaretleri
  - model çağrısı sayısı, toplam token, toplam süre
- **RAG için ayrıca:** Her konuda gelen parçalar (`chunk_index`, zaman aralığı, skor).
- **Yan yana tablo:** İki koşulun aynı konudaki soruları: konu, hedef düzey, full sorusu ve doğru cevabı, rag sorusu ve doğru cevabı. Yorum yazılmaz.

## Konular hakkında kullanıcı gözlemi (sonuçlardan önce yazıldı)

"Kemosentez Nedir?" ile "Kemosentetik Canlılar" (ikisi de kimyasal enerjiyle besin üretimi) ve "Hidrotermal Bacalar" ile "Kemosentez Ortamları" iç içe görünüyor; bazı açıklamalar belirsiz ("hakkında bilgi verilmektedir"). Konular değiştirilmeden kullanılıyor.

## Çalıştırma (31 Ekim 2026)

- **Adımlar:** Adım 1 (`konular`) çalıştırıldı ve konular kullanıcıya gösterildi. Kullanıcı gözlemini yazdırdıktan sonra Adım 2 (`kosullar`) bir kez çalıştırıldı.
- **Model çağrıları:** Toplam 13 OpenAI çağrısı: konu çıkarma 1, full 6, rag 6.
- **Konu çıkarma:** 6 konu döndü (eksik ve atılan yok). Tohumlu eşleme Adım 1'de hesaplandı ve iki koşula aynı `bloom_levels` olarak verildi. Bu yüzden kayıtlarda eşleme kaynağı "request" görünüyor.
- **Çıktı dosyaları:**
  - Konular ve eşleme: [asama-8-v3-denemesi-1-konular.json](asama-8-v3-denemesi-1-konular.json)
  - Yanıtlar ve kayıttan seçilen alanlar: [asama-8-v3-denemesi-1.json](asama-8-v3-denemesi-1.json)
- **Gizli bilgi taraması:** Çalıştırma kayıtları `backend/runs` altında kaldı. Depoya giren iki JSON dosyası ve bu çıktılar tarandı (yerel yol, anahtar, yetki başlığı, `si=`, e-posta); eşleşme yok.

### Adım 1 (betiğin `konular` çıktısı, olduğu gibi)

```
Konu çıkarma: topics-v1 · model: gpt-4o-mini · istenen 6 · dönen 6 · eksik 0 · atılan {'empty': 0, 'duplicate': 0, 'extra': 0}
  1. [Uygulama] Kemosentez Nedir? — Işık enerjisi kullanılmadan besin sentezi olan kemosentez hakkında bilgi verilmektedir.
  2. [Hatırlama] Hidrotermal Bacalar — Hidrotermal bacaların okyanus tabanında yer alan sıcak su kaynakları olduğu açıklanmaktadır.
  3. [Değerlendirme] Kemosentetik Canlılar — Kemosentetik canlıların kimyasal enerjiyi kullanarak besin ürettiği belirtilmektedir.
  4. [Yaratma] Üretici Canlılar — Üretici canlıların ototrof olarak adlandırıldığı ve iki gruba ayrıldığı anlatılmaktadır.
  5. [Anlama] Kemosentez ve Fotosentez Farkları — Kemosentez ile fotosentez arasındaki temel farklar açıklanmaktadır.
  6. [Çözümleme] Kemosentez Ortamları — Kemosentetik canlıların yaşadığı zorlu ortamlar ve örnekleri verilmektedir.
Model çağrısı: 1 · token: 7852
```

### Adım 2 (betiğin `kosullar` çıktısı, olduğu gibi)

```
Video: 109kCbVtU1U · 6 konu · düzeyler: Uygulama, Hatırlama, Değerlendirme, Yaratma, Anlama, Çözümleme

=== Koşul: full ===
İstem: questions-v3 · model: gpt-4o-mini · k: None · parçalama: None · gömme: None · eşleme: request
- Konu 1 [Uygulama] ok · bağlam 3287 kelime
    konu: Kemosentez Nedir?: Işık enerjisi kullanılmadan besin sentezi olan kemosentez hakkında bilgi verilmektedir.
    soru: Bir araştırmacı, okyanus derinliklerinde ışık olmayan bir ortamda kemosentetik canlıların besin üretim sürecini incelemektedir. Bu canlılar hangi yöntemi kullanarak besin üretmektedir?
    doğru cevap: Kimyasal enerjiyi kullanarak · kaynak: 5:40 · alıntı bulundu: evet
    reasoning: Sorunun hedef düzeyde olması, kemosentez sürecinin uygulanabilirliğini bir senaryoya dayandırarak ölçmesindendir.
- Konu 2 [Hatırlama] ok · bağlam 3287 kelime
    konu: Hidrotermal Bacalar: Hidrotermal bacaların okyanus tabanında yer alan sıcak su kaynakları olduğu açıklanmaktadır.
    soru: Hidrotermal bacalar nerede yer almaktadır?
    doğru cevap: Okyanus tabanında · kaynak: 2:14 · alıntı bulundu: evet
    reasoning: Sorunun hedef düzeyde olduğu, bağlamda açıkça belirtilen bir bilgiyi hatırlamayı gerektirmesindendir.
- Konu 3 [Değerlendirme] ok · bağlam 3287 kelime
    konu: Kemosentetik Canlılar: Kemosentetik canlıların kimyasal enerjiyi kullanarak besin ürettiği belirtilmektedir.
    soru: Kemosentetik canlıların besin üretimi için hangi koşul gereklidir?
    doğru cevap: Kimyasal enerjiyi kullanmaları · kaynak: 3:36 · alıntı bulundu: evet
    reasoning: Sorunun hedef düzeyde olması, kemosentetik canlıların besin üretimi ile ilgili bilgilerin değerlendirilmesine dayanıyor. Öğrencilerin, verilen bilgileri kullanarak kemosentetik canlıların besin üretimindeki rolünü yargılamaları bekleniyor.
- Konu 4 [Yaratma] ok · bağlam 3287 kelime
    konu: Üretici Canlılar: Üretici canlıların ototrof olarak adlandırıldığı ve iki gruba ayrıldığı anlatılmaktadır.
    soru: Kemosentez ve fotosentez arasındaki temel fark nedir?
    doğru cevap: Kemosentezde enerji kaynağı kimyasal enerjidir, fotosentezde ise ışık enerjisidir. · kaynak: yok · alıntı bulundu: hayır
    reasoning: Sorunun hedef düzeyde olması, verilen bilgileri bir araya getirerek kemosentez ve fotosentez arasındaki farkları anlamaya yönelik bir yapı oluşturmayı gerektirmesidir.
- Konu 5 [Anlama] ok · bağlam 3287 kelime
    konu: Kemosentez ve Fotosentez Farkları: Kemosentez ile fotosentez arasındaki temel farklar açıklanmaktadır.
    soru: Kemosentez ile fotosentez arasındaki temel fark nedir?
    doğru cevap: Kemosentezde kimyasal enerji kullanılırken, fotosentezde ışık enerjisi kullanılır. · kaynak: 3:27 · alıntı bulundu: evet
    reasoning: Sorunun hedef düzeyde olması, verilen bilgiyi anlamaya dayalı olarak kemosentez ve fotosentez arasındaki farkları açıklamayı gerektirmesindendir.
- Konu 6 [Çözümleme] ok · bağlam 3287 kelime
    konu: Kemosentez Ortamları: Kemosentetik canlıların yaşadığı zorlu ortamlar ve örnekleri verilmektedir.
    soru: Kemosentetik canlıların yaşadığı hidrotermal bacaların özellikleri ile bu canlıların besin üretimi arasındaki ilişki nedir?
    doğru cevap: Hidrotermal bacalar, yüksek sıcaklık ve kimyasal bileşenler içerir, bu nedenle kemosentetik canlılar burada besin üretebilir. · kaynak: 3:51 · alıntı bulundu: evet
    reasoning: Soruda, kemosentetik canlıların yaşadığı zorlu ortamların özellikleri ve bu ortamların canlıların besin üretimi üzerindeki etkileri analiz edilmektedir.
Sonuç sayıları: {'ok': 6, 'empty': 0, 'invalid': 0, 'duplicate': 0} · dönen soru: 6 / 6 · alıntısı bulunan: 5
Benzerlik (similarity-v1, eşik 0.8): işaretli çift 1
    S4–S5 · skor 0.9381
Yazım kuralı işaretleri: 2 · soru 1: kural 19, soru 6: kural 4
Toplam süre: 51936.3 ms · model çağrısı: 6 · token: 51985 giriş + 1530 çıkış = 53515
Aşama süreleri (ms): transcript_fetch_ms=1673.6, clean_ms=10.4, llm_questions_ms=18630.5, quote_verify_ms=59.5, writing_check_ms=8.5, similarity_check_ms=31553.3, total_ms=51936.3

=== Koşul: rag ===
İstem: questions-v3 · model: gpt-4o-mini · k: 5 · parçalama: fixed-150-30 · gömme: BAAI/bge-m3 · eşleme: request
- Konu 1 [Uygulama] ok · bağlam 760 kelime
    konu: Kemosentez Nedir?: Işık enerjisi kullanılmadan besin sentezi olan kemosentez hakkında bilgi verilmektedir.
    soru: Kemosentez sürecinde hangi maddeler kullanılarak besin üretimi gerçekleşir?
    doğru cevap: Karbondioksit ve su · kaynak: 20:24 · alıntı bulundu: evet
    reasoning: Sorunun hedef düzeyde olması, kemosentez sürecinin uygulanabilirliğini ölçmesidir. Verilen bilgiye dayanarak, kemosentezde hangi maddelerin kullanıldığını belirlemek, öğrencinin konuyu uygulama düzeyinde anladığını gösterir.
    parça 22 · 1212.44–1283.44 sn (20:12–21:23) · skor 0.7850
    parça 14 · 769.40–839.20 sn (12:49–13:59) · skor 0.7194
    parça 0 · 0.68–66.56 sn (0:00–1:06) · skor 0.7164
    parça 19 · 1039.36–1111.44 sn (17:19–18:31) · skor 0.7115
    parça 18 · 983.88–1054.84 sn (16:23–17:34) · skor 0.7103
- Konu 2 [Hatırlama] ok · bağlam 759 kelime
    konu: Hidrotermal Bacalar: Hidrotermal bacaların okyanus tabanında yer alan sıcak su kaynakları olduğu açıklanmaktadır.
    soru: Hidrotermal bacalar nerede bulunur?
    doğru cevap: Okyanus tabanında · kaynak: 2:14 · alıntı bulundu: evet
    reasoning: Sorunun hedef düzeyde olması, hidrotermal bacalar hakkında doğrudan bilgi hatırlamayı gerektirmesindendir.
    parça 2 · 101.52–176.88 sn (1:41–2:56) · skor 0.7730
    parça 3 · 156.20–234.16 sn (2:36–3:54) · skor 0.6109
    parça 4 · 216.84–289.48 sn (3:36–4:49) · skor 0.6025
    parça 8 · 444.92–511.88 sn (7:24–8:31) · skor 0.5949
    parça 5 · 271.60–349.04 sn (4:31–5:49) · skor 0.5685
- Konu 3 [Değerlendirme] ok · bağlam 755 kelime
    konu: Kemosentetik Canlılar: Kemosentetik canlıların kimyasal enerjiyi kullanarak besin ürettiği belirtilmektedir.
    soru: Kemosentetik canlılar hakkında iki öğrenci tartışıyor. Ali: "Kemosentetik canlılar, kimyasal enerji kullanarak besin üretirler ve bu süreçte ışığa ihtiyaç duymazlar." Ayşe: "Kemosentetik canlılar yalnızca oksijen varlığında besin üretebilirler." Bu iddialara göre hangi değerlendirme doğrudur?
    doğru cevap: Ali'nin iddiası desteklenir, Ayşe'ninki desteklenmez. · kaynak: 5:40 · alıntı bulundu: evet
    reasoning: Sorunun hedef düzeyde olduğu, kemosentetik canlıların özellikleri ve besin üretimi ile ilgili iki farklı iddianın değerlendirilmesini gerektirmesinden kaynaklanmaktadır.
    parça 10 · 547.64–614.52 sn (9:07–10:14) · skor 0.7808
    parça 6 · 331.52–409.16 sn (5:31–6:49) · skor 0.7780
    parça 13 · 712.44–786.84 sn (11:52–13:06) · skor 0.7719
    parça 16 · 881.72–947.84 sn (14:41–15:47) · skor 0.7648
    parça 4 · 216.84–289.48 sn (3:36–4:49) · skor 0.7567
- Konu 4 [Yaratma] ok · bağlam 760 kelime
    konu: Üretici Canlılar: Üretici canlıların ototrof olarak adlandırıldığı ve iki gruba ayrıldığı anlatılmaktadır.
    soru: Aşağıdaki canlılardan hangisi kemosentetik canlı olarak adlandırılır?
    doğru cevap: Hidrotermal bacalarda yaşayan bir bakteri · kaynak: 9:38 · alıntı bulundu: evet
    reasoning: Soruda, üretici canlıların özelliklerini ve enerji kaynaklarını bir araya getirerek yeni bir yapı oluşturma yeteneği ölçülmektedir.
    parça 12 · 651.00–731.48 sn (10:51–12:11) · skor 0.7026
    parça 4 · 216.84–289.48 sn (3:36–4:49) · skor 0.5745
    parça 10 · 547.64–614.52 sn (9:07–10:14) · skor 0.5569
    parça 8 · 444.92–511.88 sn (7:24–8:31) · skor 0.5538
    parça 16 · 881.72–947.84 sn (14:41–15:47) · skor 0.5519
- Konu 5 [Anlama] ok · bağlam 764 kelime
    konu: Kemosentez ve Fotosentez Farkları: Kemosentez ile fotosentez arasındaki temel farklar açıklanmaktadır.
    soru: Kemosentez ile fotosentez arasındaki temel farklardan biri nedir?
    doğru cevap: Fotosentezde enerji kaynağı güneş ışığıdır. · kaynak: 18:00 · alıntı bulundu: evet
    reasoning: Bu soru, verilen bağlamda kemosentez ve fotosentez arasındaki temel farkları anlamaya yönelik bir bilgi ölçmektedir.
    parça 21 · 1152.96–1229.04 sn (19:12–20:29) · skor 0.7093
    parça 18 · 983.88–1054.84 sn (16:23–17:34) · skor 0.7020
    parça 26 · 1426.40–1492.00 sn (23:46–24:52) · skor 0.6595
    parça 19 · 1039.36–1111.44 sn (17:19–18:31) · skor 0.6574
    parça 13 · 712.44–786.84 sn (11:52–13:06) · skor 0.6398
- Konu 6 [Çözümleme] ok · bağlam 758 kelime
    konu: Kemosentez Ortamları: Kemosentetik canlıların yaşadığı zorlu ortamlar ve örnekleri verilmektedir.
    soru: Kemosentetik canlıların yaşadığı zorlu ortamlar arasında hangisi yer almaz?
    doğru cevap: Ormanlık alanlar · kaynak: 24:07 · alıntı bulundu: evet
    reasoning: Bu soru, kemosentetik canlıların yaşadığı zorlu ortamları ve bu ortamların özelliklerini analiz etmeyi gerektiriyor. Öğrencilerin, kemosentez yapan canlıların hangi koşullarda yaşadığını ve bu koşulların diğer canlılarla olan ilişkisini anlamalarını ölçüyor.
    parça 26 · 1426.40–1492.00 sn (23:46–24:52) · skor 0.7389
    parça 10 · 547.64–614.52 sn (9:07–10:14) · skor 0.7291
    parça 4 · 216.84–289.48 sn (3:36–4:49) · skor 0.6880
    parça 13 · 712.44–786.84 sn (11:52–13:06) · skor 0.6684
    parça 11 · 597.80–665.88 sn (9:57–11:05) · skor 0.6556
Sonuç sayıları: {'ok': 6, 'empty': 0, 'invalid': 0, 'duplicate': 0} · dönen soru: 6 / 6 · alıntısı bulunan: 6
Benzerlik (similarity-v1, eşik 0.8): işaretli çift 0
Yazım kuralı işaretleri: 3 · soru 3: kural 19, soru 4: kural 4, soru 6: kural 19
Toplam süre: 22422.2 ms · model çağrısı: 6 · token: 18545 giriş + 1354 çıkış = 19899
Aşama süreleri (ms): transcript_fetch_ms=1622.4, clean_ms=4.2, index_ms=131.4, retrieval_ms=1502.3, llm_questions_ms=16440.5, quote_verify_ms=43.6, writing_check_ms=7.4, similarity_check_ms=2465.7, total_ms=22422.2

=== Aynı konuda iki koşulun soruları ===
| Konu | Hedef düzey | full sorusu | full doğru cevap | rag sorusu | rag doğru cevap |
|---|---|---|---|---|---|
| Kemosentez Nedir? | Uygulama | Bir araştırmacı, okyanus derinliklerinde ışık olmayan bir ortamda kemosentetik canlıların besin üretim sürecini incelemektedir. Bu canlılar hangi yöntemi kullanarak besin üretmektedir? | Kimyasal enerjiyi kullanarak | Kemosentez sürecinde hangi maddeler kullanılarak besin üretimi gerçekleşir? | Karbondioksit ve su |
| Hidrotermal Bacalar | Hatırlama | Hidrotermal bacalar nerede yer almaktadır? | Okyanus tabanında | Hidrotermal bacalar nerede bulunur? | Okyanus tabanında |
| Kemosentetik Canlılar | Değerlendirme | Kemosentetik canlıların besin üretimi için hangi koşul gereklidir? | Kimyasal enerjiyi kullanmaları | Kemosentetik canlılar hakkında iki öğrenci tartışıyor. Ali: "Kemosentetik canlılar, kimyasal enerji kullanarak besin üretirler ve bu süreçte ışığa ihtiyaç duymazlar." Ayşe: "Kemosentetik canlılar yalnızca oksijen varlığında besin üretebilirler." Bu iddialara göre hangi değerlendirme doğrudur? | Ali'nin iddiası desteklenir, Ayşe'ninki desteklenmez. |
| Üretici Canlılar | Yaratma | Kemosentez ve fotosentez arasındaki temel fark nedir? | Kemosentezde enerji kaynağı kimyasal enerjidir, fotosentezde ise ışık enerjisidir. | Aşağıdaki canlılardan hangisi kemosentetik canlı olarak adlandırılır? | Hidrotermal bacalarda yaşayan bir bakteri |
| Kemosentez ve Fotosentez Farkları | Anlama | Kemosentez ile fotosentez arasındaki temel fark nedir? | Kemosentezde kimyasal enerji kullanılırken, fotosentezde ışık enerjisi kullanılır. | Kemosentez ile fotosentez arasındaki temel farklardan biri nedir? | Fotosentezde enerji kaynağı güneş ışığıdır. |
| Kemosentez Ortamları | Çözümleme | Kemosentetik canlıların yaşadığı hidrotermal bacaların özellikleri ile bu canlıların besin üretimi arasındaki ilişki nedir? | Hidrotermal bacalar, yüksek sıcaklık ve kimyasal bileşenler içerir, bu nedenle kemosentetik canlılar burada besin üretebilir. | Kemosentetik canlıların yaşadığı zorlu ortamlar arasında hangisi yer almaz? | Ormanlık alanlar |
```

## Özet tablo

| | full | rag |
|---|---|---|
| Konu başına sonuç | ok 6 | ok 6 |
| Dönen soru / alıntısı transkriptte bulunan | 6 / 5 | 6 / 6 |
| Benzerlik işaretli çift (eşik 0,80) | 1 (S4–S5, 0,9381) | 0 |
| Yazım kuralı işaretleri | 2 (soru 1: kural 19; soru 6: kural 4) | 3 (soru 3: kural 19; soru 4: kural 4; soru 6: kural 19) |
| Model çağrısı | 6 | 6 |
| Token (giriş + çıkış) | 51985 + 1530 = 53515 | 18545 + 1354 = 19899 |
| Bağlamın kelime sayısı (konu başına) | 3287 | 755–764 |
| Toplam süre | 51936,3 ms | 22422,2 ms |

**Süre hakkında not:** full koşulu önce çalıştı. Benzerlik kontrolündeki BGE-M3 modeli bu süreçte ilk kez full koşulunda yüklendi; full'daki `similarity_check_ms` (31553,3 ms) bu yüklemeyi de içeriyor.

## Önceki denemeyle tek karşılaştırma

| Koşul | 7b (sonradan ölçülen skorlara eşik 0,80) | Bu deneme |
|---|---|---|
| full | 3 çift (4 soru, 6 çift üzerinden) | 1 çift (6 soru, 15 çift üzerinden) |
| rag | 3 çift (5 soru, 10 çift üzerinden) | 0 çift (6 soru, 15 çift üzerinden) |

Başka bir karşılaştırma iddiası yok. İki denemede konu kaynağı, istem ve soru sayısı farklı.

## Aynı konuda iki koşulun soruları

Yorum yazılmadı.

| Konu | Hedef düzey | full sorusu | full doğru cevap | rag sorusu | rag doğru cevap |
|---|---|---|---|---|---|
| Kemosentez Nedir? | Uygulama | Bir araştırmacı, okyanus derinliklerinde ışık olmayan bir ortamda kemosentetik canlıların besin üretim sürecini incelemektedir. Bu canlılar hangi yöntemi kullanarak besin üretmektedir? | Kimyasal enerjiyi kullanarak | Kemosentez sürecinde hangi maddeler kullanılarak besin üretimi gerçekleşir? | Karbondioksit ve su |
| Hidrotermal Bacalar | Hatırlama | Hidrotermal bacalar nerede yer almaktadır? | Okyanus tabanında | Hidrotermal bacalar nerede bulunur? | Okyanus tabanında |
| Kemosentetik Canlılar | Değerlendirme | Kemosentetik canlıların besin üretimi için hangi koşul gereklidir? | Kimyasal enerjiyi kullanmaları | Kemosentetik canlılar hakkında iki öğrenci tartışıyor. Ali: "Kemosentetik canlılar, kimyasal enerji kullanarak besin üretirler ve bu süreçte ışığa ihtiyaç duymazlar." Ayşe: "Kemosentetik canlılar yalnızca oksijen varlığında besin üretebilirler." Bu iddialara göre hangi değerlendirme doğrudur? | Ali'nin iddiası desteklenir, Ayşe'ninki desteklenmez. |
| Üretici Canlılar | Yaratma | Kemosentez ve fotosentez arasındaki temel fark nedir? | Kemosentezde enerji kaynağı kimyasal enerjidir, fotosentezde ise ışık enerjisidir. | Aşağıdaki canlılardan hangisi kemosentetik canlı olarak adlandırılır? | Hidrotermal bacalarda yaşayan bir bakteri |
| Kemosentez ve Fotosentez Farkları | Anlama | Kemosentez ile fotosentez arasındaki temel fark nedir? | Kemosentezde kimyasal enerji kullanılırken, fotosentezde ışık enerjisi kullanılır. | Kemosentez ile fotosentez arasındaki temel farklardan biri nedir? | Fotosentezde enerji kaynağı güneş ışığıdır. |
| Kemosentez Ortamları | Çözümleme | Kemosentetik canlıların yaşadığı hidrotermal bacaların özellikleri ile bu canlıların besin üretimi arasındaki ilişki nedir? | Hidrotermal bacalar, yüksek sıcaklık ve kimyasal bileşenler içerir, bu nedenle kemosentetik canlılar burada besin üretebilir. | Kemosentetik canlıların yaşadığı zorlu ortamlar arasında hangisi yer almaz? | Ormanlık alanlar |

## Sınırlar

- Tek video, tek çalıştırma, koşul başına 6 soru.
- Kalite ve düzey uyumu ölçülmedi.
