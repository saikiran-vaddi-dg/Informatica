---
name: test-case-generation
description: Generates a structured JSON test case for an Informatica workflow (Workflows/*.XML) as a DataOps DataCompare dataflow definition — actual-vs-expected sources, column mappings, and thresholds — instead of free-text prose. Use whenever review-agent drafts a test case, or a test case in HRD/ needs to be created or corrected.
metadata:
  author: Datagaps
  version: 1.0.0
  category: test-case
  tags: [test-case, dataflow, data-compare, jdbc, validation]
---

# Test Case Generation

## Why this format

A test case for a workflow in this project is not prose describing scenarios — it is a **DataCompare-shaped dataflow definition**: one source dataset representing what the workflow's logic *actually* produces, one dataset representing what the logic *should* produce (independently derived from the workflow's own SQL/expressions — either a second JDBC source, or a `SQL` transform layered on an existing source, see Step 2), and a mapping component that compares them column-by-column with explicit key columns and thresholds.

This buys two things:
- It is unambiguous — every expected result is a column mapping or a query predicate, not a sentence someone could read two ways.
- It doubles as the input to `developer-agent`'s dataflow-build step: because the shape already matches `create_dataflow`'s payload, building the dataflow is largely reusing this file, not re-deriving it.

## Instructions

### Step 1: Derive the full business logic from the workflow

Read the target workflow XML and identify, from its actual logic:
- The source query/table and any session-level SQL overrides (partitions, filters, `$$` parameters).
- Every transformation branch (CASE/IIF logic, lookups, expressions) that produces a materially different output — you'll reproduce all of them together in Step 2, not one at a time.
- The target table and load strategy (insert/update/upsert).

This is the same fact-finding review-agent does before drafting any test case — what this skill defines is the output artifact that fact-finding feeds into.

### Step 2: Model "actual" vs "expected"

- **Actual source** (`sources[0]`): a query against the workflow's real target table (`format: "QUERY"` or `"Table"`), or a query reproducing the session-level SQL override exactly as it appears in the workflow XML.
- **Expected side**: a single, independently-written query that reproduces the *entire* business rule — every CASE/IIF branch and every lookup from Step 1, not just one of them — encoded a different way than the workflow's own SQL (e.g. a `CASE WHEN` covering every branch value, with a CTE/subquery where a derived column feeds a further lookup, such as a derived ID feeding a name lookup). Not a copy-paste of the actual query — if the two sides are copies of each other, the test case proves nothing (this trap applies just as much to a SQL transform reading the actual source's own dataset as to a second JDBC query — see Common Issues).
- Model the expected side as **either**:
  - a second entry in `sources[]` (`type: "JDBC"`, its own `dataSourceName`/connection) — the default, when expected data needs its own independent query against the database; or
  - a **`SQL` transform** in a top-level `transforms[]` array, when the expected value is better derived from a dataset *already pulled into this dataflow* (typically the actual source itself, or another source already defined) rather than opening a second database connection. Shape:
    ```json
    {
      "componentName": "SQL 3",
      "type": "SQL",
      "format": "QUERY",
      "datasetName": "SQL_3",
      "sqlQuery": "SELECT ... FROM JDBC_1 ...",
      "sourceDatasetName": "JDBC_1",
      "dependencies": ["JDBC 1"],
      "excludeInNotificationIfCompletedOrPassed": "ENABLED"
    }
    ```
    Note the field is `sqlQuery`, not `query` (that name is JDBC-only); `sourceDatasetName` + `dependencies` point at the upstream `sources[]`/`transforms[]` component the `FROM` clause reads by `datasetName`. Set the dataflow's top-level `sparkSessionId` whenever `transforms[]` is used — a SQL transform executes against an already-materialized dataset in that Spark session, not a fresh database query.
- Both `sources[]` entries have `dependencies: []`; a `SQL` transform's `dependencies` list its upstream component(s) instead.
- For a JDBC source, default to `format: "Table"` with a `columns[]` list, or a single `format: "QUERY"` covering the whole target — see "When it's OK to split" below before reaching for a second, filtered query.

### Step 3: Model the comparison as one DataCompare mapping

Default to **one `mappings[]` entry** for the whole dataflow: one actual + one expected (JDBC+JDBC, or JDBC+SQL per Step 2) + one DataCompare, keyed on the row's natural/composite key. A single row-level compare over the full table already surfaces a mismatch in *any* branch — you find out which branch failed by inspecting which rows differ, not by which dataflow component failed. Do not add a separate source-pair/DataCompare group per CASE-statement value, per lookup, or per any other branch that Step 2's single query already reproduces — that multiplies components without adding coverage.

- `sourceDatasetName` / `targetDatasetName` — must reference the exact `datasetName` of the two components from Step 2, whether they came from `sources[]` or `transforms[]`.
- `columnMappings[]` — one entry per compared column: `sourceColumnName`, `targetColumnName`, `uniqueKeyColumn` (true for the natural/primary key of the row), and `ignoreColumn: true` for columns not under test (e.g. audit columns).
- `config` thresholds — start from `onlyInA`/`onlyInB`/`differences` all `"ENABLED"` with `onlyInAThreshold`/`onlyInBThreshold`/`differencesSourceThreshold`/`differencesTargetThreshold` at `"0"` (strict — any mismatch fails) unless there's a known, documented volume of tolerable drift, in which case state why in `tags` or the dataflow `description`.
- `dataTypeConversions[]` — only needed when actual/expected genuinely differ in column type (e.g. one side returns `NUMBER`, the other `VARCHAR`); omit otherwise.
- `dependencies` — the `componentName`s of both upstream components (their own `dependencies`, if either is a `SQL` transform, must already resolve within `sources[]`/`transforms[]`).

#### When it's OK to split into more than one mapping/dataflow

Only add a second JDBC-pair/DataCompare group when two parts of the logic genuinely can't be expressed in one query — a fundamentally different join or aggregation shape (e.g. one part is a row-level compare, another needs a separate aggregate/rollup compare), or a distinct load path with its own target table. A CASE/IIF branch, however complex, is never on its own a reason to split — Step 2's consolidated expected-query already covers it.

### Step 4: Fill the header

- `dataflowName` — `<WorkflowName>_TestCase` (matches the workflow file's base name).
- `engineName` — resolve via `list_engines`; don't guess.
- `folderName` — resolve via `list_folders`; ask the user which folder to use if more than one exists and none was specified — don't assume any particular folder name exists by default.
- `environment` — leave `""` unless the user specifies one.
- `sparkSessionId` — omit unless pinning to a specific session is required; set it whenever the dataflow uses a `transforms[]` `SQL` component (Step 2), since that transform runs against an already-materialized dataset in a live Spark session, not a fresh database query.
- `type` — always `"dataflow"`.
- `tags` — the workflow name and a business-area label (e.g. `["Sales", "OrderDiscount", "DataCompare"]`) — not a per-branch label, since one dataflow now covers every branch.

### Step 5: Save

Write the result to `HRD/<WorkflowName>_TestCase.json` — one file per workflow, one dataflow per test case (see "When it's OK to split" above for the narrow exception).

## Full Worked Example

```json
{
  "dataflowName": "Sales_OrderDiscount_TestCase",
  "engineName": "your_engine_name",
  "environment": "",
  "folderName": "your_folder_name",
  "type": "dataflow",
  "sources": [
    {
      "componentName": "JDBC 1",
      "type": "JDBC",
      "dataSourceName": "ORDERS_FACT",
      "format": "QUERY",
      "datasetName": "JDBC_1",
      "query": "SELECT ORDER_ID, DISCOUNT_CODE FROM ORDERS_FACT",
      "dependencies": [],
      "dataSourceLogicalName": "",
      "excludeInNotificationIfCompletedOrPassed": "ENABLED",
      "autoRepartition": "ENABLED",
      "enableTrim": "ENABLED"
    },
    {
      "componentName": "JDBC 2",
      "type": "JDBC",
      "dataSourceName": "RAW_ORDERS",
      "format": "QUERY",
      "datasetName": "JDBC_2",
      "query": "SELECT ORDER_ID, CASE WHEN ORDER_TYPE = 'PROMO' THEN PROMO_CODE WHEN ORDER_TYPE = 'CLEARANCE' THEN CLEARANCE_CODE ELSE NULL END AS DISCOUNT_CODE FROM RAW_ORDERS",
      "dependencies": [],
      "dataSourceLogicalName": "",
      "excludeInNotificationIfCompletedOrPassed": "ENABLED",
      "autoRepartition": "ENABLED",
      "enableTrim": "ENABLED"
    }
  ],
  "mappings": [
    {
      "componentName": "DataCompare 3",
      "sourceDatasetName": "JDBC_1",
      "targetDatasetName": "JDBC_2",
      "autoMap": "ENABLED",
      "applyTargetDatatypeToSource": "DISABLED",
      "datasetName": "DataCompare_3",
      "excludeInNotificationIfCompletedOrPassed": "ENABLED",
      "type": "Mapping",
      "config": {
        "onlyInA": "ENABLED",
        "onlyInB": "ENABLED",
        "differences": "ENABLED",
        "enableTrim": "ENABLED",
        "considerNullAndEmptySpaceEqual": "ENABLED",
        "automaticDataTypeConversion": "ENABLED",
        "columnWiseMismatches": "ENABLED",
        "compareIgnoreCase": "ENABLED",
        "passComponentIfDuplicatesExist": "ENABLED",
        "onlyInAThresholdUnit": "number",
        "onlyInAThreshold": "0",
        "onlyInBThresholdUnit": "number",
        "onlyInBThreshold": "0",
        "differencesSourceThresholdUnit": "number",
        "differencesSourceThreshold": "0",
        "differencesTargetThresholdUnit": "number",
        "differencesTargetThreshold": "0"
      },
      "columnMappings": [
        {
          "sourceColumnName": "ORDER_ID",
          "targetColumnName": "ORDER_ID",
          "uniqueKeyColumn": true
        },
        {
          "sourceColumnName": "DISCOUNT_CODE",
          "targetColumnName": "DISCOUNT_CODE",
          "uniqueKeyColumn": false
        }
      ],
      "dependencies": ["JDBC 1", "JDBC 2"]
    }
  ],
  "tags": ["Sales", "OrderDiscount", "DataCompare"]
}
```

One dataflow, one DataCompare, and it already covers every `ORDER_TYPE` branch (`PROMO`, `CLEARANCE`, and the implicit `ELSE`/default) — the expected query's `CASE WHEN` reproduces all of them at once. If a row mismatches, you find out which branch broke by looking at that row's `ORDER_TYPE`, not by which dataflow component failed. Only add a second source-pair/mapping group for a reason from "When it's OK to split" above (e.g. a genuinely different join/aggregation shape) — never one group per `CASE` value.

## Common Issues

**Test case "proves" nothing (always passes)**
Cause: the expected-side query is a copy of the actual-side query, so a DataCompare can never disagree. This includes a `SQL` transform whose `sqlQuery` just re-selects the actual source unchanged (e.g. `SELECT * FROM JDBC_1` compared straight back against `JDBC_1`) — reading the same upstream dataset is fine, but the query itself must still independently re-derive the expected value from it, not pass it through.
Fix: derive the expected query independently from the workflow's business rule, not from its SQL text.

**One JDBC-pair/DataCompare group per CASE branch (over-split)**
Cause: drafting a separate mapping (and often a separate filtered source pair) for every `CASE`/`IIF` value, lookup, or scenario instead of reproducing all of them in one expected-source query.
Fix: consolidate into the Step 3 default — one actual source, one expected source whose query covers every branch, one DataCompare. Split further only for a reason listed under "When it's OK to split" (Step 3) — a branch value is never such a reason.

**`componentName` collision when a split genuinely is needed**
Cause: two mapping groups reuse `"JDBC 1"`/`"DataCompare 3"` inside the same file.
Fix: number components sequentially across the whole file (`JDBC 1`, `JDBC 2`, `DataCompare 3`, `JDBC 4`, `JDBC 5`, `DataCompare 6`, ...).

**Dependency/dataset reference not found**
Cause: `sourceDatasetName`/`targetDatasetName`/`dependencies` points at a `datasetName`/`componentName` that doesn't exist in this file.
Fix: confirm the exact name of the upstream component; it must match exactly.

## Field Reference

| Field | Required | Notes |
|---|---|---|
| `dataflowName` | yes | `<WorkflowName>_TestCase` |
| `engineName` | yes | resolve via `list_engines`, don't guess |
| `folderName` | yes | resolve via `list_folders` |
| `environment` | no | default `""` |
| `type` | yes | always `"dataflow"` |
| `sparkSessionId` | no* | omit unless pinning is required; *required in practice whenever `transforms[]` is used |
| `sources[].format` | yes | `"Table"` or `"QUERY"` |
| `sources[].dataSourceName` | yes | must already be registered (`list_data_sources`) |
| `transforms[].type` | yes | always `"SQL"` |
| `transforms[].sqlQuery` | yes | note the field name — not `query` (that's JDBC-only) |
| `transforms[].sourceDatasetName` | yes | the upstream `sources[]`/`transforms[]` `datasetName` the query's `FROM` clause reads |
| `mappings[].config.*Threshold*` | yes | default to `"0"`/strict; only relax with a documented reason |
| `mappings[].columnMappings[].uniqueKeyColumn` | yes | exactly the natural key column(s) of the row |
| `tags` | no | workflow name + business-area label (not per-branch) |
