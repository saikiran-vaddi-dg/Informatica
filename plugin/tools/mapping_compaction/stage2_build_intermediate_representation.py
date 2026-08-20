"""
stage2_build_intermediate_representation.py
==============================================
Vendored from etl_mapping_compaction_api/stage2_build_intermediate_representation.py.

Takes the structured `MappingInfo` produced by `stage2_xml_parser.py` and
reduces it to a compact, LLM-ready IR: an ordered pipeline `flow`, a
target-field lineage table, and field counts.

Two non-trivial pieces of real logic live here (both plain graph algorithms):
  1. `_topological_flow` — orders pipeline stages from the CONNECTOR edges
     (Kahn's algorithm), so `flow` reflects actual execution order instead
     of XML document order.
  2. `_trace_lineage` — walks CONNECTOR edges backward from each target
     field until it hits either a SOURCE or a transformation port with a
     real (non-passthrough) EXPRESSION, so the lineage table shows the
     actual transformation rule, not just the last hop.
"""

from __future__ import annotations

from collections import defaultdict, deque
from typing import Dict, List, Optional, Tuple

from common import FieldLineage, MappingInfo, MappletInfo, SourceInfo


def _topological_flow(mapping: MappingInfo) -> List[str]:
    nodes = set()
    edges: Dict[str, set] = defaultdict(set)
    indegree: Dict[str, int] = defaultdict(int)

    for c in mapping.connectors:
        nodes.add(c.from_instance)
        nodes.add(c.to_instance)
        if c.to_instance not in edges[c.from_instance]:
            edges[c.from_instance].add(c.to_instance)
            indegree[c.to_instance] += 1
            indegree.setdefault(c.from_instance, indegree.get(c.from_instance, 0))

    # Kahn's algorithm
    queue = deque(sorted(n for n in nodes if indegree.get(n, 0) == 0))
    order: List[str] = []
    indegree_work = dict(indegree)
    while queue:
        n = queue.popleft()
        order.append(n)
        for nxt in sorted(edges.get(n, [])):
            indegree_work[nxt] -= 1
            if indegree_work[nxt] == 0:
                queue.append(nxt)

    # Anything left out (cycle, or isolated node) — append deterministically
    # rather than silently dropping it.
    remaining = sorted(nodes - set(order))
    return order + remaining


def _role_label(instance_name: str, mapping: MappingInfo) -> str:
    """Authoritative role lookup: PowerCenter's own INSTANCE.TRANSFORMATION_TYPE
    tells us exactly what an instance is (Source/Target/Mapplet/Router/...)."""
    return mapping.instance_roles.get(instance_name, instance_name)


def build_flow(mapping: MappingInfo) -> List[str]:
    order = _topological_flow(mapping)
    return [_role_label(n, mapping) for n in order]


def _find_expression(mapping: MappingInfo, instance_name: str, field_name: str) -> Optional[str]:
    for t in mapping.transformations:
        if t.name != instance_name:
            continue
        for p in t.ports:
            if p.name == field_name and p.expression and p.expression != field_name:
                return p.expression
    return None


def _find_ref_field(mapping: MappingInfo, instance_name: str, field_name: str) -> Optional[str]:
    """A Router (or other multi-group) OUTPUT port carries no CONNECTOR back
    to its own INPUT port — PowerCenter links them implicitly via REF_FIELD
    instead. Without following it, backward tracing dead-ends at the router
    and misreports a real upstream expression as passthrough."""
    for t in mapping.transformations:
        if t.name != instance_name:
            continue
        for p in t.ports:
            if p.name == field_name and p.ref_field and p.ref_field != field_name:
                return p.ref_field
    return None


def _trace_lineage(mapping: MappingInfo, target_field: str, start_instance: str, start_field: str) -> Tuple[str, str]:
    """Walk connectors backward from (start_instance, start_field) until we
    hit a SOURCE or a real (non-passthrough) expression. Returns
    (source_lineage_str, transformation_rule_str)."""
    incoming: Dict[Tuple[str, str], List] = defaultdict(list)
    for c in mapping.connectors:
        incoming[(c.to_instance, c.to_field)].append(c)

    source_names = {s.name for s in mapping.sources}
    mapplet_names = set(mapping.mapplet_refs)

    visited = set()
    instance, fld = start_instance, start_field
    hops = []
    rule = "Direct copy / passthrough"

    for _ in range(25):  # generous bound; these pipelines are shallow
        if (instance, fld) in visited:
            break
        visited.add((instance, fld))
        hops.append(f"{instance}.{fld}")

        if instance in mapplet_names:
            # Mapplets are an intentional black box here (Stage 2c treats them
            # as a shared, referenced-not-expanded object).
            rule = f"resolved inside reusable mapplet '{instance}' (see shared-object cache)"
            break

        expr = _find_expression(mapping, instance, fld)
        if expr:
            rule = expr
            break

        if instance in source_names:
            break

        preds = incoming.get((instance, fld))
        if not preds:
            ref = _find_ref_field(mapping, instance, fld)
            if ref:
                fld = ref
                continue
            break
        c = preds[0]
        instance, fld = c.from_instance, c.from_field

    return " <- ".join(hops), rule


