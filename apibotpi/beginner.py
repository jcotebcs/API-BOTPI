"""Beginner-oriented CLI helpers."""

from __future__ import annotations

import click
from tabulate import tabulate

from .registry import search_apis


@click.group()
def main() -> None:
    """Beginner commands for exploring APIs."""


@main.command("list")
@click.option("--free", is_flag=True, help="Only show free-tier APIs")
@click.option("--test-mode", is_flag=True, help="Only APIs usable without keys")
def list_beginner(free: bool, test_mode: bool) -> None:
    """List beginner-friendly APIs with optional filters."""
    quota = "free" if free else None
    public = True if test_mode else None
    rows = [
        (api["name"], api.get("url", ""))
        for api in search_apis(quota=quota, public=public)
    ]
    if rows:
        print(tabulate(rows, headers=["API", "URL"]))
    else:
        print("No APIs found.")


if __name__ == "__main__":
    main()
