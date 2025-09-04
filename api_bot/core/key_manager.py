import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

class SecureAPIKeyManager:
    """Very small key manager used by the CLI during tests.

    Keys are stored in a JSON file located in the user's home directory.  The
    format is intentionally simple and **not** meant to be a production ready
    secure store; it merely provides persistence for unit tests and examples.
    """

    def __init__(self, storage_path: Path | None = None) -> None:
        self.storage_path = storage_path or Path.home() / ".api_bot_keys.json"
        self._load()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _load(self) -> None:
        if self.storage_path.exists():
            with self.storage_path.open("r", encoding="utf-8") as fh:
                self._data: Dict[str, Dict[str, Any]] = json.load(fh)
        else:
            self._data = {}

    def _save(self) -> None:
        with self.storage_path.open("w", encoding="utf-8") as fh:
            json.dump(self._data, fh, indent=2)

    # ------------------------------------------------------------------
    # Public API used by the CLI
    # ------------------------------------------------------------------
    def store_api_key(self, service: str, api_key: str) -> None:
        """Store or update *api_key* for *service*."""
        now = datetime.utcnow().isoformat()
        record = self._data.get(service, {})
        record.update(
            {
                "service": service,
                "api_key": api_key,
                "created": record.get("created", now),
                "last_used": record.get("last_used"),
                "usage_count": record.get("usage_count", 0),
                "active": True,
            }
        )
        self._data[service] = record
        self._save()

    def list_stored_keys(self) -> List[Dict[str, Any]]:
        """Return a list of stored key metadata.

        The actual API key is stripped from the returned dictionaries so that
        callers such as the CLI cannot accidentally expose secrets when
        displaying the information.  Only non-sensitive metadata is included in
        the result.
        """
        sanitized: List[Dict[str, Any]] = []
        for record in self._data.values():
            meta = {k: v for k, v in record.items() if k != "api_key"}
            sanitized.append(meta)
        return sanitized

    def check_key_health(self, service: str) -> Dict[str, Any]:
        """Return health information for *service*.

        The simplified implementation merely checks whether the service exists in
        the store.  Real health checks would attempt to authenticate against the
        service's API.
        """
        record = self._data.get(service)
        if not record:
            return {"status": "not_found", "message": "Key not found"}

        # Update usage metrics to provide a tiny bit of realism.  The timestamp
        # and count mirror what a real health check might record when it sends a
        # request to an upstream service.
        now = datetime.utcnow().isoformat()
        record["last_used"] = now
        record["usage_count"] = record.get("usage_count", 0) + 1
        self._save()

        return {
            "status": "healthy" if record.get("active", True) else "inactive",
            "last_used": record.get("last_used"),
            "usage_count": record.get("usage_count", 0),
        }

    def delete_key(self, service: str) -> None:
        """Remove *service* from the store if present."""
        if service in self._data:
            del self._data[service]
            self._save()

# ----------------------------------------------------------------------
# Utility class used by the CLI to produce a simple dashboard
# ----------------------------------------------------------------------
class SecureAPIDiscoveryBot(SecureAPIKeyManager):
    def get_key_dashboard(self) -> str:
        keys = self.list_stored_keys()
        if not keys:
            return "No API keys stored"
        lines = ["Stored API Keys:"]
        for key in keys:
            usage = key.get("usage_count", 0)
            lines.append(f"- {key['service']}: used {usage} times")
        return "\n".join(lines)
