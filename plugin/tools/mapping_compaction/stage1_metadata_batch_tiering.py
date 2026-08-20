"""
stage1_metadata_batch_tiering.py
==================================
Vendored from etl_mapping_compaction_api/stage1_metadata_batch_tiering.py.

Reads only filesystem metadata (size, mtime) — never the file body — and
assigns a size tier so large multi-mapping exports are flagged distinctly
from small single-mapping ones.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List

# Tier thresholds are deliberately simple and overridable.
SMALL_MAX_BYTES = 1 * 1024 * 1024        # < 1 MB
MEDIUM_MAX_BYTES = 5 * 1024 * 1024       # < 5 MB
# anything above MEDIUM_MAX_BYTES => "large"


@dataclass
class ObjectMetadata:
    key: str
    size_bytes: int
    last_modified: float  # epoch seconds


@dataclass
class BatchAssignment:
    key: str
    size_tier: str          # small | medium | large
    batch: str
    reason: str


def get_object_metadata(path: str) -> ObjectMetadata:
    st = os.stat(path)
    return ObjectMetadata(key=os.path.basename(path), size_bytes=st.st_size, last_modified=st.st_mtime)


def assign_batch_tier(meta: ObjectMetadata, batch_counters: dict) -> BatchAssignment:
    """batch_counters is mutated in place: {"small": n, "medium": n, "large": n}"""
    if meta.size_bytes < SMALL_MAX_BYTES:
        tier = "small"
        reason = f"{meta.size_bytes:,} bytes < {SMALL_MAX_BYTES:,} — safe to parse inline"
    elif meta.size_bytes < MEDIUM_MAX_BYTES:
        tier = "medium"
        reason = f"{meta.size_bytes:,} bytes — likely multi-mapping export, parse per-mapping"
    else:
        tier = "large"
        reason = f"{meta.size_bytes:,} bytes >= {MEDIUM_MAX_BYTES:,} — route to chunked/streaming parser lane"

    batch_counters[tier] = batch_counters.get(tier, 0) + 1
    batch = f"{tier}-group-{((batch_counters[tier] - 1) // 4) + 1}"  # 4 files per parallel batch, arbitrary but explicit
    return BatchAssignment(key=meta.key, size_tier=tier, batch=batch, reason=reason)


def tier_files(paths: List[str]) -> List[BatchAssignment]:
    counters: dict = {}
    assignments = []
    for p in paths:
        meta = get_object_metadata(p)
        assignments.append(assign_batch_tier(meta, counters))
    return assignments
