# Kör değerlendirme paketi

Üretilen soruları iki değerlendiriciye kör olarak verir, etiketleri okur, uyumu hesaplar ve AS1/AS2 analizini yapar. OpenAI'a ve YouTube'a istek atmaz.

**Anahtar ve değerlendirici dosyaları puanlama bitene kadar depoya girmez (depo herkese açık, körleme bozulur); analizden sonra anonimleştirilmiş etiketler ve anahtar yayımlanır.** `.gitignore` bu dosyaları dışarıda tutar.

Komutlar `backend` klasöründen çalıştırılır. Windows'ta `python` yerine `.\.venv\Scripts\python.exe` yazılır.

## 1. Dışa aktar

```
python -m evaluation.export --girdi <dosyalar> --video-bilgisi <secim.json> --tohum 42 --cikti <depo-dışı-klasör> --anahtar-cikti <depo-dışı-gizli-klasör> --istem-surumu questions-v3
```

- `--girdi`: çalıştırma kaydı (`backend/runs`) ya da pilot JSON'u. Joker karakter kullanılabilir (`"../docs/bulgular/pilot-2/pilot-2-*.json"`).
- `--tohum`: soru sırasını belirler ve anahtara yazılır.
- `--istem-surumu`: girdide birden çok sürüm varsa zorunludur.
- `--video-bilgisi`: her video için alan, altyazı türü (elle / otomatik) ve iki dilli mi. Ana deneyde `docs/bulgular/video-secimi/secim.json`. Girdideki her video bu dosyada olmalıdır; bilgiler anahtara yazılır.
- Videoların transkripti önbellekte (`backend/transcripts`) olmalıdır; yoksa betik durur.
- Çıktıda gizli bilgi bulunursa dosyalar silinir ve betik hata verir.
- `--cikti` ve `--anahtar-cikti` depo dışında olmalıdır: anahtar dosyası koşul bilgisi taşır, değerlendirici dosyaları tam transkript içerir. Depo içindeki bir klasör verilirse betik hiçbir dosya oluşturmadan hata verir (çıkış kodu 1).

Çıktılar:

- `degerlendirici-A.xlsx`, `degerlendirici-B.xlsx`: içerik ve sıra aynı.
- `anahtar.json`: koşul, istem sürümü, hedef düzey, çift kimliği, kaynak kayıt ve üretilemeyen konular.

## 2. Değerlendiricilere gönder

- Her değerlendiriciye yalnızca kendi xlsx dosyasını gönder. **Anahtarı gönderme.**
- Göndermeden önce "Yönerge" sayfasını doldur.
- Değerlendiriciler birbirinden bağımsız çalışır, "Sorular" sayfasındaki sarı sütunları doldurur. Sorular 3. satırdan başlar; 2. satır açıklama satırıdır.
- "Tanıma hatası kaynaklı mı": sorudaki hata (yanlış bilgi, anlamsız ifade, yanlış doğru cevap) transkriptteki konuşma tanıma hatasından kaynaklanıyorsa evet; sorunun hatası yoksa hayır.

## 3. İçe aktar ve uyumu hesapla

```
python -m evaluation.agreement --a <A.xlsx> --b <B.xlsx> --anahtar <anahtar.json> --cikti <klasör>
```

Tartışmadan önceki etiketlerle çalıştırılır. Çıktılar:

- `uyum-raporu.md`, `uyum.json`: kappa değerleri, aralıklar, eksik ve geçersiz hücreler.
- `anlasmazliklar.xlsx`: tartışma toplantısı için; koşul bilgisi içermez.
- `ortak-etiket-sablonu.xlsx`: tartışmadan sonra doldurulacak boş dosya.

Rapordaki eksik ya da geçersiz hücreleri değerlendiriciye düzelttir ve komutu yeniden çalıştır.

## 4. Tartış

Değerlendiriciler `anlasmazliklar.xlsx` üzerinden tartışır ve bütün sorular için `ortak-etiket-sablonu.xlsx` dosyasını doldurur. Şablon boş gelir; anlaşılan sorular da doldurulur.

## 5. Analiz

```
python -m evaluation.analysis --ortak <ortak.xlsx> --anahtar <anahtar.json> --cikti <klasör> --alfa 0.05
```

Çıktılar: `analiz-raporu.md` ve `analiz.json`. Rapor yorum içermez.

## Kurallar ve yöntemler

