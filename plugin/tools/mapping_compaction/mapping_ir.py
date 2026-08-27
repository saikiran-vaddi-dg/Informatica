"""
mapping_ir.py
=============
Originally vendored from etl_mapping_compaction_api/stage2_build_intermediate_representation.py.

Takes the structured `MappingInfo` produced by `xml_parser.py` and
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

import re
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


def _find_expression_in(transformations, instance_name: str, field_name: str) -> Optional[str]:
    for t in transformations:
        if t.name != instance_name:
            continue
        for p in t.ports:
            if p.name == field_name and p.expression and p.expression != field_name:
                return p.expression
    return None


def _find_ref_field_in(transformations, instance_name: str, field_name: str) -> Optional[str]:
    """A Router (or other multi-group) OUTPUT port carries no CONNECTOR back
    to its own INPUT port — PowerCenter links them implicitly via REF_FIELD
    instead. Without following it, backward tracing dead-ends at the router
    and misreports a real upstream expression as passthrough."""
    for t in transformations:
        if t.name != instance_name:
            continue
        for p in t.ports:
            if p.name == field_name and p.ref_field and p.ref_field != field_name:
                return p.ref_field
    return None


_LEADING_BLOCK_COMMENT_RE = re.compile(r"^\s*/\*.*?\*/\s*", re.DOTALL)
_TRAILING_SQL_ALIAS_RE = re.compile(
    r"\s+AS\s+(?:\"[^\"]+\"|\[[^\]]+\]|`[^`]+`|[A-Za-z_][A-Za-z0-9_#$]*)\s*$",
    re.IGNORECASE,
)
_SIMPLE_COLUMN_REF_RE = re.compile(r"^(?:[A-Za-z_][A-Za-z0-9_#$]*\.)*([A-Za-z_][A-Za-z0-9_#$]*)$")


def _strip_sql_alias(expr: str) -> str:
    expr = _LEADING_BLOCK_COMMENT_RE.sub("", expr.strip())
    m = _TRAILING_SQL_ALIAS_RE.search(expr)
    if m:
        return expr[:m.start()].strip()
    return expr


def _is_word_boundary(sql: str, index: int) -> bool:
    if index < 0 or index >= len(sql):
        return True
    ch = sql[index]
    return not (ch.isalnum() or ch == "_")


def _extract_select_items(sql: str) -> List[str]:
    upper_sql = sql.upper()
    select_match = re.search(r"\bSELECT\b", upper_sql)
    if not select_match:
        return []

    start = select_match.end()
    depth = 0
    in_single_quote = False
    in_double_quote = False
    end = len(sql)
    i = start
    while i < len(sql):
        ch = sql[i]
        if in_single_quote:
            if ch == "'" and i + 1 < len(sql) and sql[i + 1] == "'":
                i += 2
                continue
            if ch == "'":
                in_single_quote = False
        elif in_double_quote:
            if ch == '"':
                in_double_quote = False
        else:
            if ch == "'":
                in_single_quote = True
            elif ch == '"':
                in_double_quote = True
            elif ch == "(":
                depth += 1
            elif ch == ")" and depth > 0:
                depth -= 1
            elif (
                depth == 0
                and upper_sql[i:i + 4] == "FROM"
                and _is_word_boundary(sql, i - 1)
                and _is_word_boundary(sql, i + 4)
            ):
                end = i
                break
        i += 1

    select_body = sql[start:end].strip()
    if not select_body:
        return []

    items: List[str] = []
    current: List[str] = []
    depth = 0
    in_single_quote = False
    in_double_quote = False
    i = 0
    while i < len(select_body):
        ch = select_body[i]
        if in_single_quote:
            current.append(ch)
            if ch == "'" and i + 1 < len(select_body) and select_body[i + 1] == "'":
                current.append(select_body[i + 1])
                i += 2
                continue
            if ch == "'":
                in_single_quote = False
        elif in_double_quote:
            current.append(ch)
            if ch == '"':
                in_double_quote = False
        else:
            if ch == "'":
                in_single_quote = True
                current.append(ch)
            elif ch == '"':
                in_double_quote = True
                current.append(ch)
            elif ch == "(":
                depth += 1
                current.append(ch)
            elif ch == ")" and depth > 0:
                depth -= 1
                current.append(ch)
            elif ch == "," and depth == 0:
                item = "".join(current).strip()
                if item:
                    items.append(item)
                current = []
            else:
                current.append(ch)
        i += 1

    tail = "".join(current).strip()
    if tail:
        items.append(tail)
    return items


def _session_sql_expression_for_port(mapping: MappingInfo, instance_name: str, field_name: str) -> Optional[str]:
    sq_transform = next(
        (t for t in mapping.transformations if t.name == instance_name and "source qualifier" in t.type.lower()),
        None,
    )
    if sq_transform is None:
        return None

    port_names = [p.name for p in sq_transform.ports]
    if field_name not in port_names:
        return None
    field_index = port_names.index(field_name)

    candidate_sqls: List[str] = []
    candidate_sqls.extend(
        override.attribute_value
        for override in mapping.session_partition_overrides
        if override.instance_name == instance_name
        and override.attribute_name == "Sql Query"
        and override.attribute_value
    )
    base_sql = sq_transform.table_attributes.get("Sql Query")
    if base_sql:
        candidate_sqls.append(base_sql)

    seen = set()
    derived_expressions: List[str] = []
    for sql in candidate_sqls:
        select_items = _extract_select_items(sql)
        if field_index >= len(select_items):
            continue
        expression = _strip_sql_alias(select_items[field_index])
        collapsed = " ".join(expression.split())
        if not collapsed or collapsed.upper() == "NULL" or collapsed in seen:
            continue
        seen.add(collapsed)

        simple_ref = _SIMPLE_COLUMN_REF_RE.fullmatch(expression.strip())
        if simple_ref:
            continue
        derived_expressions.append(expression)

    if not derived_expressions:
        return None

    if len(derived_expressions) == 1:
        return derived_expressions[0]

    return "session-specific SQL override:\n" + "\n---\n".join(derived_expressions)


def _walk_backward(connectors, transformations, start_instance: str, start_field: str, is_stop, find_derived_expression=None):
    """Generic backward walk over one connector graph, shared by both the
    top-level mapping trace and the mapplet-internal trace below (they only
    differ in which connector/transformation lists they walk and what counts
    as a stopping instance). `is_stop(instance) -> (stop: bool, rule_override:
    Optional[str])` lets the caller decide what ends the walk and whether
    that should override the reported rule (a mapplet boundary does; a plain
    source does not, since a real expression may still be found first).
    Returns (hops, rule, stopped_at_instance_or_None)."""
    incoming: Dict[Tuple[str, str], List] = defaultdict(list)
    for c in connectors:
        incoming[(c.to_instance, c.to_field)].append(c)

    visited = set()
    instance, fld = start_instance, start_field
    hops: List[str] = []
    rule = "Direct copy / passthrough"
    stopped_at: Optional[str] = None

    for _ in range(25):  # generous bound; these pipelines are shallow
        if (instance, fld) in visited:
            break
        visited.add((instance, fld))
        hops.append(f"{instance}.{fld}")

        stop, override = is_stop(instance)
        if stop:
            if override:
                rule = override
            stopped_at = instance
            break

        expr = _find_expression_in(transformations, instance, fld)
        if expr:
            rule = expr
            break

        if find_derived_expression is not None:
            derived_expr = find_derived_expression(instance, fld)
            if derived_expr:
                rule = derived_expr
                break

        preds = incoming.get((instance, fld))
        if not preds:
            ref = _find_ref_field_in(transformations, instance, fld)
            if ref:
                fld = ref
                continue
            break
        c = preds[0]
        instance, fld = c.from_instance, c.from_field

    return hops, rule, stopped_at


def _mapplet_boundary_transform(mplt: MappletInfo, type_substr: str):
    """A mapplet's own Input/Output Transformation — the intrinsic
    pseudo-transformations that expose its interface — identified by type
    rather than a fixed name, since PowerCenter names them per-mapplet."""
    for t in mplt.inner_transformations:
        if type_substr.lower() in (t.type or "").lower():
            return t
    return None


def _trace_into_mapplet(mplt: MappletInfo, boundary_field: str) -> Tuple[List[str], str]:
    """Continue backward-tracing inside a mapplet's own connector graph,
    starting at its Output Transformation port matching the field the caller
    wired to, instead of stopping at the boundary with a generic
    placeholder. Distinguishes a straight rename/passthrough of the
    mapplet's own input (or a source read directly inside it) from real
    cleansing logic on one of its inner transformations' ports."""
    output_transform = _mapplet_boundary_transform(mplt, "Output Transformation")
    if output_transform is None:
        # Older/partial mapplet capture (no Output Transformation found) —
        # fall back to the old placeholder rather than tracing blind.
        return [], f"resolved inside reusable mapplet '{mplt.name}' (see shared-object cache)"

    input_transform = _mapplet_boundary_transform(mplt, "Input Transformation")
    input_name = input_transform.name if input_transform else None
    source_instance_names = set(mplt.source_instance_names)

    def is_stop(instance):
        if instance == input_name or instance in source_instance_names:
            return True, None
        return False, None

    hops, rule, stopped_at = _walk_backward(
        mplt.inner_connectors, mplt.inner_transformations, output_transform.name, boundary_field, is_stop
    )

    if rule == "Direct copy / passthrough" and stopped_at is not None:
        end_field = hops[-1].split(".", 1)[1] if hops else boundary_field
        if stopped_at == input_name:
            if end_field == boundary_field:
                rule = (
                    f"straight rename/passthrough via mapplet '{mplt.name}' "
                    f"(input port '{end_field}' -> output, no cleansing)"
                )
            else:
                rule = (
                    f"renamed inside mapplet '{mplt.name}': input port '{end_field}' "
                    f"-> output port '{boundary_field}' (no cleansing)"
                )
        else:
            rule = f"passthrough from source inside mapplet '{mplt.name}' (no cleansing)"

    return hops, rule


