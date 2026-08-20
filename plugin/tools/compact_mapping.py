#!/usr/bin/env python3
"""
Deterministically compact one or more Informatica PowerCenter POWERMART
workflow XML exports into a per-mapping `MappingSummary` JSON: topological
flow, target-field lineage (traced back to its real transformation rule,
not just the last hop), resolved sources (including sources that only exist
inside a referenced mapplet), shared-mapplet dedup, and a rule-based
complexity tier + recommended model/effort level.

This is a portable, stdlib-only CLI wrapper around the pipeline vendored
into tools/mapping_compaction/ (originally built as etl_mapping_compaction_api,
a standalone FastAPI service in this same repo) — no server needed to use it
from an agent's Bash tool.

Usage:
    python tools/compact_mapping.py Workflows/<WorkflowName>.XML [--force]
    python tools/compact_mapping.py Workflows/A.XML Workflows/B.XML

Output: one compact JSON summary per <MAPPING> block, printed to stdout and
persisted right next to the source file, as
<same-directory-as-the-XML>/<WorkflowName>.summary.json (or
<WorkflowName>.<MappingName>.summary.json when one file contains more than
one mapping). Committing this alongside the XML means any clone or teammate
gets the compacted view immediately — no reprocessing, no reliance on
machine-local state.

Re-running against an unchanged file (same content hash, read back from the
existing summary's own `source_file_hash` field) skips reprocessing and
reports the already-persisted summary path instead — pass --force to
reprocess anyway. Only the mapplet dedup cache and a raw-XML archive (a
machine-local optimization, not meant to be shared) live under <cwd>/.cache/,
rooted at wherever this is invoked from (the target project), not inside
this plugin's own install location.

Read the printed complexity tier before deciding how much manual scrutiny a
mapping needs: `simple` mappings are template-shaped noise-free loads;
`complex` ones have branching/lookup/SQL-override logic worth a closer read
before drafting a test case. This pipeline doesn't parse Mapping Variables
or session-level per-partition SQL overrides — read the raw workflow XML
directly for those.
"""
import glob
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "mapping_compaction"))

from stage1_hash_ledger_check import compute_file_hash  # noqa: E402
from stage1_metadata_batch_tiering import assign_batch_tier, get_object_metadata  # noqa: E402
from stage2_shared_object_dedup_cache import SharedObjectCache  # noqa: E402
from stage2_state_summarizer import summarize_mapping, write_summary_json  # noqa: E402
from stage2_xml_parser import parse_powercenter_export  # noqa: E402
from common import to_json  # noqa: E402


def find_existing_summaries(dest_dir, workflow_stem):
    """Co-located summary file(s) for this workflow, if any: the single-file
    form (`<stem>.summary.json`) plus the multi-mapping form
    (`<stem>.<MappingName>.summary.json`)."""
    single = os.path.join(dest_dir, f"{workflow_stem}.summary.json")
    paths = [single] if os.path.exists(single) else []
    paths.extend(sorted(glob.glob(os.path.join(dest_dir, f"{workflow_stem}.*.summary.json"))))
    return paths


def process_file(path, shared_cache, batch_counters, force):
    original_name = os.path.basename(path)
    dest_dir = os.path.dirname(os.path.abspath(path)) or "."
    workflow_stem = os.path.splitext(original_name)[0]
    meta = get_object_metadata(path)
    tier = assign_batch_tier(meta, batch_counters)
    file_hash = compute_file_hash(path)

    existing = find_existing_summaries(dest_dir, workflow_stem)
    if existing and not force:
        try:
            with open(existing[0]) as f:
                prior_hash = json.load(f).get("source_file_hash")
        except (OSError, json.JSONDecodeError):
            prior_hash = None
        if prior_hash == file_hash:
            print(f"=== {original_name} ===")
            print(f"unchanged since last run (hash {file_hash[:12]}...) — skipping reprocessing.")
            for p in existing:
                print(f"  existing summary: {p}")
            print("  (pass --force to reprocess anyway)\n")
            return

    try:
        parsed = parse_powercenter_export(path, file_hash=file_hash)
    except Exception as exc:
        print(f"ERROR parsing '{original_name}': {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"=== {original_name} ({tier.size_tier}, {meta.size_bytes:,} bytes) ===\n")

    # Drop any prior-run summaries before writing the current set — covers
    # the case where this file's mapping count changed since last time.
    for p in existing:
        os.remove(p)

    multi_mapping = len(parsed["mappings"]) > 1
    for mapping in parsed["mappings"]:
        summary = summarize_mapping(
            mapping, parsed["mapplets"], parsed["sources"], path, file_hash, shared_cache
        )
        file_stem = f"{workflow_stem}.{summary.mapping}" if multi_mapping else workflow_stem
        json_path = write_summary_json(summary, output_dir=dest_dir, file_stem=file_stem)
        summary_bytes = len(to_json(summary, indent=0))
        reduction_pct = round(100 * (1 - summary_bytes / meta.size_bytes), 1) if meta.size_bytes else 0.0

        print(f"--- {summary.mapping} ---")
        print(f"complexity: {summary.complexity.tier} -> recommended effort: {summary.complexity.recommended_model}")
        print(f"size: {summary_bytes:,} bytes vs {meta.size_bytes:,} bytes raw ({reduction_pct}% smaller)")
        print(f"persisted: {json_path}\n")
        print(to_json(summary))
        print()


def main():
    args = sys.argv[1:]
    force = "--force" in args
    paths = [a for a in args if a != "--force"]
    if not paths:
        print("Usage: python tools/compact_mapping.py <Workflow.XML> [<Workflow2.XML> ...] [--force]", file=sys.stderr)
        sys.exit(1)

    shared_cache = SharedObjectCache()
    batch_counters = {}

    for path in paths:
        if not os.path.exists(path):
            print(f"ERROR: '{path}' not found", file=sys.stderr)
            sys.exit(1)
        process_file(path, shared_cache, batch_counters, force)


if __name__ == "__main__":
    main()
