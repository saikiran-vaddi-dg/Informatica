"""
complexity_scorer.py
=====================
Originally vendored from etl_mapping_compaction_api/stage2_complexity_classifier.py.

Deterministic, rule-based — no LLM call. Scores a parsed mapping on
concrete, countable signals (transformation count, connector count, lookup/
router/update-strategy presence, SQL-override join count, nested-function
usage in expressions) and assigns a tier that can be used to calibrate how
much review depth / model effort a mapping needs.
"""

from __future__ import annotations

import re
from typing import Dict, List

from common import ComplexityScore, MappingInfo, MappletInfo

# Expression functions whose presence signals real logic complexity, not a
# passthrough. Deliberately simple substring/regex matching — this is meant
# to be a fast, explainable heuristic, not a parser for PowerCenter's
# expression grammar.
COMPLEX_FUNCTIONS = ["IIF(", "DECODE(", "LOOKUP(", "AGGREGATE(", "SUM(", "COUNT(", "AVG(", "ISNULL("]

SQL_FROM_TABLE_COMMA = re.compile(r"\bFROM\b(.*?)\bWHERE\b", re.IGNORECASE | re.DOTALL)


def _count_sql_joins(sql: str) -> int:
    if not sql:
        return 0
    explicit_joins = len(re.findall(r"\bJOIN\b", sql, re.IGNORECASE))
    # crude comma-join count in the FROM clause, e.g. "FROM a, b, c WHERE ..."
    m = SQL_FROM_TABLE_COMMA.search(sql)
    comma_joins = m.group(1).count(",") if m else 0
    return explicit_joins + comma_joins


def score_mapping(mapping: MappingInfo, mapplets: Dict[str, MappletInfo]) -> ComplexityScore:
    score = ComplexityScore()
    score.transformation_count = len(mapping.transformations)
    score.connector_count = len(mapping.connectors)
    score.reusable_mapplet_count = len(mapping.mapplet_refs)

    # Mapplets are a reference, not re-embedded (see mapplet_cache.py) — but
    # for scoring purposes we still need to look INSIDE them once, otherwise
    # a mapping whose real logic lives entirely inside a referenced mapplet
    # would be mis-scored as "simple". This does NOT count toward
    # `transformation_count` — it only feeds the qualitative signals below.
    mapplet_transforms: List = []
    for ref in mapping.mapplet_refs:
        mplt = mapplets.get(ref)
        if mplt:
            mapplet_transforms.extend(mplt.inner_transformations)

    nested_fns: List[str] = []
    for t in list(mapping.transformations) + mapplet_transforms:
        t_type_lower = t.type.lower()
        if "lookup" in t_type_lower:
            score.lookup_count += 1
        if "router" in t_type_lower:
            score.router_group_count += len([g for g in t.groups if g.get("type", "").startswith("OUTPUT")])
        if "update strategy" in t_type_lower:
            score.update_strategy_present = True

        sql_override = t.table_attributes.get("Sql Query") or t.table_attributes.get("Lookup Sql Override")
        if sql_override:
            score.sql_override_present = True
            score.sql_override_join_count = max(score.sql_override_join_count, _count_sql_joins(sql_override))

        for p in t.ports:
            if not p.expression:
                continue
            for fn in COMPLEX_FUNCTIONS:
                if fn in p.expression.upper().replace(" ", "") or fn in p.expression.upper():
                    label = fn.rstrip("(")
                    if label not in nested_fns:
                        nested_fns.append(label)

    score.nested_expression_functions = nested_fns

    # --- rule-based tiering -------------------------------------------------
    signal_count = sum(
        [
            score.transformation_count > 3,
            score.lookup_count > 0,
            score.router_group_count > 0,
            score.update_strategy_present,
            score.sql_override_present,
            len(score.nested_expression_functions) >= 2,
            score.reusable_mapplet_count > 1,
        ]
    )

    if score.transformation_count <= 2 and signal_count == 0:
        score.tier = "simple"
        score.recommended_model = "template-only"
    elif signal_count <= 2:
        score.tier = "moderate"
        score.recommended_model = "small-model"
    else:
        score.tier = "complex"
        score.recommended_model = "large-reasoning-model"

    return score
