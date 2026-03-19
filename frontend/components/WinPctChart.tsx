"use client";

import { useEffect, useState } from "react";
import {
  LineChart, Line, XAxis, YAxis, Tooltip,
  ReferenceLine, ReferenceArea, ResponsiveContainer, CartesianGrid,
} from "recharts";
import type { PerformancePick } from "@/lib/db";

type Strategy = "none" | "favorites" | "underdogs" | "home" | "away";

interface ChartPoint {
  date: string;
  winPct: number;
  wins: number;
  losses: number;
  hypWinPct?: number;
  hypWins?: number;
  hypLosses?: number;
}

function hypotheticalResult(
  p: PerformancePick,
  strategy: Exclude<Strategy, "none">,
): "win" | "loss" | "push" | null {
  if (p.home_final_score == null || p.away_final_score == null) return null;

  let hypPick: "home" | "away";
  if (strategy === "home") hypPick = "home";
  else if (strategy === "away") hypPick = "away";
  else if (strategy === "favorites") hypPick = p.dk_home_spread < 0 ? "home" : "away";
  else hypPick = p.dk_home_spread > 0 ? "home" : "away"; // underdogs

  const spread = hypPick === "home" ? p.dk_home_spread : p.dk_away_spread;
  const margin = hypPick === "home"
    ? p.home_final_score - p.away_final_score
    : p.away_final_score - p.home_final_score;

  const covered = margin + spread;
  if (covered > 0) return "win";
  if (covered < 0) return "loss";
  return "push";
}

function buildChartData(picks: PerformancePick[], strategy: Strategy): ChartPoint[] {
  const byDate = new Map<string, {
    wins: number; losses: number;
    hypWins: number; hypLosses: number;
  }>();

  for (const p of picks) {
    if (!p.result || p.result === "pending" || p.result === "push") continue;
    const entry = byDate.get(p.date) ?? { wins: 0, losses: 0, hypWins: 0, hypLosses: 0 };
    if (p.result === "win") entry.wins++;
    else if (p.result === "loss") entry.losses++;

    if (strategy !== "none") {
      const hr = hypotheticalResult(p, strategy);
      if (hr === "win") entry.hypWins++;
      else if (hr === "loss") entry.hypLosses++;
    }
    byDate.set(p.date, entry);
  }

  const sorted = Array.from(byDate.entries()).sort(([a], [b]) => a.localeCompare(b));
  let cumWins = 0, cumLosses = 0, cumHypWins = 0, cumHypLosses = 0;

  return sorted.map(([date, { wins, losses, hypWins, hypLosses }]) => {
    cumWins += wins;
    cumLosses += losses;
    cumHypWins += hypWins;
    cumHypLosses += hypLosses;
    const total = cumWins + cumLosses;
    const hypTotal = cumHypWins + cumHypLosses;
    const point: ChartPoint = {
      date,
      winPct: total > 0 ? parseFloat(((cumWins / total) * 100).toFixed(1)) : 0,
      wins: cumWins,
      losses: cumLosses,
    };
    if (strategy !== "none") {
      point.hypWinPct = hypTotal > 0 ? parseFloat(((cumHypWins / hypTotal) * 100).toFixed(1)) : 0;
      point.hypWins = cumHypWins;
      point.hypLosses = cumHypLosses;
    }
    return point;
  });
}

function fmtAxisDate(iso: string): string {
  const [y, m, d] = iso.split("-").map(Number);
  return `${m}/${d}/${y}`;
}

const STRATEGY_LABELS: Record<Strategy, string> = {
  none: "None",
  favorites: "Always Favorites",
  underdogs: "Always Underdogs",
  home: "Always Home",
  away: "Always Away",
};

function CustomTooltip({ active, payload, strategy }: {
  active?: boolean;
  payload?: Array<{ payload: ChartPoint }>;
  strategy: Strategy;
}) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div
      className="rounded px-3 py-2 text-sm shadow"
      style={{ background: "var(--card)", border: "1px solid var(--border)", color: "var(--text)" }}
    >
      <p className="font-semibold mb-1">{fmtAxisDate(d.date)}</p>
      <p>Model: <span className="font-bold" style={{ color: "#4472C4" }}>{d.winPct}%</span>
        <span className="text-xs ml-1" style={{ color: "var(--text-muted)" }}>({d.wins}W–{d.losses}L)</span>
      </p>
      {strategy !== "none" && d.hypWinPct != null && (
        <p className="mt-0.5">{STRATEGY_LABELS[strategy]}: <span className="font-bold" style={{ color: "#e07b39" }}>{d.hypWinPct}%</span>
          <span className="text-xs ml-1" style={{ color: "var(--text-muted)" }}>({d.hypWins}W–{d.hypLosses}L)</span>
        </p>
      )}
    </div>
  );
}

const ZoneLabel = ({
  line1, line2, color, viewBox, fontSize,
}: {
  line1: string; line2?: string; color: string;
  viewBox?: { x?: number; y?: number; width?: number; height?: number };
  fontSize?: number;
}) => {
  const x = (viewBox?.x ?? 0) + (viewBox?.width ?? 0) + 6;
  const midY = (viewBox?.y ?? 0) + (viewBox?.height ?? 0) / 2;
  const fs = fontSize ?? 10;
  const lineHeight = fs + 2;
  if (line2) {
    return (
      <text x={x} fill={color} fontSize={fs} fontWeight="bold" textAnchor="start" fontFamily="Montserrat, sans-serif">
        <tspan x={x} dy={midY - lineHeight / 2}>{line1}</tspan>
        <tspan x={x} dy={lineHeight + 1}>{line2}</tspan>
      </text>
    );
  }
  return (
    <text x={x} y={midY + fs / 3} fill={color} fontSize={fs} fontWeight="bold" textAnchor="start" fontFamily="Montserrat, sans-serif">
      {line1}
    </text>
  );
};

