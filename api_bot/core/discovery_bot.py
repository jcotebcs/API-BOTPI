"""SQLite-backed API discovery bot with text and semantic search.

This module provides the :class:`ComprehensiveAPIBot` which stores
information about APIs in a small SQLite database.  It offers basic
discovery features, lightweight semantic search using a hashing based
embedding, and keeps a log of search queries so that recent activity can
be surfaced in statistics.

The implementation is intentionally self contained and dependency free so
that the accompanying command line interface can operate in the execution
environment used for the kata.  The design mirrors a greatly simplified
version of the application described in the project README.
"""

from __future__ import annotations

import json
import math
import hashlib
import os
import re
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

Row = sqlite3.Row

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

DEFAULT_DB = Path(os.getenv("API_BOT_DB", Path.cwd() / "apis.sqlite"))


def utcnow() -> str:
    """Return the current UTC time as an ISO formatted string."""

    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _norm_host(host_or_url: Optional[str]) -> Optional[str]:
    """Normalise *host_or_url* and return just the hostname.

    ``None`` is returned for falsy values.  When a URL is supplied the
    scheme and path are stripped leaving only the hostname.  The returned
    value is always lower case.
    """

    if not host_or_url:
        return None
    s = host_or_url.strip()
    if "://" in s:
        try:
            return re.sub(r"^https?://", "", s).split("/")[0].lower()
        except Exception:  # pragma: no cover - defensive
            return s.lower()
    return s.lower()


def _hashing_embed(text: str, dim: int = 256) -> List[float]:
    """Return a deterministic embedding for *text*.

    A very small "hashing trick" embedding is used in place of calling out
    to a model.  The resulting vector is L2 normalised so that cosine
    similarity can be computed by a simple dot product.
    """

    vec = [0.0] * dim
    tokens = re.findall(r"[a-z0-9]+", (text or "").lower())
    if not tokens:
        return vec
    for tok in tokens:
        h = int(hashlib.md5(tok.encode("utf-8")).hexdigest(), 16)
        vec[h % dim] += 1.0
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


# ---------------------------------------------------------------------------
# Bot implementation
# ---------------------------------------------------------------------------


