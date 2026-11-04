# Pilot üretim 1

## Plan (betik çalıştırılmadan önce yazıldı)

- **Amaç:** 6 pilot videoda iki koşulun (`full` / `rag`) çalıştırılması; örnek sorular, altyazı hatası örnekleri, video başına süre ve maliyet.
- **Bu bir İŞLERLİK ve ÖN GÖZLEM çalışmasıdır:** Kalite, kaynağa dayalılık ve Bloom uyumu hakkında yargı ve isabet iddiası yok. Bunlar iki bağımsız değerlendiriciyle ölçülecek.

### Videolar (temiz transkript)

| Alan | video_id | Bağlantı |
|---|---|---|
| biyoloji | `109kCbVtU1U` | https://youtu.be/109kCbVtU1U |
| tarih | `aaCHLYO3Fzg` | https://youtu.be/aaCHLYO3Fzg |
| matematik | `edSvMQ77TmU` | https://youtu.be/edSvMQ77TmU |
| ingilizce | `FetnCoTS9qY` | https://youtu.be/FetnCoTS9qY |
| edebiyat | `fgOxbhEMnQQ` | https://youtu.be/fgOxbhEMnQQ |
| python | `CEr_UiR4Gvk` | https://youtu.be/CEr_UiR4Gvk |

İngilizce videosu Türkçe-İngilizce karışık; sonuçları ayrıca gösterilecek.

### Her video için adımlar

1. `/api/topics` bir kez çağrılır (`count` 6).
2. Konular ve tohumlu Bloom eşlemesi video dosyasına yazılır.
3. Aynı konu metinleri ve aynı `bloom_levels` ile önce `context_mode=full`, sonra `context_mode=rag` çağrılır.
4. `k=5`. Her koşul bir kez. `check_support` kapalı.

### Ayarlar

