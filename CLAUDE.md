# Video Soru Üretici — Claude için proje bağlamı

Bu bir üniversite bitirme projesidir. Geliştirici öğrencidir ve ilerlemeyi danışman hocasına aşama aşama göstermesi gerekir. Kullanıcıyla **Türkçe** konuş.

## Proje nedir
YouTube ders videosu bağlantısından zaman damgalı transkript çıkaran, transkriptten özet ve **kaynağı gösterilebilir, doğrulanabilir** sorular üreten bir web uygulaması. Sorular resmî sınav için değil, alıştırma ve hızlı tanı içindir. Her soru videonun ilgili anına bağlanır ve öğretmen onayından geçer.

## Araştırma soruları ve deney tasarımı
- **AS1:** Türkçe ders videolarında RAG ile seçilen bağlam, transkriptin tamamını vermeye göre üretilen soruların kalitesini (kabul edilebilir soru oranı, kaynağa dayalılık) artırıyor mu?
  - Başarı ölçütü: RAG koşulunda kabul edilebilir (0–1 yazım hatası) soru oranı en az %70 ve tam transkript koşulundan yüksek.
- **AS2:** Bloom yönlendirmeli istem, soruların hedeflenen Bloom düzeyine uyumunu ne ölçüde sağlıyor?
  - Başarı ölçütü: uyum en az %60, değerlendiriciler arası Cohen's kappa en az 0,60.
- **AS3:** Öğrenciler sistemi ve soruları kullanılabilirlik, açıklık ve yararlılık açısından nasıl değerlendiriyor?
  - Başarı ölçütü: ortalama SUS en az 68; açıklık ve yararlılık ortalaması 5 üzerinden en az 3,5.
- **Deney:** 6 alandan ikişer, 12 video × 2 koşul (RAG / tam transkript) × Bloom'un 6 düzeyinden birer soru = 144 soru. İki koşulda aynı model (GPT-4o-mini) ve aynı istem.
- **Değerlendirme:** iki kör değerlendirici, Cohen's kappa; 10 öğrenciyle SUS. Ayrıntı: `docs/yol-haritasi.md` (Plan güncellemesi, 2026-10-31).

## Önce oku
- `docs/02-teknik-mimari.png`: dört katmanlı mimari (Sunum, Uygulama ve Orkestrasyon, Veri ve İndeksleme, Yapay Zekâ ve Bilişsel Doğrulama)
- `docs/01-literatur-degerlendirmesi.docx`: her tasarım kararının literatür gerekçesi
- `docs/yol-haritasi.md`: aşamalar
- `docs/ilerleme-gunlugu.md`: biten aşamaların kaydı

## Teknoloji kararları (değiştirme, önce sor)
- Backend: Python, FastAPI. Kod `backend/app` altında, testler `backend/tests` altında.
- Transkript: `youtube-transcript-api`, altyazı yoksa Whisper large-v3 yedeği (Aşama 3).
- LLM: OpenAI GPT-4o-mini. API anahtarı `.env` içinde, koda ve commit'e asla yazılmaz.
- Vektör DB: ChromaDB, gömme modeli BGE-M3. Kuyruk ve önbellek: Celery + Redis.
- Frontend: React / Next.js (Aşama 12).
- Video dili Türkçe ağırlıklıdır. Soruları ve istemleri Türkçe üret.

## Çalışma kuralları
1. **Aşama aşama ilerle.** Aynı anda yalnızca tek bir aşamaya çalış. Aşamayı yol haritasından al, kapsamın dışına çıkma.
2. **Her iş bitince:** testleri çalıştır (`cd backend && pytest`), `docs/ilerleme-gunlugu.md` dosyasına kaydı ekle (ne yapıldı, nasıl doğrulandı, bilinen sınırlar), sonra değişen dosyaları ve her değişikliğin ne işe yaradığını kullanıcıya sade Türkçeyle anlat.
3. **Commit ve push yapma.** Commit'i kullanıcı değişiklikleri inceledikten sonra kendi mesajıyla atar. Commit mesajı önerme.
   - Eski commit'ler yeniden yazılmaz: rebase, amend ya da force push yapılmaz. Eski önekli mesajlar olduğu gibi kalır.
4. **Test yaz.** Dış servis çağrılarını (YouTube, OpenAI) testlerde sahte nesnelerle taklit et.
5. **Gizli bilgi:** `.env`, API anahtarı ve kişisel veri commit'lenmez.
   - Çalıştırma kayıtları (`backend/runs/`) `docs/bulgular`'a kopyalanmadan önce gizli bilgi için taranır (API anahtarı, yetki başlığı, parola/token, `.env`, e-posta, yerel dosya yolu).
   - Kopyalamadan önce istek bağlantılarındaki YouTube paylaşım kodu (`si=...`) temizlenir.
   - Daha önce commit'lenmiş eski dosyalara dokunulmaz; geçmiş yeniden yazılmaz.
