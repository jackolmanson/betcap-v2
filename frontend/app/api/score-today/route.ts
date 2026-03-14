import { NextResponse } from "next/server";
import postgres from "postgres";

const sql = postgres(process.env.DATABASE_URL!, { ssl: "require" });

const ESPN_SCOREBOARD =
  "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard";

// Pacific Time offset for date boundary comparisons (matches pipeline)
function todayPT(): string {
  const now = new Date();
  const pt = new Date(now.getTime() - 8 * 60 * 60 * 1000);
  return pt.toISOString().slice(0, 10);
}

async function fetchScores(dateStr: string): Promise<Map<string, [number, number]>> {
  const yyyymmdd = dateStr.replace(/-/g, "");
  const url = `${ESPN_SCOREBOARD}?dates=${yyyymmdd}&limit=200&groups=50`;
  const res = await fetch(url, { cache: "no-store" });
  const data = await res.json();

  const scores = new Map<string, [number, number]>();
  for (const event of data.events ?? []) {
    if (!event?.status?.type?.completed) continue;
    const comp = event.competitions?.[0];
    const competitors: Array<{ homeAway: string; id: string; score: string }> =
      comp?.competitors ?? [];
    if (competitors.length !== 2) continue;

    const home = competitors.find((c) => c.homeAway === "home");
    const away = competitors.find((c) => c.homeAway === "away");
    if (!home || !away) continue;

    const key = `${home.id}_${away.id}`;
    scores.set(key, [parseInt(home.score), parseInt(away.score)]);
  }
  return scores;
}

function calculateResult(
  pick: "home" | "away",
  dkHomeSpread: number,
  homeScore: number,
  awayScore: number
): "win" | "loss" | "push" {
  const threshold = -dkHomeSpread;
  const margin = homeScore - awayScore;
  if (pick === "home") {
    if (margin > threshold) return "win";
    if (margin === threshold) return "push";
    return "loss";
  } else {
    if (margin < threshold) return "win";
    if (margin === threshold) return "push";
    return "loss";
  }
}

export async function POST() {
  try {
    const today = todayPT();

    // Fetch today's unscored picks
    const picks = await sql`
      SELECT id, home_display, away_display,
             home_espn_id, away_espn_id,
             dk_home_spread, dk_away_spread,
             pick, game_time
      FROM picks
      WHERE date = ${today}
        AND result IS NULL
      ORDER BY id
    `;

    if (picks.length === 0) {
      return NextResponse.json({ message: "No pending picks for today.", updated: 0, results: [] });
    }

    const scores = await fetchScores(today);

    const results: Array<{ matchup: string; pick: string; result: string }> = [];
    let updated = 0;
    const unmatched: string[] = [];

    for (const pick of picks) {
      const homeId = pick.home_espn_id?.toString();
      const awayId = pick.away_espn_id?.toString();

      if (!homeId || !awayId) {
        unmatched.push(`${pick.home_display} vs ${pick.away_display} (no ESPN ID)`);
        continue;
      }

      const key = `${homeId}_${awayId}`;
      const flipped = `${awayId}_${homeId}`;

      let homeScore: number, awayScore: number;
      if (scores.has(key)) {
        [homeScore, awayScore] = scores.get(key)!;
      } else if (scores.has(flipped)) {
        [awayScore, homeScore] = scores.get(flipped)!;
      } else {
        unmatched.push(`${pick.home_display} vs ${pick.away_display}`);
        continue;
      }

      const result = calculateResult(pick.pick, pick.dk_home_spread, homeScore, awayScore);
      await sql`
        UPDATE picks
        SET home_final_score = ${homeScore}, away_final_score = ${awayScore}, result = ${result}
        WHERE id = ${pick.id}
      `;

      const pickedTeam = pick.pick === "home" ? pick.home_display : pick.away_display;
      results.push({ matchup: `${pick.home_display} ${homeScore}-${awayScore} ${pick.away_display}`, pick: pickedTeam, result });
      updated++;
    }

    return NextResponse.json({
      message: `Updated ${updated}/${picks.length} picks for ${today}.`,
      updated,
      total: picks.length,
      results,
      unmatched,
    });
  } catch (err) {
    console.error(err);
    return NextResponse.json({ error: String(err) }, { status: 500 });
  }
}
