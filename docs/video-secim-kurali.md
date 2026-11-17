# Ana deney videolarının seçim kuralı

Bu kural, videolar seçilmeden önce yazılıp depoya eklenmiştir (Hafta-3 geri bildirimi). Kural sonradan değiştirilirse değişiklik tarihiyle ve gerekçesiyle bu dosyanın sonuna eklenir; önceki metin silinmez.

## 1. Kapsam

- Altı alan: biyoloji, tarih, matematik, İngilizce, edebiyat, Python programlama.
- Her alandan iki video, toplam 12 video.
- Pilot videolar (docs/bulgular/pilot-1) ve pilot kanalları (BETÜL BİYOLOJİ, Ardıç Tarih, Partikül Matematik, Ms. Jasmin ELT, tonguç 10. SINIF, Fehmi UYAR) kullanılmaz. Gerekçe: ana deney istemi pilot videolardaki sonuçlara bakılarak seçildi; aynı videolar eğitim–test ayrımını bozar.
- Alan kodları (adaylar.csv'nin alan sütununda ve seçim tohumunda kullanılır): biyoloji, tarih, matematik, ingilizce, edebiyat, python.

## 2. Arama

Arama, oturum açılmamış bir gizli tarayıcı penceresinde, YouTube'un varsayılan sıralamasıyla yapılır. Aramanın tarihi ve saati kaydedilir.

Arama 1. bölümdeki alan sırasıyla yapılır.

Arama ifadeleri:

| Alan | Arama ifadesi | Yedek ifade |
|---|---|---|
| Biyoloji | biyoloji konu anlatımı | lise biyoloji ders |
| Tarih | tarih konu anlatımı | lise tarih ders |
| Matematik | matematik konu anlatımı | lise matematik ders |
| İngilizce | ingilizce gramer konu anlatımı | ingilizce dersi türkçe anlatım |
| Edebiyat | edebiyat konu anlatımı | lise edebiyat ders |
| Python programlama | python dersleri | python programlama ders |

Sonuçlar sırayla incelenir. Kısa videolar (Shorts) bölümü, oynatma listeleri ve kanal sonuçları atlanır.

İlk 50 sonuçta beş uygun aday çıkmazsa aynı işlem yedek ifadeyle sürdürülür.

## 3. Uygunluk ölçütleri

Bir video aşağıdakilerin hepsini karşılıyorsa aday olur:

1. Anlatım Türkçedir. İngilizce videolarda anlatım Türkçe ağırlıklıdır.
2. Türkçe altyazı vardır (elle hazırlanmış ya da otomatik).
3. Süre 10–35 dakikadır. Süre olarak YouTube'da görünen süre (adaylar.csv'deki sure_dk_sn) esas alınır.
4. Lise ya da üniversite düzeyinde, tek bir konuyu anlatan bir derstir. Kısa video, canlı yayın kaydı, soru çözüm derlemesi ya da birden çok dersin birleşimi değildir.
5. Anlatım konuşmaya dayanır: ilk iki dakikada anlatıcı konuyu sözle anlatmaktadır. Yalnızca yazı, slayt ya da müzik olan videolar alınmaz.
6. Video herkese açıktır.
7. Kanal pilot kanallarından biri değildir. Bir kanaldan bütün listede en çok bir aday alınır; kanal birden çok alanda çıkarsa 1. bölümdeki alan sırasına göre ilk alana aday olur, sonraki alanlarda bu ölçütle elenir.

Her alan için uygun ilk beş video aday listesine alınır. İncelenip elenen videolar da gerekçesiyle (ölçüt numarası) listeye yazılır.

## 4. Aday listesinin kaydı

Aday listesi docs/bulgular/video-secimi/adaylar.csv dosyasına yazılır ve seçim betiği çalıştırılmadan önce depoya eklenir. Sütunlar: alan, arama_ifadesi, arama_tarihi, sira (arama sonucundaki sırası), baslik, kanal, url, sure_dk_sn, durum (aday / elendi), elenme_olcutu, not.

## 5. Seçim

- Seçim betiği (docs/bulgular/video-secimi/secim.py) yalnızca adaylar.csv'deki adaylarla çalışır. Her adayın altyazısını bir kez alıp önbelleğe yazar ve altyazı türünü (elle / otomatik) belirler.
- Betik, altyazısı alınamayan ya da süresi 10–35 dakika dışında kalan adayı gerekçesiyle eler.
- Her alanda kalan adaylar `random.Random("20261110-<alan kodu>")` ile karıştırılır. Ardından elle hazırlanmış altyazısı olan adaylar, kendi aralarındaki sıra korunarak öne alınır.
- Sıradaki ilk aday o alanın "birinci videosu", ikinci aday "ikinci videosu" olur.
- Sonuç docs/bulgular/video-secimi/secim.md ve secim.json dosyalarına yazılır.

