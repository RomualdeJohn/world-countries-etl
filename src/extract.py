from config_loader import load_config, DATA_DIR
from dotenv import load_dotenv
from logger import get_logger

import requests
import os
import json
import time

logger = get_logger(__name__)


def fetch_page_with_retry(
    url: str,
    headers: dict,
    params: dict,
    timeout: int = 30,
    max_retry: int = 5,
    sleep: int = 2,
) -> dict:
    """
    GET one API page and retry with exponential backoff on transient failures.

    Handles HTTP 429/502/503 and connection/timeout errors so pagination can continue safely.

    Input:
        url (str): REST Countries API endpoint.
            Sample: "https://api.restcountries.com/countries/v5"
        headers (dict): request headers including Authorization.
            Sample: {"Accept": "application/json", "Authorization": "Bearer <token>"}
        params (dict): query params for the page request.
            Sample: {"limit": 100, "offset": 0, "response_fields": "names.common,population"}
        timeout (int): request timeout in seconds.
            Sample: 30
        max_retry (int): maximum attempts before failing.
            Sample: 5
        sleep (int): base wait seconds used for exponential backoff.
            Sample: 2

    Result:
        dict: parsed JSON body for the requested page.
            Sample: {"data": {"objects": [...], "meta": {"more": False, "count": 54}}}
    """
    for attempt in range(max_retry):
        try:
            response = requests.get(url, headers=headers, params=params, timeout=timeout)
            logger.debug(
                "attempt=%s/%s offset=%s status=%s",
                attempt + 1,
                max_retry,
                params["offset"],
                response.status_code,
            )
            if response.status_code in (429, 502, 503):
                if attempt == max_retry - 1:
                    response.raise_for_status()
                wait = sleep * (2 ** attempt)
                logger.warning(
                    "attempt=%s/%s retrying in %ss after status %s",
                    attempt + 1,
                    max_retry,
                    wait,
                    response.status_code,
                )
                time.sleep(wait)
                continue
            response.raise_for_status()
            data = response.json()
            return data

        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            if attempt == max_retry - 1:
                raise e
            wait = sleep * (2 ** attempt)
            logger.warning(
                "attempt=%s/%s retrying in %ss after connection error: %s",
                attempt + 1,
                max_retry,
                wait,
                e,
            )
            time.sleep(wait)
    else:
        raise RuntimeError(f"Failed to fetch page after {max_retry} attempts.")


def fetch_all_countries_data() -> list[dict]:
    """
    Paginate the REST Countries API and return every country payload.

    Also writes the filtered response to data/ for local inspection and debugging.

    Input:
        None

    Result:
        list[dict]: all country objects from the API.
            Sample: [{"names": {"common": "Japan"}, "population": 125000000}]
    """
    load_dotenv()
    env = os.getenv("APP_ENV", "dev")
    config = load_config(env)
    OUTPUT_PATH = DATA_DIR / config["rest_countries"]["filename"]

    all_countries_data: list[dict] = []
    offset = 0

    if not os.getenv("API_KEY"):
        raise ValueError("API_KEY is missing")

    url = config["rest_countries"]["url"]
    base_params = {
        "limit": config["rest_countries"]["limit"],
        "response_fields": config["rest_countries"]["response_fields"],
    }
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {os.getenv('API_KEY')}",
    }

    while True:
        params = {**base_params, "offset": offset}
        countries = fetch_page_with_retry(url, headers, params)

        page = countries["data"]["objects"]
        meta = countries["data"]["meta"]

        all_countries_data.extend(page)

        if not meta["more"]:
            break
        offset += meta["count"]

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as file:
        json.dump(all_countries_data, file, indent=4)

    return all_countries_data


if __name__ == "__main__":
    countries = fetch_all_countries_data()
    logger.info("Fetched %s countries", len(countries))
