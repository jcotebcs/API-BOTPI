"""Basic tests for the Flask web interface."""

import os

import pytest

Flask = pytest.importorskip("flask")

from api_bot.web.app import create_app


def _make_client(tmp_path):
    """Create a Flask test client with an isolated database."""
    db_path = tmp_path / "web_test.sqlite"
    os.environ["API_BOT_DB"] = str(db_path)
    app = create_app()
    return app.test_client()


def test_health_search_and_stats(tmp_path):
    client = _make_client(tmp_path)

    # health endpoint
    res = client.get("/health")
    assert res.status_code == 200
    assert res.get_json()["status"] == "ok"

    # search endpoint (should accept query and return structure)
    res = client.post("/api/search", json={"query": "nasa"})
    assert res.status_code == 200
    data = res.get_json()
    assert "text" in data

    # stats endpoint
    res = client.get("/api/stats")
    assert res.status_code == 200
    stats = res.get_json()
    assert "total_apis" in stats

