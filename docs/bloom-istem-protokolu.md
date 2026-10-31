# Bloom yönlendirmeli istem protokolü (Aşama 8, istem questions-v3)

## Amaç

AS2: Bloom yönlendirmeli istem, soruların hedeflenen Bloom düzeyine uyumunu ne ölçüde sağlıyor?
- **Düzey eşlemesi:** Deneyde her videoda 6 konu var. Her konuya yenilenmiş Bloom taksonomisinin bir düzeyi eşlenir; böylece videoda her düzeyden bir soru olur.
- **İki koşul:** full ve rag koşullarında aynı konu–düzey eşlemesi ve aynı istem kullanılır.

## Literatür dayanağı

Aşağıdakiler `docs/01-literatur-degerlendirmesi.docx`'ten alındı:
- **Scaria vd. (2024):**
  - En iyi strateji, düşünce zinciri, Bloom düzeyinin açıklaması ve uzman yazımı örnek soru içeren istem oldu. En fazla bilgiyi içeren istem başarıyı düşürdü.
  - Modellerin çoğu "yaratma" düzeyinde kaliteli soru üretemedi.
- **Tourigny vd. (2026):** Soruların yalnızca %36'sı hedeflenen Bloom düzeyinde çıktı; çoğu hedeften daha düşük düzeyde kaldı.
- **Maity vd. (2025):** Örnekli istem, soruların Bloom düzeylerine dağılımını hedeflenen dağılıma yaklaştırdı. Literatür değerlendirmesinde bu, "her Bloom düzeyi için isteme örnek soru eklenmesinin gerekçesi" olarak geçiyor.
- **Proje bulgusu:** Aşama 6 testindeki 4 sorunun hepsi hatırlama düzeyindeydi ([asama-6-test-1.md](bulgular/asama-6-test-1.md), Bulgu 3).

Buna göre istemde yalnızca hedef düzeyin tanımı ve örneği verilir; altı düzeyin hepsi verilmez, aşırı bilgi yüklenmez. Model önce kısa bir gerekçe (düşünce zinciri), sonra soruyu yazar.

## Kaynak ve bu belgenin sınırı

- **Kaynak:** Anderson, L. W. ve Krathwohl, D. R. (Ed.) (2001). *A Taxonomy for Learning, Teaching, and Assessing: A Revision of Bloom's Taxonomy of Educational Objectives.* New York: Longman.
- **Kitap okunmadı:** Aşağıdaki "Tanım" ve "Tipik eylem fiilleri" alanları, bu çerçevenin bilişsel süreç boyutundaki altı kategori ve alt süreçlerinin kısa Türkçe özetidir. Kitabın kendisi bu belge hazırlanırken okunmadı ve kaynak, proje literatür değerlendirmesinin kaynakçasında yok. Tanımların kaynakla karşılaştırılması gerekir.
- **Proje yorumu:** "Çoktan seçmeli soruda nasıl görünür" alanları kaynaktan değil, bu projenin yorumudur.

## Altı düzey

### 1. Hatırlama (Remember)

- **Tanım:** İlgili bilgiyi uzun süreli bellekten geri getirmek.
- **Tipik eylem fiilleri:** tanımak, hatırlamak (anımsamak); soru kökünde: tanımla, adlandır, listele, hangisidir.
- **Çoktan seçmeli soruda (proje yorumu):** Videoda söylenen bir bilgiyi (terim, olgu, tanım) olduğu gibi tanıyıp seçmek.
- **Örnek soru:**
  - Soru: Rüzgâr hangi yönde eser?
  - A) Alçak basınç alanından yüksek basınç alanına
  - B) Yüksek basınç alanından alçak basınç alanına
  - C) Basıncın eşit olduğu alanlar boyunca
  - D) Yükseklerden alçaklara doğru, basınçtan bağımsız olarak
  - Doğru cevap: B
  - Gerekçe (neden bu düzeyde): Bağlamda doğrudan söylenen bir bilgiyi tanımayı ölçer; yorum ya da uygulama gerektirmez.

### 2. Anlama (Understand)