6. **Literatürle uyumlu kal:** her teknolojiyi bir sorunu çözdüğü ve etkisi ölçülebildiği için ekle. Ana karşılaştırma RAG / tam transkripttir (AS1); ikisi de kodda seçilebilir olmalı. Sabit / anlamsal bölütleme, ham / temiz transkript, gömme modeli ve yeniden sıralama ikincil deneylerdir: kodda seçilebilir kalabilirler, ama varsayılan sabit boyutlu bölütleme ve temiz transkripttir. İkincil deneyler ana deneylerden önce yapılmaz.
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
**Backend (Aşama 0, 1, 2, 5, 6 tamamlandı):** iskelet, FastAPI, `POST /api/transcript`, LLM soyut katmanı (`services/llm.py`), ham/temiz transkript seçimi, `POST /api/summary` ve RAG'siz taban çizgisi olarak `POST /api/questions` (istem `questions-v1`; yapı denetimi, alıntı doğrulaması `services/quotes.py`, tekrar ayıklama, sabit tohumlu seçenek karıştırma; seçeneklerin tamamı aynı birimle sayı ya da yılsa karıştırılmaz, küçükten büyüğe sıralanır). Aşama 3 (Whisper yedeği, WER) ve Aşama 4 (bölümleme) ertelendi; ~30 sn'lik bloklama (`services/chunking.py`) Aşama 4'te yeniden kullanılacak. Özet konu zamanlarında blok etiketi kontrolü var (`start_verified`: modelin verdiği değer isteme verilen blok etiketlerinden biri mi; değer değiştirilmez); konunun videoda gerçekten o anda başladığı doğrulanmıyor. Testler: `pytest` → 336 test.

**Aşama 7a (RAG altyapısı): kısmen.** Sabit boyutlu parçalar (`services/chunking.py`, `fixed-150-30`), BGE-M3 gömme katmanı (`services/embeddings.py`), ChromaDB dizini ve erişim (`services/retrieval.py`); soru üretimine 7b'de bağlandı.

**Aşama 7b (RAG soru üretimine bağlandı): kısmen.** `POST /api/questions` isteğinde `context_mode` (`full` / `rag`) verilirse konu başına bir soru `questions-v2` ile üretilir (`services/topic_questions.py`); iki koşulda aynı istem, tek fark bağlam. Verilmezse eski `questions-v1` davranışı. Kayıt sürümü 6 (`topic_generation`). Gerçek videoyla iki koşul henüz çalıştırılmadı.

**Aşama 14 (izleme ve günlükleme): kısmen, kayıt tarafı tamam.** Özet ve soru istekleri `backend/runs/` altına kaydediliyor (`services/runs.py`, git dışında; `services/metrics.py`). Kayıtta aşama bazlı süre (`metrics.stages`), her model çağrısının süresi, model adı ve token sayıları (`metrics.llm_calls`), atılan soru sayıları (`metrics.dropped`) var; hatalı istekler `-error` kaydı olarak yazılıyor (`error`: status_code, kind, detail, stage; gizli bilgi ve `si=` temizlenir). `record_version` 4. API yanıtı değişmedi. Gerçek çalıştırmada elle doğrulandı (2026-10-20, `docs/bulgular/asama-14-gercek-calistirma-1.md`; tek çalıştırma). Yok: maliyet hesabı (fiyat kullanıcıdan gelecek, kayda yazılmıyor), kayıtları görme/özetleme aracı; günlük (logging) yapılandırması bakılmadı.

