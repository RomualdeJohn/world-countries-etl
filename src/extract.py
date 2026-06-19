import requests
import os
import json
import time
from dotenv import load_dotenv

load_dotenv()

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
            print(f"Attempt {attempt + 1}/{max_retry} | offset={params['offset']} | status={response.status_code}")
            if response.status_code in (429, 502, 503):
                if attempt == max_retry - 1:
                    response.raise_for_status()
                wait = sleep * (2 ** attempt)
                print(f"Attempt {attempt + 1}/{max_retry} failed. Waiting {wait} seconds before retrying...")
                time.sleep(wait)
                continue
            response.raise_for_status()
            data = response.json()
            return data

        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            if attempt == max_retry - 1:
                raise e
            wait = sleep * (2 ** attempt)
            print(f"Attempt {attempt + 1}/{max_retry} failed. Waiting {wait} seconds before retrying. Connection error: {e}")
            time.sleep(wait)
    else:
        raise RuntimeError(f"Failed to fetch page after {max_retry} attempts.")

def fetch_all_countries_data(limit: int = 100) -> list[dict]:
    all_countries_data: list[dict] = []
    offset = 0
    url = os.getenv("API_URL")
    base_params = {
        "limit": limit,
        "response_fields": "names.common,official,capitals.name,region,subregion,area,calling_codes,currencies,government_type,population,timezones",
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
    
    with open("data/countries_raw_filtered.json", "w") as file:
        json.dump(all_countries_data, file, indent=4)

    return all_countries_data


if __name__ == "__main__":
    countries = fetch_all_countries_data()
    print(f"[+] Fetched {len(countries)} countries")