- gpt-4o-mini, `topics-v1`, `questions-v3`, `fixed-150-30`, `BAAI/bge-m3`, `similarity-v1` (eşik 0,80).
- **Model çağrısı:** Video başına 13 (konu 1, full 6, rag 6); 6 videoda toplam 78 OpenAI çağrısı.
- **Maliyet hesabı için sabit fiyat:** Girdi 0,15 USD / 1M token, çıktı 0,60 USD / 1M token (kullanıcının verdiği OpenAI gpt-4o-mini liste fiyatı; Ekim 2026'da doğrulandı). Hesap yalnızca betikte yapılır; kod ve kayıt biçimi değişmez.

### Örnek soru seçimi (sonuç görülmeden sabitlendi)

- **Kural:** Her videoda iki koşulun 12 soru yeri (`full-1` … `full-6`, `rag-1` … `rag-6`; sayı konu sırasıdır) sabit tohumla karıştırılır. Sıra baştan okunur ve soru bulunan ilk 3 yer seçilir. Bir yerde soru yoksa (`empty` / `invalid` / `duplicate`) o yer atlanır, sıradaki alınır. Başka soru seçilmez.
- **Tohum:** `int.from_bytes(sha256("pilot-1-ornek:" + video_id).digest()[:8], "big")`, karıştırma `random.Random(tohum).shuffle`. `pilot-1-ornek:` öneki, Bloom eşlemesiyle aynı tohumun kullanılmaması içindir.
- **Sıra, hesaplanmış hâliyle** (ilk 3'ü normalde seçilecek olanlar):

| Alan | Seçim sırası |
|---|---|
| biyoloji | full-1, rag-5, rag-1, rag-3, full-6, full-3, full-5, rag-4, rag-6, full-4, full-2, rag-2 |
| tarih | full-1, rag-2, rag-6, full-2, full-4, full-5, rag-4, full-3, rag-5, rag-3, full-6, rag-1 |
| matematik | full-4, rag-3, rag-2, rag-6, rag-5, full-3, rag-4, rag-1, full-5, full-2, full-6, full-1 |
| ingilizce | full-5, full-4, rag-3, rag-5, rag-4, full-2, rag-1, rag-6, full-6, full-1, full-3, rag-2 |
| edebiyat | rag-1, full-4, rag-2, full-1, rag-4, full-2, full-6, full-3, full-5, rag-6, rag-3, rag-5 |
| python | full-5, full-3, rag-4, rag-2, rag-6, rag-5, full-1, full-2, rag-3, full-6, full-4, rag-1 |

### Tohumlu Bloom eşlemesi (konu sırasına göre, hesaplanmış hâliyle)

| Alan | Konu 1 | Konu 2 | Konu 3 | Konu 4 | Konu 5 | Konu 6 |
|---|---|---|---|---|---|---|
| biyoloji | Uygulama | Hatırlama | Değerlendirme | Yaratma | Anlama | Çözümleme |
| tarih | Çözümleme | Anlama | Değerlendirme | Hatırlama | Yaratma | Uygulama |
| matematik | Hatırlama | Uygulama | Değerlendirme | Yaratma | Anlama | Çözümleme |
| ingilizce | Hatırlama | Değerlendirme | Uygulama | Anlama | Yaratma | Çözümleme |
| edebiyat | Yaratma | Anlama | Değerlendirme | Uygulama | Çözümleme | Hatırlama |
| python | Değerlendirme | Uygulama | Yaratma | Hatırlama | Çözümleme | Anlama |

### Raporlanacaklar, her video için

- **Video:** Video adı ve kanal adı (YouTube oEmbed; anahtar gerekmez), süre (dk:sn), transkript kelime sayısı, parça sayısı.
- **Her koşulda:** Konu başına sonuç (`ok` / `empty` / `invalid` / `duplicate`), dönen soru sayısı, alıntısı bulunan soru sayısı, benzerlik işaretli çift sayısı, yazım kuralı işaret sayısı.
- **Süre:** Konu çıkarma, full koşulu, rag koşulu (dizinleme ve erişim ayrı) ve toplam.
- **BGE-M3'ün ilk yüklenme süresi:** Ayrı yazılır; betik modeli ilk videodan önce bir kez yükler, bu süre hiçbir videonun süresine girmez.
- **Token:** Aşama bazında girdi/çıktı; video başına ve koşul başına tahmini maliyet (USD).
- **Seçilen 3 örnek soru:** Koşul, hedef Bloom düzeyi, soru, seçenekler, doğru cevap, kaynak alıntısı ve kaynak zamanı (dk:sn).

### Altyazı hatası adayları

- **Her video için:** Temiz transkriptte yanlış tanınmış görünen en fazla 3 yer (kelime, bağlamı ve dk:sn).
- **Bunlar ADAYDIR:** Kullanıcı videoyu o anda dinleyip doğrulayacak. Doğrulanmadan "hata" diye yazılmaz. "Kullanıcı doğrulaması" sütunu boş bırakılır.
- **Nasıl seçilir:** Claude, çalıştırmadan sonra transkriptleri okuyarak seçer. Sistematik bir tarama değildir; hata oranı hakkında bir şey söylemez.
- **Bilinen örnekler ayrıca listelenir (Genelleme denemesi 1):** Python: "guido One rossum", "mat plot lip"; İngilizce: "used to" yerine "yüz".

### Tüm videolar için özet tablo

Video, süre, toplam süre (sn), toplam token, maliyet (USD).

### Betik

- **Dosya:** [pilot-1.py](pilot-1.py). 8. aşama denemesindeki gibi FastAPI TestClient ile; istekler aynı uç noktalardan geçer, çalıştırma kayıtları `backend/runs` altına yazılır.
- **Sıra:** Videolar sırayla işlenir. Bir video hata verirse hata video dosyasına kaydedilir ve sonrakine geçilir. Yeniden deneme yapılmaz.
- **Konu eksikse:** Konu çıkarma 6'dan az konu döndürürse tohumlu eşleme yapılamaz. O videoda koşullar çalıştırılmaz ve durum hata olarak kaydedilir.
- **Çıktılar:** Video başına JSON, `docs/bulgular/pilot-1/` altında. Dosya varsa o video atlanır, üzerine yazılmaz.
- **Transkriptler:** Tam transkript depoya girmez. Altyazı adayları için yerel geçici klasörde tutulur; belgeye yalnızca kısa bağlamlar geçer.
- **Gizli bilgi:** Kayıtlardan alıntıda CLAUDE.md kural 5'e uyulur (gizli bilgi, `si=`, yerel yol yok).

## Çalıştırma (4 Kasım 2026)

- **Sonuç:** 6 videonun 4'ü tamamlandı (biyoloji, tarih, matematik, ingilizce). Edebiyat yarım kaldı, Python hiç başlamadı.
- **Neden:** YouTube bu IP'den gelen transkript isteklerini engelledi. Edebiyatın `rag` isteği (20. transkript isteği) ve Python'un ilk isteği (21.) `Transkript YouTube'dan alınamadı` hatası verdi. Bundan sonra yapılan tek tanı isteğinde (kayda geçmedi, OpenAI'a gitmedi) hata türü `IpBlocked` çıktı.
- **Edebiyat:** Konu çıkarma ve `full` koşulu bitti; sayıları aşağıdaki ham çıktıda var. Betik hata anında koşul verisini video dosyasına yazmadığı için `pilot-1-edebiyat.json` yalnızca konuları ve hatayı içeriyor; `full` kaydı `backend/runs` altında duruyor. `rag` olmadığı için örnek soru seçilmedi.
- **Python:** oEmbed bilgisi alındı; transkript alınamadığı için başka bir şey yapılmadı.
- **Yeniden deneme:** Plan gereği yapılmadı.
- **OpenAI çağrısı:** Planlanan 78 çağrının 59'u yapıldı (tamamlanan 4 videoda 52, edebiyatta 7).
- **BGE-M3 ilk yüklenme süresi:** 64,8 sn; hiçbir videonun süresine dahil değil.
- **Süreler hakkında:** Konu çıkarma, full ve rag sürelerinin her biri kendi transkript çekme süresini içeriyor. Biyoloji `backend/chroma` dizininde önceden olduğu için dizinleme süresi (0,2 sn) önbellekten geliyor.
- **Çıktı dosyaları:** Video başına `pilot-1-<alan>.json` ve `pilot-1-ozet.json`. Çalıştırma kayıtları `backend/runs` altında kaldı. Depoya girecek JSON dosyaları ve ham çıktı tarandı (yerel yol, anahtar, yetki başlığı, `si=`, e-posta); eşleşme yok.

## Tüm videolar için özet tablo

| Video | Süre | Toplam süre (sn) | Toplam token | Maliyet (USD) |
|---|---|---|---|---|
| biyoloji | 25:13 | 75,0 | 81374 | 0,013658 |
| tarih | 32:59 | 109,7 | 99995 | 0,016141 |
| matematik | 25:50 | 86,2 | 80382 | 0,013300 |
| ingilizce | 13:56 | 56,5 | 46316 | 0,008234 |
| edebiyat | 12:35 | tamamlanmadı | tamamlanmadı | tamamlanmadı |
| python | alınamadı | tamamlanmadı | tamamlanmadı | tamamlanmadı |
| **Tamamlanan 4 video** | — | 327,4 | 308067 | 0,051333 |

Edebiyat için tamamlanmamış işin harcaması tabloya girmedi: konu çıkarma 5067 token (0,000867 USD), full 36651 token (0,006102 USD). Tümüyle birlikte toplam 349785 token, 0,058302 USD. Maliyet liste fiyatıyla tahmindir.

## Video sonuçları

### Biyoloji

- **Video:** 4) Kemosentez (Işık Enerjisi Kullanılmadan Besin Sentezi) | 10. Sınıf Biyoloji (Yeni Müfredat)
- **Kanal:** BETÜL BİYOLOJİ
- **Süre:** 25:13 · **Transkript:** 3287 kelime · **Parça:** 28

**Konular ve hedef düzeyler**

| # | Hedef düzey | Konu | full sonucu | rag sonucu |
|---|---|---|---|---|
| 1 | Uygulama | Kemosentez Nedir? | ok | ok |
| 2 | Hatırlama | Hidrotermal Bacalar | ok | ok |
| 3 | Değerlendirme | Kemosentetik Canlılar | ok | ok |
| 4 | Yaratma | Üretici Canlılar | ok | ok |
| 5 | Anlama | Kemosentez Ortamları | ok | ok |
| 6 | Çözümleme | Fotosentez ve Kemosentez Farkları | ok | ok |

**Koşullar**

| | full | rag |
|---|---|---|
| Dönen soru | 6 / 6 | 6 / 6 |
| Alıntısı bulunan | 6 | 5 |
| Benzerlik işaretli çift | 2 | 1 |
| Yazım kuralı işareti | 1 | 2 |

**Süre ve token**

| Aşama | Süre (sn) | Girdi token | Çıktı token | Maliyet (USD) |
|---|---|---|---|---|
| Konu çıkarma | 6,7 | 7606 | 240 | 0,001285 |
| full | 38,8 | 51979 | 1559 | 0,008732 |
| rag | 29,4 | 18562 | 1428 | 0,003641 |
| **Toplam** | 75,0 | 78147 | 3227 | 0,013658 |

rag içinde dizinleme 0,2 sn, erişim 1,3 sn.

**Seçilen 3 örnek soru** (yorum yok)

1. **full-1** · koşul full · hedef düzey Uygulama
   - **Soru:** Okyanus derinliklerinde, ışık enerjisi bulunmayan bir ortamda kemosentetik canlılar nasıl besin üretir?
   - **Seçenekler:** Klorofil pigmenti ile fotosentez yaparlar. / Işık enerjisini kullanarak besin sentezlerler. / İnorganik maddeleri oksitlerler ve enerji açığa çıkarırlar. / Sadece su ve oksijen kullanarak besin üretirler.
   - **Doğru cevap:** İnorganik maddeleri oksitlerler ve enerji açığa çıkarırlar.
   - **Kaynak alıntısı:** Kemosentetik canlılar inorganik maddeleri oksitlerler ve bunun sonucunda enerji açığa çıkartırlar.
   - **Kaynak zamanı:** 6:30 · alıntı transkriptte bulundu: evet
2. **rag-5** · koşul rag · hedef düzey Anlama
   - **Soru:** Kemosentetik canlıların yaşadığı ortamlar arasında hangisi bulunmamaktadır?
   - **Seçenekler:** Ormanlık alanlar / Okyanus derinlikleri / Lağım çamuru / Çöplükler
   - **Doğru cevap:** Ormanlık alanlar
   - **Kaynak alıntısı:** Kemosentetik canlılara da kemosentetik canlılar adını veriyoruz. Bu canlıların yaşadığı ortamları konuşacak olursak... Okyanusların derinlikleri, derin deniz dipleri, çöplükler, lağımlar...
   - **Kaynak zamanı:** yok · alıntı transkriptte bulundu: hayır
3. **rag-1** · koşul rag · hedef düzey Uygulama
   - **Soru:** Kemosentez sürecinde inorganik maddelerin oksitlenmesi sonucunda hangi tür enerji açığa çıkar?
   - **Seçenekler:** Işık enerjisi / Kimyasal enerji / Termal enerji / Mekanik enerji
   - **Doğru cevap:** Kimyasal enerji
   - **Kaynak alıntısı:** inorganik madde oksitleniyor ve bunun sonucunda bir enerji açığa çıkarılıyordu.
   - **Kaynak zamanı:** 11:57 · alıntı transkriptte bulundu: evet

### Tarih

- **Video:** 10.Sınıf Tarih - 1.Ünite Türkistan'dan Türkiye'ye  | yeni müfredat ( maarif model )
- **Kanal:** Ardıç Tarih
- **Süre:** 32:59 · **Transkript:** 4116 kelime · **Parça:** 35

**Konular ve hedef düzeyler**

| # | Hedef düzey | Konu | full sonucu | rag sonucu |
|---|---|---|---|---|
| 1 | Çözümleme | Malazgirt Savaşı'nın Önemi | ok | ok |
| 2 | Anlama | Birinci Beylikler Dönemi | ok | ok |
| 3 | Değerlendirme | Haçlı Seferlerinin Nedenleri | ok | ok |
| 4 | Hatırlama | Miri Kefalon Savaşı | ok | ok |
| 5 | Yaratma | Kösedağ Savaşı'nın Sonuçları | empty | empty |
| 6 | Uygulama | İkinci Beylikler Dönemi | ok | ok |

**Koşullar**

| | full | rag |
|---|---|---|
| Dönen soru | 5 / 6 | 5 / 6 |
| Alıntısı bulunan | 3 | 4 |
| Benzerlik işaretli çift | 0 | 0 |
| Yazım kuralı işareti | 2 | 1 |

**Süre ve token**

| Aşama | Süre (sn) | Girdi token | Çıktı token | Maliyet (USD) |
|---|---|---|---|---|
| Konu çıkarma | 7,5 | 10215 | 287 | 0,001704 |
| full | 39,0 | 67680 | 1165 | 0,010851 |
| rag | 63,2 | 19561 | 1087 | 0,003586 |
| **Toplam** | 109,7 | 97456 | 2539 | 0,016141 |

rag içinde dizinleme 44,3 sn, erişim 1,3 sn.

**Seçilen 3 örnek soru** (yorum yok)

1. **full-1** · koşul full · hedef düzey Çözümleme
   - **Soru:** Malazgirt Savaşı'nın ardından Anadolu'da hangi gelişme kesinleşmiştir?
   - **Seçenekler:** Anadolu'nun Türkleşmesi ve İslamlaşması / Türklerin Anadolu'dan atılma ihtimali / Haçlı seferlerinin başlaması / Bizans'ın Anadolu'daki hakimiyeti
   - **Doğru cevap:** Anadolu'nun Türkleşmesi ve İslamlaşması
   - **Kaynak alıntısı:** Bu savaş bir dönüm noktasıydı. Bu savaşa yurt açan, yurt kuran savaşı da derler. Çünkü Anadolu'da Türklerin yerleşmesinde bu savaş dönüm noktası olmuş.
   - **Kaynak zamanı:** yok · alıntı transkriptte bulundu: hayır
2. **rag-2** · koşul rag · hedef düzey Anlama
   - **Soru:** Malazgirt Savaşı'ndan sonra Anadolu'da kurulan ilk beylikler hangi savaşın ardından ortaya çıkmıştır?
   - **Seçenekler:** Küçük Asya Savaşı / Dandanakan Savaşı / Malazgirt Savaşı / Ahlat Savaşı
   - **Doğru cevap:** Malazgirt Savaşı
   - **Kaynak alıntısı:** Bu savaştan sonra Anadolu'da 1. Beylikler dönemi başlamış.
   - **Kaynak zamanı:** 1:39 · alıntı transkriptte bulundu: evet
3. **rag-6** · koşul rag · hedef düzey Uygulama
   - **Soru:** Kösedağ Savaşı'ndan sonra Anadolu'da ikinci beylikler hangi bölgelerde yoğunlaşmıştır?
   - **Seçenekler:** Güneyde / Batıda / Doğuda / Kuzeyde
   - **Doğru cevap:** Batıda
   - **Kaynak alıntısı:** O zaman ik beylikler nerede yoğunlaşır? Bu bölgelerde.
   - **Kaynak zamanı:** 26:54 · alıntı transkriptte bulundu: evet

### Matematik

- **Video:** 10.Sınıf Matematik | Açıortay - 1 | Üçgenin Yardımcı Elemanları | Maarif Model | 5.Ders
- **Kanal:** Partikül Matematik
- **Süre:** 25:50 · **Transkript:** 3271 kelime · **Parça:** 28

**Konular ve hedef düzeyler**

| # | Hedef düzey | Konu | full sonucu | rag sonucu |
|---|---|---|---|---|
| 1 | Hatırlama | Açıortay Teoremi | ok | ok |
| 2 | Uygulama | Açıortayın Tanımı | ok | ok |
| 3 | Değerlendirme | İç Açıortay Teoremi İspatı | ok | ok |
| 4 | Yaratma | Açıortay Teoremi Uygulamaları | empty | empty |
| 5 | Anlama | Dik Açıortay ve Kenarortay | ok | ok |
| 6 | Çözümleme | Açıortay Teoremi ile Oranlama | ok | ok |

**Koşullar**

| | full | rag |
|---|---|---|
| Dönen soru | 5 / 6 | 5 / 6 |
| Alıntısı bulunan | 4 | 4 |
| Benzerlik işaretli çift | 0 | 1 |
| Yazım kuralı işareti | 2 | 3 |

**Süre ve token**

| Aşama | Süre (sn) | Girdi token | Çıktı token | Maliyet (USD) |
|---|---|---|---|---|
| Konu çıkarma | 6,6 | 7536 | 279 | 0,001298 |
| full | 27,6 | 51593 | 1184 | 0,008449 |
| rag | 52,0 | 18491 | 1299 | 0,003553 |
| **Toplam** | 86,2 | 77620 | 2762 | 0,013300 |

rag içinde dizinleme 30,3 sn, erişim 1,3 sn.

**Seçilen 3 örnek soru** (yorum yok)

1. **rag-3** · koşul rag · hedef düzey Değerlendirme
   - **Soru:** İç açıortay teoremi ile ilgili olarak, iki öğrencinin tartışması sonucunda hangi değerlendirme doğrudur? Ali: "İç açıortay teoremi, bir üçgende açıortayın oluşturduğu oranların eşit olduğunu söyler." Ayşe: "Bu teorem sadece açıların eşitliğine dayanır, oranlarla ilgili değildir."
   - **Seçenekler:** Ali'nin iddiası doğrudur, Ayşe'ninki yanlıştır. / Ayşe'nin iddiası doğrudur, Ali'ninki yanlıştır. / İki iddia da doğrudur. / İki iddia da yanlıştır.
   - **Doğru cevap:** Ali'nin iddiası doğrudur, Ayşe'ninki yanlıştır.
   - **Kaynak alıntısı:** İşte burada C'nin X'e oranı, yani sağ bölü sağ parça B'nin Y'ye oranına eşit, yani sol bölü sol parça gibi düşünebilirsin.
   - **Kaynak zamanı:** 1:47 · alıntı transkriptte bulundu: evet
2. **rag-2** · koşul rag · hedef düzey Uygulama
   - **Soru:** Bir üçgende açıortay ile ilgili olarak, A açısının kolu 15 birim ve bu kolun ayırdığı parça 10 birim ise, diğer kolun ayırdığı parça ne olmalıdır?
   - **Seçenekler:** 5 birim / 10 birim / 15 birim / 20 birim
   - **Doğru cevap:** 15 birim
   - **Kaynak alıntısı:** açıortay ile beraber ayırdığı parça X. İşte burada C'nin X'e oranı, yani sağ bölü sağ parça B'nin Y'ye oranına eşit,
   - **Kaynak zamanı:** 1:44 · alıntı transkriptte bulundu: evet
3. **rag-6** · koşul rag · hedef düzey Çözümleme
   - **Soru:** Açıortay teoremi kullanılarak, üçgenin kenar uzunlukları arasındaki oranlar nasıl belirlenir?
   - **Seçenekler:** Üçgenin alanları birbirine eşittir. / Birinci kolun uzunluğu, ikinci kolun uzunluğuna eşittir. / Birinci kolun birinci parçaya oranı, ikinci kolun ikinci parçaya oranına eşittir. / Kenar uzunlukları toplamı, açıortay uzunluğuna eşittir.
   - **Doğru cevap:** Birinci kolun birinci parçaya oranı, ikinci kolun ikinci parçaya oranına eşittir.
   - **Kaynak alıntısı:** C'nin X'e oranı, yani sağ bölü sağ parça B'nin Y'ye oranına eşit,
   - **Kaynak zamanı:** 1:47 · alıntı transkriptte bulundu: evet

## İngilizce (Türkçe-İngilizce karışık video; ayrı gösterim)

### İngilizce

- **Video:** 10.SINIF İNGİLİZCE 4.ÜNİTE KONU ANLATIMI VE KELİMELERİ | TRADITIONS
- **Kanal:** Ms. Jasmin ELT
- **Süre:** 13:56 · **Transkript:** 1312 kelime · **Parça:** 11

**Konular ve hedef düzeyler**

| # | Hedef düzey | Konu | full sonucu | rag sonucu |
|---|---|---|---|---|
| 1 | Hatırlama | Gelenekler ve Önemli Kelimeler | ok | ok |
| 2 | Değerlendirme | Yüz Kalıbının Kullanımı | ok | ok |
| 3 | Uygulama | Olumlu Cümle Yapısı | ok | ok |
| 4 | Anlama | Olumsuz Cümle Yapısı | ok | ok |
| 5 | Yaratma | Soru Cümlesi Oluşturma | ok | ok |
| 6 | Çözümleme | Alıştırma Soruları | ok | ok |

**Koşullar**

| | full | rag |
|---|---|---|
| Dönen soru | 6 / 6 | 6 / 6 |
| Alıntısı bulunan | 6 | 5 |
| Benzerlik işaretli çift | 0 | 0 |
| Yazım kuralı işareti | 0 | 0 |

**Süre ve token**

| Aşama | Süre (sn) | Girdi token | Çıktı token | Maliyet (USD) |
|---|---|---|---|---|
| Konu çıkarma | 5,3 | 2879 | 242 | 0,000577 |
| full | 21,0 | 23617 | 1351 | 0,004353 |
| rag | 30,1 | 16961 | 1266 | 0,003304 |
| **Toplam** | 56,5 | 43457 | 2859 | 0,008234 |

rag içinde dizinleme 9,5 sn, erişim 1,3 sn.

**Seçilen 3 örnek soru** (yorum yok)

1. **full-5** · koşul full · hedef düzey Yaratma
   - **Soru:** Aşağıdaki cümlelerden hangisi yüz kalıbı kullanılarak doğru bir soru cümlesi oluşturulmuştur?
   - **Seçenekler:** Did you playing football when you were a child? / Did you played football when you were a child? / Did you plays football when you were a child? / Did you play football when you were a child?
   - **Doğru cevap:** Did you play football when you were a child?
   - **Kaynak alıntısı:** Eğer yüz ifadesini soru yapacaksak şu kurallara dikkat etmeliyiz Biz sürekli olarak cümlenin başında da ifadesini kullanırız ardından İngilizce'de bulunan yedi tane Özen'in bir tanesini yazarız ve daha sonra yüz kalıbının kendisini yazdıktan sonra fiilin birinci haline ek almamış halinde kullanırız
   - **Kaynak zamanı:** 10:12 · alıntı transkriptte bulundu: evet
2. **full-4** · koşul full · hedef düzey Anlama
   - **Soru:** Yüz kalıbıyla olumsuz bir cümle kurmak için hangi kelime kullanılmalıdır?
   - **Seçenekler:** does / did / do / had
   - **Doğru cevap:** did
   - **Kaynak alıntısı:** negatif belirtmek için did kelimesini kullanırız ama Özellikle belirtmek istediğim bir nokta vardır
   - **Kaynak zamanı:** 8:21 · alıntı transkriptte bulundu: evet
3. **rag-3** · koşul rag · hedef düzey Uygulama
   - **Soru:** Aşağıdaki cümlelerden hangisi yüz kalıbıyla olumlu bir cümle kurma kuralına uygundur?
   - **Seçenekler:** I did not play football. / He did play football. / She did not play football. / They did not play football.
   - **Doğru cevap:** He did play football.
   - **Kaynak alıntısı:** Eğer olumlu bir cümle kurmak istiyorsanız şu kurallara dikkat etmemiz gerekir
   - **Kaynak zamanı:** 5:33 · alıntı transkriptte bulundu: evet

## Tamamlanamayan videolar

### Edebiyat

- **Video:** Milli Edebiyat Dönemi Hikâyesi  | 10. Sınıf Edebiyat #2026
- **Kanal:** tonguç 10. SINIF
- **Süre:** 12:35 · **Transkript:** 1881 kelime · **Parça:** 16
- **Yapılan:** Konu çıkarma ve `full` koşulu (ham çıktıda). `rag` çalıştırılamadı, örnek soru seçilmedi.

### Python

- **Video:** Ders 1 Python Programlamaya Giriş
- **Kanal:** Fehmi UYAR
- **Yapılan:** Yalnızca oEmbed. Transkript alınamadı.

## Altyazı hatası adayları

Bunlar ADAYDIR. Claude transkriptleri okuyarak seçti; sistematik bir tarama değildir ve hata oranı hakkında bir şey söylemez. Kullanıcı videoyu o anda dinleyip doğrulayacak. Doğrulanmadan "hata" diye yazılmaz. Zamanlar, kelimenin geçtiği altyazı segmentinin başlangıcıdır.

| Video | Kelime | Bağlam | Zaman | Kullanıcı doğrulaması |
|---|---|---|---|---|
| biyoloji | 350400 S D | "İç kısımlarında 350400 S D, ağız kısımlarında ise" | 2:44 |  |
| biyoloji | siyonobakterilerde, alklerde | "Bitkilerde, siyonobakterilerde, alklerde olan fotosentez tepkimesi" | 19:00 |  |
| biyoloji | ipleri | "okyanus tabanları dediğimiz yerler derin deniz ipleri değil mi?" | 23:00 |  |
| tarih | 109699 | "1. Haçlı seferi 109699 yılları arasında" | 12:49 |  |
| tarih | Hıdin | "Kudüs'ü Haçlılardan Hıdin savaşıyla alıyor" | 16:10 |  |
| tarih | Mir Kefalon | "Şimdi geldik Mir Kefalon Savaşı'na canlarım" (videoda Miri Kefalon, Mir Kefolon, Miro Kefalon, Niriya Kefalon yazımları da var; konu başlığına "Miri Kefalon Savaşı" olarak geçti) | 21:13 |  |
| matematik | haşırt the | "5. Şimdicik. Burada haşırt the blackboard." | 13:31 |  |
| matematik | x + a 6 | "Neydi burası? x + a 6. O zaman burası da ne olacak? x + 6 olacak." | 20:05 |  |
| matematik | Niğde Niğde | "Burası da açıortay farklı bir açı Niğde Niğde dedim." | 23:10 |  |
| ingilizce | gördüğü tions | "dördüncü ünitesi olan gördüğü tions yani gelenekler" | 0:05 |  |
| ingilizce | Hobbit | "Hobbit alışkanlık" | 0:48 |  |
| ingilizce | Hayır slimwell What çay aldım | "Hayır slimwell What çay aldım Ben çocukken yüzerdim" | 6:15 |  |
| edebiyat | Lerze-i Ruşen | "Serveti Fünun'u hatırlar mısınız? Lerze-i Ruşen falan" | 1:31 |  |
| edebiyat | İctihat | "İctihat dergisi bunu temsil etmeye çalışacaklar" | 7:29 |  |
| edebiyat | ve dilden | "Sanatlı, süslü ve dilden kaçınılacak." | 9:22 |  |

Python transkripti alınamadığı için bu video için aday seçilmedi.

### Bilinen örnekler (Genelleme denemesi 1)

| Video | Kelime | Bağlam | Zaman | Kullanıcı doğrulaması |
|---|---|---|---|---|
| python | guido One rossum | "dilidir ve guido One rossum tarafından" | 1:07 (Genelleme denemesi 1'den) |  |
| python | mat plot lip | S3 alıntısı | 6:01 (Genelleme denemesi 1'den) |  |
| ingilizce | yüz ("used to" yerine) | "Bu dersimizde yüz çık kalıbının kullanımını öğreneceğiz" (videoda "100 Türk kalıbı", "Yusuf", "yüzüstü" yazımları da var; konu başlığına "Yüz Kalıbının Kullanımı" olarak geçti) | 5:01 |  |

## Betiğin ham çıktısı (olduğu gibi)

```
BGE-M3 ilk yüklenme süresi: 64.8 sn (hiçbir videonun süresine dahil değil)

=== biyoloji (109kCbVtU1U) ===
  video: 4) Kemosentez (Işık Enerjisi Kullanılmadan Besin Sentezi) | 10. Sınıf Biyoloji (Yeni Müfredat) · kanal: BETÜL BİYOLOJİ
  süre 25:13 · dil tr · otomatik altyazı True · kelime 3287 · parça 28
  [konu] 6 konu · süre 6.7 sn · token 7606 girdi + 240 çıktı · maliyet 0.001285 USD
    1. [Uygulama] Kemosentez Nedir?
    2. [Hatırlama] Hidrotermal Bacalar
    3. [Değerlendirme] Kemosentetik Canlılar
    4. [Yaratma] Üretici Canlılar
    5. [Anlama] Kemosentez Ortamları
    6. [Çözümleme] Fotosentez ve Kemosentez Farkları
  [full] sonuçlar: ok, ok, ok, ok, ok, ok · {'ok': 6, 'empty': 0, 'invalid': 0, 'duplicate': 0}
  [full] dönen 6/6 · alıntısı bulunan 6 · benzer çift 2 · yazım işareti 1 (19)
  [full] süre 38.8 sn · çağrı 6 · token 51979 girdi + 1559 çıktı · maliyet 0.008732 USD
  [rag] sonuçlar: ok, ok, ok, ok, ok, ok · {'ok': 6, 'empty': 0, 'invalid': 0, 'duplicate': 0}
  [rag] dönen 6/6 · alıntısı bulunan 5 · benzer çift 1 · yazım işareti 2 (4, 19)
  [rag] süre 29.4 sn (dizinleme 0.2 sn, erişim 1.3 sn) · çağrı 6 · token 18562 girdi + 1428 çıktı · maliyet 0.003641 USD
  toplam 75.0 sn · 81374 token · 0.013658 USD
  seçilen örnekler: full-1, rag-5, rag-1

=== tarih (aaCHLYO3Fzg) ===
  video: 10.Sınıf Tarih - 1.Ünite Türkistan'dan Türkiye'ye  | yeni müfredat ( maarif model ) · kanal: Ardıç Tarih
  süre 32:59 · dil tr · otomatik altyazı True · kelime 4116 · parça 35
  [konu] 6 konu · süre 7.5 sn · token 10215 girdi + 287 çıktı · maliyet 0.001704 USD
    1. [Çözümleme] Malazgirt Savaşı'nın Önemi
    2. [Anlama] Birinci Beylikler Dönemi
    3. [Değerlendirme] Haçlı Seferlerinin Nedenleri
    4. [Hatırlama] Miri Kefalon Savaşı
    5. [Yaratma] Kösedağ Savaşı'nın Sonuçları
    6. [Uygulama] İkinci Beylikler Dönemi
  [full] sonuçlar: ok, ok, ok, ok, empty, ok · {'ok': 5, 'empty': 1, 'invalid': 0, 'duplicate': 0}
  [full] dönen 5/6 · alıntısı bulunan 3 · benzer çift 0 · yazım işareti 2 (12, 12)
  [full] süre 39.0 sn · çağrı 6 · token 67680 girdi + 1165 çıktı · maliyet 0.010851 USD
  [rag] sonuçlar: ok, ok, ok, ok, empty, ok · {'ok': 5, 'empty': 1, 'invalid': 0, 'duplicate': 0}
  [rag] dönen 5/6 · alıntısı bulunan 4 · benzer çift 0 · yazım işareti 1 (12)
  [rag] süre 63.2 sn (dizinleme 44.3 sn, erişim 1.3 sn) · çağrı 6 · token 19561 girdi + 1087 çıktı · maliyet 0.003586 USD
  toplam 109.7 sn · 99995 token · 0.016141 USD
  seçilen örnekler: full-1, rag-2, rag-6

=== matematik (edSvMQ77TmU) ===
  video: 10.Sınıf Matematik | Açıortay - 1 | Üçgenin Yardımcı Elemanları | Maarif Model | 5.Ders · kanal: Partikül Matematik
  süre 25:50 · dil tr · otomatik altyazı True · kelime 3271 · parça 28
  [konu] 6 konu · süre 6.6 sn · token 7536 girdi + 279 çıktı · maliyet 0.001298 USD
    1. [Hatırlama] Açıortay Teoremi
    2. [Uygulama] Açıortayın Tanımı
    3. [Değerlendirme] İç Açıortay Teoremi İspatı
    4. [Yaratma] Açıortay Teoremi Uygulamaları
    5. [Anlama] Dik Açıortay ve Kenarortay
    6. [Çözümleme] Açıortay Teoremi ile Oranlama
  [full] sonuçlar: ok, ok, ok, empty, ok, ok · {'ok': 5, 'empty': 1, 'invalid': 0, 'duplicate': 0}
  [full] dönen 5/6 · alıntısı bulunan 4 · benzer çift 0 · yazım işareti 2 (11, 19)
  [full] süre 27.6 sn · çağrı 6 · token 51593 girdi + 1184 çıktı · maliyet 0.008449 USD
  [rag] sonuçlar: ok, ok, ok, empty, ok, ok · {'ok': 5, 'empty': 1, 'invalid': 0, 'duplicate': 0}
  [rag] dönen 5/6 · alıntısı bulunan 4 · benzer çift 1 · yazım işareti 3 (4, 19, 4)
  [rag] süre 52.0 sn (dizinleme 30.3 sn, erişim 1.3 sn) · çağrı 6 · token 18491 girdi + 1299 çıktı · maliyet 0.003553 USD
  toplam 86.2 sn · 80382 token · 0.013300 USD
  seçilen örnekler: rag-3, rag-2, rag-6

=== ingilizce (FetnCoTS9qY) ===
  video: 10.SINIF İNGİLİZCE 4.ÜNİTE KONU ANLATIMI VE KELİMELERİ | TRADITIONS · kanal: Ms. Jasmin ELT
  süre 13:56 · dil tr · otomatik altyazı True · kelime 1312 · parça 11
  [konu] 6 konu · süre 5.3 sn · token 2879 girdi + 242 çıktı · maliyet 0.000577 USD
    1. [Hatırlama] Gelenekler ve Önemli Kelimeler
    2. [Değerlendirme] Yüz Kalıbının Kullanımı
    3. [Uygulama] Olumlu Cümle Yapısı
    4. [Anlama] Olumsuz Cümle Yapısı
    5. [Yaratma] Soru Cümlesi Oluşturma
    6. [Çözümleme] Alıştırma Soruları
  [full] sonuçlar: ok, ok, ok, ok, ok, ok · {'ok': 6, 'empty': 0, 'invalid': 0, 'duplicate': 0}
  [full] dönen 6/6 · alıntısı bulunan 6 · benzer çift 0 · yazım işareti 0 (yok)
  [full] süre 21.0 sn · çağrı 6 · token 23617 girdi + 1351 çıktı · maliyet 0.004353 USD
  [rag] sonuçlar: ok, ok, ok, ok, ok, ok · {'ok': 6, 'empty': 0, 'invalid': 0, 'duplicate': 0}
  [rag] dönen 6/6 · alıntısı bulunan 5 · benzer çift 0 · yazım işareti 0 (yok)
  [rag] süre 30.1 sn (dizinleme 9.5 sn, erişim 1.3 sn) · çağrı 6 · token 16961 girdi + 1266 çıktı · maliyet 0.003304 USD
  toplam 56.5 sn · 46316 token · 0.008234 USD
  seçilen örnekler: full-5, full-4, rag-3

=== edebiyat (fgOxbhEMnQQ) ===
  video: Milli Edebiyat Dönemi Hikâyesi  | 10. Sınıf Edebiyat #2026 · kanal: tonguç 10. SINIF
  süre 12:35 · dil tr · otomatik altyazı True · kelime 1881 · parça 16
  [konu] 6 konu · süre 5.7 sn · token 4829 girdi + 238 çıktı · maliyet 0.000867 USD
    1. [Yaratma] Milli Edebiyat Dönemi Nedir?
    2. [Anlama] Yeni Lisan Hareketi
    3. [Değerlendirme] Halk Edebiyatı ve Folklor
    4. [Uygulama] Balkan Savaşları ve Edebiyat
    5. [Çözümleme] Osmanlıcılık ve Türkçülük Akımları
    6. [Hatırlama] Olay ve Durum Hikayeleri
  [full] sonuçlar: ok, ok, ok, ok, ok, ok · {'ok': 6, 'empty': 0, 'invalid': 0, 'duplicate': 0}
  [full] dönen 6/6 · alıntısı bulunan 4 · benzer çift 0 · yazım işareti 1 (4)
  [full] süre 21.7 sn · çağrı 6 · token 35309 girdi + 1342 çıktı · maliyet 0.006102 USD
  HATA: PilotError: /api/questions: 404 Transkript YouTube'dan alınamadı.

=== python (CEr_UiR4Gvk) ===
  video: Ders 1 Python Programlamaya Giriş · kanal: Fehmi UYAR
  HATA: TranscriptUnavailable: Transkript YouTube'dan alınamadı.

=== Özet ===
| Video | Süre | Toplam süre (sn) | Toplam token | Maliyet (USD) |
|---|---|---|---|---|
| biyoloji | 25:13 | 75.0 | 81374 | 0.013658 |
| tarih | 32:59 | 109.7 | 99995 | 0.016141 |
| matematik | 25:50 | 86.2 | 80382 | 0.013300 |
| ingilizce | 13:56 | 56.5 | 46316 | 0.008234 |
| edebiyat | hata | — | — | — |
| python | hata | — | — | — |
| TOPLAM | — | 327.4 | 308067 | 0.051333 |
```

## Sınırlar

- 6 videonun 4'ü tamamlandı; edebiyatın `rag` koşulu ve Python çalıştırılamadı (YouTube IP engeli).
- Her video tek çalıştırma.
- Kalite ölçülmedi.
- Konular `topics-v1`'den geldi.
- Maliyet liste fiyatıyla tahmindir.
- Süre, transkriptin son segmentinin bitişinden hesaplanır; videonun gerçek süresinden biraz farklı olabilir.
- Biyoloji videosu `backend/chroma` dizininde önceden var; onun dizinleme süresi önbellekten gelir, diğer videolarla karşılaştırılamaz.