export default function WinPctChart({ picks }: { picks: PerformancePick[] }) {
  const [isMobile, setIsMobile] = useState(false);
  const [strategy, setStrategy] = useState<Strategy>("none");

  useEffect(() => {
    const check = () => setIsMobile(window.innerWidth < 640);
    check();
    window.addEventListener("resize", check);
    return () => window.removeEventListener("resize", check);
  }, []);

  const data = buildChartData(picks, strategy);

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

  const allPcts = data.flatMap((d) =>
    strategy !== "none" && d.hypWinPct != null
      ? [d.winPct, d.hypWinPct]
      : [d.winPct]
  );
  const dataMin = Math.min(...allPcts);
  const dataMax = Math.max(...allPcts);
  const yMin = Math.floor(Math.min(dataMin, 40) / 5) * 5;
  const yMax = Math.ceil(Math.max(dataMax, 60) / 5) * 5;

  const ticks: number[] = [];
  for (let t = yMin; t <= yMax; t += 5) ticks.push(t);

  const rightMargin = isMobile ? 78 : 160;
  const chartHeight = isMobile ? 260 : 320;
  const labelFontSize = isMobile ? 9 : 10;

  return (
    <div
      className="rounded-lg p-4 sm:p-6 mb-6"
      style={{ background: "var(--card)", border: "1px solid var(--border)" }}
    >
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-sm font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>
          Cumulative Win % Over Time
        </h2>
        <div className="flex items-center gap-2">
          <label className="text-xs font-semibold" style={{ color: "var(--text-muted)" }}>Compare:</label>
          <select
            value={strategy}
            onChange={(e) => setStrategy(e.target.value as Strategy)}
            className="text-xs rounded px-2 py-1"
            style={{ border: "1px solid var(--border)", background: "var(--bg)", color: "var(--text)" }}
          >
            {(Object.keys(STRATEGY_LABELS) as Strategy[]).map((s) => (
              <option key={s} value={s}>{STRATEGY_LABELS[s]}</option>
            ))}
          </select>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={chartHeight}>
        <LineChart data={data} margin={{ top: 16, right: rightMargin, left: 0, bottom: 8 }}>
          <CartesianGrid vertical={false} stroke="var(--border)" strokeOpacity={0.6} />
          <XAxis
            dataKey="date"
            tickFormatter={fmtAxisDate}
            tick={{ fontSize: isMobile ? 9 : 11, fill: "var(--text-muted)", fontFamily: "Montserrat, sans-serif" }}
            tickLine={{ stroke: "var(--border)" }}
            axisLine={{ stroke: "var(--border)" }}
            interval="preserveStartEnd"
          />
          <YAxis
            domain={[yMin, yMax]}
            ticks={ticks}
            tickFormatter={(v) => `${v}%`}
            tick={{ fontSize: isMobile ? 9 : 11, fill: "var(--text-muted)", fontFamily: "Montserrat, sans-serif" }}
            tickLine={false}
            axisLine={false}
            width={isMobile ? 36 : 44}
          />
          <Tooltip content={<CustomTooltip strategy={strategy} />} cursor={{ stroke: "var(--border)", strokeWidth: 1 }} />

          <ReferenceArea y1={52.38} y2={yMax} fill="#16a34a" fillOpacity={0.08} ifOverflow="hidden"
            label={<ZoneLabel line1="PROFITABLE" line2="MODEL" color="#16a34a" fontSize={labelFontSize} />} />
          <ReferenceArea y1={47.62} y2={52.38} fill="red" fillOpacity={0.08} ifOverflow="hidden"
            label={<ZoneLabel line1="NOT" line2="PROFITABLE" color="red" fontSize={labelFontSize} />} />
          <ReferenceArea y1={yMin} y2={47.62} fill="#000000" fillOpacity={0.08} ifOverflow="hidden"
            label={<ZoneLabel line1="PROFITABLE" line2="MUSH MODEL" color="#2b2b2b" fontSize={labelFontSize} />} />

          <ReferenceLine y={52.38} stroke="#16a34a" strokeWidth={2} />
          <ReferenceLine y={47.62} stroke="#2b2b2b" strokeWidth={2} />

          <Line
            type="linear"
            dataKey="winPct"
            stroke="#4472C4"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 5, fill: "#4472C4", strokeWidth: 0 }}
            name="Model"
          />
          {strategy !== "none" && (
            <Line
              type="linear"
              dataKey="hypWinPct"
              stroke="#e07b39"
              strokeWidth={2}
              strokeDasharray="5 3"
              dot={false}
              activeDot={{ r: 5, fill: "#e07b39", strokeWidth: 0 }}
              name={STRATEGY_LABELS[strategy]}
              connectNulls
            />
          )}
        </LineChart>
      </ResponsiveContainer>

      {strategy !== "none" && (
        <div className="flex items-center gap-5 mt-3 text-xs" style={{ color: "var(--text-muted)" }}>
          <span className="flex items-center gap-1.5">
            <span style={{ display: "inline-block", width: 16, height: 2, background: "#4472C4" }} />
            Model picks
          </span>
          <span className="flex items-center gap-1.5">
            <span style={{ display: "inline-block", width: 16, height: 2, background: "#e07b39", borderTop: "2px dashed #e07b39" }} />
            {STRATEGY_LABELS[strategy]}
          </span>
        </div>
      )}
    </div>
  );
}
