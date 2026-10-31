# Aşama 9 · Benzer sorular 1

## Amaç

Anlamca benzer (metni birebir aynı olmayan ama aynı bilgiyi soran) soruları BGE-M3 ile bulup işaretlemek için önce elle etiketlenmiş bir çift listesi hazırlanır. Gerekçe: 7b koşul denemesinde ([asama-7b-kosul-denemesi-1.md](asama-7b-kosul-denemesi-1.md)) mevcut `drop_duplicates`, yalnızca birebir aynı metni yakaladığı için aynı bilgiyi soran sorular listede kaldı.

## Veri

- **Kaynak:** [asama-7b-kosul-denemesi-1.json](asama-7b-kosul-denemesi-1.json) (kemosentez videosu, `109kCbVtU1U`).
- **Soru sayısı:** full 4 soru, rag 5 soru.
- **Çiftler:** Her koşulun kendi içindeki bütün soru çiftleri listelendi; koşullar arası çift yok. Toplam 16 çift.
- **Sıralama:** Soru numaraları (S1, S2, …) koşulun yanıtındaki sıradır.

## Etiket ölçütü (etiketlemeden ve gömme hesaplanmadan önce yazıldı)

İkili ölçüt:
- **aynı bilgi:** İki soru aynı bilgiyi ölçüyor; birini bilen öteki de bilir.
- **farklı:** Değil.

## Çiftler

| Çift | Koşul | Soru A | A doğru cevap | Soru B | B doğru cevap | Kullanıcı etiketi |
|---|---|---|---|---|---|---|
| 1 | full | S1: Kemosentez yapan canlılar hangi tür enerji kaynağını kullanarak besin üretirler? | Kimyasal enerji | S2: Hidrotermal bacaların etrafında hangi canlılar kemosentez yaparak besin üretir? | Yengeçler | farklı |
| 2 | full | S1: Kemosentez yapan canlılar hangi tür enerji kaynağını kullanarak besin üretirler? | Kimyasal enerji | S3: Kemosentetik canlılar hangi enerji kaynağını kullanarak besin üretimi gerçekleştirir? | Kimyasal enerji | aynı bilgi |
| 3 | full | S1: Kemosentez yapan canlılar hangi tür enerji kaynağını kullanarak besin üretirler? | Kimyasal enerji | S4: Kemosentetik canlılar hangi enerji kaynağını kullanarak besin üretirler? | Kimyasal enerji | aynı bilgi |
| 4 | full | S2: Hidrotermal bacaların etrafında hangi canlılar kemosentez yaparak besin üretir? | Yengeçler | S3: Kemosentetik canlılar hangi enerji kaynağını kullanarak besin üretimi gerçekleştirir? | Kimyasal enerji | farklı |
| 5 | full | S2: Hidrotermal bacaların etrafında hangi canlılar kemosentez yaparak besin üretir? | Yengeçler | S4: Kemosentetik canlılar hangi enerji kaynağını kullanarak besin üretirler? | Kimyasal enerji | farklı |
| 6 | full | S3: Kemosentetik canlılar hangi enerji kaynağını kullanarak besin üretimi gerçekleştirir? | Kimyasal enerji | S4: Kemosentetik canlılar hangi enerji kaynağını kullanarak besin üretirler? | Kimyasal enerji | aynı bilgi |
| 7 | rag | S1: Kemosentez yapan canlılar hangi hücre yapısına sahiptir? | Prokaryot hücre yapısına | S2: Hidrotermal bacaların etrafında hangi tür canlılar yaşayabilir? | Kemosentetik canlılar | farklı |
| 8 | rag | S1: Kemosentez yapan canlılar hangi hücre yapısına sahiptir? | Prokaryot hücre yapısına | S3: Kemosentetik canlılar hangi tür hücre yapısına sahiptir? | Prokaryot | aynı bilgi |
| 9 | rag | S1: Kemosentez yapan canlılar hangi hücre yapısına sahiptir? | Prokaryot hücre yapısına | S4: Fotosentez ile kemosentez arasındaki temel fark nedir? | Fotosentezde güneş ışığı kullanılır, kemosentezde kimyasal enerji kullanılır. | farklı |
| 10 | rag | S1: Kemosentez yapan canlılar hangi hücre yapısına sahiptir? | Prokaryot hücre yapısına | S5: Kemosentez yapan canlıların hücre yapısı nedir? | Prokaryot hücre yapısına sahiptirler | aynı bilgi |
| 11 | rag | S2: Hidrotermal bacaların etrafında hangi tür canlılar yaşayabilir? | Kemosentetik canlılar | S3: Kemosentetik canlılar hangi tür hücre yapısına sahiptir? | Prokaryot | farklı |
| 12 | rag | S2: Hidrotermal bacaların etrafında hangi tür canlılar yaşayabilir? | Kemosentetik canlılar | S4: Fotosentez ile kemosentez arasındaki temel fark nedir? | Fotosentezde güneş ışığı kullanılır, kemosentezde kimyasal enerji kullanılır. | farklı |
| 13 | rag | S2: Hidrotermal bacaların etrafında hangi tür canlılar yaşayabilir? | Kemosentetik canlılar | S5: Kemosentez yapan canlıların hücre yapısı nedir? | Prokaryot hücre yapısına sahiptirler | farklı |
| 14 | rag | S3: Kemosentetik canlılar hangi tür hücre yapısına sahiptir? | Prokaryot | S4: Fotosentez ile kemosentez arasındaki temel fark nedir? | Fotosentezde güneş ışığı kullanılır, kemosentezde kimyasal enerji kullanılır. | farklı |
| 15 | rag | S3: Kemosentetik canlılar hangi tür hücre yapısına sahiptir? | Prokaryot | S5: Kemosentez yapan canlıların hücre yapısı nedir? | Prokaryot hücre yapısına sahiptirler | aynı bilgi |
| 16 | rag | S4: Fotosentez ile kemosentez arasındaki temel fark nedir? | Fotosentezde güneş ışığı kullanılır, kemosentezde kimyasal enerji kullanılır. | S5: Kemosentez yapan canlıların hücre yapısı nedir? | Prokaryot hücre yapısına sahiptirler | farklı |

