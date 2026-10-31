# Aşama 7a · Erişim denemesi 1

## Plan (betik çalıştırılmadan önce yazıldı)

- **Amaç:** BGE-M3 + ChromaDB ile ilk gerçek erişim denemesi. Soru üretimi yok, OpenAI çağrısı yok.
- **Video:** Aşama 6'daki kemosentez videosu (`109kCbVtU1U`), temiz transkript.
- **Kurulum:**
  - Parçalama `fixed-150-30` (yaklaşık 150 kelime, en az 30 kelime örtüşme).
  - Gömme modeli `BAAI/bge-m3`.
  - Dizin `backend/chroma`.
  - Her sorgu için `retrieve(k=3)`.
- **Betik:** [asama-7a-erisim-denemesi-1.py](asama-7a-erisim-denemesi-1.py). Bir kez çalıştırılacak.

### Sorgular ve beklenen zamanlar

| Sorgu | Metin | Beklenen |
|---|---|---|
| a | Hidrotermal bacalar nerede bulunur? | Yaklaşık 124. saniyeyi içeren parça (Aşama 6 testinde elle doğrulandı) |
| b | Kemosentetik canlıların hücre yapısı nasıldır, prokaryot mudur? | Yaklaşık 435. saniyeyi içeren parça (Aşama 6 testinde elle doğrulandı; "Kemosentetik canlıların tamamının prokaryot olduğunu unutma") |
| c | Kemosentez nedir ve fotosentezden farkı nedir? | Beklenen zaman yok; sonucu kullanıcı gözle değerlendirecek |

### Ölçüt

- **a ve b için tek ölçüt:** Beklenen saniye, ilk sıradaki parçanın başlangıç–bitiş aralığında mı (evet/hayır)? Değilse ilk 3 içinde mi?
- **c için:** Kullanıcı değerlendirecek.

### Ön not (ölçütü değiştirmez)

[asama-6-test-1.md](asama-6-test-1.md)'deki bilgiler:
- **a:** 124 sn, hidrotermal baca sorusunun alıntısının bulunduğu 30 sn'lik bloğun etiketi. Alıntının başladığı segment 134,16 sn.
- **b:** 435,4 sn, prokaryot cümlesinin bulunduğu bloğun (435,4–467,96 sn) başı. Aynı belgeye göre "tamamı prokaryot" fikri videoda 582,3 sn ve 736,2 sn'de de başka sözcüklerle tekrarlanıyor. Bu yüzden b sorgusunda başka bir parçanın ilk sıraya çıkması mümkün.

## Çalıştırma (31 Ekim 2026)

- **Kaç kez:** Betik bir kez çalıştırıldı. Model (OpenAI) çağrısı yapılmadı.
- **Kurulum:** sentence-transformers 6.2.0, torch 2.15.0, chromadb 1.5.9.
- **İlk model yüklemesi:** Model Hugging Face'ten indirildi; ilk yükleme süresine indirme de dahil. Önbellekte ölçülen boyut 4,3 GB: modelin iki ağırlık dosyası (`pytorch_model.bin` ve `model.safetensors`, her biri yaklaşık 2,27 GB) indi.

### Betiğin çıktısı (olduğu gibi)