class ComprehensiveAPIBot:
    """SQLite backed API collector and searcher.

    The interface intentionally mirrors the minimal subset of behaviour the
    CLI requires.  The database schema is initialised automatically on first
    use.  Search queries are logged in a ``search_log`` table so that summary
    statistics can display recent activity.
    """

    def __init__(self, db_path: Path = DEFAULT_DB):
        self.db_path = Path(db_path)
        self.con = sqlite3.connect(self.db_path)
        self.con.row_factory = sqlite3.Row
        self._fts_available = self._check_fts5()
        self.setup_database()

    # ------------------------------------------------------------------
    # Database initialisation
    # ------------------------------------------------------------------

    def _check_fts5(self) -> bool:
        """Return ``True`` if FTS5 is available in the SQLite build."""

        try:
            cur = self.con.cursor()
            cur.execute("CREATE VIRTUAL TABLE IF NOT EXISTS _fts5_probe USING fts5(x)")
            cur.execute("DROP TABLE _fts5_probe")
            return True
        except sqlite3.OperationalError:  # pragma: no cover - depends on build
            return False

    def is_db_initialized(self) -> bool:
        cur = self.con.cursor()
        cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='apis'"
        )
        return cur.fetchone() is not None

    def setup_database(self) -> None:
        """Create database schema if it does not already exist."""

        cur = self.con.cursor()
        cur.executescript(
            """
        PRAGMA journal_mode=WAL;
        PRAGMA synchronous=NORMAL;

        CREATE TABLE IF NOT EXISTS apis(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          name TEXT NOT NULL,
          host TEXT NOT NULL,
          base_url TEXT,
          description TEXT,
          category TEXT,
          docs_url TEXT,
          openapi_url TEXT,
          auth TEXT DEFAULT 'none',
          rate_limit TEXT,
          status TEXT DEFAULT 'unknown',
          source TEXT,
          created_at TEXT DEFAULT CURRENT_TIMESTAMP,
          updated_at TEXT,
          UNIQUE(name, host)
        );

        CREATE TABLE IF NOT EXISTS endpoints(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          api_id INTEGER NOT NULL,
          method TEXT,
          path TEXT,
          description TEXT,
          UNIQUE(api_id, method, path),
          FOREIGN KEY(api_id) REFERENCES apis(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS embeddings(
          api_id INTEGER PRIMARY KEY,
          dim INTEGER NOT NULL,
          vector TEXT NOT NULL,
          FOREIGN KEY(api_id) REFERENCES apis(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS search_log(
          ts TEXT,
          query TEXT
        );
        """
        )
        if self._fts_available:
            cur.executescript(
                """
            CREATE VIRTUAL TABLE IF NOT EXISTS apis_fts
            USING fts5(name, description, category, content='apis', content_rowid='id');
            """
            )
            cur.execute("SELECT count(1) FROM apis_fts")
            if (cur.fetchone()[0] or 0) == 0:
                cur.execute(
                    "INSERT INTO apis_fts(rowid, name, description, category)"
                    " SELECT id, name, description, category FROM apis"
                )
        self.con.commit()

    # backward compatible aliases used by the CLI
    def setup(self) -> None:  # pragma: no cover - passthrough
        self.setup_database()

    def init_db(self) -> None:  # pragma: no cover - passthrough
        self.setup_database()

    # ------------------------------------------------------------------
    # Upserts and indexing
    # ------------------------------------------------------------------

    def _upsert_api(self, api: Dict[str, Any]) -> int:
        name = api.get("name") or "Unknown"
        host = _norm_host(
            api.get("host")
            or api.get("base_url")
            or api.get("baseUrl")
            or "unknown"
        )
        now = utcnow()
        cur = self.con.cursor()
        cur.execute(
            """
        INSERT INTO apis(name, host, base_url, description, category, docs_url,
                         openapi_url, auth, rate_limit, status, source, updated_at)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(name, host) DO UPDATE SET
            base_url=excluded.base_url,
            description=COALESCE(excluded.description, apis.description),
            category=COALESCE(excluded.category, apis.category),
            docs_url=COALESCE(excluded.docs_url, apis.docs_url),
            openapi_url=COALESCE(excluded.openapi_url, apis.openapi_url),
            auth=COALESCE(excluded.auth, apis.auth),
            rate_limit=COALESCE(excluded.rate_limit, apis.rate_limit),
            status=COALESCE(excluded.status, apis.status),
            source=COALESCE(excluded.source, apis.source),
            updated_at=?
        """,
            (
                name,
                host,
                api.get("base_url") or api.get("baseUrl"),
                api.get("description"),
                api.get("category"),
                api.get("docs_url") or api.get("docsUrl"),
                api.get("openapi_url") or api.get("openapiUrl"),
                api.get("auth") or api.get("auth_type") or "none",
                api.get("rate_limit") or api.get("rateLimit"),
                api.get("status") or "unknown",
                api.get("source"),
                now,
            ),
        )
        api_id = cur.lastrowid
        if api_id == 0:
            cur.execute("SELECT id FROM apis WHERE name=? AND host=?", (name, host))
            api_id = int(cur.fetchone()["id"])
        if self._fts_available:
            cur.execute(
                "INSERT INTO apis_fts(rowid, name, description, category) VALUES(?,?,?,?)"
                " ON CONFLICT(rowid) DO UPDATE SET name=excluded.name,"
                " description=excluded.description, category=excluded.category",
                (api_id, name, api.get("description"), api.get("category")),
            )
        self._upsert_embedding(api_id, name, api.get("description") or "")
        self.con.commit()
        eps = api.get("endpoints") or []
        if eps:
            self._upsert_endpoints(api_id, eps)
        return api_id

    def _upsert_endpoints(self, api_id: int, endpoints: List[Dict[str, Any]]) -> None:
        cur = self.con.cursor()
        rows = []
        for ep in endpoints:
            rows.append(
                (
                    api_id,
                    (ep.get("method") or "GET").upper(),
                    ep.get("path") or "/",
                    ep.get("description"),
                )
            )
        cur.executemany(
            """
            INSERT INTO endpoints(api_id, method, path, description)
            VALUES(?,?,?,?)
            ON CONFLICT(api_id, method, path) DO UPDATE SET description=excluded.description
            """,
            rows,
        )
        self.con.commit()

    def _upsert_embedding(self, api_id: int, name: str, description: str) -> None:
        text = f"{name}\n{description or ''}"
        vec = _hashing_embed(text, dim=256)
        cur = self.con.cursor()
        cur.execute(
            """
        INSERT INTO embeddings(api_id, dim, vector) VALUES(?,?,?)
        ON CONFLICT(api_id) DO UPDATE SET dim=excluded.dim, vector=excluded.vector
        """,
            (api_id, 256, json.dumps(vec)),
        )
        self.con.commit()

    # ------------------------------------------------------------------
    # Discovery / update
    # ------------------------------------------------------------------

    def update_database(self) -> str:
        """Import APIs from ``apis.json`` if present and seed some defaults."""

        imported = 0
        merged = 0
        p = Path.cwd() / "apis.json"
        if p.exists():
            try:
                payload = json.loads(p.read_text(encoding="utf-8"))
                items = payload.get("apis", payload if isinstance(payload, list) else [])
                for item in items:
                    self._upsert_api(item)
                    merged += 1
            except Exception:  # pragma: no cover - best effort
                pass

        seeds = [
            {
                "name": "NASA Open APIs",
                "host": "api.nasa.gov",
                "base_url": "https://api.nasa.gov",
                "description": "Space imagery and data (e.g., APOD, EPIC).",
                "category": "space",
                "docs_url": "https://api.nasa.gov/",
                "auth": "apiKey",
                "source": "seed",
            },
            {
                "name": "US Census APIs",
                "host": "api.census.gov",
                "base_url": "https://api.census.gov",
                "description": "Population and economic datasets.",
                "category": "government",
                "docs_url": "https://www.census.gov/data/developers/data-sets.html",
                "auth": "none",
                "source": "seed",
            },
            {
                "name": "Library of Congress",
                "host": "loc.gov",
                "base_url": "https://www.loc.gov",
                "description": "Digital collections search endpoints.",
                "category": "culture",
                "docs_url": "https://libraryofcongress.github.io/data-exploration/",
                "auth": "none",
                "source": "seed",
            },
            {
                "name": "GovInfo",
                "host": "api.govinfo.gov",
                "base_url": "https://api.govinfo.gov",
                "description": "Government Publishing Office document APIs.",
                "category": "government",
                "docs_url": "https://api.govinfo.gov/docs/",
                "auth": "apiKey",
                "source": "seed",
            },
        ]
        for s in seeds:
            self._upsert_api(s)
            imported += 1
        return f"Merged from apis.json: {merged}; Seeded: {imported}"

    # ------------------------------------------------------------------
    # Export helpers
    # ------------------------------------------------------------------

    def list_apis(self) -> List[Dict[str, Any]]:  # pragma: no cover - simple proxy
        cur = self.con.cursor()
        cur.execute("SELECT * FROM apis ORDER BY name")
        return [dict(r) for r in cur.fetchall()]

    def fetch_all_apis(self) -> List[Dict[str, Any]]:  # pragma: no cover - alias
        return self.list_apis()

    def dump_json(self) -> Dict[str, Any]:
        cur = self.con.cursor()
        cur.execute("SELECT * FROM apis")
        apis = [dict(r) for r in cur.fetchall()]
        cur.execute("SELECT api_id, method, path, description FROM endpoints")
        ep_map: Dict[int, List[Dict[str, Any]]] = {}
        for r in cur.fetchall():
            ep_map.setdefault(r["api_id"], []).append(
                {
                    "method": r["method"],
                    "path": r["path"],
                    "description": r["description"],
                }
            )
        for a in apis:
            a["endpoints"] = ep_map.get(a["id"], [])
        return {"apis": apis}

    def export_json(self, path: str) -> None:
        Path(path).write_text(
            json.dumps(self.dump_json(), ensure_ascii=False, indent=2), encoding="utf-8"
        )

    # backward compatible wrapper expected by the CLI
    def export_results(self, path: str) -> str:
        """Export API data to *path* and return the written path."""

        self.export_json(path)
        return str(Path(path))

    # ------------------------------------------------------------------
    # Statistics and endpoints lookups
    # ------------------------------------------------------------------

    def get_stats(self) -> Dict[str, Any]:
        cur = self.con.cursor()
        cur.execute("SELECT COUNT(*) AS c FROM apis")
        total = int(cur.fetchone()["c"])

        cur.execute(
            "SELECT COALESCE(category,'uncategorized') AS k, COUNT(*) AS c"
            " FROM apis GROUP BY k ORDER BY c DESC"
        )
        by_category = {r["k"]: int(r["c"]) for r in cur.fetchall()}

        cur.execute(
            "SELECT COALESCE(source,'unknown') AS s, COUNT(*) AS c"
            " FROM apis GROUP BY s ORDER BY c DESC"
        )
        by_source = {r["s"]: int(r["c"]) for r in cur.fetchall()}

        week_ago = time.time() - 7 * 24 * 3600
        cur.execute(
            "SELECT COUNT(*) AS c FROM search_log WHERE strftime('%s', ts) >= ?",
            (int(week_ago),),
        )
        searches_last_week = int(cur.fetchone()["c"])

        cur.execute("SELECT query FROM search_log ORDER BY rowid DESC LIMIT 5")
        recent_searches = [r["query"] for r in cur.fetchall()]

        return {
            "total_apis": total,
            "by_category": by_category,
            "by_source": by_source,
            "searches_last_week": searches_last_week,
            "recent_searches": recent_searches,
        }

    def count_apis(self) -> int:  # pragma: no cover - simple proxy
        return self.get_stats()["total_apis"]

    def get_api_endpoints(self, api_id: int) -> List[Dict[str, Any]]:
        cur = self.con.cursor()
        cur.execute(
            "SELECT method, path, description FROM endpoints WHERE api_id=? ORDER BY method, path",
            (api_id,),
        )
        return [dict(r) for r in cur.fetchall()]

    def get_api_endpoints_by_name_host(self, name: str, host: str) -> List[Dict[str, Any]]:
        cur = self.con.cursor()
        cur.execute("SELECT id FROM apis WHERE name=? AND host=?", (name, _norm_host(host)))
        r = cur.fetchone()
        return self.get_api_endpoints(int(r["id"])) if r else []

    def get_api_endpoints_by_name(self, name: str) -> List[Dict[str, Any]]:  # pragma: no cover
        cur = self.con.cursor()
        cur.execute("SELECT id FROM apis WHERE name=?", (name,))
        r = cur.fetchone()
        return self.get_api_endpoints(int(r["id"])) if r else []

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def comprehensive_search(self, query: str) -> Dict[str, List[Dict[str, Any]]]:
        # log search
        self.con.execute(
            "INSERT INTO search_log(ts, query) VALUES(?, ?)", (utcnow(), query)
        )
        self.con.commit()

        text_hits = self._text_search(query, limit=25)
        sem_hits = self._semantic_search(query, limit=25, threshold=0.2)

        return {"text": text_hits, "semantic": sem_hits}

    def _text_search(self, query: str, limit: int = 25) -> List[Dict[str, Any]]:
        cur = self.con.cursor()
        if self._fts_available:
            cur.execute(
                """
                SELECT a.*
                FROM apis a
                JOIN apis_fts f ON f.rowid = a.id
                WHERE apis_fts MATCH ?
                LIMIT ?
                """,
                (query, limit),
            )
        else:
            like = f"%{query}%"
            cur.execute(
                """
                SELECT * FROM apis
                WHERE name LIKE ? OR description LIKE ? OR category LIKE ?
                LIMIT ?
                """,
                (like, like, like, limit),
            )
        rows = cur.fetchall()
        return [self._row_to_api(r) for r in rows]

    def _semantic_search(
        self, query: str, limit: int = 25, threshold: float = 0.2
    ) -> List[Dict[str, Any]]:
        qv = _hashing_embed(query)
        cur = self.con.cursor()
        cur.execute(
            """
            SELECT e.api_id, e.vector, a.*
            FROM embeddings e
            JOIN apis a ON a.id = e.api_id
            """
        )
        scored: List[Tuple[float, Row]] = []
        for r in cur.fetchall():
            vec = json.loads(r["vector"])
            score = sum((qv[i] * vec[i]) for i in range(min(len(qv), len(vec))))
            if score >= threshold:
                scored.append((score, r))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [self._row_to_api(r) for (s, r) in scored[:limit]]

    def format_search_results(
        self, results: Dict[str, List[Dict[str, Any]]], query: str
    ) -> str:
        lines = [f"# Results for: **{query}**"]
        for bucket in ("text", "semantic"):
            items = results.get(bucket, [])
            if not items:
                continue
            lines.append(f"\n## {bucket.title()} matches ({len(items)})")
            for i, a in enumerate(items, 1):
                docs = a.get("docs_url") or a.get("documentation") or "—"
                lines.append(
                    f"{i}. **{a['name']}** — *{a.get('category','unknown')}*  \n"
                    f"   `{a.get('base_url') or ''}`  \n   {a.get('description') or ''}  \n"
                    f"   Docs: {docs}"
                )
        if len(lines) == 1:
            lines.append("\n_No results._")
        return "\n".join(lines)

    def _row_to_api(self, r: Row) -> Dict[str, Any]:
        return {
            "id": r["id"],
            "name": r["name"],
            "host": r["host"],
            "base_url": r["base_url"],
            "description": r["description"],
            "category": r["category"],
            "documentation": r["docs_url"],
            "docs_url": r["docs_url"],
            "openapi_url": r["openapi_url"],
            "auth": r["auth"],
            "rate_limit": r["rate_limit"],
            "status": r["status"],
            "source": r["source"],
        }

