"use client";

import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ReferenceLine, ResponsiveContainer, Legend,
} from "recharts";
import type { PerformancePick } from "@/lib/db";

interface ChartPoint {
  date: string;
  winPct: number;
  wins: number;
  losses: number;
}

function buildChartData(picks: PerformancePick[]): ChartPoint[] {
  // Group settled picks by date, then compute cumulative win %
  const byDate = new Map<string, { wins: number; losses: number }>();

  for (const p of picks) {
    if (!p.result || p.result === "pending" || p.result === "push") continue;
    const entry = byDate.get(p.date) ?? { wins: 0, losses: 0 };
    if (p.result === "win") entry.wins++;
    else entry.losses++;
    byDate.set(p.date, entry);
  }

  const sorted = Array.from(byDate.entries()).sort(([a], [b]) => a.localeCompare(b));

  let cumWins = 0;
  let cumLosses = 0;

  return sorted.map(([date, { wins, losses }]) => {
    cumWins += wins;
    cumLosses += losses;
    const total = cumWins + cumLosses;
    return {
      date,
      winPct: total > 0 ? parseFloat(((cumWins / total) * 100).toFixed(1)) : 0,
      wins: cumWins,
      losses: cumLosses,
    };
  });
}

function fmtDate(iso: string): string {
  const [y, m, d] = iso.split("-").map(Number);
  return new Date(y, m - 1, d).toLocaleDateString("en-US", {
    month: "short", day: "numeric", timeZone: "America/New_York",
  });
}

interface TooltipPayload {
  winPct: number;
  wins: number;
  losses: number;
  date: string;
}

function CustomTooltip({ active, payload }: { active?: boolean; payload?: Array<{ payload: TooltipPayload }> }) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div
      className="rounded-lg px-3 py-2 text-sm shadow-lg"
      style={{ background: "var(--card)", border: "1px solid var(--border)", color: "var(--text)" }}
    >
      <p className="font-semibold mb-1">{fmtDate(d.date)}</p>
      <p>Win %: <span style={{ color: "var(--accent)" }}>{d.winPct}%</span></p>
      <p className="text-xs mt-1" style={{ color: "var(--text-muted)" }}>
        {d.wins}W – {d.losses}L (cumulative)
      </p>
    </div>
  );
}

export default function WinPctChart({ picks }: { picks: PerformancePick[] }) {
  const data = buildChartData(picks);

  if (data.length === 0) {
    return (
      <div
        className="rounded-lg p-8 text-center text-sm mb-6"
        style={{ background: "var(--card)", border: "1px solid var(--border)", color: "var(--text-muted)" }}
      >
        No settled picks to chart yet.
      </div>
    );
  }

  const yMin = Math.min(30, Math.floor(Math.min(...data.map((d) => d.winPct)) / 5) * 5);
  const yMax = Math.max(75, Math.ceil(Math.max(...data.map((d) => d.winPct)) / 5) * 5);

  return (
    <div
      className="rounded-lg p-4 sm:p-6 mb-6"
      style={{ background: "var(--card)", border: "1px solid var(--border)" }}
    >
      <h2 className="text-sm font-semibold mb-4 uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>
        Cumulative Win % Over Time
      </h2>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data} margin={{ top: 8, right: 24, left: 0, bottom: 8 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
          <XAxis
            dataKey="date"
            tickFormatter={fmtDate}
            tick={{ fontSize: 11, fill: "var(--text-muted)" }}
            tickLine={false}
            axisLine={{ stroke: "var(--border)" }}
            interval="preserveStartEnd"
          />
          <YAxis
            domain={[yMin, yMax]}
            tickFormatter={(v) => `${v}%`}
            tick={{ fontSize: 11, fill: "var(--text-muted)" }}
            tickLine={false}
            axisLine={false}
            width={44}
          />
          <Tooltip content={<CustomTooltip />} />

          {/* Profitability reference lines */}
          <ReferenceLine
            y={52.38}
            stroke="#16a34a"
            strokeDasharray="6 3"
            strokeWidth={1.5}
            label={{ value: "52.38% — Profitability line when tailing", position: "insideTopLeft", fontSize: 10, fill: "#16a34a", dy: -6 }}
          />
          <ReferenceLine
            y={47.62}
            stroke="#dc2626"
            strokeDasharray="6 3"
            strokeWidth={1.5}
            label={{ value: "47.62% — Profitability line when fading", position: "insideBottomLeft", fontSize: 10, fill: "#dc2626", dy: 6 }}
          />

          <Line
            type="monotone"
            dataKey="winPct"
            stroke="var(--accent)"
            strokeWidth={2.5}
            dot={{ r: 4, fill: "var(--accent)", strokeWidth: 0 }}
            activeDot={{ r: 6, fill: "var(--accent)" }}
            name="Win %"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