**Aşama 12 (web arayüzü): 12a-12e yapıldı.** Tarayıcı doğrulamasının ayrıntısı `docs/yol-haritasi.md`'de.
- 12a: `frontend/` altında Next.js (App Router, TypeScript) iskeleti, ana sayfada `/health` sağlık göstergesi; backend'de yalnızca `http://localhost:3000` kaynağına izin veren CORS. Tarayıcıda gözle doğrulandı.
- 12b: ana sayfada YouTube bağlantısı formu ve `POST /api/summary` çağrısı. İstek kodu `frontend/lib/api.ts`, tarayıcıdaki bağlantı denetimi `frontend/lib/youtube.ts` (backend'deki `extract_video_id` ile aynı kurallar).
- 12c: başarılı özet yanıtı okunaklı bir sonuç kartında (`frontend/app/summary-result.tsx`); konu başlıkları dakika:saniye zamanlarıyla, başlık videoyu o saniyeden açar; blok etiketi olmayan zamanın yanında "(doğrulanamadı)" işareti, kartın altında koddaki durumla uyumlu not. Zaman/bağlantı yardımcıları `frontend/lib/format.ts`. Tarayıcıda gözle doğrulandı (zaman bağlantısının doğru saniyeyi açtığı denenmedi); konu zamanları çalıştırmadan çalıştırmaya değişiyor.
- 12d: özet kartının altında ayrı "Soruları üret" düğmesi `POST /api/questions` çağırır (`frontend/app/questions-section.tsx`). Her soru bir kart (`frontend/app/question-card.tsx`): seçenek seçilmeden doğru cevap görünmez; seçilince doğru/yanlış, açıklama, kaynak alıntısı, "alıntı transkriptte bulundu/bulunamadı" ve videoyu o saniyeden açan kaynak süresi çıkar. Kaynağı doğrulanamayan sorular gizlenmez, ayrı görünür. Tarayıcıda kısmen doğrulandı.
- 12e: "Soruları üret" yanında varsayılan kapalı onay kutusu; işaretliyse istek `check_support: true` ile gider. Kartta model değerlendirmesi yalnızca şık seçildikten sonra, alıntının altında, renk + simge + metinle gösterilir; "kontrol edilmedi" ve "kontrol edilemedi" ayrı mesajlar. Kontrol kapalıyken görünüm 12d ile aynı. Tarayıcıda kısmen doğrulandı.

**Aşama 9 (otomatik doğrulama): kısmen.** Alıntı-cevap destek kontrolü ve kodla kontrol edilen soru yazım kuralları yapıldı. Destek kontrolü: `services/support_check.py`, istem `support-v1`. `check_support: true` iken alıntısı transkriptte bulunan her soru için ayrı bir model çağrısıyla alıntının doğru cevabı destekleyip desteklemediği sorulur (`destekliyor` / `kısmen` / `desteklemiyor`; kodun verdiği `kontrol edilmedi` / `kontrol edilemedi`). Varsayılan kapalı. **Bu bir model değerlendirmesidir, kesin doğru değildir.**
- Üç deneme yapıldı (`docs/bulgular/asama-9-destek-kontrolu-1/2/3.md`); elle etiketler her seferinde model çağrısından önce commit'lendi, model tek çalıştırmayla etiketledi. Birleşik: sayıma giren 31 soruda 21 eşleşme. İsabet iddiası yok: tek etiketleyen, sorular bağımsız değil, tek çalıştırma.
- Soru yazım kuralları (2026-10-20, `services/writing_check.py`, `writing-rules-v1`, `docs/soru-yazim-hatalari.md`): Moore vd. (2023) 19 maddelik listesinin 11 maddesi (3, 4, 6, 9, 10, 11, 12, 14, 16, 17, 19) kodla kontrol ediliyor. Kurallar yalnızca işaretler; soru atılmaz, API yanıtı değişmez. Sonuç kayıtta `writing_check` alanında, `record_version` 5. Kurallar mevcut sorular üzerinde çalıştırılmadı, isabet ölçülmedi. 1, 2, 5, 8, 13, 18 model gerektiriyor; 7 ve 15 için Türkçede güvenilir kural bulunamadı.
- Sadakat (faithfulness), Bloom ve benzerlik eşiğiyle tekrar kontrolleri yapılmadı.
- Sonraki adım: bir sonraki denemeden önce elle etiketleme ölçütü ikili olarak (doğrudan destekliyor / değil) önceden belirlenecek.
- **Maliyet notu:** `check_support: true` iken soru üretimine ek olarak doğrulanmış soru sayısı kadar OpenAI çağrısı yapılır (5 soru → en çok 5 ek çağrı). Çağrılar sırayla yapılır, yanıt süresi de buna göre uzar.

**Genelleme denemesi 1 yapıldı** (2026-10-17, `docs/bulgular/genelleme-denemesi-1.md`): 4 yeni video (matematik, edebiyat, python, ingilizce), 20 soru, 18'inin alıntısı transkriptte bulundu. İngilizce transkriptte "used to" 0, "yüz" 25 kez geçiyor; Python transkriptinde "guido One rossum", "mat plot lip" gibi yazımlar var. Soru kalitesi ve özet doğruluğu ölçülmedi.

**Yapılmayanlar:** Aşama 7, 8, 10 ve 11; Aşama 3 ve 4 ertelendi; Aşama 9 ve 14'ün eksik kısımları (yukarıda); konunun videoda gerçekten o anda başladığı doğrulanmıyor. Sırada Aşama 9'un sonraki adımları, Aşama 7 ya da ertelenen Aşama 3 / 4 var; kullanıcı seçer.

Windows notu: `python` komutu PATH'te değil; sanal ortam `backend\.venv` (`py -3.12 -m venv .venv` ile kuruldu), komutlar `.\.venv\Scripts\python.exe -m pytest` biçiminde çalıştırılır.

Plan 31 Ekim 2026'da Hafta-1 geri bildirimine göre güncellendi; ayrıntı docs/yol-haritasi.md'de.
