# Alan öğretmeni alt kümesinin seçim kuralı

Bu kural 144 soru üretilmeden ve puanlama başlamadan önce yazıldı. Kural yazıldıktan sonra değişirse değişiklik tarihi ve gerekçesiyle aşağıdaki "Değişiklikler" bölümüne eklenir.

## Amaç

İki değerlendiricinin ortak etiketlerinin geçerliliğini sınamak için bir alan öğretmeni (ya da eğitim bilimleri alanından bir araştırma görevlisi) 144 sorudan 36'sını da puanlar. Alan öğretmeninin etiketleri ana analize (AS1, AS2) katılmaz; yalnızca geçerlilik göstergesi olarak raporlanır.

## Girdi

- export.py'nin ürettiği anahtar dosyası (anahtar.json): her sorunun kimliği, video_id, koşulu (rag / full) ve hedef Bloom düzeyi (bloom_target). Değerlendiricilerin etiketleri seçimde kullanılmaz.
- Anahtardaki "videos" bölümü: her videonun alanı.
- Anahtardaki alanlar tam olarak altı alan kodu olmalı ve her alanda iki video bulunmalıdır; değilse betik hata verir.

## Denge

- Alt kümede 6 alanın her birinden 6 soru, toplam 36 soru olur.
- Her alanda her hedef Bloom düzeyinden 1 soru seçilir.
- Her alanda 3 soru RAG, 3 soru tam transkript koşulundandır. Her Bloom düzeyinde de 3 soru RAG, 3 soru tam transkript koşulundandır (6 alan üzerinden).
- Her alanda 3 soru alanın bir videosundan, 3 soru öbür videosundan gelir.

## Seçim yöntemi

1. Tohum: random.Random("20261118-alt-kume"). Aşağıdaki karıştırmalar bu tek üreteçle, yazılan sırayla yapılır.
2. Alanlar alfabetik sıralanır (biyoloji, edebiyat, ingilizce, matematik, python, tarih). Bloom düzeyleri şu sıradadır: Hatırlama, Anlama, Uygulama, Çözümleme, Değerlendirme, Yaratma.
3. Koşul tablosu: satırı alan (i = 0..5), sütunu Bloom düzeyi (j = 0..5) olan 6×6 bir tabloda, i + j çiftse hücreye "rag", tekse "full" yazılır. Böylece her satırda ve her sütunda 3 rag, 3 full olur.
4. Satırlar (alanlar) üreteçle karıştırılır: alan listesinin bir kopyası rng.shuffle ile karıştırılır ve tablonun i. satırı karıştırılmış listenin i. alanına verilir. Sonra sütunlar aynı biçimde Bloom düzeyi listesinin rng.shuffle ile karıştırılmış kopyasına verilir.
5. Video ataması: alanlar alfabetik sırayla dolaşılır. Her alanın iki videosu video_id'ye göre sıralanır. İlk videoya, o alanın 6 Bloom düzeyinden rng.sample(Bloom düzeyleri, 3) ile seçilen 3 düzey verilir; kalan 3 düzey ikinci videoya verilir. video_id'ler Python'un varsayılan metin sıralamasıyla sıralanır (büyük harf küçük harften önce gelir). rng.sample, Bloom düzeylerinin 2. adımdaki sırayla yazılmış listesi üzerinde çalışır.
6. Her hücre için soru: alan, Bloom düzeyi, koşul ve video belli olduğunda, anahtarda bu video_id, condition ve bloom_target'a sahip soru seçilir.

## Eksik soru

Seçilen hücrede soru yoksa (model boş yanıt döndürdüyse, yanıt yapı denetiminden geçmediyse ya da soru tekrar olarak atıldıysa) aynı alan, aynı Bloom düzeyi ve aynı koşulda öbür videonun sorusu alınır. O da yoksa hücre boş kalır ve alt küme 36'dan küçük olur. Değiştirilen ve boş kalan hücreler seçim dosyasına yazılır ve raporlanır.

## Ne zaman, nasıl kaydedilir

- Seçim, 144 soru üretilip export.py ile anahtar dosyası oluşturulduktan sonra, değerlendirici dosyaları dağıtılmadan önce yapılır.
- Seçim dosyası (alt-kume.json) anahtar dosyasıyla birlikte depo dışında saklanır. Koşul bilgisi içerdiği için puanlama bitene kadar depoya konmaz.
- Seçim dosyasının SHA-256 özet değeri, değerlendirici dosyaları dağıtılmadan önce docs/bulgular/alt-kume-ozet.txt dosyasına yazılıp commit'lenir. Puanlama bittikten sonra seçim dosyası depoya eklenir; herkes özet değerini kontrol ederek listenin sonradan değişmediğini görebilir.
- Alan öğretmenine yalnızca alt kümedeki sorular, değerlendiricilerle aynı biçimdeki bir dosyada ve aynı yönergeyle verilir. Sıra tohumla karıştırılır. Koşul, hedef düzey ve alt kümenin nasıl seçildiği alan öğretmenine söylenmez.

## Analiz

- Alan öğretmeninin etiketleri, iki değerlendiricinin tartışmadan sonraki ortak etiketleriyle karşılaştırılır.
- Her ölçüt için ham uyum oranı ve Cohen's kappa (%95 güven aralığıyla) verilir: Bloom düzeyi, kabul edilebilirlik (0–1 hata), kaynağa dayalılık, cevaplanabilirlik ve tanıma hatası. Bloom düzeyi ve cevaplanabilirlik için doğrusal ağırlıklı kappa da verilir.
- Kategoriler dengesiz dağıldığında kappa ham uyuma göre düşük çıkabilir. Bu yüzden her ölçütte iki tarafın kategori dağılımı da verilir (Artstein ve Poesio, 2008; Sim ve Wright, 2005).
- Ek bilgi olarak alan öğretmeni ile her değerlendiricinin tartışma öncesi etiketleri arasındaki kappa da verilir.
- 36 soru kappa için küçük bir örneklemdir; sonuçlar güven aralıklarıyla betimsel olarak yorumlanır.

## Değişiklikler

- 2026-11-25, puanlayıcı: Danışmanın Hafta-5 geri bildirimiyle alt kümeyi puanlayacak kişi "alan öğretmeni (ya da eğitim bilimleri alanından bir araştırma görevlisi)" yerine "eğitim fakültesinin ölçme ve değerlendirme alanından bir araştırma görevlisi ya da öğretim elemanı" oldu. Gerekçe: sorular altı alandan geliyor ve tek bir alan öğretmeni bunların en fazla birinde uzman olur; Bloom düzeyi ve soru yazım hataları alan bilgisinden çok ölçme ve değerlendirme bilgisine dayanır. Bu kuraldaki "alan öğretmeni" ifadeleri bu kişiyi anlatır. Girdi, denge, seçim yöntemi, tohum, eksik soru kuralı ve kayıt biçimi değişmedi; değişiklik soru üretiminden ve seçimden önce yapıldı.
- 2026-11-25, analiz: Danışmanın önerisiyle, uzmanla uyumdaki kappa değerleri için büyük örneklem güven aralığının yanında bootstrap güven aralığı da verilecek. Bu bir ekleme; var olan hesaplar değişmedi.
