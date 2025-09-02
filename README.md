# API-BOTPI

This repository provides a minimal Python package skeleton.

## Installation

Run the installer script to set up a virtual environment and install the package:

```bash
./install.sh
```

After installation, activate the environment with:

```bash
source .venv/bin/activate
```

## Project layout

```
apibotpi/        # package code and API registry
install.sh       # one-step installer
pyproject.toml   # build configuration
```

## Searching APIs

Use the helper to look up APIs by quota or whether they are in the public domain. Results include copy-and-paste URLs.

List public domain APIs:

```bash
api-search --public
```

Search for APIs with "free" in their quota description:

```bash
api-search --quota free
```

If the console script is unavailable, you can run the module directly:

```bash
python -m apibotpi.search --public
```

Let the tool guide you interactively:

```bash
api-search --wizard
```

## Calling an API

Fetch a sample response from an API without writing any code:

```bash
api-call "Cat Facts"
```

## Beginner-friendly APIs

List free APIs that work without keys:

```bash
api-beginner list --free --test-mode
```

## Adding a new API

API information lives in `apibotpi/apis.json`. Each entry looks like:

```json
{
  "name": "Example API",
  "description": "What it does",
  "quota": "1000 calls/day",
  "public_domain": true,
  "url": "https://example.com/api"
}
```

Append a new object to the JSON array and re-run `api-search` to confirm it appears. Copy and paste the example above to get started.

## Installing API specs

Instead of editing the registry by hand, install an OpenAPI or JSON spec directly:

```bash
install-api path-or-url-to-spec
```

The command deduplicates entries based on name and host before appending them to `apibotpi/apis.json`.

## SQL snippets

For experimentation with a future database-backed registry, sample SQL is included:

- `migrations/001_provenance_and_rankings.sql` adds provenance fields and a providers table.
- `queries/facet_filter.sql` demonstrates filtering APIs with facets.
