# Genelleme denemesi 1

**Tarih:** 17 Ekim 2026
**Amaç:** Sistemi daha önce denenmemiş dört farklı dersin videosuyla çalıştırıp neyin ölçüldüğünü kaydetmek.
**Ayarlar:** `POST /api/questions` · `count: 5` · `transcript_mode: clean` · `check_support: false` · gpt-4o-mini · istem `questions-v1`
**Ham sonuçlar:** [matematik](genelleme-1-matematik.json) · [edebiyat](genelleme-1-edebiyat.json) · [python](genelleme-1-python.json) · [ingilizce](genelleme-1-ingilizce.json) (`backend/runs/` kayıtlarının birebir kopyaları, kayıt sürümü 3)

> Bu dosya yalnızca ölçülenleri içerir. Soru kalitesi ve özet doğruluğu ölçülmedi; bunlar hakkında hüküm verilmez.

## Sonuçlar

Her video için bir çalıştırma yapıldı.

| Video | Kimlik | Dönen soru | Alıntısı transkriptte bulunan (`verified`) |
|---|---|---|---|
| matematik | `edSvMQ77TmU` | 5 | 4/5 |
| edebiyat | `fgOxbhEMnQQ` | 5 | 5/5 |
| python | `CEr_UiR4Gvk` | 5 | 5/5 |
| ingilizce | `FetnCoTS9qY` | 5 | 4/5 |

**Doğrulanamayan iki soru:**
- matematik S3: *"Açıortay teoremi ile ilgili oranlar nasıl yazılır?"*
- ingilizce S5: *"Yüz kalıbı ile olumsuz cümle kurarken hangi kelime kullanılmaz?"*

**Hata:** Kullanıcının dört çalıştırmasında hata yanıtı alınmadı. (Kayıtlar yalnızca başarılı yanıtları saklar.)

**Python özetinin konu zamanları:** Konu başlıkları 0:00 ile 8:48 arasında başlıyor (0:00, 3:37, 5:40, 7:46, 8:48). Kullanıcıya göre video 9:23 sürüyor; transkriptin son segmenti 9:25'te (565,96 sn) bitiyor. Konu zamanları videonun başından sonuna yayılıyor.

## Yabancı sözcük yazımları (olduğu gibi)

**ingilizce (`FetnCoTS9qY`)**, Türkçe otomatik altyazı:

| Terim | Ham transkriptte |
|---|---|
| "used to" | 0 kez |
| "yüz" | 25 kez |

- Özet ve konu başlığı **"used to"** yazıyor: *"…geçmişteki alışkanlıkları anlatan 'used to' kalıbının…"*, başlık *"Used to Kalıbının Kullanımı"*.
- Soru metinlerinin beşi de **"Yüz kalıbı"** ile başlıyor (S1-S5).
- Doğrulanan S1, S2 ve S3'ün alıntıları "yüz" yazımını içeriyor (ör. S1: *"yüz kalıbı şu amaçlarla kullanılır…"*). Alıntılar bu hatalı yazımla transkriptte bulunduğu için doğrulandı çıkıyor.
- Transkriptten örnek segmentler: 5:01 *"Bu dersimizde yüz çık kalıbının"*, 5:04 *"kullanımını öğreneceğiz yüz kalıbı şu"*.

**python (`CEr_UiR4Gvk`)**, Türkçe otomatik altyazı. Transkriptte şu yazımlar var:
- *"guido One rossum"* (1:07 segmenti: *"dilidir ve guido One rossum tarafından"*)
- *"mat plot lip"* (6:01 segmenti ve S3 alıntısı)
- *"non python"* (5:46 ve 6:01 segmentleri, S3 alıntısı)

Bu yazımlar S1 ve S3'ün doğrulanmış alıntılarında da aynen geçiyor.

## Sınırlar

- 4 video, video başına tek çalıştırma.
- Destek kontrolü etiketlemesi (alıntının doğru cevabı destekleyip desteklemediği) bu sorular için henüz yapılmadı.
- Soru kalitesi ve özet doğruluğu ölçülmedi.
