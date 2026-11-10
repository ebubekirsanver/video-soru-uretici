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
