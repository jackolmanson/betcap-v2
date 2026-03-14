"use client";

import {
  LineChart, Line, XAxis, YAxis, Tooltip,
  ReferenceLine, ReferenceArea, ResponsiveContainer, CartesianGrid,
} from "recharts";
import type { PerformancePick } from "@/lib/db";

interface ChartPoint {
  date: string;
  winPct: number;
  wins: number;
  losses: number;
}

function buildChartData(picks: PerformancePick[]): ChartPoint[] {
  const byDate = new Map<string, { wins: number; losses: number }>();
  for (const p of picks) {
    if (!p.result || p.result === "pending" || p.result === "push") continue;
    const entry = byDate.get(p.date) ?? { wins: 0, losses: 0 };
    if (p.result === "win") entry.wins++;
    else entry.losses++;
    byDate.set(p.date, entry);
  }

  const sorted = Array.from(byDate.entries()).sort(([a], [b]) => a.localeCompare(b));
  let cumWins = 0, cumLosses = 0;

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

function fmtAxisDate(iso: string): string {
  const [y, m, d] = iso.split("-").map(Number);
  return `${m}/${d}/${y}`;
}

function CustomTooltip({ active, payload }: { active?: boolean; payload?: Array<{ payload: ChartPoint }> }) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div
      className="rounded px-3 py-2 text-sm shadow"
      style={{ background: "var(--card)", border: "1px solid var(--border)", color: "var(--text)" }}
    >
      <p className="font-semibold mb-0.5">{fmtAxisDate(d.date)}</p>
      <p>Win %: <span className="font-bold" style={{ color: "#4472C4" }}>{d.winPct}%</span></p>
      <p className="text-xs mt-1" style={{ color: "var(--text-muted)" }}>{d.wins}W – {d.losses}L</p>
    </div>
  );
}

const RefLabel = ({ label, color, viewBox }: { label: string; color: string; viewBox?: { x?: number; y?: number; width?: number } }) => {
  const x = (viewBox?.x ?? 0) + (viewBox?.width ?? 0) + 8;
  const y = (viewBox?.y ?? 0) + 4;
  return (
    <text x={x} y={y} fill={color} fontSize={10} textAnchor="start" fontFamily="Montserrat, sans-serif">
      {label}
    </text>
  );
};

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

  const allPcts = data.map((d) => d.winPct);
  const dataMin = Math.min(...allPcts);
  const dataMax = Math.max(...allPcts);
  const yMin = Math.floor(Math.min(dataMin, 47) / 5) * 5;
  const yMax = Math.ceil(Math.max(dataMax, 53) / 5) * 5;

  // Build Y-axis ticks in 5% increments
  const ticks: number[] = [];
  for (let t = yMin; t <= yMax; t += 5) ticks.push(t);

  return (
    <div
      className="rounded-lg p-4 sm:p-6 mb-6"
      style={{ background: "var(--card)", border: "1px solid var(--border)" }}
    >
      <h2 className="text-sm font-semibold mb-4 uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>
        Cumulative Win % Over Time
      </h2>
      <ResponsiveContainer width="100%" height={320}>
        <LineChart data={data} margin={{ top: 16, right: 160, left: 0, bottom: 8 }}>
          <CartesianGrid vertical={false} stroke="var(--border)" strokeOpacity={0.6} />
          <XAxis
            dataKey="date"
            tickFormatter={fmtAxisDate}
            tick={{ fontSize: 11, fill: "var(--text-muted)", fontFamily: "Montserrat, sans-serif" }}
            tickLine={{ stroke: "var(--border)" }}
            axisLine={{ stroke: "var(--border)" }}
            interval="preserveStartEnd"
          />
          <YAxis
            domain={[yMin, yMax]}
            ticks={ticks}
            tickFormatter={(v) => `${v}%`}
            tick={{ fontSize: 11, fill: "var(--text-muted)", fontFamily: "Montserrat, sans-serif" }}
            tickLine={false}
            axisLine={false}
            width={44}
          />
          <Tooltip content={<CustomTooltip />} cursor={{ stroke: "var(--border)", strokeWidth: 1 }} />

          <ReferenceArea y1={47.62} y2={52.38} fill="red" fillOpacity={0.08} ifOverflow="hidden" />

          <ReferenceLine
            y={52.38}
            stroke="#16a34a"
            strokeWidth={2}
            label={<RefLabel label="52.38% — Tailing Profitability Line (anything higher)" color="#16a34a" />}
          />
          <ReferenceLine
            y={47.62}
            stroke="#2b2b2b"
            strokeWidth={2}
            label={<RefLabel label="47.62% — Fading Profitability Line (anything lower)" color="#2b2b2b" />}
          />

          <Line
            type="linear"
            dataKey="winPct"
            stroke="#4472C4"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 5, fill: "#4472C4", strokeWidth: 0 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
