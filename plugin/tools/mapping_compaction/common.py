"""
common.py
=========
Shared data structures used by every deterministic step in the mapping
compaction pipeline (vendored from etl_mapping_compaction_api/common.py so
the coding-agent plugin carries this pipeline with it wherever it's
installed).

These dataclasses are intentionally plain (stdlib `dataclasses` + `dict`/`list`
only) so that every stage can serialize its output straight to JSON.

No third-party dependencies. Python 3.9+.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


def to_json(obj: Any, indent: int = 2) -> str:
    """Serialize a dataclass (or nested dataclasses/dicts/lists) to JSON."""

    def _default(o):
        if hasattr(o, "__dataclass_fields__"):
            return asdict(o)
        raise TypeError(f"Object of type {type(o)} is not JSON serializable")

    return json.dumps(obj, indent=indent, default=_default)


# ---------------------------------------------------------------------------
# Stage 2 — parsed / structural representation
# ---------------------------------------------------------------------------

@dataclass
class PortInfo:
    """One TRANSFORMFIELD / SOURCEFIELD / TARGETFIELD port."""
    name: str
    datatype: str = ""
    precision: str = ""
    scale: str = ""
    port_type: str = ""          # INPUT / OUTPUT / INPUT/OUTPUT / LOCAL VARIABLE
    expression: Optional[str] = None
    group: Optional[str] = None  # Router transformations tag ports with a GROUP


@dataclass
class TransformationInfo:
    """One TRANSFORMATION block (Expression, Filter, Lookup, Router, ...)."""
    name: str
    type: str
    reusable: bool = False
    description: str = ""
    ports: List[PortInfo] = field(default_factory=list)
    table_attributes: Dict[str, str] = field(default_factory=dict)  # e.g. "Filter Condition"
    groups: List[Dict[str, str]] = field(default_factory=list)      # Router GROUP elements


@dataclass
class FieldDef:
    name: str
    datatype: str = ""
    precision: str = ""
    scale: str = ""


@dataclass
class SourceInfo:
    name: str
    database_type: str = ""
    owner: str = ""
    fields: List[FieldDef] = field(default_factory=list)


@dataclass
class TargetInfo:
    name: str
    database_type: str = ""
    fields: List[FieldDef] = field(default_factory=list)


@dataclass
class ConnectorInfo:
    from_field: str
    from_instance: str
    from_instance_type: str
    to_field: str
    to_instance: str
    to_instance_type: str


@dataclass
class MappingInfo:
    """Full parsed representation of one <MAPPING> block — still 'raw-ish',
    this is the direct output of the XML parser (Stage 2a), before the
    compact IR builder (Stage 2b) strips it down further."""
    name: str
    description: str = ""
    sources: List[SourceInfo] = field(default_factory=list)
    targets: List[TargetInfo] = field(default_factory=list)
    transformations: List[TransformationInfo] = field(default_factory=list)
    mapplet_refs: List[str] = field(default_factory=list)   # names of MAPPLET instances used
    connectors: List[ConnectorInfo] = field(default_factory=list)
    instance_roles: Dict[str, str] = field(default_factory=dict)  # INSTANCE name -> "type:resolved_name"

    source_file: str = ""
    source_file_hash: str = ""


@dataclass
class MappletInfo:
    """A reusable shared object (Mapplet or reusable Transformation/Lookup)."""
    name: str
    type: str
    version: str = ""
    description: str = ""
    inner_transform_names: List[str] = field(default_factory=list)
    source_refs: List[str] = field(default_factory=list)  # SOURCE definitions consumed inside this mapplet
    inner_transformations: List["TransformationInfo"] = field(default_factory=list)  # full detail, for complexity scoring


# ---------------------------------------------------------------------------
# Stage 2 — compact intermediate representation / mapping summary
# ---------------------------------------------------------------------------

@dataclass
class FieldLineage:
    target_field: str
    source_lineage: str
    transformation_rule: str


@dataclass
class ComplexityScore:
    transformation_count: int = 0
    connector_count: int = 0
    reusable_mapplet_count: int = 0
    lookup_count: int = 0
    router_group_count: int = 0
    update_strategy_present: bool = False
    sql_override_present: bool = False
    sql_override_join_count: int = 0
    nested_expression_functions: List[str] = field(default_factory=list)
    tier: str = "simple"          # simple | moderate | complex
    recommended_model: str = "template-only"  # template-only | small-model | large-reasoning-model


@dataclass
class MappingSummary:
    """The compact object persisted per mapping, co-located next to the
    source workflow XML it was derived from. Everything else (raw XML, full
    parsed MappingInfo) is archived out-of-band and referenced by hash only.

    `source_file_hash` is what lets a re-run recognize this summary as still
    current by reading the persisted JSON itself — no separate local ledger
    needed, so the check still works after a fresh git clone."""
    mapping: str
    description: str
    sources: List[str]
    target: str
    flow: List[str]
    field_lineage: List[FieldLineage]
    shared_object_refs: List[str]
    field_counts: Dict[str, int]
    complexity: ComplexityScore
    raw_archive_ref: str  # e.g. "blob://mapping-cache/<mapping>/<hash>.xml"
    source_file_hash: str = ""  # sha256 of the workflow XML this summary was generated from
