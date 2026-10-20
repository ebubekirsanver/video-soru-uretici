# Aşama 14 · Gerçek çalıştırma 1

**Tarih:** 20 Ekim 2026
**Deneme:** Aşama 14 kodu (`record_version` 4) ile gerçek bir soru üretimi çalıştırması, destek kontrolü açık. Ardından videosu olmayan bir bağlantıyla bir hata isteği.
**Kim baktı:** Kullanıcı, kayıt dosyalarını (`backend/runs/`) elle açıp inceledi. Aşağıdaki değerler kullanıcının kayıtta gördükleridir.
**Kayıt:** Kayıt dosyaları yerelde kaldı, depoya kopyalanmadı.

> **Tek çalıştırma.** Süre ve token sayıları bu çalıştırmaya aittir; ortalama ya da genel değer değildir.

## Başarılı istek (soru üretimi, destek kontrolü açık)

- Kayıtta `record_version: 4` var.
- Kayıtta `metrics.stages` ve `metrics.llm_calls` alanları var.
- `metrics.llm_calls` içinde toplam 4 çağrı var: 1 soru üretimi (`questions`) ve 3 destek kontrolü (`support`).

| Çağrı | Token | Süre |
|---|---|---|
| Soru üretimi | 7913 giriş + 520 çıkış = 8433 | 5516,9 ms |
| Destek kontrolü 1-3 | 602, 610 ve 594 | her biri yaklaşık 1,0-1,7 sn |

- **Süreler:** Aşama süreleri toplamı, `total_ms` değeriyle (11496,2 ms) eşleşiyor. Fark yaklaşık 0,2 ms.
- **Destek çağrılarının süreleri:** Destek çağrılarının toplamı 3980,9 ms, destek kontrolü aşaması 4009,2 ms. İki değer tutarlı.
- **Atılan sorular:** `metrics.dropped` içinde `structure_invalid: 0`, `duplicate: 0`.
- **Paylaşım kodu:** `request.url` içinde `si=` yok.

## Hata isteği (videosu olmayan bağlantı)

- `...-error.json` adıyla bir hata kaydı oluştu.
- Kullanıcı kayıtta şunları gördü:
  - `outcome: "error"`
  - `error.kind` ve `error.stage` alanları dolu
  - `response: null`
  - dosyada `sk-` dizgisi yok

## Sınırlar

- **Tek çalıştırma:** Ortalama değil, tekrar yapılmadı.
- **Maliyet hesaplanmadı:** Fiyat kayda yazılmıyor, kayıtta yalnızca model adı ve token sayıları var.
- **Destek çağrısı sayısı kontrol edilmedi:** Yanıttaki "kaynağı doğrulanan" soru sayısının destek çağrısı sayısıyla (3) eşleştiği kullanıcı tarafından kontrol edilmedi. Yalnızca süre toplamının (3980,9 ms / 4009,2 ms) tutarlı olduğu görüldü.
- **Hata kaydındaki değerler bu belgeye yazılmadı:** `error.kind` ve `error.stage` alanlarının hangi değeri aldığı aktarılmadı, yalnızca alanların var olduğu görüldü.
- **Kayıt dosyalarını yalnızca kullanıcı inceledi:** Dosyalar depoya kopyalanmadı ve asistan tarafından ayrıca okunmadı.
