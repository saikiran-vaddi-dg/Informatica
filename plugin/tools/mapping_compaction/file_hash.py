"""
file_hash.py
============
Originally vendored from etl_mapping_compaction_api/stage1_hash_ledger_check.py,
since trimmed to what this plugin actually uses.

`compact_mapping.py`'s skip-reprocessing check reads a file's prior hash
straight back out of the co-located `<stem>.summary.json` (see
`common.MappingSummary.source_file_hash`) rather than a separate ledger file,
so it still works after a fresh git clone — a machine-local `.cache/` ledger
would not. The upstream service's `Ledger`/`HashCheckResult` classes existed
for a ledger-based variant of that check this plugin doesn't use; they were
dropped here rather than carried as dead code.
"""

from __future__ import annotations

import hashlib


def compute_file_hash(path: str, algo: str = "sha256", chunk_size: int = 1 << 20) -> str:
    """Stream the file in chunks so this works fine on large exports."""
    h = hashlib.new(algo)
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()
