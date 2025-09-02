"""Fetch data from an API in the registry."""

from __future__ import annotations

import argparse
import json
import urllib.request

from .registry import load_apis


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
            with urllib.request.urlopen(url) as resp:
                data = resp.read().decode("utf-8")
            try:
                parsed = json.loads(data)
                print(json.dumps(parsed, indent=2))
            except json.JSONDecodeError:
                print(data)
            return
    print("API not found.")


if __name__ == "__main__":
    main()