def _trace_lineage(
    mapping: MappingInfo, mapplets: Dict[str, MappletInfo], target_field: str, start_instance: str, start_field: str
) -> Tuple[str, str]:
    """Walk connectors backward from (start_instance, start_field) until we
    hit a SOURCE or a real (non-passthrough) expression. When the trail leads
    into a referenced mapplet, keeps walking inside that mapplet's own
    connector graph (see `_trace_into_mapplet`) instead of stopping at the
    boundary — so a straight rename/passthrough field is reported as such,
    and a real cleansing formula inside the mapplet becomes the
    transformation_rule, rather than a generic "see shared-object cache"
    placeholder. Returns (source_lineage_str, transformation_rule_str)."""
    source_names = {s.name for s in mapping.sources}
    mapplet_names = set(mapping.mapplet_refs)

    def is_stop(instance):
        if instance in mapplet_names or instance in source_names:
            return True, None
        return False, None

    def find_derived_expression(instance, field):
        return _session_sql_expression_for_port(mapping, instance, field)

    hops, rule, stopped_at = _walk_backward(
        mapping.connectors, mapping.transformations, start_instance, start_field, is_stop, find_derived_expression
    )

    if stopped_at in mapplet_names:
        boundary_field = hops[-1].split(".", 1)[1]
        mplt = mapplets.get(stopped_at)
        if mplt and mplt.inner_transformations:
            inner_hops, inner_rule = _trace_into_mapplet(mplt, boundary_field)
            hops.extend(f"[{stopped_at}]{h}" for h in inner_hops)
            rule = inner_rule
        else:
            rule = f"resolved inside reusable mapplet '{stopped_at}' (see shared-object cache)"

    return " <- ".join(hops), rule


