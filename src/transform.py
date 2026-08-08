from config_loader import load_config
from dotenv import load_dotenv
from logger import get_logger

import psycopg2
import os


logger = get_logger(__name__)


def get_db_connection(config: dict):
    """
    Open a PostgreSQL connection using config values and DB_PASSWORD.

    Shared by load/transform so database credentials stay in one place.

    Input:
        config (dict): merged app config containing database host/port/name/user.
            Sample: {"database": {"host": "127.0.0.1", "port": 5432, "name": "countries_pipeline_dev", "user": "countries_etl_user_dev"}}

    Result:
        psycopg2.extensions.connection: open database connection.
            Sample: <connection object at 0x...>
    """
    db = config["database"]
    password = os.getenv("DB_PASSWORD")
    if not password:
        raise ValueError("DB_PASSWORD is missing")

    return psycopg2.connect(
        host=db["host"],
        port=db["port"],
        dbname=db["name"],
        user=db["user"],
        password=password,
    )


TRUNCATE_COUNTRIES_SQL = "TRUNCATE TABLE {target} CASCADE"

INSERT_COUNTRIES_SQL = """
    INSERT INTO {target} (
        country_name, capital, region, subregion,
        area_km, population, government_type,
        timezones, calling_codes, currencies_raw, loaded_at
    )
    SELECT
        payload->'names'->>'common',
        payload->'capitals'->0->>'name',
        payload->>'region',
        payload->>'subregion',
        (payload->'area'->>'kilometers')::numeric,
        (payload->>'population')::bigint,
        payload->>'government_type',
        ARRAY(SELECT jsonb_array_elements_text(payload->'timezones')),
        ARRAY(SELECT jsonb_array_elements_text(payload->'calling_codes')),
        payload->'currencies',
        loaded_at
    FROM {source};
"""

TRUNCATE_CURRENCIES_SQL = "TRUNCATE TABLE {currencies}"

INSERT_CURRENCIES_SQL = """
    INSERT INTO {currencies} (
        country_id, country_name, currency_code, currency_name, currency_symbol
    )
    SELECT
        c.id,
        c.country_name,
        curr->>'code',
        curr->>'name',
        curr->>'symbol'
    FROM {countries} c
    CROSS JOIN LATERAL jsonb_array_elements(
        COALESCE(c.currencies_raw, '[]'::jsonb)
    ) AS curr;
"""


def transform_countries() -> tuple[int, int]:
    """
    Flatten raw JSONB countries into analytics tables, including currencies.

    Truncates and reloads analytics.countries, then unnests currencies_raw
    into analytics.country_currencies.

    Input:
        None

    Result:
        tuple[int, int]: country row count and currency row count.
            Sample: (254, 272)
    """
    load_dotenv()
    env = os.getenv("APP_ENV", "dev")
    config = load_config(env)

    raw = config["database"]["raw"]
    transformed = config["database"]["transformed"]
    currencies = config["database"]["currencies"]

    source = f"{raw['schema']}.{raw['table']}"
    target = f"{transformed['schema']}.{transformed['table']}"
    currencies_table = f"{currencies['schema']}.{currencies['table']}"

    conn = get_db_connection(config)
    try:
        with conn.cursor() as cur:
            logger.info("Transforming %s -> %s", source, target)
            cur.execute(TRUNCATE_COUNTRIES_SQL.format(target=target))
            cur.execute(INSERT_COUNTRIES_SQL.format(source=source, target=target))
            cur.execute(f"SELECT COUNT(*) FROM {target}")
            country_count = cur.fetchone()[0]
            logger.info("Transformed %s rows into %s", country_count, target)

            logger.info("Flattening currencies into %s", currencies_table)
            cur.execute(TRUNCATE_CURRENCIES_SQL.format(currencies=currencies_table))
            cur.execute(
                INSERT_CURRENCIES_SQL.format(
                    currencies=currencies_table,
                    countries=target,
                )
            )
            cur.execute(f"SELECT COUNT(*) FROM {currencies_table}")
            currency_count = cur.fetchone()[0]
            logger.info("Loaded %s currency rows into %s", currency_count, currencies_table)

        conn.commit()
        return country_count, currency_count
    except Exception:
        conn.rollback()
        logger.exception("Transform failed")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    country_count, currency_count = transform_countries()
    logger.info(
        "Transform completed with %s countries and %s currency rows",
        country_count,
        currency_count,
    )
