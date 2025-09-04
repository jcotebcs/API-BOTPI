import json
import os
import sys
from pathlib import Path

# Ensure project root on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api_bot.core.key_manager import SecureAPIKeyManager


def test_key_manager_handles_corrupt_file(tmp_path):
    corrupt = tmp_path / "keys.json"
    corrupt.write_text("{not: valid}")
    manager = SecureAPIKeyManager(storage_path=corrupt)
    # loading should not raise and should produce empty key list
    assert manager.list_stored_keys() == []
    # storing a key should work and be persisted
    manager.store_api_key("alpha", "secret")
    data = json.loads(corrupt.read_text())
    assert "alpha" in data
