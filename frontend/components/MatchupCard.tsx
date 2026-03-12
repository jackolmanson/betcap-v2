import type { Pick } from "@/lib/db";
import Image from "next/image";

function TeamLogo({
  espnId,
  name,
}: {
  espnId: number | null;
  name: string;
}) {
  if (espnId) {
    return (
      <Image
        src={`https://a.espncdn.com/i/teamlogos/ncaa/500/${espnId}.png`}
        alt={name}
        width={72}
        height={72}
        className="object-contain"
        unoptimized
      />
    );
  }
  // Fallback: initials
  const initials = name
    .split(" ")
    .map((w) => w[0])
    .slice(0, 2)
    .join("");
  return (
    <div className="w-[72px] h-[72px] rounded-full bg-slate-700 flex items-center justify-center text-xl font-bold text-slate-300">
      {initials}
    </div>
  );
}

function spread(n: number): string {
  return n > 0 ? `+${n.toFixed(1)}` : n.toFixed(1);
}

export default function MatchupCard({ pick }: { pick: Pick }) {
  const isPick = (side: "home" | "away") => pick.pick === side;

  return (
    <div className="bg-slate-800 rounded-2xl border border-slate-700 overflow-hidden">
      {/* Teams row */}
      <div className="grid grid-cols-[1fr_auto_1fr]">
        {/* Home */}
        <div
          className={`flex flex-col items-center gap-3 p-6 ${
            isPick("home") ? "bg-emerald-950/60" : ""
          }`}
        >
          <TeamLogo espnId={pick.home_espn_id} name={pick.home_display} />
          <span className="text-white font-semibold text-center text-sm leading-tight">
            {pick.home_display}
          </span>
          {isPick("home") && (
            <span className="text-xs font-bold tracking-widest text-emerald-400 uppercase">
              ★ Pick
            </span>
          )}
        </div>

        {/* Divider */}
        <div className="flex items-center justify-center px-4 text-slate-500 font-medium text-sm">
          vs
        </div>

        {/* Away */}
        <div
          className={`flex flex-col items-center gap-3 p-6 ${
            isPick("away") ? "bg-emerald-950/60" : ""
          }`}
        >
          <TeamLogo espnId={pick.away_espn_id} name={pick.away_display} />
          <span className="text-white font-semibold text-center text-sm leading-tight">
            {pick.away_display}
          </span>
          {isPick("away") && (
            <span className="text-xs font-bold tracking-widest text-emerald-400 uppercase">
              ★ Pick
            </span>
          )}
        </div>
      </div>

      {/* Spreads row */}
      <div className="border-t border-slate-700 grid grid-cols-2 divide-x divide-slate-700">
        <SpreadCell
          label="DraftKings"
          home={pick.dk_home_spread}
          away={pick.dk_away_spread}
          pickSide={pick.pick}
        />
        <SpreadCell
          label="Model"
          home={pick.model_home_spread}
          away={pick.model_away_spread}
          pickSide={null}
        />
      </div>
    </div>
  );
}

function SpreadCell({
  label,
  home,
  away,
  pickSide,
}: {
  label: string;
  home: number;
  away: number;
  pickSide: "home" | "away" | null;
}) {
  return (
    <div className="flex flex-col items-center py-3 gap-1">
      <span className="text-xs text-slate-500 uppercase tracking-wider font-medium">
        {label}
      </span>
      <div className="flex gap-6">
        <span
          className={`text-sm font-bold ${
            pickSide === "home" ? "text-emerald-400" : "text-slate-300"
          }`}
        >
          {spread(home)}
        </span>
        <span
          className={`text-sm font-bold ${
            pickSide === "away" ? "text-emerald-400" : "text-slate-300"
          }`}
        >
          {spread(away)}
        </span>
      </div>
    </div>
  );
}
