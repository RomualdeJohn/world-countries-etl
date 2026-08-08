from quality.exceptions import DataQualityError
from logger import get_logger


logger = get_logger(__name__)

MIN_COUNTRY_COUNT = 200


def assert_min_country_count(country_count: int, minimum: int = MIN_COUNTRY_COUNT) -> None:
    """
    Fail if the transformed countries table has too few rows.

    Guards against partial API loads or truncated transforms.

    Input:
        country_count (int): number of rows in the countries table.
            Sample: 254
        minimum (int): lowest acceptable row count.
            Sample: 200

    Result:
        None
    """
    if country_count <= minimum:
        raise DataQualityError(
            f"Country row count {country_count} is not greater than {minimum}"
        )
    logger.info("DQ passed: country_count=%s > %s", country_count, minimum)


def assert_no_negative_population(cur, table: str) -> None:
    """
    Fail if any country row has a negative population.

    Runs after transform so invalid numeric values never reach analytics consumers.

    Input:
        cur: open psycopg2 cursor used to query the table.
            Sample: <cursor object at 0x...>
        table (str): fully qualified countries table name.
            Sample: "analytics.countries"

    Result:
        None
    """
    cur.execute(f"SELECT COUNT(*) FROM {table} WHERE population < 0")
    negative_count = cur.fetchone()[0]
    if negative_count > 0:
        raise DataQualityError(
            f"Found {negative_count} row(s) with negative population in {table}"
        )
    logger.info("DQ passed: no negative population in %s", table)


def run_country_quality_checks(
    cur,
    table: str,
    country_count: int,
    minimum: int = MIN_COUNTRY_COUNT,
) -> None:
    """
    Run all country-level data quality checks and raise on the first failure.

    Called from transform after countries are loaded so a bad snapshot is rolled back.

    Input:
        cur: open psycopg2 cursor used for SQL checks.
            Sample: <cursor object at 0x...>
        table (str): fully qualified countries table name.
            Sample: "analytics.countries"
        country_count (int): row count already computed by transform.
            Sample: 254
        minimum (int): lowest acceptable country row count.
            Sample: 200

    Result:
        None
    """
    logger.info("Running country data quality checks on %s", table)
    assert_min_country_count(country_count, minimum=minimum)
    assert_no_negative_population(cur, table)
    logger.info("All country data quality checks passed")
