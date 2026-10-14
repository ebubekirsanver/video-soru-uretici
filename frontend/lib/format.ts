// Zaman ve bağlantı biçimlendirme yardımcıları (özet ekranı ve 12d'deki soru ekranı kullanır).

/** Saniyeyi dakika:saniye biçimine çevirir (591,2 → "9:51"); bir saatten uzunsa saat:dakika:saniye.
 *  Saniye aşağı yuvarlanır, YouTube'un gösterdiği gibi. Geçersiz ya da negatif değer "0:00" olur. */
export function formatTimestamp(seconds: number): string {
  const total = Number.isFinite(seconds) && seconds > 0 ? Math.floor(seconds) : 0;
  const h = Math.floor(total / 3600);
  const m = Math.floor((total % 3600) / 60);
  const s = String(total % 60).padStart(2, "0");
  return h > 0 ? `${h}:${String(m).padStart(2, "0")}:${s}` : `${m}:${s}`;
}

/** Videoyu verilen saniyeden açan bağlantı: https://youtu.be/<video_id>?t=<saniye> */
export function youtubeTimeUrl(videoId: string, seconds: number): string {
  const t = Number.isFinite(seconds) && seconds > 0 ? Math.floor(seconds) : 0;
  return `https://youtu.be/${encodeURIComponent(videoId)}?t=${t}`;
}
