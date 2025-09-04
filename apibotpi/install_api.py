"""CLI for installing API specs into the registry."""

from __future__ import annotations

import json
import os
import tempfile
from typing import Tuple
import urllib.request
from urllib.parse import urlparse
import hashlib

import click

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    yaml = None

REGISTRY_PATH = os.path.join(os.path.dirname(__file__), "apis.json")


def load_spec(source: str) -> dict:
    """Load a spec from a URL or local file."""
    if source.startswith(("http://", "https://")):
        with urllib.request.urlopen(source) as resp:  # type: ignore[arg-type]
            text = resp.read().decode("utf-8")
    else:
        with open(source, "r", encoding="utf-8") as f:
            text = f.read()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        if not yaml:
            raise
        return yaml.safe_load(text)  # type: ignore[no-any-return]


def normalize_spec(spec: dict, source: str) -> dict:
    """Extract a minimal record from a spec."""
    name = spec.get("info", {}).get("title") or spec.get("name", "Unknown")
    servers = spec.get("servers") or []
    base_url = ""
    if servers:
        first = servers[0]
        if isinstance(first, dict):
            base_url = first.get("url", "")
        elif isinstance(first, str):
            base_url = first
    host = urlparse(base_url).netloc
    public = bool(spec.get("public_domain"))
    record = {
        "name": name,
        "base_url": base_url,
        "host": host,
        "public_domain": public,
        "spec_hash": hashlib.sha256(
            json.dumps(spec, sort_keys=True, ensure_ascii=False).encode("utf-8")
        ).hexdigest(),
    }
    if source.startswith(("http://", "https://")):
        record["spec_url"] = source
    return record


REQUIRED = ("name", "host")


def validate_record(rec: dict) -> Tuple[bool, list]:
    missing = [k for k in REQUIRED if not rec.get(k)]
    return (len(missing) == 0, missing)


def upsert_api(record: dict, path: str = REGISTRY_PATH) -> int:
    """Insert or update an API record in the registry."""
    ok, missing = validate_record(record)
    if not ok:
        raise ValueError(f"Record missing fields: {missing}")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    for idx, api in enumerate(data):
        if str(api.get("name", "")).strip().lower() == str(record["name"]).strip().lower() and str(api.get("host", "")).lower() == str(record["host"]).lower():
            api.update(record)
            break
    else:
        data.append(record)
        idx = len(data) - 1
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), prefix=".apis.", suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, path)
    return idx


@click.command()
@click.argument("source")
def main(source: str) -> None:
    """Install API from OpenAPI/Postman/JSON."""
    spec = load_spec(source)
    record = normalize_spec(spec, source)
    api_id = upsert_api(record)
    click.echo(f"✅ Installed {record['name']} (id={api_id})")


if __name__ == "__main__":
    main()
