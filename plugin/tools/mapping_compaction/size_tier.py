"""
size_tier.py
============
Originally vendored from etl_mapping_compaction_api/stage1_metadata_batch_tiering.py,
since trimmed to what this plugin actually uses.

Reads only filesystem metadata (size, mtime) — never the file body — and
classifies a workflow export into a size tier, purely for the informational
label printed alongside each file's compaction result. The upstream
service's batch-grouping concept (`BatchAssignment.batch`, `tier_files()`)
and its "large -> chunked/streaming parser lane" framing assumed a
multi-worker service; this CLI processes one file at a time with no such
lane, so that machinery was dropped rather than carried as dead code.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

# Tier thresholds are deliberately simple and overridable.
SMALL_MAX_BYTES = 1 * 1024 * 1024        # < 1 MB
MEDIUM_MAX_BYTES = 5 * 1024 * 1024       # < 5 MB
# anything above MEDIUM_MAX_BYTES => "large"


@dataclass
class ObjectMetadata:
    key: str
    size_bytes: int
    last_modified: float  # epoch seconds


def get_object_metadata(path: str) -> ObjectMetadata:
    st = os.stat(path)
    return ObjectMetadata(key=os.path.basename(path), size_bytes=st.st_size, last_modified=st.st_mtime)


def classify_size_tier(size_bytes: int) -> str:
    if size_bytes < SMALL_MAX_BYTES:
        return "small"
    if size_bytes < MEDIUM_MAX_BYTES:
        return "medium"
    return "large"
