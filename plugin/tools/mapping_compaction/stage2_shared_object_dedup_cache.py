"""
stage2_shared_object_dedup_cache.py
======================================
Vendored from etl_mapping_compaction_api/stage2_shared_object_dedup_cache.py.

A JSON-backed cache keyed by `<name>@<version>` so a reusable mapplet (or
reusable Lookup/Transformation) is parsed and summarized exactly once, no
matter how many mappings in the folder use it. Mappings store only a
reference (`shared_object_refs`) instead of re-embedding the mapplet's
internal transformation list.

Rooted at `os.getcwd()` (the calling project), not `os.path.dirname(__file__)`
— see stage1_hash_ledger_check.py's note on why.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict
from typing import Dict, List

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
        """Idempotent: registers the object if new/changed, returns a small
        decision record."""
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

    def register_all(self, mapplets: Dict[str, MappletInfo]) -> List[dict]:
        return [self.register(m) for m in mapplets.values()]

    def get(self, name: str, version: str = "") -> dict:
        if version:
            return self._data.get(self._key(name, version), {})
        # fall back to newest matching name if version not specified
        matches = [v for k, v in self._data.items() if k.startswith(f"{name}@")]
        return matches[-1] if matches else {}

    def resolve_refs(self, mapplet_refs: List[str]) -> List[dict]:
        """What a mapping's `mapplet_refs` resolve to."""
        resolved = []
        for name in mapplet_refs:
            obj = self.get(name)
            if obj:
                resolved.append({"name": name, "type": obj.get("type"), "purpose": obj.get("description") or None})
            else:
                resolved.append({"name": name, "type": "unknown", "purpose": None})
        return resolved
