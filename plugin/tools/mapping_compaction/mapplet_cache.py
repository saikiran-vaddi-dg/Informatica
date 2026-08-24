"""
mapplet_cache.py
================
Originally vendored from etl_mapping_compaction_api/stage2_shared_object_dedup_cache.py,
since trimmed to what this plugin actually uses.

A JSON-backed cache keyed by `<name>@<version>` recording which reusable
mapplets (or reusable Lookups/Transformations) have been seen, so mappings
can reference a shared object (`shared_object_refs`) instead of re-embedding
its internal transformation list in every mapping summary that uses it. The
upstream service's `register_all`/`get`/`resolve_refs` lookup helpers were
unused by this plugin's actual call path (only `register` is ever called)
and were dropped rather than carried as dead code.

Rooted at `os.getcwd()` (the calling project), not `os.path.dirname(__file__)`
— see file_hash.py's note on why.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict
from typing import Dict

from common import MappletInfo

DEFAULT_CACHE_PATH = os.path.join(os.getcwd(), ".cache", "shared_object_cache.json")


class SharedObjectCache:
    def __init__(self, path: str = DEFAULT_CACHE_PATH):
        self.path = path
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self._data: Dict[str, dict] = self._load()

    def _load(self) -> dict:
        if os.path.exists(self.path):
            with open(self.path, "r") as f:
                return json.load(f)
        return {}

    def _save(self) -> None:
        with open(self.path, "w") as f:
            json.dump(self._data, f, indent=2)

    @staticmethod
    def _key(name: str, version: str) -> str:
        return f"{name}@{version or 'unversioned'}"

    def register(self, mplt: MappletInfo) -> dict:
        """Idempotent: registers the object if new, returns a small decision
        record."""
        key = self._key(mplt.name, mplt.version)
        already_cached = key in self._data
        if not already_cached:
            self._data[key] = asdict(mplt)
            self._save()
        return {
            "name": mplt.name,
            "version": mplt.version,
            "cache_key": key,
            "already_cached": already_cached,
            "action": "reference by ID" if already_cached else "parsed once, cached",
        }
