import json
from collections import Counter
from pathlib import Path
from typing import Dict, List, Any

class ComprehensiveAPIBot:
    """Simple in-memory API discovery bot used for tests.

    The real project aims to collect information about public APIs and
    provide search facilities.  For the purposes of the kata the class only
    implements a tiny subset of that behaviour so that the CLI can operate
    during tests without contacting external services.
    """

    def __init__(self) -> None:
        # Sample data set representing discovered APIs.  Each entry contains the
        # fields that the CLI expects.  In a real application this data would be
        # loaded from a database.
        self.apis: List[Dict[str, Any]] = [
            {
                "id": 1,
                "name": "Sample Weather API",
                "host": "weather.example.com",
                "manufacturer": "Weather Co",
                "category": "weather",
                "description": "Access current weather information",
                "auth_type": "apiKey",
                "pricing": "Free",
                "rate_limit": "1000/day",
                "documentation": "https://weather.example.com/docs",
                "endpoints": [
                    {
                        "method": "GET",
                        "path": "/v1/current",
                        "description": "Current weather data"
                    }
                ]
            },
            {
                "id": 2,
                "name": "Space Images",
                "host": "images.nasa.gov",
                "manufacturer": "NASA",
                "category": "space",
                "description": "Retrieve imagery from NASA archives",
                "auth_type": "None",
                "pricing": "Free",
                "rate_limit": "Unlimited",
                "documentation": "https://api.nasa.gov/",
                "endpoints": [
                    {
                        "method": "GET",
                        "path": "/v1/search",
                        "description": "Search the image archive"
                    }
                ]
            }
        ]

    # ------------------------------------------------------------------
    # Search and formatting helpers
    # ------------------------------------------------------------------
    def comprehensive_search(self, query: str) -> Dict[str, List[Dict[str, Any]]]:
        """Return APIs whose name or description contains *query*.

        The real implementation would aggregate results from a variety of
        sources.  Here we simply perform a case-insensitive search over the
        small in-memory catalogue.
        """
        query_lower = query.lower()
        matches = [
            api for api in self.apis
            if query_lower in api["name"].lower() or query_lower in api["description"].lower()
        ]
        # Results are grouped by a source key.  Using a single ``catalog`` source
        # keeps the structure compatible with the CLI.
        return {"catalog": matches}

    def format_search_results(self, results: Dict[str, List[Dict[str, Any]]], query: str) -> str:
        """Format search *results* as a human readable string.

        The function produces Markdown so that, when ``rich`` is available, the
        output is nicely rendered.  Tests can simply inspect the returned text.
        """
        lines = [f"# Results for '{query}'"]
        for source, apis in results.items():
            lines.append(f"## {source.title()}")
            if not apis:
                lines.append("No APIs found.")
            else:
                for api in apis:
                    lines.append(
                        f"- **{api['name']}** ({api.get('category', 'Unknown')}): {api['description']}"
                    )
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Data helpers
    # ------------------------------------------------------------------
    def get_api_endpoints(self, api_id: int) -> List[Dict[str, Any]]:
        """Return endpoint metadata for *api_id*.

        If the API is unknown an empty list is returned.
        """
        for api in self.apis:
            if api["id"] == api_id:
                return api.get("endpoints", [])
        return []

    def get_stats(self) -> Dict[str, Any]:
        """Return basic statistics about the catalog.

        The statistics mirror those expected by the CLI: total number of APIs,
        a breakdown by category and by source and some information about recent
        activity.  The latter is static but provides a useful structure for the
        user interface.
        """
        total = len(self.apis)
        by_category = Counter(api.get("category", "Unknown") for api in self.apis)
        stats = {
            "total_apis": total,
            "by_category": dict(by_category),
            # In this simplified implementation everything comes from the same
            # in-memory catalog.
            "by_source": {"catalog": total},
            # Placeholder metric used by the CLI
            "searches_last_week": 0,
        }
        return stats

    def update_database(self) -> bool:
        """Placeholder for database updates.

        Returning ``True`` indicates that an update would have been performed.
        """
        return True

    def setup_database(self) -> bool:
        """Placeholder for initial database setup."""
        return True

    def export_results(self, filepath: str) -> str:
        """Export the current catalog to *filepath* in JSON format."""
        path = Path(filepath)
        with path.open("w", encoding="utf-8") as fh:
            json.dump(self.apis, fh, indent=2)
        return str(path)
