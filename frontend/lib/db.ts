import postgres from "postgres";

const sql = postgres(process.env.DATABASE_URL!, { ssl: "require" });

export interface Pick {
  id: number;
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
      pick
    FROM picks
    WHERE date = ${date}
    ORDER BY id
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
  const rows = await sql`
    SELECT date::text FROM picks ORDER BY date DESC LIMIT 1
  `;
  if (rows.length === 0) return null;
  return rows[0].date as string;
}
