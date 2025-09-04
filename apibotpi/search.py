"""Command-line helpers for searching the API registry."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from typing import List

from .registry import search_apis


def _print_table(results: List[dict]) -> None:
    for api in results:
        url = api.get("url", "")
        extra = f" - {url}" if url else ""
        print(
            f"{api['name']}: {api['description']} (quota: {api['quota']}){extra}"
        )


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
    parser.add_argument(
        "--no-auth",
        action="store_true",
        help="prefer no-auth/public APIs",
    )
    parser.add_argument("--json", action="store_true", help="output JSON")
    parser.add_argument(
        "--format",
        choices=["table", "json", "csv", "xlsx"],
        default="table",
        help="output format",
    )
    args = parser.parse_args()

    quota = args.quota
    public = args.public
    if args.wizard:
        print("What do you want to do?")
        print("  1) Learn APIs  2) Weather  3) Countries  4) Space  5) Health info")
        choice = (input("Choose [1-5]: ").strip() or "1")
        if choice == "2":
            quota, public = None, True
        elif choice == "3":
            quota, public = None, True
        elif choice == "4":
            quota, public = "free", True
        elif choice == "5":
            quota, public = "free", True
        else:
            quota = None
            public = None
    if args.no_auth:
        public = True

    out_format = "json" if args.json else args.format

    results = list(search_apis(quota=quota, public=public))
    if not results:
        print("No APIs found.")
        return

    if out_format == "json":
        print(json.dumps(results, indent=2, ensure_ascii=False))
    elif out_format == "csv":
        writer = csv.DictWriter(sys.stdout, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)
    elif out_format == "xlsx":
        try:
            import pandas as pd  # type: ignore

            df = pd.DataFrame(results)
            df.to_excel("apis.xlsx", index=False)
            print("Wrote apis.xlsx")
        except Exception as exc:  # pragma: no cover - optional dependency
            print(f"xlsx export requires pandas and openpyxl ({exc})")
    else:
        _print_table(results)


if __name__ == "__main__":
    main()
