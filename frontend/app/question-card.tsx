"use client";

import { useState } from "react";
import type { QuestionOut } from "@/lib/api";
import { formatTimestamp, youtubeTimeUrl } from "@/lib/format";

const LETTERS = ["A", "B", "C", "D"];

interface ViewProps {
  question: QuestionOut;
  index: number; // 1'den başlayan soru sırası
  videoId: string;
  selected: number | null; // seçilen seçenek; null ise cevap henüz açılmadı
  onSelect?: (option: number) => void;
}

/** Durum tutmayan görünüm: aynı soru, seçim yapılmadan ve yapıldıktan sonra farklı görünür. */
export function QuestionView({ question: q, index, videoId, selected, onSelect }: ViewProps) {
  const answered = selected !== null;
  const correct = answered && selected === q.correct_index;

  return (
    <article className={`question-card${q.verified ? "" : " unverified"}`} aria-labelledby={`q${index}`}>
      <header className="question-head">
        <span className="question-no">Soru {index}</span>
        {!q.verified && <span className="badge-unverified">Kaynak doğrulanamadı</span>}
      </header>
      <p id={`q${index}`} className="question-text">
        {q.question}
      </p>

      <ol className="options">
        {q.options.map((option, i) => {
          // Doğru cevap yalnızca bir seçenek seçildikten sonra işaretlenir
          const state = !answered ? "" : i === q.correct_index ? " is-correct" : i === selected ? " is-wrong" : "";
          return (
            <li key={i}>
              <button
                type="button"
                className={`option${state}`}
                onClick={() => onSelect?.(i)}
                disabled={answered}
                aria-pressed={answered ? i === selected : undefined}
              >
                <span className="letter">{LETTERS[i] ?? i + 1}</span>
                <span className="option-text">{option}</span>
                {answered && i === q.correct_index && <span className="mark">✓ Doğru cevap</span>}
                {answered && i === selected && i !== q.correct_index && <span className="mark">✗ Senin cevabın</span>}
              </button>
            </li>
          );
        })}
      </ol>

      {answered && (
        <div className="reveal" aria-live="polite">
          <p className={`verdict ${correct ? "verdict-ok" : "verdict-wrong"}`}>
            {correct ? "Doğru!" : `Yanlış. Doğru cevap: ${LETTERS[q.correct_index] ?? q.correct_index + 1}`}
          </p>
          {q.explanation && <p className="explanation">{q.explanation}</p>}

          <div className="source">
            <p className="source-status">
              {q.verified
                ? q.quote_match === "trimmed"
                  ? "Alıntı transkriptte bulundu (kenarındaki birkaç sözcük atılarak)."
                  : "Alıntı transkriptte bulundu."
                : "Alıntı transkriptte bulunamadı."}
            </p>
            <blockquote>{q.source_quote}</blockquote>
            <p className="source-time">
              Kaynak süresi:{" "}
              {q.source_start_seconds !== null ? (
                <a
                  href={youtubeTimeUrl(videoId, q.source_start_seconds)}
                  target="_blank"
                  rel="noopener noreferrer"
                  title="Videoyu bu saniyeden yeni sekmede aç"
                >
                  {formatTimestamp(q.source_start_seconds)}
                </a>
              ) : (
                <span className="muted">yok (alıntı bulunamadığı için)</span>
              )}
            </p>
          </div>
        </div>
      )}
    </article>
  );
}

/** Seçimi tutan kart: bir seçenek seçilince cevap açılır ve değiştirilemez. */
export default function QuestionCard(props: Omit<ViewProps, "selected" | "onSelect">) {
  const [selected, setSelected] = useState<number | null>(null);
  return <QuestionView {...props} selected={selected} onSelect={(i) => setSelected((prev) => prev ?? i)} />;
}
