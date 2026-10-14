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
  start_seconds: number;
}

export interface SummaryResponse {
  video_id: string;
  language: string;
  transcript_mode: TranscriptMode;
  model: string;
  summary: string;
  topics: SummaryTopic[];
}

/** Hatanın türü: arayüz her birine ayrı, sade bir Türkçe mesaj gösterir. */
export type ApiErrorKind =
  | "invalid_url" // 422: backend bağlantıyı geçersiz buldu
  | "invalid_request" // 422: istek gövdesi şemaya uymadı (doğrulama listesi)
  | "transcript_unavailable" // 404: altyazı yok / kapalı / video erişilemiyor / temizlikten sonra boş
  | "llm_not_configured" // 503: sunucuda OpenAI API anahtarı tanımlı değil
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

// Özet, uzun videolarda LLM yüzünden onlarca saniye sürebilir
const DEFAULT_TIMEOUT_MS = 180_000;

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
  if (status === 503) return "llm_not_configured";
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
    case "llm_failed":
      // Ayrıntı OpenAI'den geldiği için İngilizce olabilir; başlık sade Türkçe
      return { title: "Yapay zekâ servisinden geçerli bir yanıt alınamadı. Biraz sonra yeniden deneyin.", detail: err.detail };
    case "network":
      return {
        title: "Sunucuya ulaşılamadı.",
        detail: `Backend çalışıyor mu? Adres: ${API_URL}. Sayfayı localhost:3000 adresinden açtığınızdan emin olun.`,
      };
    case "timeout":
      return { title: "Sunucu zamanında yanıt vermedi.", detail: "Video uzunsa özet uzun sürebilir; biraz sonra yeniden deneyin." };
    default:
      return {
        title: "Sunucuda beklenmeyen bir hata oluştu.",
        detail: err.status ? `HTTP ${err.status}${err.detail ? `: ${err.detail}` : ""}` : err.detail,
      };
  }
}
