"use client";

import { useEffect, useRef, useState } from "react";
import {
  describeError,
  getQuestions,
  TOPIC_QUESTIONS_TIMEOUT_MS,
  type ContextMode,
  type QuestionsRequest,
  type QuestionsResponse,
} from "@/lib/api";
import QuestionCard from "./question-card";

type State =
  | { phase: "idle" }
  | { phase: "loading"; mode: GenerationMode }
  | { phase: "error"; title: string; detail: string | null }
  | { phase: "success"; result: QuestionsResponse };

/** Soru üretim biçimi. rag ve full ana deneydeki yoldur; baseline bugünkü (12d) istektir. */
type GenerationMode = "rag" | "full" | "baseline";

// Konu + Bloom yolunda konu sayısı. Backend Bloom düzeylerini kendisi eşleyecekse 6 konu ister
// (Bloom'un 6 düzeyi; deney tasarımı: video başına 6 soru).
const TOPIC_COUNT = 6;

const MODES: { value: GenerationMode; label: string; help: string }[] = [
  {
    value: "rag",
    label: "Konu + Bloom, RAG",
    help: "Videodan 6 konu çıkarılır, her konuya bir Bloom düzeyi atanır ve soru, konuya en ilgili transkript parçalarından üretilir.",
  },
  {
    value: "full",
    label: "Konu + Bloom, tam transkript",
    help: "Videodan 6 konu çıkarılır, her konuya bir Bloom düzeyi atanır ve soru, transkriptin tamamı verilerek üretilir.",
  },
  {
    value: "baseline",
    label: "Taban çizgisi (RAG'siz, Bloom'suz)",
    help: "Konu çıkarılmaz ve Bloom düzeyi verilmez; sorular transkriptin tamamından tek seferde üretilir.",
  },
];

const CONDITION_TEXT: Record<ContextMode, string> = { rag: "RAG", full: "Tam transkript" };

/** "6 konudan 5'i": sayıya Türkçe iyelik eki (kesme işaretiyle). */
function possessive(n: number): string {
  const last = n % 10;
  const tens = n % 100;
  let suffix: string;
  if (last !== 0) {
    suffix = ["", "i", "si", "ü", "ü", "i", "sı", "si", "i", "u"][last];
  } else {
    // 0: sıfırı, 10: onu, 20: yirmisi, 30: otuzu ...
    suffix = { 0: "ı", 10: "u", 20: "si", 30: "u", 40: "ı", 50: "si", 60: "ı", 70: "i", 80: "i", 90: "ı" }[tens] ?? "i";
  }
  return `${n}'${suffix}`;
}

/** Başarılı soru yanıtının listesi: özet satırı, soru kartları ve dürüstlük notu. */
export function QuestionList({ result }: { result: QuestionsResponse }) {
  // Destek kontrolü yalnızca o istekte açıldıysa yanıtta istem sürümü gelir
  const supportChecked = result.support_prompt_version !== undefined;
  // Koşul yalnızca Konu + Bloom yolunda gelir; taban çizgisinde bu satırlar hiç görünmez
  const condition = result.context_mode;
  // Konu başına en çok bir soru: dönen soru sayısı, soru üretilen konu sayısıdır
  const missingTopics = condition ? result.requested_count - result.returned_count : 0;
  return (
    <div className="question-list">
      {condition && (
        <p className="meta condition-line">
          <strong>
            {CONDITION_TEXT[condition] ?? condition} · {result.prompt_version}
          </strong>{" "}
          · {result.requested_count} konudan {possessive(result.returned_count)} için soru üretildi
        </p>
      )}
      <p className={condition ? "meta meta-follow" : "meta"}>
        {result.returned_count} soru (istenen {result.requested_count}) · Kaynağı doğrulanan {result.verified_count} ·
        İstem: {result.prompt_version} · Model: {result.model}
        {supportChecked && <> · Destek kontrolü: {result.support_prompt_version}</>}
      </p>
      {missingTopics > 0 && (
        <p className="topic-gap-note">
          Bazı konular için kullanılabilir soru çıkmadı (model soru üretmedi, geçersiz soru üretti ya da soru başka bir
          konunun tekrarı olarak atıldı); bu durum değerlendirmede kabul edilemez sayılır.
        </p>
      )}
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
        {condition && (
          <> Bloom etiketi sorunun hedeflendiği düzeydir; sorunun gerçekten bu düzeyde olduğu ölçülmedi.</>
        )}
        {supportChecked && (
          <> Destek kontrolü bir model değerlendirmesidir ve yanılabilir; sorunun doğruluğunu garanti etmez.</>
        )}
      </p>
    </div>
  );
}

