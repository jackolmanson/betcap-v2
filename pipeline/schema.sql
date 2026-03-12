CREATE TABLE IF NOT EXISTS picks (
    id              SERIAL PRIMARY KEY,
    date            DATE NOT NULL,
    home_display    TEXT NOT NULL,
    away_display    TEXT NOT NULL,
    home_sportsref  TEXT NOT NULL,
    away_sportsref  TEXT NOT NULL,
    home_espn_id    INTEGER,
    away_espn_id    INTEGER,
    model_home_spread FLOAT NOT NULL,
    model_away_spread FLOAT NOT NULL,
    dk_home_spread  FLOAT NOT NULL,
    dk_away_spread  FLOAT NOT NULL,
    pick            TEXT NOT NULL CHECK (pick IN ('home', 'away')),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS picks_date_idx ON picks (date);
