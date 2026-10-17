# Video Soru Üretici — Claude için proje bağlamı

Bu bir üniversite bitirme projesidir. Geliştirici öğrencidir ve ilerlemeyi danışman hocasına aşama aşama göstermesi gerekir. Kullanıcıyla **Türkçe** konuş.

## Proje nedir
YouTube ders videosu bağlantısından zaman damgalı transkript çıkaran, transkriptten özet ve **kaynağı gösterilebilir, doğrulanabilir** sorular üreten bir web uygulaması. Sorular resmî sınav için değil, alıştırma ve hızlı tanı içindir. Her soru videonun ilgili anına bağlanır ve öğretmen onayından geçer.

## Önce oku
- `docs/02-teknik-mimari.png`: dört katmanlı mimari (Sunum, Uygulama ve Orkestrasyon, Veri ve İndeksleme, Yapay Zekâ ve Bilişsel Doğrulama)
- `docs/01-literatur-degerlendirmesi.docx`: her tasarım kararının literatür gerekçesi
- `docs/yol-haritasi.md`: aşamalar
- `docs/ilerleme-gunlugu.md`: biten aşamaların kaydı

## Teknoloji kararları (değiştirme, önce sor)
- Backend: Python, FastAPI. Kod `backend/app` altında, testler `backend/tests` altında.
- Transkript: `youtube-transcript-api`, altyazı yoksa Whisper yedeği (Aşama 3).
- LLM: OpenAI GPT-4o-mini. API anahtarı `.env` içinde, koda ve commit'e asla yazılmaz.
- Vektör DB: ChromaDB, gömme modeli BGE-M3. Kuyruk ve önbellek: Celery + Redis.
- Frontend: React / Next.js (Aşama 12).
- Video dili Türkçe ağırlıklıdır. Soruları ve istemleri Türkçe üret.

## Çalışma kuralları
1. **Aşama aşama ilerle.** Aynı anda yalnızca tek bir aşamaya çalış. Aşamayı yol haritasından al, kapsamın dışına çıkma.
2. **Her aşama bitince:** testleri çalıştır (`cd backend && pytest`), `docs/ilerleme-gunlugu.md` dosyasına aşamanın kaydını ekle (ne yapıldı, nasıl doğrulandı, bilinen sınırlar), sonra commit at.
3. **Küçük, anlamlı commit'ler** at. Push'u kullanıcı yapar, sen yalnızca commit at.
   - Mesajın ilk satırı sade Türkçe, tek cümle olsun ve ne yapıldığını doğrudan anlatsın. `feat:`, `fix:`, `docs:` gibi teknik önekler **kullanılmaz**.
   - İlk satır emir kipiyle bitsin: "ekle", "geliştir", "düzelt", "doğrula", "iyileştir" gibi.
   - Gerekirse bir boş satır bırakıp kısa bir açıklama yaz: neden yapıldı, nasıl doğrulandı.
   - Örnekler:
     - `Transkript temizlemeyi ekle ve ham/temiz seçimini mümkün kıl`
     - `Videodan çoktan seçmeli soru üretimini ve kaynak alıntısı doğrulamasını ekle`
     - `Soru tekrarlarını benzerlik eşiğiyle ele`
     - `API anahtarı eksikken anlaşılır hata mesajı ver`
   - Eski commit'ler yeniden yazılmaz: rebase, amend ya da force push yapılmaz. Eski önekli mesajlar olduğu gibi kalır.
4. **Test yaz.** Dış servis çağrılarını (YouTube, OpenAI) testlerde sahte nesnelerle taklit et.
5. **Gizli bilgi:** `.env`, API anahtarı ve kişisel veri commit'lenmez.
6. **Literatürle uyumlu kal:** her teknolojiyi bir sorunu çözdüğü ve etkisi ölçülebildiği için ekle. Karşılaştırma gerektiren yerlerde (sabit boyutlu ve anlamsal bölütleme, RAG'li ve RAG'siz, ham ve temiz transkript) ikisini de kodda seçilebilir bırak ki ölçülebilsin.
7. **Anlaşılır ol:** kullanıcı öğrencidir. Yaptığın değişikliği kısa ve sade Türkçeyle açıkla, kod yorumlarını Türkçe yaz.
8. **Kendi başlatmadığın süreçleri asla kapatma** (uvicorn, `npm run dev` vb.). Port doluysa oradaki süreci durdurma: kullanıcıya söyle ya da başka bir port kullan. Yalnızca kendi başlattığın süreci, komut satırını kontrol ederek kapat.

## Sık kullanılan komutlar
```
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload     # http://localhost:8000/docs
pytest

cd frontend
npm install
npm run dev                       # http://localhost:3000 (backend ayrıca çalışmalı)
npm run typecheck
```

## Şu anki durum
Aşama 0, 1, 2, 5 ve 6 tamamlandı: iskelet, FastAPI, `POST /api/transcript`, LLM soyut katmanı (`services/llm.py`), ham/temiz transkript seçimi, `POST /api/summary` ve RAG'siz taban çizgisi olarak `POST /api/questions` (istem `questions-v1`; yapı denetimi, alıntı doğrulaması `services/quotes.py`, tekrar ayıklama, sabit tohumlu seçenek karıştırma). Aşama 3 (Whisper yedeği, WER) ve Aşama 4 (bölümleme) ertelendi; ~30 sn'lik bloklama (`services/chunking.py`) Aşama 4'te yeniden kullanılacak. Aşama 14'ün küçük bir parçası öne alındı: başarılı yanıtlar `backend/runs/` altına kaydediliyor (`services/runs.py`, git dışında).

