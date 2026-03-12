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

export async function getLatestPickDate(): Promise<string | null> {
  const rows = await sql`
    SELECT date FROM picks ORDER BY date DESC LIMIT 1
  `;
  if (rows.length === 0) return null;
  return (rows[0].date as Date).toISOString().split("T")[0];
}