def build_field_lineage(mapping: MappingInfo) -> List[FieldLineage]:
    lineage = []
    target_names = {t.name for t in mapping.targets}
    for c in mapping.connectors:
        if c.to_instance not in target_names:
            continue
        source_lineage, rule = _trace_lineage(mapping, c.to_field, c.from_instance, c.from_field)
        lineage.append(
            FieldLineage(
                target_field=c.to_field,
                source_lineage=source_lineage,
                transformation_rule=rule,
            )
        )
    return lineage


def build_field_counts(mapping: MappingInfo, all_sources: Optional[Dict[str, "SourceInfo"]] = None,
                        resolved_source_names: Optional[List[str]] = None) -> dict:
    if all_sources and resolved_source_names:
        source_field_total = sum(len(all_sources[n].fields) for n in resolved_source_names if n in all_sources)
    else:
        source_field_total = sum(len(s.fields) for s in mapping.sources)
    return {
        "source_fields": source_field_total,
        "target_fields": sum(len(t.fields) for t in mapping.targets),
        "transform_ports": sum(len(t.ports) for t in mapping.transformations),
    }


# TABLEATTRIBUTE names that carry row-level business logic (a SQL override,
# a join/filter/lookup predicate, an update-strategy condition) as opposed to
# operational/performance settings (cache sizing, tracing level, formatting)
# that don't affect what data comes out.
LOGIC_ATTRIBUTE_NAMES = {
    "Sql Query",
    "Source Filter",
    "Lookup condition",
    "Lookup Source Filter",
    "Lookup Sql Override",
    "Lookup table name",
    "Filter Condition",
    "User Defined Join",
    "Pre SQL",
    "Post SQL",
    "Update Strategy Expression",
    "Update Dynamic Cache Condition",
    "Insert Else Update",
    "Update Else Insert",
}


def build_transformation_logic(mapping: MappingInfo) -> List[dict]:
    """Per-transformation business logic that lives in TABLEATTRIBUTEs or
    GROUP conditions rather than the port/connector graph — SQL overrides,
    lookup/filter/join conditions, router branch predicates. field_lineage
    traces *what* feeds a target field; this captures *why* a join includes
    what it does or a router sends a row down one branch vs another, which
    the port graph alone can't show without reading the raw XML."""
    entries = []
    for t in mapping.transformations:
        attrs = {k: v for k, v in t.table_attributes.items() if k in LOGIC_ATTRIBUTE_NAMES}
        group_conditions = [
            {"name": g["name"], "condition": g["condition"]}
            for g in t.groups
            if g.get("condition")
        ]
        if attrs or group_conditions:
            entries.append(
                {
                    "transformation": t.name,
                    "type": t.type,
                    "attributes": attrs,
                    "group_conditions": group_conditions,
                }
            )
    return entries


def resolve_sources(mapping: MappingInfo, mapplets: Dict[str, MappletInfo]) -> List[str]:
    """Sources aren't always wired directly into the top-level mapping —
    often they're consumed inside a referenced mapplet instead. Resolve
    transitively through one level of mapplet nesting so the IR reports the
    true originating tables."""
    direct = [s.name for s in mapping.sources]
    via_mapplets: List[str] = []
    for ref in mapping.mapplet_refs:
        mplt = mapplets.get(ref)
        if mplt:
            via_mapplets.extend(mplt.source_refs)
    # de-dupe, preserve order
    seen = set()
    ordered = []
    for name in direct + via_mapplets:
        if name and name not in seen:
            seen.add(name)
            ordered.append(name)
    return ordered


def build_intermediate_representation(
    mapping: MappingInfo,
    mapplets: Optional[Dict[str, MappletInfo]] = None,
    all_sources: Optional[Dict[str, SourceInfo]] = None,
) -> dict:
    """Returns the partial IR — complexity scoring (Stage 2e), shared-object
    resolution (Stage 2c) and the raw-archive pointer (Stage 2f) are merged
    in by `stage2_state_summarizer.py`."""
    mapplets = mapplets or {}
    resolved_sources = resolve_sources(mapping, mapplets)
    return {
        "mapping": mapping.name,
        "description": mapping.description,
        "sources": resolved_sources,
        "target": mapping.targets[0].name if mapping.targets else None,
        "flow": build_flow(mapping),
        "field_lineage": [fl.__dict__ for fl in build_field_lineage(mapping)],
        "field_counts": build_field_counts(mapping, all_sources, resolved_sources),
        "mapplet_refs": list(mapping.mapplet_refs),
        "mapping_variables": [mv.__dict__ for mv in mapping.mapping_variables],
        "session_partition_overrides": [o.__dict__ for o in mapping.session_partition_overrides],
        "transformation_logic": build_transformation_logic(mapping),
    }
