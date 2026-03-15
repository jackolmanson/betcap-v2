"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function ScoreTodayButton() {
  const [scoring, setScoring] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const router = useRouter();

  async function handleClick() {
    setScoring(true);
    setMsg(null);
    try {
      const res = await fetch("/api/score-today", { method: "POST" });
      const data = await res.json();
      setMsg(data.message ?? data.error ?? "Done.");
      router.refresh();
    } catch {
      setMsg("Request failed.");
    } finally {
      setScoring(false);
    }
  }

  return (
    <div className="flex items-center gap-3">
      {msg && (
        <span className="text-xs" style={{ color: "var(--text-muted)" }}>{msg}</span>
      )}
      <button
        onClick={handleClick}
        disabled={scoring}
        className="text-xs px-3 py-1.5 rounded font-semibold"
        style={{ background: "var(--accent)", color: "white", opacity: scoring ? 0.6 : 1 }}
      >
        {scoring ? "Scoring…" : "Score Today's Games"}
      </button>
    </div>
  );
}
