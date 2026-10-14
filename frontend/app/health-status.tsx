"use client";

import { useCallback, useEffect, useState } from "react";
import { API_URL } from "@/lib/config";

type Status = "checking" | "ok" | "down";

// Backend yanıt vermezse sonsuza kadar beklememek için
const TIMEOUT_MS = 5000;

const LABELS: Record<Status, string> = {
  checking: "Sunucu kontrol ediliyor…",
  ok: "Sunucu çalışıyor",
  down: "Sunucuya ulaşılamıyor",
};

export default function HealthStatus() {
  const [status, setStatus] = useState<Status>("checking");

  const check = useCallback(async (signal?: AbortSignal) => {
    setStatus("checking");
    const timeout = AbortSignal.timeout(TIMEOUT_MS);
    try {
      const res = await fetch(`${API_URL}/health`, {
        signal: signal ? AbortSignal.any([signal, timeout]) : timeout,
        cache: "no-store",
      });
      const body = res.ok ? await res.json() : null;
      setStatus(body?.status === "ok" ? "ok" : "down");
    } catch {
      // Sayfa kapanırken iptal edilen istek durum değiştirmesin
      if (!signal?.aborted) setStatus("down");
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    check(controller.signal);
    return () => controller.abort();
  }, [check]);

  return (
    <section className={`health health-${status}`} role="status" aria-live="polite">
      <span className="dot" aria-hidden="true" />
      <span className="label">{LABELS[status]}</span>
      <code className="url">{API_URL}</code>
      {status === "down" && (
        <button type="button" onClick={() => check()}>
          Yeniden dene
        </button>
      )}
    </section>
  );
}
