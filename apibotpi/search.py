"""Command-line helpers for searching the API registry."""

from __future__ import annotations

import argparse

from .registry import search_apis


def main() -> None:
    parser = argparse.ArgumentParser(description="Search available APIs")
    parser.add_argument("--quota", help="substring to match within the quota description")
    parser.add_argument(
        "--public",
        action="store_true",
        default=None,
        help="only show APIs in the public domain",
    )
    parser.add_argument(
        "--wizard",
        action="store_true",
        help="prompt for filters interactively",
    )
    args = parser.parse_args()

    quota = args.quota
    public = args.public
    if args.wizard:
        quota = input("Filter by quota substring (leave blank for any): ") or None
        public_choice = (
            input("Only public domain APIs? [y/n/blank for any]: ")
            .strip()
            .lower()
        )
        if public_choice == "y":
            public = True
        elif public_choice == "n":
            public = False
        else:
            public = None

    results = list(search_apis(quota=quota, public=public))
    if not results:
        print("No APIs found.")
        return
    for api in results:
        url = api.get("url", "")
        extra = f" - {url}" if url else ""
        print(
            f"{api['name']}: {api['description']} (quota: {api['quota']}){extra}"
        )


if __name__ == "__main__":
    main()
