# Soru yazım hataları listesi ve kural sürümü `writing-rules-v1`

## Kaynak

- **Liste:** Moore vd. (2023), "Assessing the Quality of Multiple-Choice Questions Using GPT-4 and Rule-Based Methods", arXiv 2307.08161, Tablo 1. Listede 19 madde var.
- **Kontrol:** Kullanıcı 19 maddenin adlarını ve sırasını makaledeki tabloyla karşılaştırdı (20 Ekim 2026). Adlar ve sıra aynı.
- **Makalenin geri kalanı:** Asistan tarafından okunmadı. Aşağıdaki Türkçe açıklamalar maddelerin adlarına dayanan kısa tanımlardır, makaleden alıntı değildir.
- **Literatür değerlendirmesiyle ilişki:** Literatür değerlendirmesinde aynı yazarların 19 maddelik listeyi kullanan SAQUET aracı Moore vd. (2024) olarak geçiyor; bu belgedeki kaynak 2023 tarihli makaledir.
- **Dil:** Moore vd. listeyi İngilizce sorularda kullandı. Liste ve kurallar Türkçe sorularda denenmedi. Bu belgedeki kurallar Türkçeye uyarlama denemesidir; isabetleri henüz ölçülmedi.

## Uygulama

- **Kod ve sürüm:** `backend/app/services/writing_check.py`, kural sürümü `writing-rules-v1`.
- **Etkisi:** Kurallar yalnızca **işaretler**; soru atılmaz, API yanıtı değişmez.
- **Kayıt:** Sonuç çalıştırma kaydında `writing_check` alanına yazılır: `rules_version` ve soru başına `flags` listesi. Her işaret `rule_id`, `rule_name` ve kısa `detail` içerir. Kontrolün süresi `metrics.stages.writing_check_ms` olarak kaydedilir.
- **Hangi sorular:** Kontrol, seçenekler karıştırıldıktan sonraki son sorular üzerinde çalışır. `correct_index` karıştırılmış sıraya göredir.
- **Normalleştirme:** Metinler, alıntı doğrulamasındaki `normalize` ile karşılaştırılır: köşeli etiketler silinir, Türkçe küçük harfe çevrilir (I → ı, İ → i), noktalama boşluğa çevrilir.
- **Kural ya da liste değişirse:** Anahtar kelime listesi ya da eşik değişirse sürüm `writing-rules-v2` olur. Eşikler ve listeler sonuçlara bakılarak değiştirilmez.

## Sınıflar

- **kodla:** Kural tanımı açık, kodla kontrol ediliyor.
- **kodla-kısmen:** Kodla kontrol ediliyor ama Türkçede yanlış pozitif ya da kaçırma beklenir.
- **model:** Anlam yargısı gerektirir, bu sürümde kontrol edilmiyor.
- **bu sürümde kontrol edilmiyor:** Güvenilir bir Türkçe kural bulunamadı.

## 19 madde

