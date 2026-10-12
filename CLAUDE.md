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

## Sık kullanılan komutlar
```
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload     # http://localhost:8000/docs
pytest
```

## Şu anki durum
Aşama 0, 1, 2 ve 5 tamamlandı: iskelet, FastAPI, `POST /api/transcript`, LLM soyut katmanı (`services/llm.py`), ham/temiz transkript seçimi ve `POST /api/summary`. Aşama 3 (Whisper yedeği, WER) ve Aşama 4 (bölümleme) ertelendi; ~30 sn'lik bloklama (`services/chunking.py`) Aşama 4'te yeniden kullanılacak. Sırada Aşama 6 (RAG'siz temel soru üretimi) ya da ertelenen Aşama 3 / 4 var; kullanıcı seçer.

Windows notu: `python` komutu PATH'te değil; sanal ortam `backend\.venv` (`py -3.12 -m venv .venv` ile kuruldu), komutlar `.\.venv\Scripts\python.exe -m pytest` biçiminde çalıştırılır.