- **Tanım:** Sözlü, yazılı ya da görsel öğretim iletilerinden anlam kurmak.
- **Tipik eylem fiilleri:** yorumlamak, örneklendirmek, sınıflandırmak, özetlemek, çıkarımda bulunmak, karşılaştırmak, açıklamak.
- **Çoktan seçmeli soruda (proje yorumu):** Videodaki bir bilgiyi başka sözcüklerle ifade eden, bir örneği doğru sınıfa koyan ya da iki kavramı karşılaştıran seçeneği bulmak.
- **Örnek soru:**
  - Soru: "Isınan yerlerde alçak basınç oluşur" bilgisinin nedenini en iyi açıklayan ifade hangisidir?
  - A) Isınan havanın miktarı artar.
  - B) Isınan hava ağırlaşıp yere doğru alçalır.
  - C) Isınan hava genişleyip hafifler ve yükselir, bu yüzden yere uyguladığı ağırlık azalır.
  - D) Isınan yerlerde rüzgâr esmediği için hava hareketsiz kalır.
  - Doğru cevap: C
  - Gerekçe (neden bu düzeyde): Bağlamdaki bilgiyi farklı sözlerle yeniden ifade etmeyi ve açıklamayı ölçer; ezber cümleyi tanımak yetmez.

### 3. Uygulama (Apply)

- **Tanım:** Bir işlemi (yöntemi, kuralı) verilen bir durumda yürütmek ya da kullanmak.
- **Tipik eylem fiilleri:** yürütmek, uygulamak (kullanmak); soru kökünde: hesapla, uygula, kullan, çöz.
- **Çoktan seçmeli soruda (proje yorumu):** Öğrenilen bilgiyi videoda geçmeyen yeni bir duruma uygulamak.
- **Örnek soru:**
  - Soru: Bir dağcı deniz seviyesinden 3000 metre yüksekliğe tırmanıyor. Anlatılana göre dağcının bulunduğu yerdeki hava basıncı nasıl değişir?
  - A) Azalır.
  - B) Artar.
  - C) Değişmez.
  - D) Önce artar, sonra azalır.
  - Doğru cevap: A
  - Gerekçe (neden bu düzeyde): Bağlamdaki kuralı (yükseldikçe basınç azalır) bağlamda geçmeyen yeni bir duruma uygulamayı ölçer. Gereken bilgi bağlamda var; yalnızca senaryo yeni.

### 4. Çözümleme (Analyze)

- **Tanım:** Bir bütünü parçalarına ayırmak ve parçaların birbiriyle ve genel yapıyla ya da amaçla nasıl ilişkili olduğunu belirlemek.
- **Tipik eylem fiilleri:** ayırt etmek, düzenlemek, nitelendirmek (bir görüşün ardındaki amacı ya da bakış açısını belirlemek).
- **Çoktan seçmeli soruda (proje yorumu):** Bir süreçteki adımlar, nedenler ve sonuçlar arasındaki ilişkiyi ya da ilgili bilgiyi ilgisiz bilgiden ayırt eden seçeneği bulmak.
- **Örnek soru:**
  - Soru: Kıyıda gündüz denizden karaya meltem esmesini açıklayan doğru sıra hangisidir?
  - A) Deniz daha çabuk ısınır → denizde alçak basınç oluşur → hava karadan denize akar.
  - B) Kara daha çabuk ısınır → karada alçak basınç oluşur → hava denizden karaya akar.
  - C) Kara soğur → karada yüksek basınç oluşur → hava karadan denize akar.
  - D) Deniz soğur → iki alan arasındaki basınç farkı kalkar → rüzgâr durur.
  - Doğru cevap: B
  - Gerekçe (neden bu düzeyde): Bağlamdaki ayrı bilgileri (ısınma, basınç, rüzgâr yönü) birbirine bağlayıp neden–sonuç zincirini kurmayı ölçer.

### 5. Değerlendirme (Evaluate)

- **Tanım:** Ölçütlere ve standartlara dayanarak yargıda bulunmak.
- **Tipik eylem fiilleri:** denetlemek, eleştirmek; soru kökünde: değerlendir, savun, hangisi daha uygundur, gerekçelendir.
- **Çoktan seçmeli soruda (proje yorumu):** Verilen bir iddiayı, çözümü ya da yaklaşımı videodaki bilgilere ve bir ölçüte göre yargılayıp en iyi gerekçelendirilmiş seçeneği seçmek.
- **Örnek soru:**
  - Soru: İki öğrenci tartışıyor. Ali: "İki şehir arasındaki basınç farkı artarsa aralarında esen rüzgâr hızlanır." Ayşe: "Rüzgârın hızı yalnızca sıcaklığa bağlıdır, basınç farkının bir etkisi yoktur." Anlatılanlara göre hangi değerlendirme doğrudur?
  - A) Ali'nin iddiası desteklenir, Ayşe'ninki desteklenmez.
  - B) Ayşe'nin iddiası desteklenir, Ali'ninki desteklenmez.
  - C) İki iddia da desteklenir.
  - D) İki iddia da anlatılanlarla çelişir.
  - Doğru cevap: A
  - Gerekçe (neden bu düzeyde): İddiaları bağlamdaki bilgiyi ölçüt alarak yargılamayı ölçer; doğru cevap için bilgiyi hatırlamak yetmez, iddiaları ona göre tartmak gerekir.

