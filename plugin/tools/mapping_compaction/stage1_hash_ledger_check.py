"""
stage1_hash_ledger_check.py
=============================
Vendored from etl_mapping_compaction_api/stage1_hash_ledger_check.py.

Provides `compute_file_hash`, the SHA-256 helper `compact_mapping.py` uses
for both naming and its skip-reprocessing check. That check itself now reads
the hash straight back out of the co-located `<stem>.summary.json` (see
`common.MappingSummary.source_file_hash`) rather than a separate ledger file,
so it still works after a fresh git clone — a machine-local `.cache/` ledger
would not. The `Ledger` class below is kept as a small, still-usable,
JSON-backed hash ledger for callers that do want that pattern; the CLI just
doesn't use it for this particular check anymore.

Unlike the standalone API (where this file lives next to the pipeline code
and any ledger sits beside it), the plugin always runs with the calling
project as the working directory — so `DEFAULT_LEDGER_PATH` is rooted at
`os.getcwd()`, not `os.path.dirname(__file__)`, keeping any such state
inside whichever project the plugin is currently operating on.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from typing import Optional

DEFAULT_LEDGER_PATH = os.path.join(os.getcwd(), ".cache", "processed_files_ledger.json")


def compute_file_hash(path: str, algo: str = "sha256", chunk_size: int = 1 << 20) -> str:
    """Stream the file in chunks so this works fine on large exports."""
    h = hashlib.new(algo)
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()


class Ledger:
    """Tiny JSON-backed ledger: { "<file_name>": {"hash": ..., "mapping_summary_ref": ...} }"""

    def __init__(self, path: str = DEFAULT_LEDGER_PATH):
        self.path = path
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self._data = self._load()

    def _load(self) -> dict:
        if os.path.exists(self.path):
            with open(self.path, "r") as f:
                return json.load(f)
        return {}

    def save(self) -> None:
        with open(self.path, "w") as f:
            json.dump(self._data, f, indent=2)

    def lookup(self, file_name: str, content_hash: str) -> dict:
        entry = self._data.get(file_name)
        if entry is not None and entry.get("hash") == content_hash:
            return {"file": file_name, "hash": content_hash, "ledger_status": "MATCH", "action": "skip"}
        return {"file": file_name, "hash": content_hash, "ledger_status": "NOT_FOUND", "action": "process"}

    def record(self, file_name: str, content_hash: str, **extra) -> None:
        self._data[file_name] = {"hash": content_hash, **extra}
        self.save()


@dataclass
class HashCheckResult:
    file_name: str
    content_hash: str
    ledger_status: str  # MATCH | NOT_FOUND
    action: str          # skip | process


def check_file(path: str, ledger: Optional[Ledger] = None) -> HashCheckResult:
    ledger = ledger or Ledger()
    file_name = os.path.basename(path)
    content_hash = compute_file_hash(path)
    decision = ledger.lookup(file_name, content_hash)
    return HashCheckResult(
        file_name=file_name,
        content_hash=content_hash,
        ledger_status=decision["ledger_status"],
        action=decision["action"],
    )