Etiketler kullanıcı tarafından verildi. Etiketlerken her sorunun neyi sorduğunu özetleyen kısa açıklamalar kullanıldı; bu açıklamalar ayrı bir Claude oturumunda (claude.ai) hazırlandı.

## Ölçüm (31 Ekim 2026, etiketler commit'lendikten sonra)

- **Betik:** [asama-9-benzer-sorular-1.py](asama-9-benzer-sorular-1.py). Bir kez çalıştırıldı.
- **Hesaplama:** Gerçek BGE-M3 (`BAAI/bge-m3`) yerelde çalıştı; model (OpenAI) çağrısı yapılmadı.
- **İki skor:** Her çift için iki kosinüs benzerliği hesaplandı:
  - **(a) soru + doğru cevap:** similarity-v1'in gömdüğü metin.
  - **(b) yalnızca soru metni.**
- **Etiketler:** Yukarıdaki commit'li tablodan okundu.

### Betiğin çıktısı (olduğu gibi)

```
Gömme modeli: BAAI/bge-m3 · etiketli çift: 16

| Çift | Koşul | Sorular | (a) soru + doğru cevap | (b) yalnızca soru | Kullanıcı etiketi |
|---|---|---|---|---|---|
| 1 | full | S1–S2 | 0.6690 | 0.7710 | farklı |
| 2 | full | S1–S3 | 0.9507 | 0.9498 | aynı bilgi |
| 3 | full | S1–S4 | 0.9546 | 0.9524 | aynı bilgi |
| 4 | full | S2–S3 | 0.6348 | 0.7493 | farklı |
| 5 | full | S2–S4 | 0.6369 | 0.7497 | farklı |
| 6 | full | S3–S4 | 0.9942 | 0.9959 | aynı bilgi |
| 7 | rag | S1–S2 | 0.5791 | 0.4793 | farklı |
| 8 | rag | S1–S3 | 0.9140 | 0.9217 | aynı bilgi |
| 9 | rag | S1–S4 | 0.5842 | 0.7347 | farklı |
| 10 | rag | S1–S5 | 0.9623 | 0.9798 | aynı bilgi |
| 11 | rag | S2–S3 | 0.6471 | 0.4795 | farklı |
| 12 | rag | S2–S4 | 0.4684 | 0.3281 | farklı |
| 13 | rag | S2–S5 | 0.6002 | 0.4852 | farklı |
| 14 | rag | S3–S4 | 0.5414 | 0.6783 | farklı |
| 15 | rag | S3–S5 | 0.9066 | 0.9030 | aynı bilgi |
| 16 | rag | S4–S5 | 0.5880 | 0.7371 | farklı |

(a) soru + doğru cevap: 'aynı bilgi' en düşük = 0.9066 (6 çift) · 'farklı' en yüksek = 0.6690 (10 çift) · ayrışıyor mu: evet
(b) yalnızca soru: 'aynı bilgi' en düşük = 0.9030 (6 çift) · 'farklı' en yüksek = 0.7710 (10 çift) · ayrışıyor mu: evet
```

### Ayrışma

| Skor | "aynı bilgi" en düşük (6 çift) | "farklı" en yüksek (10 çift) | Ayrışıyor mu |
|---|---|---|---|
| (a) soru + doğru cevap | 0,9066 (çift 15) | 0,6690 (çift 1) | evet |
| (b) yalnızca soru | 0,9030 (çift 15) | 0,7710 (çift 1) | evet |

- **Eşik önerilmedi:** Eşik bu sayılar görüldükten sonra kullanıcıyla birlikte seçilecek.
- **Koddaki değer geçici:** Koddaki 0,90 değeri ölçümden önce yazıldı ve "geçici" olarak işaretli.

## Karar

Eşik 0,80 (soru + doğru cevap skoru). Bu 16 çiftte 'farklı' etiketlilerin en yüksek skoru 0,669, 'aynı bilgi' etiketlilerin en düşük skoru 0,907; eşik ikisinin arasından, iki tarafa pay bırakacak biçimde seçildi. Eşik aynı veride seçildiği için iyimser; pilot videolarda yeniden bakılacak. Kod soruları yalnızca işaretler, atmaz.

## Sınırlar

- Tek video, 16 çift, tek etiketleyen.
- Sorular bağımsız değil (aynı videodan, aynı konu listesinden).
- Eşik aynı veride seçilirse iyimser olur; pilot videolarda yeniden bakılacak.

