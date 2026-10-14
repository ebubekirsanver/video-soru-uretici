"use client";

import { useEffect, useRef, useState } from "react";
import { describeError, getQuestions, type QuestionsResponse } from "@/lib/api";
import QuestionCard from "./question-card";

type State =
  | { phase: "idle" }
  | { phase: "loading" }
  | { phase: "error"; title: string; detail: string | null }
  | { phase: "success"; result: QuestionsResponse };

/** Başarılı soru yanıtının listesi: özet satırı, soru kartları ve dürüstlük notu. */
export function QuestionList({ result }: { result: QuestionsResponse }) {
  return (
    <div className="question-list">
      <p className="meta">
        {result.returned_count} soru (istenen {result.requested_count}) · Kaynağı doğrulanan {result.verified_count} ·
        İstem: {result.prompt_version} · Model: {result.model}
      </p>
      {result.questions.length === 0 ? (
        <p className="muted">Model kullanılabilir soru üretemedi.</p>
      ) : (
        result.questions.map((q, i) => (
          <QuestionCard key={`${result.video_id}-${i}`} question={q} index={i + 1} videoId={result.video_id} />
        ))
      )}
      <p className="note">
        “Alıntı transkriptte bulundu” yalnızca sorunun dayandığı alıntının videonun transkriptinde geçtiğini gösterir;
        sorunun ya da cevabın doğru olduğunu garanti etmez. Kaynak süresi alıntının başladığı altyazı satırının
        başıdır, cümle birkaç saniye sonra başlayabilir.
      </p>
    </div>
  );
}

/** Özet kartının altındaki "Soruları üret" düğmesi ve soru listesi.
 *  Özetten ayrı bir istektir: ikisi de OpenAI'ya gider ve ücretlidir. */
export default function QuestionsSection({ url }: { url: string }) {
  const [state, setState] = useState<State>({ phase: "idle" });
  const controllerRef = useRef<AbortController | null>(null);

  // Bölüm kapanırsa (ör. yeni özet istenirse) süren isteği iptal et
  useEffect(() => () => controllerRef.current?.abort(), []);

  const loading = state.phase === "loading";

  async function generate() {
    if (loading) return;
    controllerRef.current?.abort();
    const controller = new AbortController();
    controllerRef.current = controller;
    setState({ phase: "loading" }); // eski sorular ve hata ekrandan kalkar

    try {
      const result = await getQuestions({ url }, { signal: controller.signal });
      setState({ phase: "success", result });
    } catch (err) {
      if (controller.signal.aborted) return;
      setState({ phase: "error", ...describeError(err) });
    }
  }

  return (
    <section className="questions" aria-labelledby="questions-title">
      <h2 id="questions-title">Alıştırma soruları</h2>
      <button type="button" className="primary" onClick={generate} disabled={loading}>
        {loading ? "Sorular hazırlanıyor..." : state.phase === "success" ? "Yeniden soru üret" : "Soruları üret"}
      </button>

      <div aria-live="polite">
        {loading && <p className="muted">Sorular hazırlanıyor... Video uzunsa bu birkaç dakika sürebilir.</p>}

        {state.phase === "error" && (
          <div className="alert" role="alert">
            <strong>{state.title}</strong>
            {state.detail && <p>{state.detail}</p>}
          </div>
        )}

        {state.phase === "success" && <QuestionList result={state.result} />}
      </div>
    </section>
  );
}
