---
name: compacted-mapping-analysis
description: Read a compact_mapping.py summary.json like an experienced Informatica ETL developer and translate its field_lineage/transformation_logic into the real SQL an "expected" query needs — the Informatica-expression-to-SQL cheat sheet and mapplet-reading rules that test-case-generation assumes but doesn't spell out. Use whenever review-agent or developer-agent needs to derive or verify the actual business-rule SQL behind a mapping, not just its JSON shape.
metadata:
  author: Datagaps
  version: 1.0.0
  category: etl-analysis
  tags: [informatica, etl, sql, transformation, mapplet, lineage]
---

# Compacted Mapping Analysis

## Why this exists

`compact_mapping.py`'s summary answers *what feeds what* (`flow`, `field_lineage`) and *what the row-level business rule is* (`transformation_logic`, and `field_lineage[].transformation_rule`) — but it reports that rule in **Informatica's own expression language** (`IIF`, `DECODE`, `ISNULL`, `||`, router `GROUP` conditions, `Lookup condition` table attributes). `test-case-generation` then needs that same rule restated as **real SQL** for the test case's expected-side query — and nothing until now spelled out how to make that translation correctly, or how to read the summary's mapplet-related fields without misinterpreting them. This skill is that missing middle step: read the JSON precisely, translate the expression, hand a review-ready SQL fragment to `test-case-generation`.

Treat this as the ETL-developer literacy layer underneath test case drafting — not a replacement for `test-case-generation` (which owns the HRD JSON shape) or `dataflow-environment-config` (which owns container/engine/`$$`-parameter resolution). Use all three together.

## Reading the summary precisely

Current schema (`schema_version: 4`) fields relevant here:

- **`field_lineage[]`** — per target field, `source_lineage` (the hop chain) and `transformation_rule` (the actual rule at the hop where tracing stopped). Since the mapplet-tracing fix, a hop chain that passes through a mapplet is written `A.f <- [MappletName]inner_instance.field <- ...` and `transformation_rule` is either a real inner expression, or an explicit `"straight rename/passthrough via mapplet 'X' (input port 'Y' -> output, no cleansing)"` / `"passthrough from source inside mapplet 'X' (no cleansing)"` string. **Read that string as-is — it already tells you whether there's a real formula to translate or nothing to do.** Don't re-derive it from the raw XML; if it says "no cleansing," the column is a straight copy, full stop.
- **`transformation_logic[]`** — entries only exist where there's something a lineage trace alone can't (fully) surface: `attributes` (SQL overrides, filter/lookup/join conditions, keyed by the exact `TABLEATTRIBUTE` name), `group_conditions` (Router branch predicates), `port_expressions` (a transformation's own port formulas — this is where an Expression transformation's real formula lives, e.g. `Exp_Integration_ID`'s `VAR_INTEGRATION_ID = VAR_ACCOUNT_TYPE || '~' || TO_CHAR(BANK_ACCOUNT_ID)`). An entry's `mapplet` field is `null` for the mapping's own transformations, or the mapplet name when the entry came from inside a referenced mapplet — **don't treat a `mapplet`-tagged entry as separate/optional scope; it's still part of the same target field's rule**, just physically defined inside a shared object.
- **`mapping_variables[]`** — `$$`-style parameters/variables referenced in any expression above. Resolve each one to a concrete literal before it goes into an expected-side query (see "Handling `$$` parameters" below) — never leave `$$NAME` sitting in generated SQL.
- **`session_partition_overrides[]`** — a session-level `Sql Query`/`Source Filter` override wins over the mapping-level one for that instance; if present, it's what production actually runs. Prefer it over the mapping's own `Sql Query` attribute when they'd otherwise conflict.
- **`complexity.tier`** — use it to calibrate depth, not to skip reading `transformation_logic` — even a `simple` mapping can carry a real formula in `port_expressions` that a shallow pass would miss.

## Informatica expression -> SQL cheat sheet

| Informatica | SQL equivalent | Notes |
|---|---|---|
| `IIF(cond, a, b)` | `CASE WHEN cond THEN a ELSE b END` | Nested `IIF` -> nested/chained `CASE WHEN` |
| `DECODE(expr, v1,r1, v2,r2, ..., default)` | `CASE expr WHEN v1 THEN r1 WHEN v2 THEN r2 ... ELSE default END` | Positional args, not named |
| `ISNULL(x)` | `x IS NULL` | Informatica's `ISNULL` is a predicate, not `NVL` |
| `IIF(ISNULL(x), y, x)` | `COALESCE(x, y)` | Extremely common pattern — recognize it as `COALESCE`, don't transliterate the `IIF` literally |
| `a \|\| b` | `a \|\| b` (Oracle/Postgres) or `CONCAT(a, b)` (SQL Server/MySQL) | Match the target platform's dialect, not Informatica's |
| `TO_CHAR(x, fmt)` / `TO_DATE(x, fmt)` | Platform-native cast/format function | Keep the format mask semantics, not the literal string |
| `SUBSTR`, `INSTR`, `LTRIM`/`RTRIM` | Usually identical or near-identical in most SQL dialects | Verify target platform's exact signature (1- vs 0-based indexing) |
| Router `GROUP` condition (`group_conditions[]`) | A `WHEN`/`WHERE` branch in the consolidated expected query | Each group is one branch of the single query test-case-generation Step 2/3 wants — never a separate mapping |
| `Filter Condition` | `WHERE <condition>` | Applies to the whole downstream flow from that transformation |
| `Lookup condition` / `Lookup Sql Override` / `Lookup table name` | `JOIN <lookup_table> ON <lookup_condition>` (or a subquery, if the lookup returns one row per key) | An unconnected/unused lookup port doesn't need a join — check `field_lineage` actually traces through it first |
| `Sql Query` / `User Defined Join` (Source Qualifier) | Already real SQL — reuse verbatim as the base `FROM`/`JOIN`, don't re-derive it | This is production's own extraction query; treat it as ground truth |
| Aggregator transformation | `GROUP BY` + aggregate functions on its output ports | Group-by columns are the non-aggregated output ports |
| Update Strategy expression | Not relevant to a single-snapshot DataCompare | A DataCompare tests row *state*, not insert/update/delete classification — note this in `_notes` rather than modeling it |

## Handling mapplets

Since the lineage-tracing fix, a mapplet is no longer an opaque stop — use what's already been traced for you:
- If `transformation_rule` names a real expression (e.g. from an inner Expression transformation), translate it with the cheat sheet above exactly like a top-level one.
- If it says "straight rename/passthrough" or "no cleansing," the expected query's column is a direct copy of the traced-back source column — don't invent a transformation that isn't there.
- If `transformation_logic` has an entry tagged with a `mapplet` name (e.g. a Source Qualifier's SQL override living inside the mapplet), that query is part of how the *source side* of the field is populated — fold it into the expected query's `FROM`/`JOIN` the same as a top-level SQL override would be.
- Only fall back to reading the raw XML if `_trace_into_mapplet` couldn't resolve a boundary (rare — happens only if a mapplet's Output Transformation wasn't found, e.g. an unusual/legacy mapplet shape); the summary itself will still show the generic "resolved inside reusable mapplet" placeholder in that case, which is your signal to go read the raw XML for that one field only.

## Handling `$$` parameters

Cross-reference `mapping_variables[]` against `dataflow-environment-config`'s resolution order (project `dataops.config.yaml` override -> workflow's own `DEFAULTVALUE` -> `on_unresolved` policy). Substitute the resolved literal into the expected query. If it resolves to blank (`on_unresolved: leave_blank`), mark that column/predicate in the test case's `_notes` as depending on an unresolved runtime parameter rather than silently hardcoding an empty string as if it were meaningful business logic.

## Worked example

From a real `field_lineage`/`transformation_logic` pair (BankDimension's `INTEGRATION_ID`):

```
transformation_logic: {
  "transformation": "Exp_Integration_ID", "type": "Expression",
  "port_expressions": [
    {"port": "VAR_ACCOUNT_TYPE", "expression": "IIF(ACCOUNT_TYPE = 'EXTERNAL','E','I')"},
    {"port": "VAR_INTEGRATION_ID", "expression": "VAR_ACCOUNT_TYPE || '~' || TO_CHAR(BANK_ACCOUNT_ID)"}
  ]
}
```

Translates to:

```sql
CASE WHEN ACCOUNT_TYPE = 'EXTERNAL' THEN 'E' ELSE 'I' END || '~' || TO_CHAR(BANK_ACCOUNT_ID)
```

— which is exactly the expression `test-case-generation`'s Step 2 expected query should compute for `INTEGRATION_ID`, not a restatement of the Informatica syntax and not a guess at what a "typical" integration ID looks like.

## Common pitfalls

- **Leaving Informatica syntax untranslated in generated SQL.** `IIF`/`DECODE`/`ISNULL` are not valid on most target platforms — an expected query that still contains them will fail to execute, not just fail the compare.
- **Guessing instead of resolving a `$$` parameter.** Always resolve through `dataflow-environment-config`, never hardcode a plausible-looking literal.
- **Treating a `mapplet`-tagged `transformation_logic` entry as out of scope.** It's the same field's rule, just defined in a shared object — fold it in.
- **Re-deriving from raw XML when the summary already answered it.** If `field_lineage`/`transformation_logic` gives a real expression or an explicit "no cleansing" note, that's the answer — a raw-XML read here is exactly the fallback this project's compaction tool exists to avoid.
