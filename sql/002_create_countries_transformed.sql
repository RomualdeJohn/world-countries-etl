CREATE SCHEMA IF NOT EXISTS analytics;

CREATE TABLE IF NOT EXISTS analytics.countries (
    id               SERIAL PRIMARY KEY,
    country_name     TEXT NOT NULL,
    capital          TEXT,
    region           TEXT,
    subregion        TEXT,
    area_km          NUMERIC,
    population       BIGINT,
    government_type  TEXT,
    timezones        TEXT[],
    calling_codes    TEXT[],
    currencies_raw   JSONB,
    loaded_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);