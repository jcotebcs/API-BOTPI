"""Fetch data from an API in the registry with safety guards."""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
from urllib.parse import urlparse

import requests

from .registry import load_apis


def safe_request(fn):
    """Retry helper with exponential backoff."""

    def wrapper(*a, **k):
        timeout = k.pop("timeout", 15)
        last_exc = None
        for attempt in range(5):
            try:
                return fn(*a, timeout=timeout, **k)
            except requests.exceptions.RequestException as exc:
                last_exc = exc
                time.sleep(min(2 ** attempt + random.random(), 30))
        if last_exc:
            raise last_exc

    return wrapper


@safe_request
def _get(url: str, **kwargs) -> requests.Response:
    return requests.get(url, **kwargs)


def _print(obj: object) -> None:
    print(json.dumps(obj, indent=2, ensure_ascii=False))


def main() -> None:
    p = argparse.ArgumentParser(description="Call an API by name")
    p.add_argument("name")
    p.add_argument("--timeout", type=float, default=20.0)
    p.add_argument("--header", action="append", default=[], help="k:v")
    p.add_argument("--param", action="append", default=[], help="k=v")
    args = p.parse_args()

    headers = dict(h.split(":", 1) for h in args.header) if args.header else {}
    params = dict(p.split("=", 1) for p in args.param) if args.param else {}

    for api in load_apis():
        if api["name"].lower() == args.name.lower():
            url = api.get("url") or api.get("base_url")
            if not url:
                print("No URL configured.")
                return
            if urlparse(url).scheme != "https":
                print("Refusing insecure HTTP URL. Use HTTPS.")
                return
            try:
                r = _get(url, headers=headers, params=params, timeout=args.timeout)
                r.raise_for_status()
                try:
                    _print(r.json())
                except Exception:
                    print(r.text[:10000])
            except requests.exceptions.RequestException as e:
                print(f"Request failed: {e}", file=sys.stderr)
                sys.exit(2)
            return
    print("API not found.")


if __name__ == "__main__":
    main()