| # | Ad (İngilizce) | Kısa açıklama | Sınıf | Türkçeye özgü not |
|---|---|---|---|---|
| 1 | Ambiguous or unclear information | Soru ya da seçenekler birden çok biçimde anlaşılabiliyor. | model | Anlam yargısı gerekir. |
| 2 | Implausible distractors | Çeldiriciler akla yatkın değil, kolayca eleniyor. | model | Konu bilgisi gerekir. Arif vd. (2024) bunu en sık hata olarak bulmuştu. |
| 3 | None of the above | Seçeneklerden biri "hiçbiri" türünde. | kodla | Seçenekten dolgu kelimeleri çıkınca yalnızca "hiçbiri" kalıyorsa işaretlenir. |
| 4 | Longest option correct | Doğru seçenek belirgin biçimde en uzun seçenek. | kodla | Eşik aşağıda. |
| 5 | Gratuitous information | Kökte soruya gerekmeyen bilgi var. | model | Neyin gereksiz olduğu anlamla belirlenir. |
| 6 | True/false question | Soru aslında doğru-yanlış sorusu. | kodla-kısmen | Yalnızca seçenekler "Doğru", "Yanlış", "Evet", "Hayır" gibi ifadelerden oluşuyorsa yakalanır. "Hangisi doğrudur?" biçimli öncüllü sorular yakalanmaz. |
| 7 | Convergence cues | Doğru cevap, seçeneklerin ortak öğelerinden tahmin edilebiliyor. | bu sürümde kontrol edilmiyor | Ortak öğe karşılaştırması için Türkçede güvenilir bir kural bulunamadı. |
| 8 | Logical cues | Kök ile doğru seçenek arasında mantıksal ipucu var. | model | |
| 9 | All of the above | Seçeneklerden biri "hepsi" türünde. | kodla | Dolgu kelimeleri çıkınca yalnızca "hepsi" ya da "tümü" kalıyorsa işaretlenir. |
| 10 | Fill-in-blank | Kökte doldurulacak boşluk var. | kodla | Kökün sonundaki üç nokta sayılmaz, boşluktan sonra kelime gelmeli. Türkçe "...... denir." kalıbı yakalanır. |
| 11 | Absolute terms | Seçeneklerde kesin ifadeler var. | kodla-kısmen | Yalnızca tam kelime ya da öbek eşleşir. Ek almış hâller ("hiçbirinde", "tümünde") kaçırılır. |
| 12 | Word repeats | Kökteki bir kelime yalnızca doğru seçenekte tekrar ediyor. | kodla-kısmen | Türkçe ekler yüzünden kelimeler ilk 5 harfle karşılaştırılır. Sınırları aşağıda. |
| 13 | Unfocused stem | Kök tek başına net bir soru sormuyor. | model | |
| 14 | Complex or K-type | "I ve II", "Yalnız I" gibi birleşik seçenekler var. | kodla-kısmen | Romen rakamı ya da A-E büyük harfleriyle gösterilen öncüller aranır. |
| 15 | Grammatical cues | Kök ile yalnızca doğru seçenek dilbilgisi olarak uyuşuyor. | bu sürümde kontrol edilmiyor | Türkçede ek uyumu (hâl ekleri, çoğul) için morfoloji çözümleyicisi gerekir; teknoloji kararı olduğu için eklenmedi. |
| 16 | Lost sequence | Sayısal ya da kronolojik seçenekler sıralı değil. | kodla | **Bizim kodumuz seçenekleri karıştırdığı için bu işaret çoğu zaman karıştırmanın sonucudur.** Aşağıya bakın. |
| 17 | Vague terms | Seçeneklerde belirsiz sıklık ya da miktar ifadeleri var. | kodla-kısmen | Yalnızca tam kelime ya da öbek eşleşir. |
| 18 | More than one correct | Birden çok seçenek doğru olabilir. | model | Transkripte göre yargı gerekir; sadakat denetimiyle örtüşür. |
| 19 | Negative worded | Soru kökü olumsuz. | kodla-kısmen | Yanlış pozitif olabilir. Aşağıya bakın. |

## Kuralların tanımları (`writing-rules-v1`)

Listelerdeki kelimeler normalleştirilmiş hâldedir.

### 3 ve 9: hiçbiri / hepsi
- **Kural:** Seçenekten dolgu kelimeleri çıkarılır. Geriye kalan kelimelerin hepsi aşağıdaki kümedeyse işaretlenir.
- **Dolgu kelimeleri:** yukarıdakilerin, yukarıdaki, seçeneklerin, verilenlerin, de, da, doğru, doğrudur, değil, değildir
- **3. madde:** hiçbiri, hiçbirisi, hiçbiridir
- **9. madde:** hepsi, hepsidir, tümü, tümüdür
- **Kapsam dışı:** "Hiçbir canlı ışık kullanmaz" gibi normal seçenekler işaretlenmez.

### 4: en uzun seçenek doğru
- **Kural:** Doğru seçenek en uzun seçenekse **ve** en uzun çeldiricinin en az **1,3 katıysa** işaretlenir.
- **Uzunluk:** Normalleştirilmiş metnin karakter sayısıyla ölçülür.
- **Eşik:** 1,3 bu sürüm için önceden seçildi, sonuçlara bakılarak değiştirilmeyecek.

### 6: doğru-yanlış
- **Kural:** En az 2 seçenek tek başına şu ifadelerden biriyse işaretlenir: doğru, yanlış, doğrudur, yanlıştır, evet, hayır.

### 10: boşluk doldurma
- **Kural:** Kökte iki ya da daha fazla alt çizgi (`__`), üç ya da daha fazla nokta (`...`) ya da üç nokta karakteri (`…`) varsa **ve** ardından bir kelime geliyorsa işaretlenir.

### 11: kesin ifadeler (seçeneklerde)
- **Kelimeler:** her zaman, hiçbir zaman, asla, daima, kesinlikle, mutlaka, tümü, tamamı, hiçbir
- **Çakışma:** Seçenek tek başına "tümü" ise 9. madde sayılır, burada tekrar işaretlenmez.

