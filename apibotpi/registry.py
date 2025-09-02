"""Simple API registry with search helpers."""

from __future__ import annotations

import json
from importlib import resources
from typing import Iterable, Optional, Dict, Any


def load_apis() -> Iterable[Dict[str, Any]]:
    """Return all APIs from the bundled registry."""
    with resources.files(__package__).joinpath("apis.json").open("r", encoding="utf-8") as f:
        return json.load(f)


def search_apis(*, quota: Optional[str] = None, public: Optional[bool] = None) -> Iterable[Dict[str, Any]]:
    """Search the API registry.

    Parameters
    ----------
    quota:
        Substring to match within the quota description.
    public:
        If ``True``, only return APIs in the public domain. ``False`` returns
        only non-public APIs. ``None`` disables the filter.
    """
    apis = load_apis()
    for api in apis:
        if quota and quota.lower() not in api["quota"].lower():
            continue
        if public is not None and api["public_domain"] != public:
            continue
        yield api
