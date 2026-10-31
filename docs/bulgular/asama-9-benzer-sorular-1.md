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
