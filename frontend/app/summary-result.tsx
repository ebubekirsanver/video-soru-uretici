import type { SummaryResponse } from "@/lib/api";
import { formatTimestamp, youtubeTimeUrl } from "@/lib/format";

const MODE_LABELS: Record<SummaryResponse["transcript_mode"], string> = {
  clean: "temiz",
  raw: "ham",
};

/** Başarılı özet yanıtını okunaklı bir kart olarak gösterir. */
export default function SummaryResult({ result }: { result: SummaryResponse }) {
  // Model özeti 1-2 paragraf yazar; boş satırlardan bölünür
  const paragraphs = result.summary
    .split(/\n\s*\n/)
    .map((p) => p.trim())
    .filter(Boolean);

  return (
    <article className="result-card" aria-labelledby="result-title">
      <p className="meta">
        Video: <code>{result.video_id}</code> · Dil: {result.language} · Model: {result.model} · Transkript:{" "}
        {MODE_LABELS[result.transcript_mode]}
      </p>

      <h2 id="result-title">Özet</h2>
      {paragraphs.map((p, i) => (
        <p key={i} className="summary-text">
          {p}
        </p>
      ))}

      <h2>Konu başlıkları</h2>
      {result.topics.length === 0 ? (
        <p className="muted">Konu başlığı bulunamadı.</p>
      ) : (
        <ol className="topics">
          {result.topics.map((topic, i) => (
            <li key={`${topic.start_seconds}-${i}`}>
              <a
                href={youtubeTimeUrl(result.video_id, topic.start_seconds)}
                target="_blank"
                rel="noopener noreferrer"
                title="Videoyu bu saniyeden yeni sekmede aç"
              >
                <span className="time">
                  {formatTimestamp(topic.start_seconds)}
                  {!topic.start_verified && (
                    <span className="time-unverified" title="Bu zaman, isteme verilen blok etiketlerinden biri değil">
                      {" "}
                      (doğrulanamadı)
                    </span>
                  )}
                </span>
                <span className="topic-title">{topic.title}</span>
              </a>
            </li>
          ))}
        </ol>
      )}
      <p className="note">
        Konu zamanları modelin verdiği değerlerdir. Yalnızca verilen blok etiketlerinden biri olup olmadığı denetlenir;
        konunun videoda gerçekten o anda başladığı doğrulanmamıştır. “(doğrulanamadı)” işareti, modelin verdiği zamanın
        bu blok etiketlerinden biri olmadığını gösterir.
      </p>
    </article>
  );
}
