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
   - Çalıştırma kayıtları (`backend/runs/`) `docs/bulgular`'a kopyalanmadan önce gizli bilgi için taranır (API anahtarı, yetki başlığı, parola/token, `.env`, e-posta, yerel dosya yolu).
   - Kopyalamadan önce istek bağlantılarındaki YouTube paylaşım kodu (`si=...`) temizlenir.
   - Daha önce commit'lenmiş eski dosyalara dokunulmaz; geçmiş yeniden yazılmaz.
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
**Backend (Aşama 0, 1, 2, 5, 6 tamamlandı):** iskelet, FastAPI, `POST /api/transcript`, LLM soyut katmanı (`services/llm.py`), ham/temiz transkript seçimi, `POST /api/summary` ve RAG'siz taban çizgisi olarak `POST /api/questions` (istem `questions-v1`; yapı denetimi, alıntı doğrulaması `services/quotes.py`, tekrar ayıklama, sabit tohumlu seçenek karıştırma). Aşama 3 (Whisper yedeği, WER) ve Aşama 4 (bölümleme) ertelendi; ~30 sn'lik bloklama (`services/chunking.py`) Aşama 4'te yeniden kullanılacak. Özet konu zamanlarında blok etiketi kontrolü var (`start_verified`: modelin verdiği değer isteme verilen blok etiketlerinden biri mi; değer değiştirilmez); konunun videoda gerçekten o anda başladığı doğrulanmıyor. Testler: `pytest` → 238 test.

**Aşama 14 (izleme ve günlükleme): kısmen, kayıt tarafı tamam.** Özet ve soru istekleri `backend/runs/` altına kaydediliyor (`services/runs.py`, git dışında; `services/metrics.py`). Kayıtta aşama bazlı süre (`metrics.stages`), her model çağrısının süresi, model adı ve token sayıları (`metrics.llm_calls`), atılan soru sayıları (`metrics.dropped`) var; hatalı istekler `-error` kaydı olarak yazılıyor (`error`: status_code, kind, detail, stage; gizli bilgi ve `si=` temizlenir). `record_version` 4. API yanıtı değişmedi. Gerçek çalıştırmada elle doğrulandı (2026-10-20, `docs/bulgular/asama-14-gercek-calistirma-1.md`; tek çalıştırma). Yok: maliyet hesabı (fiyat kullanıcıdan gelecek, kayda yazılmıyor), kayıtları görme/özetleme aracı; günlük (logging) yapılandırması bakılmadı.

**Aşama 12 (web arayüzü): 12a-12e yapıldı.** Tarayıcı doğrulamasının ayrıntısı `docs/yol-haritasi.md`'de.
- 12a: `frontend/` altında Next.js (App Router, TypeScript) iskeleti, ana sayfada `/health` sağlık göstergesi; backend'de yalnızca `http://localhost:3000` kaynağına izin veren CORS. Tarayıcıda gözle doğrulandı.
- 12b: ana sayfada YouTube bağlantısı formu ve `POST /api/summary` çağrısı. İstek kodu `frontend/lib/api.ts`, tarayıcıdaki bağlantı denetimi `frontend/lib/youtube.ts` (backend'deki `extract_video_id` ile aynı kurallar).
- 12c: başarılı özet yanıtı okunaklı bir sonuç kartında (`frontend/app/summary-result.tsx`); konu başlıkları dakika:saniye zamanlarıyla, başlık videoyu o saniyeden açar; blok etiketi olmayan zamanın yanında "(doğrulanamadı)" işareti, kartın altında koddaki durumla uyumlu not. Zaman/bağlantı yardımcıları `frontend/lib/format.ts`. Tarayıcıda gözle doğrulandı (zaman bağlantısının doğru saniyeyi açtığı denenmedi); konu zamanları çalıştırmadan çalıştırmaya değişiyor.
- 12d: özet kartının altında ayrı "Soruları üret" düğmesi `POST /api/questions` çağırır (`frontend/app/questions-section.tsx`). Her soru bir kart (`frontend/app/question-card.tsx`): seçenek seçilmeden doğru cevap görünmez; seçilince doğru/yanlış, açıklama, kaynak alıntısı, "alıntı transkriptte bulundu/bulunamadı" ve videoyu o saniyeden açan kaynak süresi çıkar. Kaynağı doğrulanamayan sorular gizlenmez, ayrı görünür. Tarayıcıda kısmen doğrulandı.
- 12e: "Soruları üret" yanında varsayılan kapalı onay kutusu; işaretliyse istek `check_support: true` ile gider. Kartta model değerlendirmesi yalnızca şık seçildikten sonra, alıntının altında, renk + simge + metinle gösterilir; "kontrol edilmedi" ve "kontrol edilemedi" ayrı mesajlar. Kontrol kapalıyken görünüm 12d ile aynı. Tarayıcıda kısmen doğrulandı.

**Aşama 9 (otomatik doğrulama): kısmen.** Yalnızca alıntı-cevap destek kontrolü yapıldı (`services/support_check.py`, istem `support-v1`). `check_support: true` iken alıntısı transkriptte bulunan her soru için ayrı bir model çağrısıyla alıntının doğru cevabı destekleyip desteklemediği sorulur (`destekliyor` / `kısmen` / `desteklemiyor`; kodun verdiği `kontrol edilmedi` / `kontrol edilemedi`). Varsayılan kapalı. **Bu bir model değerlendirmesidir, kesin doğru değildir.**
- Üç deneme yapıldı (`docs/bulgular/asama-9-destek-kontrolu-1/2/3.md`); elle etiketler her seferinde model çağrısından önce commit'lendi, model tek çalıştırmayla etiketledi. Birleşik: sayıma giren 31 soruda 21 eşleşme. İsabet iddiası yok: tek etiketleyen, sorular bağımsız değil, tek çalıştırma.
- Sadakat (faithfulness), Bloom, yazım hatası ve tekrar kontrolleri yapılmadı.
- Sonraki adım: bir sonraki denemeden önce elle etiketleme ölçütü ikili olarak (doğrudan destekliyor / değil) önceden belirlenecek.
- **Maliyet notu:** `check_support: true` iken soru üretimine ek olarak doğrulanmış soru sayısı kadar OpenAI çağrısı yapılır (5 soru → en çok 5 ek çağrı). Çağrılar sırayla yapılır, yanıt süresi de buna göre uzar.

**Genelleme denemesi 1 yapıldı** (2026-10-17, `docs/bulgular/genelleme-denemesi-1.md`): 4 yeni video (matematik, edebiyat, python, ingilizce), 20 soru, 18'inin alıntısı transkriptte bulundu. İngilizce transkriptte "used to" 0, "yüz" 25 kez geçiyor; Python transkriptinde "guido One rossum", "mat plot lip" gibi yazımlar var. Soru kalitesi ve özet doğruluğu ölçülmedi.

**Yapılmayanlar:** Aşama 7, 8, 10 ve 11; Aşama 3 ve 4 ertelendi; Aşama 9 ve 14'ün eksik kısımları (yukarıda); konunun videoda gerçekten o anda başladığı doğrulanmıyor. Sırada Aşama 9'un sonraki adımları, Aşama 7 ya da ertelenen Aşama 3 / 4 var; kullanıcı seçer.

Windows notu: `python` komutu PATH'te değil; sanal ortam `backend\.venv` (`py -3.12 -m venv .venv` ile kuruldu), komutlar `.\.venv\Scripts\python.exe -m pytest` biçiminde çalıştırılır.
