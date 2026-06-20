from psycopg2.extras import Json, execute_batch
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


def load_countries_data(countries: list[dict]) -> int:
    load_dotenv()
    env = os.getenv("APP_ENV", "dev")
    config = load_config(env)

    schema = config["database"]["raw"]["schema"]
    table = config["database"]["raw"]["table"]
    full_table = f"{schema}.{table}"

    conn = get_db_connection(config)
    try:
        with conn.cursor() as cur:
            logger.info("Truncating %s", full_table)
            cur.execute(f"TRUNCATE TABLE {full_table}")

            logger.info("Inserting %s countries", len(countries))
            execute_batch(
                cur,
                f"INSERT INTO {full_table} (payload) VALUES (%s)",
                [(Json(country),) for country in countries],
            )

        conn.commit()
        logger.info("Loaded %s rows into %s", len(countries), full_table)
        return len(countries)
    except Exception:
        conn.rollback()
        logger.exception("Load failed")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    from extract import fetch_all_countries_data

    countries = fetch_all_countries_data()
    load_countries_data(countries)