"""
stage2_state_summarizer.py
=============================
Vendored from etl_mapping_compaction_api/stage2_state_summarizer.py.

Assembly point: combines the compact IR (stage2_build_intermediate_representation),
the complexity score (stage2_complexity_classifier), and the shared-object
references (stage2_shared_object_dedup_cache) into one `MappingSummary`,
archives the raw XML bytes to a local content-addressed cache directory, and
returns the compact summary.

The persisted summary JSON is written next to the source workflow XML (see
`write_summary_json`'s `output_dir`/`file_stem` args, set by the caller in
compact_mapping.py) so it travels with the file in git — any clone or
teammate gets the benefit without reprocessing. Only the raw-XML archive
below stays under `.cache/`, rooted at `os.getcwd()` (the calling project,
not `os.path.dirname(__file__)`) — see stage1_hash_ledger_check.py's note on
why — since that's a machine-local optimization, not a shareable artifact.
"""

from __future__ import annotations

import os
import shutil
from typing import Dict

from common import FieldLineage, MappingInfo, MappingSummary, MappletInfo, SourceInfo, to_json
from stage2_build_intermediate_representation import build_intermediate_representation
from stage2_complexity_classifier import score_mapping
from stage2_shared_object_dedup_cache import SharedObjectCache

BLOB_CACHE_DIR = os.path.join(os.getcwd(), ".cache", "blob_cache")


def archive_raw_xml(source_path: str, mapping_name: str, file_hash: str) -> str:
    """Copies the raw export into a content-addressed cache directory and
    returns the reference string that stands in for a blob:// URI. The raw
    bytes never travel any further than this — everything downstream works
    off the MappingSummary only."""
    dest_dir = os.path.join(BLOB_CACHE_DIR, mapping_name)
    os.makedirs(dest_dir, exist_ok=True)
    dest_path = os.path.join(dest_dir, f"{file_hash[:12]}.xml")
    if not os.path.exists(dest_path):
        shutil.copy2(source_path, dest_path)
    return f"blob://mapping-cache/{mapping_name}/{file_hash[:12]}.xml"


def summarize_mapping(
    mapping: MappingInfo,
    mapplets: Dict[str, MappletInfo],
    all_sources: Dict[str, SourceInfo],
    source_path: str,
    file_hash: str,
    shared_cache: SharedObjectCache,
) -> MappingSummary:
    ir = build_intermediate_representation(mapping, mapplets, all_sources)
    complexity = score_mapping(mapping, mapplets)

    # Register this mapping's referenced mapplets in the shared cache (Stage
    # 2c) and get back reference records rather than full re-embedded copies.
    for ref in mapping.mapplet_refs:
        mplt = mapplets.get(ref)
        if mplt:
            shared_cache.register(mplt)

    raw_archive_ref = archive_raw_xml(source_path, mapping.name, file_hash)

    return MappingSummary(
        mapping=ir["mapping"],
        description=ir["description"],
        sources=ir["sources"],
        target=ir["target"],
        flow=ir["flow"],
        field_lineage=[FieldLineage(**fl) for fl in ir["field_lineage"]],
        shared_object_refs=ir["mapplet_refs"],
        field_counts=ir["field_counts"],
        complexity=complexity,
        raw_archive_ref=raw_archive_ref,
        source_file_hash=file_hash,
    )


def write_summary_json(summary: MappingSummary, output_dir: str, file_stem: str) -> str:
    """Persists the compact MappingSummary to a standalone, inspectable
    `<file_stem>.summary.json` file inside `output_dir`. Returns the path
    written.

    The caller (compact_mapping.py) always passes the source XML's own
    directory as `output_dir`, so the summary sits right beside the file it
    describes, and a `file_stem` derived from the source file's name (with a
    mapping-name suffix only when one file contains more than one mapping).
    """
    os.makedirs(output_dir, exist_ok=True)
    safe_name = "".join(c if c.isalnum() or c in "-_." else "_" for c in file_stem)
    dest_path = os.path.join(output_dir, f"{safe_name}.summary.json")
    with open(dest_path, "w") as f:
        f.write(to_json(summary))
    return dest_path