Aşama 12 (web arayüzü) parçalara bölündü (12a-12e); **yalnızca 12a, 12b, 12c ve 12d yapıldı**, 12e ve Aşama 12'nin geneli bitmedi.
- 12a: `frontend/` altında Next.js (App Router, TypeScript) iskeleti, ana sayfada `/health` sağlık göstergesi; backend'de yalnızca `http://localhost:3000` kaynağına izin veren CORS. Tarayıcıda gözle doğrulandı.
- 12b: ana sayfada YouTube bağlantısı formu ve `POST /api/summary` çağrısı. İstek kodu `frontend/lib/api.ts` (12c ve 12d de bunu kullanacak), tarayıcıdaki bağlantı denetimi `frontend/lib/youtube.ts` (backend'deki `extract_video_id` ile aynı kurallar).
- 12c: başarılı özet yanıtı okunaklı bir sonuç kartında (`frontend/app/summary-result.tsx`): teknik bilgiler sönük bir satırda, özet paragraf olarak, konu başlıkları dakika:saniye zamanlarıyla; başlık videoyu o saniyeden yeni sekmede açar. Konu zamanlarının transkriptle doğrulanmadığı notu kartta yazıyor. Zaman/bağlantı yardımcıları `frontend/lib/format.ts`. Tarayıcıda gözle doğrulandı (zaman bağlantısının doğru saniyeyi açtığı henüz denenmedi); konu zamanları çalıştırmadan çalıştırmaya değişiyor.
- 12d: özet kartının altında ayrı "Soruları üret" düğmesi `POST /api/questions` çağırır (`frontend/app/questions-section.tsx`). Her soru bir kart (`frontend/app/question-card.tsx`): seçenek seçilmeden doğru cevap görünmez; seçilince doğru/yanlış, açıklama, kaynak alıntısı, "alıntı transkriptte bulundu/bulunamadı" ve videoyu o saniyeden açan kaynak süresi çıkar. Kaynağı doğrulanamayan sorular gizlenmez, ayrı görünür. Tarayıcıda gözle doğrulanması kullanıcının onayını bekliyor.
Aşama 9 (otomatik doğrulama) **kısmen** yapıldı: yalnızca ilk adım olan alıntı-cevap destek kontrolü (`services/support_check.py`, istem `support-v1`). `POST /api/questions` isteğinde `check_support: true` verilirse, alıntısı transkriptte bulunan her soru için ayrı bir model çağrısıyla alıntının doğru cevabı destekleyip desteklemediği sorulur. Model yalnızca soru, doğru cevabın metni ve alıntıyı görür; sonuç `destekliyor` / `kısmen` / `desteklemiyor`. Kod iki etiket daha verir: `kontrol edilmedi` (alıntı bulunamadı, çağrı yapılmadı) ve `kontrol edilemedi` (çağrı ya da yanıt geçersiz). Varsayılan kapalı; kapalıyken yanıt eskisiyle aynı. **Bu bir model değerlendirmesidir, kesin doğru değildir.** Üç deneme yapıldı (`docs/bulgular/asama-9-destek-kontrolu-1/2/3.md`); her birinde elle etiketler model çağrısından önce commit'lendi, model tek çalıştırmayla etiketledi: Deneme 1'de 5 soruda 3, Deneme 2'de 9 soruda 7, Deneme 3'te sayıma giren 17 soruda 11 eşleşme (ingilizce S3 sayım dışı); birleşik 31 soruda 21 eşleşme. Sınırlar: tek etiketleyen, sorular bağımsız değil, tek çalıştırma. Aşama 9'da yalnızca bu alıntı-cevap destek kontrolü yapıldı; sadakat (faithfulness), Bloom, yazım hatası ve tekrar kontrolleri yapılmadı. **Sonraki adım:** bir sonraki denemeden önce elle etiketleme ölçütü ikili olarak (doğrudan destekliyor / değil) önceden belirlenecek.

**Genelleme denemesi 1** (2026-10-17, `docs/bulgular/genelleme-denemesi-1.md`): 4 yeni video (matematik, edebiyat, python, ingilizce), 20 soru, 18'inin alıntısı transkriptte bulundu. İngilizce transkriptte "used to" 0, "yüz" 25 kez geçiyor; Python transkriptinde "guido One rossum", "mat plot lip" gibi yazımlar var. Soru kalitesi ve özet doğruluğu ölçülmedi.

**Maliyet notu:** `check_support: true` iken soru üretimine ek olarak doğrulanmış soru sayısı kadar OpenAI çağrısı yapılır (5 soru → en çok 5 ek çağrı). Çağrılar sırayla yapılır, yanıt süresi de buna göre uzar.

- Özet konu zamanları doğrulanmıyor; Aşama 7, 8, 10 ve 11 yapılmadı, Aşama 9 kısmen. Sırada 12e, Aşama 9'un sonraki adımları, Aşama 7 ya da ertelenen Aşama 3 / 4 var; kullanıcı seçer.

Windows notu: `python` komutu PATH'te değil; sanal ortam `backend\.venv` (`py -3.12 -m venv .venv` ile kuruldu), komutlar `.\.venv\Scripts\python.exe -m pytest` biçiminde çalıştırılır.
