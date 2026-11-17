// Backend ile konuşan istek kodu. Bileşenler fetch'i doğrudan kullanmaz,
// buradaki fonksiyonları çağırır (12c ve 12d de aynı dosyayı kullanacak).
// Türler backend/app/schemas.py ile birebir aynıdır; orası değişirse burası da güncellenmeli.

import { API_URL } from "./config";

export type TranscriptMode = "clean" | "raw";

export interface SummaryRequest {
  url: string;
  transcript_mode?: TranscriptMode; // backend varsayılanı "clean"
}

export interface SummaryTopic {
  title: string;
  start_seconds: number; // modelin verdiği değer
  // true: değer isteme verilen blok etiketlerinden biri. Konunun videoda
  // gerçekten o anda başladığını göstermez.
  start_verified: boolean;
}

export interface SummaryResponse {
  video_id: string;
  language: string;
  transcript_mode: TranscriptMode;
  model: string;
  summary: string;
  topics: SummaryTopic[];
}

/** AS1 koşulu. rag: konu için erişilen transkript parçaları; full: transkriptin tamamı. */
export type ContextMode = "full" | "rag";

export interface QuestionsRequest {
  url: string;
  // 1-20, backend varsayılanı 5. context_mode ile konu sayısıdır; Bloom eşlemesi
  // otomatik yapılacaksa 6 olmalı (backend bloom_levels verilmezse 6 konu ister)
  count?: number;
  transcript_mode?: TranscriptMode; // backend varsayılanı "clean"; rag yalnızca "clean" ile
  // true ise her doğrulanmış soru için ayrı bir (ücretli) model çağrısıyla alıntının
  // doğru cevabı destekleyip desteklemediği sorulur; backend varsayılanı false
  check_support?: boolean;
  // Verilirse konu çıkarma + konu başına bir soru (Bloom yönlendirmeli istem, backend
  // varsayılanı questions-v3). Verilmezse taban çizgisi (questions-v1).
  context_mode?: ContextMode;
}

/** destekliyor / kısmen / desteklemiyor: modelin değerlendirmesi.
 *  kontrol edilmedi: alıntı transkriptte bulunamadığı için çağrı yapılmadı.
 *  kontrol edilemedi: çağrı başarısız oldu ya da model geçersiz yanıt verdi. */
export type SupportLabel = "destekliyor" | "kısmen" | "desteklemiyor" | "kontrol edilmedi" | "kontrol edilemedi";

/** Alıntı-cevap destek kontrolü. Bir model değerlendirmesidir; kesin doğru değildir. */
export interface SupportOut {
  label: SupportLabel;
  reason: string; // en fazla bir cümlelik gerekçe
}

export interface QuestionOut {
  question: string;
  options: string[]; // 4 seçenek
  correct_index: number; // 0-3
  explanation: string;
  // Doğrulandıysa transkriptteki metin; doğrulanamadıysa modelin yazdığı alıntı
  source_quote: string;
  // Alıntının başladığı transkript satırının (segment) başlangıcı; doğrulanamadıysa null
  source_start_seconds: number | null;
  verified: boolean; // alıntı transkriptte bulundu mu (sorunun doğruluğunu göstermez)
  quote_match: "exact" | "trimmed" | null;
  // Yalnızca check_support=true iken gelir; kapalıyken anahtar yanıtta hiç yoktur
  support?: SupportOut;
  // Yalnızca context_mode ile gelir (taban çizgisinde anahtar yoktur).
  // topic: sorunun üretildiği konu, çoğunlukla "Başlık: açıklama" biçiminde.
  topic?: string | null;
  // Hedef Bloom düzeyi: sorunun istemde hedeflendiği düzeydir; sorunun gerçekten
  // bu düzeyde olduğu iddia edilmez.
  bloom_level?: string | null;
}

export interface QuestionsResponse {
  video_id: string;
  transcript_mode: TranscriptMode;
  model: string;
  prompt_version: string; // taban çizgisinde questions-v1, context_mode ile questions-v3 (varsayılan)
  // context_mode ile istenen konu sayısı; taban çizgisinde istenen soru sayısı
  requested_count: number;
  returned_count: number;
  verified_count: number;
  questions: QuestionOut[];
  // Yalnızca context_mode verildiyse gelir (AS1 koşulu)
  context_mode?: ContextMode;
  // Yalnızca check_support=true iken gelir: destek kontrolünde kullanılan istem sürümü
  support_prompt_version?: string;
}

/** Hatanın türü: arayüz her birine ayrı, sade bir Türkçe mesaj gösterir. */
export type ApiErrorKind =
  | "invalid_url" // 422: backend bağlantıyı geçersiz buldu
  | "invalid_request" // 422: istek gövdesi şemaya uymadı (doğrulama listesi)
  | "transcript_unavailable" // 404: altyazı yok / kapalı / video erişilemiyor / temizlikten sonra boş
  | "llm_not_configured" // 503: sunucuda OpenAI API anahtarı tanımlı değil
  | "youtube_blocked" // 503: YouTube bu ağdan gelen istekleri engelledi
  | "llm_failed" // 502: OpenAI çağrısı başarısız ya da yanıt bozuk
  | "server" // diğer HTTP hataları (ör. 500)
  | "network" // sunucuya hiç ulaşılamadı (kapalı, yanlış adres ya da CORS)
  | "timeout"; // sunucu belirlenen sürede yanıt vermedi

export class ApiError extends Error {
  kind: ApiErrorKind;
  status: number | null;
  detail: string | null; // backend'in verdiği ham mesaj (varsa)

  constructor(kind: ApiErrorKind, status: number | null, detail: string | null) {
    super(detail ?? kind);
    this.name = "ApiError";
    this.kind = kind;
    this.status = status;
    this.detail = detail;
  }
}

