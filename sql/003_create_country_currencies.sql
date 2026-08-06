CREATE TABLE IF NOT EXISTS analytics.country_currencies (
    id              SERIAL PRIMARY KEY,
    country_id      INTEGER NOT NULL REFERENCES analytics.countries(id) ON DELETE CASCADE,
    country_name    TEXT NOT NULL,
    currency_code   TEXT,
    currency_name   TEXT,
    currency_symbol TEXT
);