/** Özet kartının altındaki "Soruları üret" düğmesi, üretim biçimi seçimi ve soru listesi.
 *  Özetten ayrı bir istektir: ikisi de OpenAI'ya gider ve ücretlidir. */
export default function QuestionsSection({ url }: { url: string }) {
  const [state, setState] = useState<State>({ phase: "idle" });
  // Varsayılan: ana deneydeki RAG koşulu
  const [mode, setMode] = useState<GenerationMode>("rag");
  // Varsayılan kapalı: açıkken soru sayısı kadar ek, ücretli model çağrısı yapılır
  const [checkSupport, setCheckSupport] = useState(false);
  const controllerRef = useRef<AbortController | null>(null);

  // Bölüm kapanırsa (ör. yeni özet istenirse) süren isteği iptal et
  useEffect(() => () => controllerRef.current?.abort(), []);

  const loading = state.phase === "loading";
  const selected = MODES.find((m) => m.value === mode) ?? MODES[0];

  async function generate() {
    if (loading) return;
    controllerRef.current?.abort();
    const controller = new AbortController();
    controllerRef.current = controller;
    setState({ phase: "loading", mode }); // eski sorular ve hata ekrandan kalkar

    try {
      // Taban çizgisinde istek 12d/12e ile birebir aynı: context_mode ve count gönderilmez.
      // prompt_version hiç gönderilmez; backend varsayılanı (questions-v3) kullanılır.
      const request: QuestionsRequest =
        mode === "baseline" ? { url } : { url, context_mode: mode, count: TOPIC_COUNT };
      // Destek kontrolü kapalıyken alan hiç gönderilmez
      if (checkSupport) request.check_support = true;
      const options =
        mode === "baseline"
          ? { signal: controller.signal }
          : { signal: controller.signal, timeoutMs: TOPIC_QUESTIONS_TIMEOUT_MS };
      const result = await getQuestions(request, options);
      setState({ phase: "success", result });
    } catch (err) {
      if (controller.signal.aborted) return;
      setState({ phase: "error", ...describeError(err) });
    }
  }

  return (
    <section className="questions" aria-labelledby="questions-title">
      <h2 id="questions-title">Alıştırma soruları</h2>
      <div className="question-controls">
        <button type="button" className="primary" onClick={generate} disabled={loading}>
          {loading ? "Sorular hazırlanıyor..." : state.phase === "success" ? "Yeniden soru üret" : "Soruları üret"}
        </button>
        <fieldset className="mode-select" disabled={loading /* istek sürerken değiştirilemez */}>
          <legend>Üretim biçimi</legend>
          {MODES.map((m) => (
            <label key={m.value} className="mode-option">
              <input
                type="radio"
                name="generation-mode"
                value={m.value}
                checked={mode === m.value}
                onChange={() => setMode(m.value)}
              />{" "}
              {m.label}
            </label>
          ))}
        </fieldset>
        <label className="support-toggle">
          <input
            type="checkbox"
            checked={checkSupport}
            onChange={(e) => setCheckSupport(e.target.checked)}
            disabled={loading} // istek sürerken değiştirilemez
          />{" "}
          Alıntı-cevap destek kontrolünü de çalıştır (soru sayısı kadar ek model çağrısı yapar)
        </label>
      </div>
      <p className="mode-help">{selected.help}</p>

      <div aria-live="polite">
        {state.phase === "loading" &&
          (state.mode === "baseline" ? (
            <p className="muted">Sorular hazırlanıyor... Video uzunsa bu birkaç dakika sürebilir.</p>
          ) : (
            <p className="muted">
              Konular çıkarılıyor ve her konu için ayrı soru üretiliyor... Bu, taban çizgisinden uzun sürer. Sunucu
              açıldıktan sonraki ilk istekte BGE-M3 gömme modeli yüklendiği için yaklaşık 1 dakika daha sürebilir.
            </p>
          ))}

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
