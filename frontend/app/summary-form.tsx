"use client";

import { type FormEvent, useEffect, useRef, useState } from "react";
import { describeError, getSummary, type SummaryResponse } from "@/lib/api";
import { validateYouTubeUrl } from "@/lib/youtube";
import QuestionsSection from "./questions-section";
import SummaryResult from "./summary-result";

type State =
  | { phase: "idle" }
  | { phase: "loading" }
  | { phase: "error"; title: string; detail: string | null }
  // url: özeti çıkarılan bağlantı; sorular da bununla istenir (kutu sonradan değişse bile)
  | { phase: "success"; result: SummaryResponse; url: string };

export default function SummaryForm() {
  const [url, setUrl] = useState("");
  const [fieldError, setFieldError] = useState<string | null>(null);
  const [state, setState] = useState<State>({ phase: "idle" });
  const controllerRef = useRef<AbortController | null>(null);

  // Sayfadan çıkılırsa süren isteği iptal et
  useEffect(() => () => controllerRef.current?.abort(), []);

  const loading = state.phase === "loading";

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (loading) return;

    const problem = validateYouTubeUrl(url);
    setFieldError(problem);
    if (problem) return; // geçersiz bağlantıyla istek gönderilmez

    controllerRef.current?.abort();
    const controller = new AbortController();
    controllerRef.current = controller;
    setState({ phase: "loading" });

    try {
      const requestedUrl = url.trim();
      const result = await getSummary({ url: requestedUrl }, { signal: controller.signal });
      setState({ phase: "success", result, url: requestedUrl });
    } catch (err) {
      if (controller.signal.aborted) return; // iptal edilen istek ekranı değiştirmesin
      setState({ phase: "error", ...describeError(err) });
    }
  }

  return (
    <section className="summary">
      <form onSubmit={handleSubmit} noValidate>
        <label htmlFor="video-url">YouTube video bağlantısı</label>
        <div className="row">
          <input
            id="video-url"
            type="url"
            inputMode="url"
            placeholder="https://www.youtube.com/watch?v=..."
            value={url}
            onChange={(e) => {
              setUrl(e.target.value);
              if (fieldError) setFieldError(null); // yazmaya başlayınca uyarı kalksın
            }}
            readOnly={loading}
            aria-invalid={fieldError ? true : undefined}
            aria-describedby={fieldError ? "video-url-error" : undefined}
            autoComplete="off"
          />
          <button type="submit" disabled={loading}>
            {loading ? "Özet hazırlanıyor..." : "Özet çıkar"}
          </button>
        </div>
        {fieldError && (
          <p id="video-url-error" className="field-error" role="alert">
            {fieldError}
          </p>
        )}
      </form>

      <div aria-live="polite">
        {loading && <p className="muted">Özet hazırlanıyor... Video uzunsa bu birkaç dakika sürebilir.</p>}

        {state.phase === "error" && (
          <div className="alert" role="alert">
            <strong>{state.title}</strong>
            {state.detail && <p>{state.detail}</p>}
          </div>
        )}

        {state.phase === "success" && (
          <>
            <SummaryResult result={state.result} />
            {/* Yeni özet istenince bu bölüm kaldırılır, eski sorular da gider */}
            <QuestionsSection url={state.url} />
          </>
        )}
      </div>
    </section>
  );
}
