# Kör değerlendirme paketi

Üretilen soruları iki değerlendiriciye kör olarak verir, etiketleri okur, uyumu hesaplar ve AS1/AS2 analizini yapar. OpenAI'a ve YouTube'a istek atmaz.

**Anahtar ve değerlendirici dosyaları puanlama bitene kadar depoya girmez (depo herkese açık, körleme bozulur); analizden sonra anonimleştirilmiş etiketler ve anahtar yayımlanır.** `.gitignore` bu dosyaları dışarıda tutar.

Komutlar `backend` klasöründen çalıştırılır. Windows'ta `python` yerine `.\.venv\Scripts\python.exe` yazılır.

## 1. Dışa aktar

```
python -m evaluation.export --girdi <dosyalar> --video-bilgisi <secim.json> --tohum 42 --cikti <klasör> --anahtar-cikti <gizli-klasör> --istem-surumu questions-v3
```

- `--girdi`: çalıştırma kaydı (`backend/runs`) ya da pilot JSON'u. Joker karakter kullanılabilir (`"../docs/bulgular/pilot-2/pilot-2-*.json"`).
- `--tohum`: soru sırasını belirler ve anahtara yazılır.
- `--istem-surumu`: girdide birden çok sürüm varsa zorunludur.
- `--video-bilgisi`: her video için alan, altyazı türü (elle / otomatik) ve iki dilli mi. Ana deneyde `docs/bulgular/video-secimi/secim.json`. Girdideki her video bu dosyada olmalıdır; bilgiler anahtara yazılır.
- Videoların transkripti önbellekte (`backend/transcripts`) olmalıdır; yoksa betik durur.
- Çıktıda gizli bilgi bulunursa dosyalar silinir ve betik hata verir.

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
