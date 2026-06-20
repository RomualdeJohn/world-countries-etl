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
        "Authorization": f"Bearer {os.getenv("API_KEY")}",
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