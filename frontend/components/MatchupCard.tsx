import type { Pick } from "@/lib/db";
import Image from "next/image";

function TeamLogo({ espnId, name }: { espnId: number | null; name: string }) {
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
  const initials = name.split(" ").map((w) => w[0]).slice(0, 2).join("");
  return (
    <div
      className="w-16 h-16 sm:w-18 sm:h-18 rounded-full flex items-center justify-center text-lg font-bold"
      style={{ background: "var(--bg)", color: "var(--text-muted)" }}
    >
      {initials}
    </div>
  );
}

function fmt(n: number): string {
  return n > 0 ? `+${n.toFixed(1)}` : n.toFixed(1);
}

function fmtGameTime(gameTime: Date | null): string {
  if (!gameTime) return "";
  return new Date(gameTime).toLocaleString("en-US", {
    timeZone: "America/New_York",
    weekday: "short",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
  }) + " ET";
}

export default function MatchupCard({ pick }: { pick: Pick }) {
  const homePick = pick.pick === "home";
  const awayPick = pick.pick === "away";

  return (
    <div
      className="rounded-xl overflow-hidden flex flex-col"
      style={{
        background: "var(--card)",
        border: "1px solid var(--border)",
        boxShadow: "0 2px 6px rgba(0,0,0,0.06)",
      }}
    >
      {/* Game time */}
      {pick.game_time && (
        <div
          className="text-center text-xs font-medium py-2 px-4 tracking-wide"
          style={{ borderBottom: "1px solid var(--border)", color: "var(--text-muted)", background: "var(--bg)" }}
        >
          {fmtGameTime(pick.game_time)}
        </div>
      )}

      {/* Teams */}
      <div className="grid grid-cols-[1fr_40px_1fr] flex-1">
        <TeamSide
          name={pick.home_display}
          espnId={pick.home_espn_id}
          isPick={homePick}
          label="HOME"
          spread={pick.dk_home_spread}
        />
        <div
          className="flex items-center justify-center text-sm font-semibold"
          style={{ color: "var(--text-muted)" }}
        >
          vs
        </div>
        <TeamSide
          name={pick.away_display}
          espnId={pick.away_espn_id}
          isPick={awayPick}
          label="AWAY"
          spread={pick.dk_away_spread}
        />
      </div>
    </div>
  );
}

function TeamSide({
  name, espnId, isPick, label, spread,
}: {
  name: string; espnId: number | null; isPick: boolean; label: string; spread: number;
}) {
  return (
    <div
      className="flex flex-col items-center gap-2 py-6 px-3"
      style={isPick ? { background: "#fff4ee" } : {}}
    >
      <TeamLogo espnId={espnId} name={name} />
      <span
        className="text-sm font-semibold text-center leading-snug"
        style={{ color: "var(--text)" }}
      >
        {name}
      </span>
      <span
        className="text-xs font-medium tracking-widest uppercase"
        style={{ color: "var(--text-muted)" }}
      >
        {label}
      </span>
      <span
        className="text-base font-bold"
        style={{ color: isPick ? "var(--accent)" : "var(--text)" }}
      >
        {fmt(spread)}
      </span>
      {isPick && (
        <span
          className="text-xs font-bold tracking-wider px-3 py-1 rounded-full"
          style={{ background: "var(--accent)", color: "white" }}
        >
          PICK
        </span>
      )}
    </div>
  );
}
