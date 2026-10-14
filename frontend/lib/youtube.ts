// YouTube bağlantısını tarayıcıda, istek göndermeden önce denetler.
// Kurallar backend'deki extract_video_id (backend/app/services/youtube.py) ile aynıdır;
// son karar yine backend'indir (geçersizse 422 döner).

const VIDEO_ID_RE = /^[A-Za-z0-9_-]{11}$/;
const YOUTUBE_HOSTS = new Set(["youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com"]);
const PATH_PREFIXES = new Set(["embed", "shorts", "live", "v"]);

/** Bağlantıdan 11 karakterlik video kimliğini çıkarır; geçersizse null döner. */
export function extractVideoId(input: string): string | null {
  let text = input.trim();
  if (!text) return null;
  if (VIDEO_ID_RE.test(text)) return text;

  if (!text.includes("://")) text = "https://" + text;
  let url: URL;
  try {
    url = new URL(text);
  } catch {
    return null;
  }
  const host = url.hostname.toLowerCase();

  let candidate: string | null = null;
  if (host === "youtu.be") {
    candidate = url.pathname.replace(/^\/+/, "").split("/")[0];
  } else if (YOUTUBE_HOSTS.has(host)) {
    if (url.pathname === "/watch") {
      candidate = url.searchParams.get("v");
    } else {
      const parts = url.pathname.split("/").filter(Boolean);
      if (parts.length >= 2 && PATH_PREFIXES.has(parts[0])) candidate = parts[1];
    }
  }
  return candidate && VIDEO_ID_RE.test(candidate) ? candidate : null;
}

/** Form için Türkçe uyarı; bağlantı uygunsa null. */
export function validateYouTubeUrl(input: string): string | null {
  if (!input.trim()) return "Lütfen bir YouTube video bağlantısı girin.";
  if (!extractVideoId(input)) {
    return "Bu geçerli bir YouTube video bağlantısına benzemiyor. Örnek: https://www.youtube.com/watch?v=xxxxxxxxxxx";
  }
  return null;
}