## 6. Yedek planlar

- Zaman yetmezse değerlendirme kümesi, her alanın birinci videosundan oluşan altı videoya (72 soru) indirilir.
- Seçilen bir video sonradan işlenemezse (altyazı alınamaz, video kaldırılır) o alanın sıradaki adayı alınır. Değişiklik gerekçesiyle secim.md'ye eklenir.

## 7. Kaydedilen değişkenler

Her video için: alan, başlık, kanal, bağlantı, süre, altyazı türü (elle / otomatik), iki dilli mi (İngilizce alanının videoları evet), kelime sayısı, parça sayısı. Altyazı türü ve iki dilli olma analizde değişken olarak kullanılır.

## 8. Sıra

1. Bu kural depoya eklenir.
2. Arama yapılır ve adaylar.csv depoya eklenir.
3. Seçim betiği çalıştırılır ve sonuç depoya eklenir.

## Değişiklikler

- 2026-11-14 (aday kaydı başlamadan önce): İlk aramada sonuçların üst kısmının oynatma listesi, kurs ve kanal sonuçlarından oluştuğu görüldü. Netleştirme: (1) Arama yapıldıktan sonra YouTube'un "Filtreler → Tür: Video" seçeneği kullanılır; sıralama varsayılan kalır. Bu, 2. bölümdeki "oynatma listeleri ve kanal sonuçları atlanır" kuralının uygulanma biçimidir. (2) "İlk 50 sonuç" yalnızca tekil videoları sayar; reklamlar ve Shorts sayılmaz.
- 2026-11-14 (aday kaydı başlamadan önce): YouTube'un aynı aramada sonuç sırasını değiştirdiği görüldü (15:24'teki aramanın sonuçları filtre penceresi açılınca değişti). Netleştirme: (1) Her alan için arama yeni bir gizli pencerede yapılır ve "Tür: Video" filtresi uygulanır. (2) Hiçbir videoya tıklamadan, ilk 50 tekil video sonucunun ekran görüntüleri alınır ve arama saati kaydedilir. (3) Değerlendirme bu ekran görüntülerindeki sıraya göre yapılır; videolar ölçüt kontrolü için ayrı sekmede açılır. (4) Ekran görüntüleri docs/bulgular/video-secimi/ekran-goruntuleri/<alan kodu>/ klasörüne konur ve adaylar.csv ile birlikte depoya eklenir.
- 2026-11-17 (aday kaydı sırasında yapılan netleştirmeler; adaylar.csv ile aynı commit'te eklendi):
  (1) Ölçüt 4: Bir ünitenin ya da konunun ilk kez anlatıldığı konu anlatımı videoları aday olur; birden çok üniteyi kapsayan ya da konuları tekrar eden videolar (tam/genel/son tekrar, yazılıya hazırlık, soru çözümü, özet derlemesi) elenir.
  (2) Arama yöntemi: Biyoloji ana araması kullanıcı tarafından gizli pencerede yapıldı (2026-11-14 15:36, ekran görüntüleri ekran-goruntuleri/biyoloji/). Biyoloji yedek araması ve diğer beş alanın aramaları Claude tarafından Claude in Chrome ile yapıldı; kullanıcının tarayıcısında YouTube oturumu açık olduğu için istekler çerez gönderilmeden (oturumsuz ziyaretçi olarak) atıldı. Filtre Tür: Video, sıralama varsayılan, hl=tr, gl=TR; ilk 50 tekil video alındı. Bu aramalarda ekran görüntüsü yerine ham sonuçlar arama-sonuclari.json dosyasında saklanır.
  (3) Ölçüt 1, 2 ve 5: Claude'un incelediği adaylarda YouTube'un altyazı listesine bakıldı. Türkçe otomatik altyazının bulunması, anlatımın Türkçe ve konuşmaya dayalı olduğunu gösterir (otomatik altyazı konuşmadan üretilir). Biyoloji ana aramasının adaylarını kullanıcı videoyu açarak kontrol etti.
  (4) Yedek ifadeyle de beş aday çıkmazsa bulunan adaylarla devam edilir. Matematikte iki aramada toplam iki aday çıktı (sonuçların çoğu ilkokul/ortaokul düzeyinde ya da soru çözümüydü); ikisi de seçilir, bu alanda yedek video yoktur.
  (5) "tonguç 9. SINIF" pilot kanalı değildir (pilot kanal "tonguç 10. SINIF").
  (6) adaylar.csv'ye her aramanın, alandaki beşinci adaya kadar olan sonuçları yazıldı; beş aday çıkmayan aramalarda 50 sonucun tamamı yazıldı.