### 12: kelime tekrarı
- **Kökteki içerik kelimeleri:** En az 4 harfli olan ve aşağıdaki listede olmayan kelimeler.
- **Sayılmayan kelimeler:** aşağıdakilerden, aşağıdaki, hangisi, hangisidir, hangi, nedir, neden, nasıl, nelerdir, kaçtır, için, olarak, göre, gibi, kadar, daha, olan, olur, olduğu, olduğunu, videoda, videodaki, anlatılan, anlatıldığına, belirtilen, söylenen, bahsedilen, hakkında, ilgili, doğru, doğrudur, yanlış, yanlıştır, değil, değildir, verilen
- **Karşılaştırma:** Kelimeler ilk 5 harfleriyle (kısaysa tamamıyla) karşılaştırılır.
- **Kural:** Kökteki bir kelimenin ön eki doğru seçenekte geçiyor ve hiçbir çeldiricide geçmiyorsa işaretlenir.
- **Sınırlar:**
  - Ünsüz yumuşaması ("kitap" / "kitabı") ve ilk 5 harfi değişen kökler kaçırılır.
  - İlk 5 harfi aynı olan farklı kelimeler eşleşir: kemosentez / kemosentetik aynı kökten olduğu için doğru eşleşir, ama ilgisiz kelimeler de eşleşebilir.
  - Kelimenin cevaba ipucu verip vermediğine bakılmaz.

### 14: birleşik seçenekler
- **Kural:** Seçenek özgün yazımıyla aranır, çünkü küçük harfe çevirmek "I" harfini "ı" yapar. Şu durumlarda işaretlenir:
  - "I ve II", "A, B" gibi iki öncül (I, II, III, IV, V ya da A-E) arasında `,`, "ve", "veya" ya da "ile" geçiyorsa
  - seçenek "Yalnız", "Yalnızca" ya da "Sadece" ile başlayıp bir öncülle devam ediyorsa
- **Yanlış pozitif:** "C ve D vitaminleri" gibi seçenekler de işaretlenir.

### 16: sayısal sıra
- **Kural:** Bütün seçenekler tek bir sayıdan oluşuyorsa, önündeki ve arkasındaki metin her seçenekte aynıysa (ör. "1923", "%20", "350 °C") ve sayılar artan ya da azalan sırada değilse işaretlenir.
- **Sayı biçimi:** Ondalık ayırıcı olarak virgül ve nokta kabul edilir. Binlik ayırıcıyla yazılmış sayılar ("1.500") ondalık okunur.
- **Karıştırma etkisi:** Kod (`shuffle_options`) seçenekleri her soruda karıştırıyor. Bu yüzden model sayıları sıralı yazsa bile son soruda sıra çoğu zaman bozulur, işaret de çoğu zaman bizim karıştırmamızdan gelir.
- **Bu sürümde:** Karıştırma değiştirilmedi, çünkü API yanıtı değişmeyecekti. Sayısal seçenekleri sıralı bırakmak ayrı bir karar.

### 17: belirsiz ifadeler (seçeneklerde)
- **Kelimeler:** bazen, genellikle, genelde, sıklıkla, çoğunlukla, nadiren, ara sıra, zaman zaman, çoğu zaman

### 19: olumsuz soru kökü
- **Kural:** Kökteki bir kelime aşağıdaki kelimelerden biriyse ya da aşağıdaki eklerden biriyle bitiyorsa (ve ekten en az 2 harf uzunsa) işaretlenir.
- **Kelimeler:** değil, değildir, olmayan, olmaz, yoktur, yanlıştır
- **Ekler:** -maz, -mez, -mazlar, -mezler, -mayan, -meyen, -madığı, -mediği, -mamış, -memiş, -mamaktadır, -memektedir
- **Yanlış pozitif:**
  - "-maz/-mez" ile biten olumsuz olmayan kelimeler işaretlenir (ör. "namaz").
  - "Hangisi yanlıştır?" olumsuz sayılır.
- **Kaçırma:**
  - Listede olmayan olumsuz biçimler ("-madan", "-meksizin") kaçırılır.
  - "hariç", "dışında" gibi ifadeler kaçırılır.

## Sınırlar

- **İsabet ölçülmedi:** Kurallar mevcut sorular üzerinde henüz çalıştırılmadı. Bu ayrı bir adım olacak; önce elle etiketleme ölçütü belirlenecek.
- **Model gerektiren maddeler:** 1, 2, 5, 8, 13 ve 18 bu sürümde kontrol edilmiyor.
- **Güvenilir Türkçe kural bulunamayan maddeler:** 7 ve 15 bu sürümde kontrol edilmiyor.
- **Liste İngilizce için hazırlandı:** Türkçede eksik ya da fazla madde olabilir.