- **Kabul edilebilir:** 0-1 yazım hatası.
- **Üretilemeyen konu (empty / invalid / duplicate):** Değerlendirici dosyasına girmez. AS1'de o koşulda kabul edilemez ve kaynağa dayalı değil sayılır. Cevaplanabilirliği yoktur: çift Wilcoxon'dan çıkarılır, sayısı raporlanır.
- **AS2 paydası:** Birincil sonuç "bütün konular"dır: üretilemeyen konu hedef düzeye uyumsuz sayılır. "Yalnızca üretilen sorular" ikincil olarak verilir.
- **Kappa aralığı:** Fleiss, Cohen ve Everitt (1969) büyük örneklem varyansı.
- **Oran farkı aralığı:** Newcombe (1998) 10. yöntem.
- **McNemar:** Uyumsuz çiftlerde iki yönlü kesin binom testi.
- **Wilcoxon:** Sıfır farklar çıkarılır, bağ düzeltmeli normal yaklaşım. r = Z / √N; N sıfır olmayan fark sayısı.
- **Tanıma hatası kaynaklı sorular (duyarlılık):** AS1'de iki sorudan biri işaretli olan çift, AS2'de işaretli soru çıkarılarak yeniden hesaplanır; çıkarılan sayılar raporda yazar. İşareti eksik olanlar ayrı sayılır.
- **İki dilli videolar (alt grup):** AS1 ve AS2 iki dilli videolar hariç yeniden hesaplanır.
- **Altyazı türü:** Kabul edilebilir oranı ve hedef düzeye uyum elle / otomatik altyazıya göre betimsel verilir; test yok.
- **Birincil sonuç:** Bütün videolar ve bütün sorularla hesaplanan sonuçtur; duyarlılık ve alt grup sonuçları birincil değildir.
- **Tanımsız değerler:** Kappa iki değerlendirici de tek kategori kullanırsa tanımsızdır; rapora "tanımsız" yazılır, oransal uyum yine verilir. Hiç uyumsuz çift yoksa McNemar p = 1. Bütün farklar sıfırsa Wilcoxon uygulanmaz.

Formüller `stats.py` başındadır.

## Alan öğretmeni alt kümesi

Kural: [docs/alt-kume-secim-kurali.md](../../docs/alt-kume-secim-kurali.md). İki değerlendiricinin ortak etiketlerinin geçerliliğini sınamak için bir alan öğretmeni 144 sorudan 36'sını da puanlar. Alan öğretmeninin etiketleri ana analize (AS1, AS2) katılmaz.

Sıra: **export → subset → özet değerinin commit'lenmesi → dosyaların dağıtılması.**

1. `export` ile değerlendirici dosyaları ve anahtar üretilir (yukarıdaki 1. adım).
2. Alt küme seçilir. `--cikti` depo dışında olmalı; depo içindeki bir klasör verilirse betik hata verir:

   ```
   python -m evaluation.subset --anahtar <anahtar.json> --cikti <depo-dışı-klasör>
   ```

   Ekrana seçilen soru sayısı, öbür videodan alınan ve boş kalan hücreler (yalnızca alan ve Bloom düzeyi) ve `alt-kume.json` dosyasının SHA-256 değeri yazılır. Soru kimliği ve koşul yazılmaz. Dosya varsa ve aynıysa dokunulmaz; farklıysa üzerine yazılmaz.
3. **`alt-kume.json` depoya konmaz** (koşul bilgisi taşır, körleme bozulur). Yalnızca ekrandaki SHA-256 değeri `docs/bulgular/alt-kume-ozet.txt` dosyasına yazılıp commit'lenir. Puanlama bittikten sonra seçim dosyası depoya eklenir; özet değeri listenin sonradan değişmediğini gösterir.
4. Alan öğretmeni dosyası yazılır (önerilen ad `alan-ogretmeni.xlsx`; tam transkript içerdiği için depo dışında olmalı, depo içindeki bir yol verilirse betik `alt-kume.json` dahil hiçbir dosya yazmadan hata verir): alt kümedeki sorular, değerlendirici dosyasıyla aynı biçimde (aynı sütunlar, açılır listeler, Yönerge ve yazım maddeleri sayfaları) ve tohumla karıştırılmış sırayla. Soru metinleri anahtarda olmadığı için `export`'a verilen girdi dosyalarının aynısı `--girdi` ile verilir; kimliklerin anahtarla aynı olduğu denetlenir:

   ```
   python -m evaluation.subset --anahtar <anahtar.json> --cikti <depo-dışı-klasör> --ogretmen-dosyasi <depo-dışı-klasör>/alan-ogretmeni.xlsx --tohum <sayı> --girdi <dosyalar>
   ```

5. Değerlendirici dosyaları ve alan öğretmeni dosyası dağıtılır. Alan öğretmenine koşul, hedef düzey ve alt kümenin nasıl seçildiği söylenmez.
6. Puanlama ve tartışma bittikten sonra uyum hesaplanır (`--ortak`: tartışmadan sonraki ortak etiket dosyası; `--a` ve `--b` isteğe bağlı, tartışma öncesi dosyalar):

   ```
   python -m evaluation.validity --ogretmen <depo-dışı-klasör>/alan-ogretmeni.xlsx --ortak <ortak.xlsx> --alt-kume <alt-kume.json> --anahtar <anahtar.json> --cikti <klasör> [--a <A.xlsx> --b <B.xlsx>]
   ```

   Çıktı `alan-ogretmeni-uyumu.md` ve `.json`. Her ölçüt için ham uyum (Wilson aralığı), kappa (aralığıyla), iki tarafın kategori dağılımı ve hesaba girmeyen soru sayısı verilir; Bloom düzeyi ve cevaplanabilirlik için doğrusal ağırlıklı kappa da var. Raporda soru kimlikleri ve koşullar listelenmez. Alt küme dosyası başka bir anahtarla üretildiyse (SHA-256 farklı) betik hata verir.