### 6. Yaratma (Create)

- **Tanım:** Öğeleri bir araya getirerek tutarlı ya da işlevsel bir bütün oluşturmak; öğeleri yeni bir örüntü ya da yapı içinde yeniden düzenlemek.
- **Tipik eylem fiilleri:** üretmek (hipotez kurmak), planlamak (tasarlamak), oluşturmak (inşa etmek).
- **Çoktan seçmeli soruda (proje yorumu):** Çoktan seçmeli biçimde en uygun planı, hipotezi ya da tasarımı seçtirmek.
- **Literatür notu:** Scaria vd. (2024) modellerin çoğunun bu düzeyde kaliteli soru üretemediğini bildiriyor.
- **Örnek soru:**
  - Soru: Bir öğrenci "ısınan hava yükselir" bilgisini sınıfta göstermek için bir düzenek planlıyor. Aşağıdaki planlardan hangisi bu amaca en uygundur?
  - A) İki odanın sıcaklığını termometreyle ölçüp karşılaştırmak.
  - B) Rüzgârlı bir günde dışarıdaki bir bayrağın hareketini izlemek.
  - C) Yanan bir mumun biraz yukarısına hafif bir kâğıt fırıldak asıp fırıldağın dönüp dönmediğini gözlemek.
  - D) Bir balonu buzdolabına koyup bir saat sonra boyutunu ölçmek.
  - Doğru cevap: C
  - Gerekçe (neden bu düzeyde): Bağlamdaki bilgiyi kullanarak bir amaca uygun planı seçmeyi ölçer; çoktan seçmeli biçimde yaratma düzeyine en yakın biçim budur. Bu düzeyin çoktan seçmeli soruyla tam ölçülemediği ve modellerin burada zorlandığı literatürde biliniyor (Scaria vd., 2024).

## Örnek soru kuralları

1. **Konu kısıtı:** Örnek sorular deney videolarının konularından OLMAMALI:
   - 6 pilot alanın videoları (biyoloji, tarih, matematik, İngilizce, edebiyat, Python)
   - ileride seçilecek 6 video

   Aksi hâlde istem bu videoların cevaplarını modele sızdırır.
2. **Biçim:** Her örnek, deneyde üretilecek sorularla aynı biçimde olur: soru kökü ve 4 seçenek.
3. **Cevap ve gerekçe:** Her örnekte doğru cevap ve kısa bir gerekçe olur. Gerekçe, sorunun neden o düzeyde olduğunu söyler.
4. **Yazar:** Örnek soruları kullanıcı yazar. İstem (questions-v3) bu belgedeki tanımları ve örnekleri birebir kullanır.

## Örnek bağlam

Örnek bağlam (bütün örnek sorular için ortak)

Konu: hava basıncı ve rüzgâr (coğrafya; deney videolarının alanlarından değil).

"Hava basıncı, havanın yeryüzüne uyguladığı ağırlıktır. Yükseklere çıkıldıkça hava seyrekleşir ve basınç azalır. Sıcaklık arttığında hava genişler, hafifler ve yükselir; bu yüzden ısınan yerlerde alçak basınç oluşur. Soğuyan hava ise ağırlaşıp alçalır ve yüksek basınç oluşturur. Rüzgâr, yüksek basınç alanından alçak basınç alanına doğru eser; iki alan arasındaki basınç farkı ne kadar büyükse rüzgâr o kadar hızlı eser. Gündüz kara denizden daha çabuk ısındığı için kıyılarda gündüz denizden karaya doğru meltem eser."

## Konu–düzey eşlemesi kuralı

1. **6 konuya 6 düzey:** Her düzey bir kez kullanılır.
2. **Tohumlu karıştırma:** Konular videodaki sırayla geldiği için düzeyler sabit sırayla eşlenirse aynı düzey hep videonun başına ya da sonuna düşer. Bunu önlemek için düzey sırası, video_id'den türetilen sabit bir tohumla karıştırılır. Aynı video her zaman aynı eşlemeyi verir.
3. **Elle eşleme:** Eşleme istekte elle de verilebilir.
4. **İki koşulda aynı eşleme:** full ve rag koşullarında aynı eşleme kullanılır.
5. **Konu sayısı 6 değilse:** Eşlemenin nasıl yapılacağı henüz belirlenmedi; kullanıcıyla birlikte karar verilecek.
