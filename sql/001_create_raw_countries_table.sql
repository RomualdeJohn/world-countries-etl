CREATE TABLE IF NOT EXISTS raw_countries.countries_raw (
    id         SERIAL PRIMARY KEY,
    payload    JSONB NOT NULL,
    loaded_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);