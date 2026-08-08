from psycopg2.extras import Json, execute_batch
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


def load_countries_data(countries: list[dict]) -> int:
    """
    Truncate the raw countries table and insert a full dump of API payloads.

    Used after extract so analysts always see a fresh snapshot of country JSON.

    Input:
        countries (list[dict]): list of country payloads from the API.
            Sample: [{"names": {"common": "Japan"}, "population": 125000000}]

    Result:
        int: number of rows inserted.
            Sample: 254
    """
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