def build_field_lineage(mapping: MappingInfo, mapplets: Optional[Dict[str, MappletInfo]] = None) -> List[FieldLineage]:
    mapplets = mapplets or {}
    lineage = []
    target_names = {t.name for t in mapping.targets}
    for c in mapping.connectors:
        if c.to_instance not in target_names:
            continue
        source_lineage, rule = _trace_lineage(mapping, mapplets, c.to_field, c.from_instance, c.from_field)
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


def build_transformation_logic(mapping: MappingInfo, mapplets: Optional[Dict[str, MappletInfo]] = None) -> List[dict]:
    """Per-transformation business logic that a port/connector-graph trace
    can't (always) surface:
      - TABLEATTRIBUTEs / GROUP conditions — SQL overrides, lookup/filter/join
        conditions, router branch predicates. These live in per-instance
        configuration, not a port expression, so field_lineage never sees them.
      - A port's own EXPRESSION — an Expression (or Aggregator/Rank/...)
        transformation's real formula. field_lineage only reports one of
        these if it's the exact hop a target field's trace happens to pass
        through; a formula on a port nothing downstream directly maps to (or
        one a trace never reaches because a later hop resolves inside a
        mapplet) would otherwise be invisible.

    Also walks each referenced mapplet's own inner transformations — tagged
    with which mapplet they came from via the `mapplet` field — since the
    same two kinds of logic (a Source Qualifier's SQL override, an
    Expression's cleansing formula) can live inside a mapplet just as
    easily, and previously only showed up in `field_lineage` as a generic
    "resolved inside reusable mapplet" placeholder with no detail at all."""
    entries: List[dict] = []

    def _collect(transformations, mapplet_name: Optional[str] = None) -> None:
        for t in transformations:
            attrs = {k: v for k, v in t.table_attributes.items() if k in LOGIC_ATTRIBUTE_NAMES}
            group_conditions = [
                {"name": g["name"], "condition": g["condition"]}
                for g in t.groups
                if g.get("condition")
            ]
            port_expressions = [
                {"port": p.name, "expression": p.expression}
                for p in t.ports
                if p.expression and p.expression != p.name
            ]
            if attrs or group_conditions or port_expressions:
                entries.append(
                    {
                        "transformation": t.name,
                        "type": t.type,
                        "attributes": attrs,
                        "group_conditions": group_conditions,
                        "port_expressions": port_expressions,
                        "mapplet": mapplet_name,
                    }
                )

    _collect(mapping.transformations)

    mapplets = mapplets or {}
    for ref in mapping.mapplet_refs:
        mplt = mapplets.get(ref)
        if mplt:
            _collect(mplt.inner_transformations, mapplet_name=mplt.name)

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
        "field_lineage": [fl.__dict__ for fl in build_field_lineage(mapping, mapplets)],
        "field_counts": build_field_counts(mapping, all_sources, resolved_sources),
        "mapplet_refs": list(mapping.mapplet_refs),
        "mapping_variables": [mv.__dict__ for mv in mapping.mapping_variables],
        "session_partition_overrides": [o.__dict__ for o in mapping.session_partition_overrides],
        "transformation_logic": build_transformation_logic(mapping, mapplets),
    }
