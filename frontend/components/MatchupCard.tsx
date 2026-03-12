import type { Pick } from "@/lib/db";
import Image from "next/image";

function TeamLogo({ espnId, name }: { espnId: number | null; name: string }) {
  if (espnId) {
    return (
      <Image
        src={`https://a.espncdn.com/i/teamlogos/ncaa/500/${espnId}.png`}
        alt={name}
        width={64}
        height={64}
        className="object-contain"
        unoptimized
      />
    );
  }
  const initials = name.split(" ").map((w) => w[0]).slice(0, 2).join("");
  return (
    <div
      className="w-16 h-16 rounded-full flex items-center justify-center text-lg font-bold"
      style={{ background: "var(--bg)", color: "var(--text-muted)" }}
    >
      {initials}
    </div>
  );
}

function fmt(n: number): string {
  return n > 0 ? `+${n.toFixed(1)}` : n.toFixed(1);
}

export default function MatchupCard({ pick }: { pick: Pick }) {
  const homePick = pick.pick === "home";
  const awayPick = pick.pick === "away";

  return (
    <div
      className="rounded-lg overflow-hidden"
      style={{
        background: "var(--card)",
        border: "1px solid var(--border)",
        boxShadow: "0 1px 3px rgba(0,0,0,0.08)",
      }}
    >
      {/* Teams */}
      <div className="grid grid-cols-[1fr_32px_1fr]">
        <TeamSide
          name={pick.home_display}
          espnId={pick.home_espn_id}
          isPick={homePick}
          label="HOME"
        />
        <div
          className="flex items-center justify-center text-xs font-medium"
          style={{ color: "var(--text-muted)" }}
        >
          vs
        </div>
        <TeamSide
          name={pick.away_display}
          espnId={pick.away_espn_id}
          isPick={awayPick}
          label="AWAY"
        />
      </div>

      {/* Spreads */}
      <div
        className="grid grid-cols-2 text-center text-xs py-3"
        style={{ borderTop: "1px solid var(--border)" }}
      >
        <div>
          <div className="font-semibold mb-1" style={{ color: "var(--text-muted)" }}>
            DraftKings
          </div>
          <div className="flex justify-center gap-6">
            <Spread value={pick.dk_home_spread} highlight={homePick} />
            <Spread value={pick.dk_away_spread} highlight={awayPick} />
          </div>
        </div>
        <div style={{ borderLeft: "1px solid var(--border)" }}>
          <div className="font-semibold mb-1" style={{ color: "var(--text-muted)" }}>
            Model
          </div>
          <div className="flex justify-center gap-6">
            <Spread value={pick.model_home_spread} highlight={false} />
            <Spread value={pick.model_away_spread} highlight={false} />
          </div>
        </div>
      </div>
    </div>
  );
}

function TeamSide({
  name,
  espnId,
  isPick,
  label,
}: {
  name: string;
  espnId: number | null;
  isPick: boolean;
  label: string;
}) {
  return (
    <div
      className="flex flex-col items-center gap-2 py-5 px-3"
      style={isPick ? { background: "#fff4ee" } : {}}
    >
      <TeamLogo espnId={espnId} name={name} />
      <span
        className="text-sm font-semibold text-center leading-tight"
        style={{ color: "var(--text)" }}
      >
        {name}
      </span>
      <span
        className="text-xs font-medium"
        style={{ color: "var(--text-muted)", opacity: 0.6 }}
      >
        {label}
      </span>
      {isPick && (
        <span
          className="text-xs font-bold tracking-wider px-2 py-0.5 rounded"
          style={{ background: "var(--accent)", color: "white" }}
        >
          PICK
        </span>
      )}
    </div>
  );
}

function Spread({ value, highlight }: { value: number; highlight: boolean }) {
  return (
    <span
      className="font-bold text-sm"
      style={{ color: highlight ? "var(--accent)" : "var(--text)" }}
    >
      {fmt(value)}
    </span>
  );
}
