#!/usr/bin/env python3
"""Enhanced Flask web interface for the API Discovery Bot.

This module exposes a small web application used by the tests and can
also be launched manually.  The interface intentionally keeps
dependencies light so it can run in restricted environments.  When
available, :mod:`flask_cors` is enabled so the API can be reached from
browser extensions or other local tools.
"""

from __future__ import annotations

import sys
from pathlib import Path
from datetime import datetime

try:
    from flask import Flask, jsonify, render_template_string, request
    try:  # optional CORS support
        from flask_cors import CORS  # type: ignore
    except Exception:  # pragma: no cover - optional dependency
        CORS = None
except Exception as exc:  # pragma: no cover - handled at runtime
    raise SystemExit(
        "Flask is required to run the web app. Install with `pip install flask`"
    ) from exc

# Ensure package imports work when running as a script
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from api_bot.core.discovery_bot import ComprehensiveAPIBot


# ---------------------------------------------------------------------------
# HTML template served at `/`
# ---------------------------------------------------------------------------
def get_web_template() -> str:
    """Return the HTML template for the web interface."""
    return (
        "<!doctype html>\n"
        "<title>API Discovery Bot</title>\n"
        "<h1>API Discovery Bot</h1>\n"
        "<form id='search-form'>\n"
        "  <input id='query' placeholder='Search APIs' required>\n"
        "  <button type='submit'>Search</button>\n"
        "</form>\n"
        "<pre id='results'></pre>\n"
        "<script>\n"
        "const form = document.getElementById('search-form');\n"
        "form.addEventListener('submit', async (e) => {\n"
        "  e.preventDefault();\n"
        "  const res = await fetch('/api/search', {\n"
        "    method: 'POST',\n"
        "    headers: {'Content-Type': 'application/json'},\n"
        "    body: JSON.stringify({query: document.getElementById('query').value})\n"
        "  });\n"
        "  const data = await res.json();\n"
        "  document.getElementById('results').textContent = JSON.stringify(data, null, 2);\n"
        "});\n"
        "</script>\n"
    )


def create_app() -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)
    if CORS is not None:  # pragma: no branch - trivial
        CORS(app)  # enable CORS when available

    bot = ComprehensiveAPIBot()
    # Seed database with the built-in examples if empty so the UI is useful
    try:
        if bot.count_apis() == 0:
            bot.update_database()
    except Exception:  # pragma: no cover - best effort
        pass

    @app.get("/")
    def index() -> str:
        return render_template_string(get_web_template())

    @app.get("/health")
    def health() -> tuple[dict[str, str], int]:
        """Health check with timestamp and version information."""
        payload = {
            "status": "ok",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "version": "1.0",
        }
        return jsonify(payload), 200

    @app.post("/api/search")
    def api_search() -> tuple[dict, int]:
        payload = request.get_json(silent=True) or {}
        query = (payload.get("query") or "").strip()
        if not query:
            return jsonify({"error": "missing query"}), 400
        results = bot.comprehensive_search(query)
        return jsonify(results), 200

    @app.get("/api/stats")
    def api_stats() -> tuple[dict, int]:
        return jsonify(bot.get_stats()), 200

    return app


if __name__ == "__main__":  # pragma: no cover
    create_app().run(debug=True)