```
Video: 109kCbVtU1U · dil: tr · segment: 678 · süre: 1513.79 sn (25:13)
Gömme modeli: BAAI/bge-m3 · ilk yükleme süresi: 96.5 sn
Parçalama: fixed-150-30 · toplam parça: 28 · dizinleme süresi: 43.1 sn · yeni gömme yapıldı: True

Sorgu a) Hidrotermal bacalar nerede bulunur?
  1. chunk_index=2 · 101.52–176.88 sn (1:41–2:56) · skor=0.7624
     tek bir noktadan çok kolaylıkla ulaşabilirsin. WhatsApp kanalına katılmak tamamen ücretsiz. Kanala katılmanı istiyorum ve seni orada bekliyorum. Şimdi hemen konuya başlarken kısmıyla da girişimi yapıy
  2. chunk_index=3 · 156.20–234.16 sn (2:36–3:54) · skor=0.6048
     kanalının 500 km batısındaki Galapagos adalarının bulunduğu büyük okyanus tabanında keşfedildi. İç kısımlarında 350400 S D, ağız kısımlarında ise yaklaşık 150 S D sıcaklığa sahip olan bu hidrotermal b
  3. chunk_index=8 · 444.92–511.88 sn (7:24–8:31) · skor=0.5823
     prokaryot olduğunu unutma. Bak bu çok önemliydi. Ünlemle böyle sağa sola, kenara, köşeye bir yere bunu yaz. Tamam mı? Şimdi inorganik madde oksitlendikten sonra yeni inorganik madde yapılır. Burası ço
  Ölçüt: beklenen 124 sn ilk sıradaki parçanın aralığında mı: evet

Sorgu b) Kemosentetik canlıların hücre yapısı nasıldır, prokaryot mudur?
  1. chunk_index=13 · 712.44–786.84 sn (11:52–13:06) · skor=0.6968
     kemosentetik canlılarda gerekli enerji canlının kendisi tarafından üretilmiş olur. Peki nasıl üretiliyordu? inorganik madde oksitleniyor ve bunun sonucunda bir enerji açığa çıkarılıyordu. Peki fotosen
  2. chunk_index=10 · 547.64–614.52 sn (9:07–10:14) · skor=0.6611
     enerjiyi kullanarak karbondioksit özümlemesi yapan canlı nedir desem kesinlikle hocam bunu artık çok iyi bir şekilde öğrendim. Bu kemos yapan canlıdır dersin. Harika dersin, süper dersin. İşte böyle ç
  3. chunk_index=26 · 1426.40–1492.00 sn (23:46–24:52) · skor=0.6484
     kendimi koyarak şimdi bu soruyu yazıyorum. Kemosentez yapan canlılarda enerji ve besin üretimi oluyor. Ama neden bunlar fotosentez yapanlar kadar yaygın değil diye düşünebilirsin. Bence haklı da bir d
  Ölçüt: beklenen 435 sn ilk sıradaki parçanın aralığında mı: hayır · ilk 3 içinde mi: hayır

Sorgu c) Kemosentez nedir ve fotosentezden farkı nedir?
  1. chunk_index=21 · 1152.96–1229.04 sn (19:12–20:29) · skor=0.7231
     bakterilerinden bahsetmiştik. Onlar e hidrojen kaynağı olarak H2S'i kullanıyordu. H2S değiştiği için de yani H2O yerine H2S kullanılmış olduğu için de açığa çıkan gazın da farklı olduğunu bir önceki v
  2. chunk_index=18 · 983.88–1054.84 sn (16:23–17:34) · skor=0.6962
     sadece ışık varlığında gerçekleşmiş oluyordu. Şurada anlattığım kısım en sözün özünün olduğu kısımdı. Ama bu kadar yeter mi? Hayır yetmez. kapgeç bilgileriyle, soru yaptırır kısımlarla son noktayı koy
  3. chunk_index=19 · 1039.36–1111.44 sn (17:19–18:31) · skor=0.6665
     Besin üretimi var mı burada? Evet var. Yani inorganik maddeden organik besin sentezi hem fotosentezde hem de kemosentezde var. Peki bu iki reaksiyonda enzimatik reaksiyon mu? Evet öyle. Peki fotosente
  Ölçüt: kullanıcı değerlendirecek
```

## Sonuç

| Sorgu | Beklenen | İlk sıradaki parça | Ölçüt |
|---|---|---|---|
| a | ~124 sn | chunk 2 · 101,52–176,88 sn (1:41–2:56) | ilk sıradaki parçanın aralığında: **evet** |
| b | ~435 sn | chunk 13 · 712,44–786,84 sn (11:52–13:06) | ilk sıradaki parçanın aralığında: **hayır** · ilk 3 içinde: **hayır** |
| c | yok | chunk 21 · 1152,96–1229,04 sn (19:12–20:29) | kullanıcı değerlendirdi: ilk 3 parça ilgili |

### b sorgusu için ek gözlem (ölçüt sonucunu değiştirmez)

Bu bilgiler çalıştırmadan sonra, model yeniden çalıştırılmadan, dizindeki parçaların tam metnine bakılarak çıkarıldı:

- **Beklenen parça ilk 3'te değil:** 435 sn'yi içeren parça chunk 7 (392,56–460,08 sn). İçinde "prokaryot" bir kez geçiyor.
- **İlk iki sıradaki parçalarda da "prokaryot" geçiyor:**
  - **1. sıra, chunk 13 (712,44–786,84 sn):** "prokaryot" iki kez geçiyor. Aralık, Aşama 6 belgesinde anılan 736,2 sn tekrarını kapsıyor.
  - **2. sıra, chunk 10 (547,64–614,52 sn):** "prokaryot" bir kez geçiyor. Aralık, 582,3 sn tekrarını kapsıyor.
  - **3. sıra, chunk 26:** "prokaryot" geçmiyor.
- **Tekrarlar ölçütte sayılmadı:** Ölçüt önceden yalnızca ~435 sn olarak yazıldığı için bu tekrarlar başarı sayılmadı.

### Kullanıcı değerlendirmesi (c sorgusu)

Kullanıcı, c sorgusu için dönen ilk 3 parçayı (chunk 21, 18, 19) elle kontrol etti: üçü de kemosentez ile fotosentez arasındaki farkı anlatıyor.

## Sınırlar

- Tek video, 3 sorgu, tek çalıştırma.
- İsabet iddiası yok.
- Beklenen zamanlar 30 sn'lik blok etiketlerinden geliyor; parçalar ~150 kelime olduğu için aralık kontrolü kaba bir ölçüttür.
