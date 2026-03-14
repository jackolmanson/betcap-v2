"use client";

import { useEffect, useState } from "react";
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

const ZoneLabel = ({
  line1, line2, color, viewBox, fontSize,
}: {
  line1: string;
  line2?: string;
  color: string;
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

  useEffect(() => {
    const check = () => setIsMobile(window.innerWidth < 640);
    check();
    window.addEventListener("resize", check);
    return () => window.removeEventListener("resize", check);
  }, []);

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
  const yMin = Math.floor(Math.min(dataMin, 40) / 5) * 5;
  const yMax = Math.ceil(Math.max(dataMax, 60) / 5) * 5;

  // Build Y-axis ticks in 5% increments
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
      <h2 className="text-sm font-semibold mb-4 uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>
        Cumulative Win % Over Time
      </h2>
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
          <Tooltip content={<CustomTooltip />} cursor={{ stroke: "var(--border)", strokeWidth: 1 }} />

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
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