// Özet ve soru üretimi, uzun videolarda LLM yüzünden onlarca saniye sürebilir
const DEFAULT_TIMEOUT_MS = 180_000;
// Konu + Bloom soru üretimi: konu çıkarma, konu başına bir model çağrısı ve ilk istekte
// BGE-M3 gömme modelinin yüklenmesi (yaklaşık 1 dakika) nedeniyle daha uzun sürer
export const TOPIC_QUESTIONS_TIMEOUT_MS = 300_000;

interface RequestOptions {
  signal?: AbortSignal; // bileşen kapanınca isteği iptal etmek için
  timeoutMs?: number;
}

/** FastAPI hata gövdesinden okunabilir metni çıkarır: {"detail": "..."} ya da {"detail": [{msg}, ...]}. */
function readDetail(body: unknown): string | null {
  if (!body || typeof body !== "object" || !("detail" in body)) return null;
  const detail = (body as { detail: unknown }).detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    const messages = detail
      .map((d) => (d && typeof d === "object" && "msg" in d ? String((d as { msg: unknown }).msg) : null))
      .filter((m): m is string => Boolean(m));
    return messages.length ? messages.join("; ") : null;
  }
  return null;
}

function kindForStatus(status: number, body: unknown): ApiErrorKind {
  if (status === 422) {
    // Bağlantı hatası metin, şema hatası liste olarak gelir
    const isList = Boolean(body && typeof body === "object" && Array.isArray((body as { detail?: unknown }).detail));
    return isList ? "invalid_request" : "invalid_url";
  }
  if (status === 404) return "transcript_unavailable";
  if (status === 503) {
    // Hata türü yalnızca çalıştırma kaydında; API yanıtında ayırt edici olan mesajın kendisi
    const detail = readDetail(body);
    return detail?.includes("YouTube") && detail.includes("engelledi") ? "youtube_blocked" : "llm_not_configured";
  }
  if (status === 502) return "llm_failed";
  return "server";
}

async function postJson<T>(path: string, payload: unknown, options: RequestOptions = {}): Promise<T> {
  const timeout = AbortSignal.timeout(options.timeoutMs ?? DEFAULT_TIMEOUT_MS);
  const signal = options.signal ? AbortSignal.any([options.signal, timeout]) : timeout;

  let res: Response;
  try {
    res = await fetch(`${API_URL}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal,
    });
  } catch (err) {
    // Kullanıcı ya da bileşen iptal ettiyse hatayı olduğu gibi ilet
    if (options.signal?.aborted) throw err;
    if (timeout.aborted) throw new ApiError("timeout", null, null);
    throw new ApiError("network", null, null);
  }

  let body: unknown = null;
  try {
    body = await res.json();
  } catch {
    body = null; // JSON olmayan yanıt (ör. vekil sunucu hata sayfası)
  }

  if (!res.ok) throw new ApiError(kindForStatus(res.status, body), res.status, readDetail(body));
  return body as T;
}

/** POST /api/summary: videonun Türkçe özetini ve konu başlıklarını ister. */
export function getSummary(request: SummaryRequest, options?: RequestOptions): Promise<SummaryResponse> {
  return postJson<SummaryResponse>("/api/summary", request, options);
}

/** POST /api/questions: videodan doğrulanmış çoktan seçmeli sorular ister. */
export function getQuestions(request: QuestionsRequest, options?: RequestOptions): Promise<QuestionsResponse> {
  return postJson<QuestionsResponse>("/api/questions", request, options);
}

/** Hatayı kullanıcıya gösterilecek sade Türkçe başlık ve açıklamaya çevirir. */
export function describeError(err: unknown): { title: string; detail: string | null } {
  if (!(err instanceof ApiError)) {
    return { title: "Beklenmeyen bir hata oluştu.", detail: err instanceof Error ? err.message : null };
  }
  switch (err.kind) {
    case "invalid_url":
      return { title: "Bağlantı geçerli bir YouTube videosu değil.", detail: err.detail };
    case "invalid_request":
      return { title: "İstek sunucu tarafından kabul edilmedi.", detail: err.detail };
    case "transcript_unavailable":
      // Backend'in mesajları zaten Türkçe ve sade (ör. "Bu videoda altyazılar kapalı.")
      return { title: "Bu videonun altyazısı alınamadı.", detail: err.detail };
    case "llm_not_configured":
      return {
        title: "Sunucuda OpenAI API anahtarı tanımlı değil.",
        detail: "Backend'deki .env dosyasına OPENAI_API_KEY eklenip sunucu yeniden başlatılmalı.",
      };
    case "youtube_blocked":
      // Backend'in mesajı zaten Türkçe ve ne yapılacağını söylüyor
      return { title: err.detail ?? "YouTube bu ağdan gelen istekleri geçici olarak engelledi.", detail: null };
    case "llm_failed":
      // Ayrıntı OpenAI'den geldiği için İngilizce olabilir; başlık sade Türkçe
      return { title: "Yapay zekâ servisinden geçerli bir yanıt alınamadı. Biraz sonra yeniden deneyin.", detail: err.detail };
    case "network":
      return {
        title: "Sunucuya ulaşılamadı.",
        detail: `Backend çalışıyor mu? Adres: ${API_URL}. Sayfayı localhost:3000 adresinden açtığınızdan emin olun.`,
      };
    case "timeout":
      return { title: "Sunucu zamanında yanıt vermedi.", detail: "Video uzunsa işlem uzun sürebilir; biraz sonra yeniden deneyin." };
    default:
      return {
        title: "Sunucuda beklenmeyen bir hata oluştu.",
        detail: err.status ? `HTTP ${err.status}${err.detail ? `: ${err.detail}` : ""}` : err.detail,
      };
  }
}
