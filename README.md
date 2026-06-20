# world-countries-etl

ETL pipeline that pulls country data from the [REST Countries API](https://restcountries.com/) (v5) and loads it into PostgreSQL for downstream transformation and analytics.

## Overview

This project is a hands-on data engineering pipeline with four main stages:

1. **Extract** — fetch country data from the REST Countries API (paginated, filtered fields, retry with exponential backoff)
2. **Load** — full-dump into a raw PostgreSQL table (`raw_countries.countries_raw`) as JSONB
3. **Transform** — flatten nested JSON, normalize currencies, apply data quality checks *(planned)*
4. **Orchestrate** — schedule runs, containerize, and add alerting *(planned)*

The current focus is on building a reliable extract-and-load foundation before moving into transformation and production deployment.
