"use client";

import { useState, useMemo } from "react";
import type { PerformancePick } from "@/lib/db";

type ResultFilter = "all" | "win" | "loss" | "push" | "pending";
type SideFilter = "all" | "home" | "away";
type TypeFilter = "all" | "favorite" | "underdog";

function pickedSpread(p: PerformancePick) {
  return p.pick === "home" ? p.dk_home_spread : p.dk_away_spread;
}

function pickedTeam(p: PerformancePick) {
  return p.pick === "home" ? p.home_display : p.away_display;
}

function pickedConference(p: PerformancePick) {
  return p.pick === "home" ? p.home_conference : p.away_conference;
}

function fmt(n: number) {
  return n > 0 ? `+${n.toFixed(1)}` : n.toFixed(1);
}

function fmtDate(isoDate: string): string {
  const [year, month, day] = isoDate.split("-").map(Number);
  return new Date(year, month - 1, day).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    timeZone: "America/New_York",
  });
}

function ResultBadge({ result }: { result: PerformancePick["result"] }) {
  const styles: Record<string, string> = {
    win: "background:#d1fae5;color:#065f46",
    loss: "background:#fee2e2;color:#991b1b",
    push: "background:#e0e7ff;color:#3730a3",
    pending: "background:#f3f4f6;color:#6b7280",
  };
  const label = result ?? "pending";
  return (
    <span
      className="text-xs font-semibold px-2 py-0.5 rounded"
      style={Object.fromEntries(
        (styles[label] ?? styles.pending)
          .split(";")
          .map((s) => s.split(":").map((x) => x.trim()))
      )}
    >
      {label.toUpperCase()}
    </span>
  );
}

