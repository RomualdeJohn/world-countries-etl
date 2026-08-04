from config_loader import load_config
from dotenv import load_dotenv
from logger import get_logger

import psycopg2
import os


logger = get_logger(__name__)


def get_db_connection(config: dict):
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



TRANSFORM_SQL = """
        TRUNCATE TABLE {target};
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


def transform_countries() -> int:
    load_dotenv()
    env = os.getenv("APP_ENV", "dev")
    config = load_config(env)

    raw = config["database"]["raw"]
    transformed = config["database"]["transformed"]
    source = f"{raw['schema']}.{raw['table']}"
    target = f"{transformed['schema']}.{transformed['table']}"

    conn = get_db_connection(config)
    try:
        with conn.cursor() as cur:
            logger.info("Transforming %s -> %s", source, target)
            cur.execute(TRANSFORM_SQL.format(source=source, target=target))
            cur.execute(f"SELECT COUNT(*) FROM {target}")
            row_count = cur.fetchone()[0]

        conn.commit()
        logger.info("Transformed %s rows into %s", row_count, target)
        return row_count
    except Exception:
        conn.rollback()
        logger.exception("Transform failed")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    row_count = transform_countries()
    logger.info("Transform completed with %s rows", row_count)