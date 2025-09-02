"""Fetch data from an API in the registry."""

from __future__ import annotations

import argparse
import json
import random
import time

import requests

from .registry import load_apis


def safe_request(fn):
    def wrapper(*a, **k):
        last_exc = None
        for attempt in range(5):
            try:
                return fn(*a, timeout=15, **k)
            except requests.exceptions.RequestException as exc:
                last_exc = exc
                time.sleep(min(2 ** attempt + random.random(), 30))
        if last_exc:
            raise last_exc
    return wrapper


@safe_request
def fetch(url: str, **kwargs) -> requests.Response:
    return requests.get(url, **kwargs)


def main() -> None:
    parser = argparse.ArgumentParser(description="Call an API by name")
    parser.add_argument("name", help="name of the API to call")
    args = parser.parse_args()

    for api in load_apis():
        if api["name"].lower() == args.name.lower():
            url = api.get("url")
            if not url:
                print("No URL configured for this API.")
                return
            resp = fetch(url)
            data = resp.text
            try:
                parsed = json.loads(data)
                print(json.dumps(parsed, indent=2))
            except json.JSONDecodeError:
                print(data)
            return
    print("API not found.")


if __name__ == "__main__":
    main()