export default function PerformanceClient({ picks }: { picks: PerformancePick[] }) {
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [sideFilter, setSideFilter] = useState<SideFilter>("all");
  const [typeFilter, setTypeFilter] = useState<TypeFilter>("all");
  const [resultFilter, setResultFilter] = useState<ResultFilter>("all");
  const [confFilter, setConfFilter] = useState("all");

  // Unique sorted conferences from the data
  const conferences = useMemo(() => {
    const set = new Set<string>();
    for (const p of picks) {
      const c = pickedConference(p);
      if (c) set.add(c);
    }
    return ["all", ...Array.from(set).sort()];
  }, [picks]);

  const filtered = useMemo(() => {
    return picks.filter((p) => {
      if (dateFrom && p.date < dateFrom) return false;
      if (dateTo && p.date > dateTo) return false;
      if (sideFilter !== "all" && p.pick !== sideFilter) return false;
      if (resultFilter !== "all") {
        const r = p.result ?? "pending";
        if (r !== resultFilter) return false;
      }
      if (typeFilter !== "all") {
        const spread = pickedSpread(p);
        if (typeFilter === "favorite" && spread >= 0) return false;
        if (typeFilter === "underdog" && spread <= 0) return false;
      }
      if (confFilter !== "all" && pickedConference(p) !== confFilter) return false;
      return true;
    });
  }, [picks, dateFrom, dateTo, sideFilter, typeFilter, resultFilter, confFilter]);

  // Summary stats (excluding pending)
  const settled = filtered.filter((p) => p.result && p.result !== "pending");
  const wins = settled.filter((p) => p.result === "win").length;
  const losses = settled.filter((p) => p.result === "loss").length;
  const pushes = settled.filter((p) => p.result === "push").length;
  const winPct = settled.length > 0 ? ((wins / (wins + losses)) * 100).toFixed(1) : "—";
  // ROI at -110: win = +100/110 units, loss = -1 unit
  const roi =
    settled.length > 0
      ? (((wins * (100 / 110) - losses) / (wins + losses)) * 100).toFixed(1)
      : "—";

  return (
    <main className="max-w-6xl mx-auto px-6 py-8">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold mb-1" style={{ color: "var(--text)" }}>
          Performance
        </h1>
        <hr className="mt-4" style={{ borderColor: "var(--border)" }} />
      </div>

      {/* Stats bar */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-6">
        {[
          { label: "Record", value: `${wins}-${losses}${pushes > 0 ? `-${pushes}` : ""}` },
          { label: "Win %", value: winPct === "—" ? "—" : `${winPct}%` },
          { label: "ROI", value: roi === "—" ? "—" : `${roi}%` },
          { label: "Picks shown", value: filtered.length },
          { label: "Pending", value: filtered.filter((p) => !p.result || p.result === "pending").length },
        ].map(({ label, value }) => (
          <div
            key={label}
            className="rounded-lg p-4 text-center"
            style={{ background: "var(--card)", border: "1px solid var(--border)" }}
          >
            <div className="text-xs mb-1" style={{ color: "var(--text-muted)" }}>{label}</div>
            <div className="text-xl font-bold" style={{ color: "var(--accent)" }}>{value}</div>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div
        className="flex flex-wrap gap-3 mb-6 p-4 rounded-lg"
        style={{ background: "var(--card)", border: "1px solid var(--border)" }}
      >
        <div className="flex flex-col gap-1">
          <label className="text-xs font-semibold" style={{ color: "var(--text-muted)" }}>From</label>
          <input
            type="date"
            value={dateFrom}
            onChange={(e) => setDateFrom(e.target.value)}
            className="text-sm rounded px-2 py-1"
            style={{ border: "1px solid var(--border)", background: "var(--bg)", color: "var(--text)" }}
          />
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-xs font-semibold" style={{ color: "var(--text-muted)" }}>To</label>
          <input
            type="date"
            value={dateTo}
            onChange={(e) => setDateTo(e.target.value)}
            className="text-sm rounded px-2 py-1"
            style={{ border: "1px solid var(--border)", background: "var(--bg)", color: "var(--text)" }}
          />
        </div>
        <FilterSelect label="Pick Side" value={sideFilter} onChange={(v) => setSideFilter(v as SideFilter)}
          options={[["all", "All"], ["home", "Home"], ["away", "Away"]]} />
        <FilterSelect label="Pick Type" value={typeFilter} onChange={(v) => setTypeFilter(v as TypeFilter)}
          options={[["all", "All"], ["favorite", "Favorites"], ["underdog", "Underdogs"]]} />
        <FilterSelect label="Result" value={resultFilter} onChange={(v) => setResultFilter(v as ResultFilter)}
          options={[["all", "All"], ["win", "Wins"], ["loss", "Losses"], ["push", "Pushes"], ["pending", "Pending"]]} />
        <FilterSelect label="Conference" value={confFilter} onChange={setConfFilter}
          options={conferences.map((c) => [c, c === "all" ? "All Conferences" : c])} />
        {(dateFrom || dateTo || sideFilter !== "all" || typeFilter !== "all" || resultFilter !== "all" || confFilter !== "all") && (
          <button
            onClick={() => { setDateFrom(""); setDateTo(""); setSideFilter("all"); setTypeFilter("all"); setResultFilter("all"); setConfFilter("all"); }}
            className="self-end text-xs px-3 py-1 rounded"
            style={{ color: "var(--accent)", border: "1px solid var(--accent)" }}
          >
            Clear filters
          </button>
        )}
      </div>

      {/* Table */}
      {filtered.length === 0 ? (
        <p className="text-center py-12" style={{ color: "var(--text-muted)" }}>No picks match the current filters.</p>
      ) : (
        <div className="rounded-lg overflow-hidden" style={{ border: "1px solid var(--border)" }}>
          <table className="w-full text-sm">
            <thead>
              <tr style={{ background: "var(--navbar)", color: "white" }}>
                {["Date", "Matchup", "Pick", "Spread", "Score", "Result"].map((h) => (
                  <th key={h} className="text-left px-4 py-3 font-semibold text-xs">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtered.map((p, i) => (
                <tr
                  key={p.id}
                  style={{
                    background: i % 2 === 0 ? "var(--card)" : "var(--bg)",
                    borderBottom: "1px solid var(--border)",
                  }}
                >
                  <td className="px-4 py-3 whitespace-nowrap" style={{ color: "var(--text-muted)" }}>
                    {fmtDate(p.date)}
                  </td>
                  <td className="px-4 py-3" style={{ color: "var(--text)" }}>
                    {p.home_display} vs {p.away_display}
                  </td>
                  <td className="px-4 py-3 font-semibold" style={{ color: "var(--accent)" }}>
                    {pickedTeam(p)}
                    {pickedConference(p) && (
                      <span className="ml-1 text-xs font-normal" style={{ color: "var(--text-muted)" }}>
                        ({pickedConference(p)})
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3 font-mono" style={{ color: "var(--text)" }}>
                    {fmt(pickedSpread(p))}
                  </td>
                  <td className="px-4 py-3 font-mono" style={{ color: "var(--text-muted)" }}>
                    {p.home_final_score != null
                      ? `${p.home_display} ${p.home_final_score}-${p.away_final_score} ${p.away_display}`
                      : "—"}
                  </td>
                  <td className="px-4 py-3">
                    <ResultBadge result={p.result} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </main>
  );
}

function FilterSelect({
  label, value, onChange, options,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  options: [string, string][];
}) {
  return (
    <div className="flex flex-col gap-1">
      <label className="text-xs font-semibold" style={{ color: "var(--text-muted)" }}>{label}</label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="text-sm rounded px-2 py-1"
        style={{ border: "1px solid var(--border)", background: "var(--bg)", color: "var(--text)" }}
      >
        {options.map(([val, lbl]) => (
          <option key={val} value={val}>{lbl}</option>
        ))}
      </select>
    </div>
  );
}
