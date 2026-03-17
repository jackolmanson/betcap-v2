import postgres from "postgres";

const sql = postgres(process.env.DATABASE_URL!, { ssl: "require" });

export interface Pick {
  id: number;
  date?: string;
  home_display: string;
  away_display: string;
  home_sportsref: string;
  away_sportsref: string;
  home_espn_id: number | null;
  away_espn_id: number | null;
  model_home_spread: number;
  model_away_spread: number;
  dk_home_spread: number;
  dk_away_spread: number;
  pick: "home" | "away";
  game_time: Date | null;
  home_final_score: number | null;
  away_final_score: number | null;
  result: "win" | "loss" | "push" | "pending" | null;
}

export async function getPicksForDate(date: string): Promise<Pick[]> {
  const rows = await sql<Pick[]>`
    SELECT
      id,
      home_display, away_display,
      home_sportsref, away_sportsref,
      home_espn_id, away_espn_id,
      model_home_spread, model_away_spread,
      dk_home_spread, dk_away_spread,
      pick,
      game_time,
      home_final_score, away_final_score,
      result
    FROM picks
    WHERE date = ${date}
    ORDER BY game_time ASC NULLS LAST, id
  `;
  return rows;
}

export interface PerformancePick {
  id: number;
  date: string;
  home_display: string;
  away_display: string;
  dk_home_spread: number;
  dk_away_spread: number;
  pick: "home" | "away";
  home_final_score: number | null;
  away_final_score: number | null;
  result: "win" | "loss" | "push" | "pending" | null;
  home_conference: string | null;
  away_conference: string | null;
}

export async function getAllPicksWithResults(): Promise<PerformancePick[]> {
  const rows = await sql<PerformancePick[]>`
    SELECT
      id,
      date::text,
      home_display, away_display,
      dk_home_spread, dk_away_spread,
      pick,
      home_final_score, away_final_score,
      result,
      home_conference, away_conference
    FROM picks
    ORDER BY date DESC, id
  `;
  return rows;
}

export async function getLatestPickDate(): Promise<string | null> {
  // Return the earliest upcoming date with picks (today or future),
  // falling back to the most recent past date if nothing is upcoming.
  const upcoming = await sql`
    SELECT date::text FROM picks
    WHERE date >= CURRENT_DATE
    ORDER BY date ASC LIMIT 1
  `;
  if (upcoming.length > 0) return upcoming[0].date as string;

  const past = await sql`
    SELECT date::text FROM picks
    ORDER BY date DESC LIMIT 1
  `;
  if (past.length === 0) return null;
  return past[0].date as string;
}

export async function getUpcomingPicks(startDate: string, minGames = 25): Promise<Pick[]> {
  // Fetch picks starting from startDate, spanning additional days until we have minGames.
  const rows = await sql<Pick[]>`
    SELECT
      id, date::text AS date,
      home_display, away_display,
      home_sportsref, away_sportsref,
      home_espn_id, away_espn_id,
      model_home_spread, model_away_spread,
      dk_home_spread, dk_away_spread,
      pick,
      game_time,
      home_final_score, away_final_score,
      result
    FROM picks
    WHERE date >= ${startDate}
    ORDER BY date ASC, game_time ASC NULLS LAST, id
    LIMIT 200
  `;

  // Return just the startDate's picks if already >= minGames,
  // otherwise keep adding days until we reach minGames.
  const byDate: Record<string, Pick[]> = {};
  for (const row of rows) {
    const d = (row as Pick & { date: string }).date;
    (byDate[d] ??= []).push(row);
  }

  const result: Pick[] = [];
  for (const date of Object.keys(byDate).sort()) {
    result.push(...byDate[date]);
    if (result.length >= minGames) break;
  }
  return result;
}
