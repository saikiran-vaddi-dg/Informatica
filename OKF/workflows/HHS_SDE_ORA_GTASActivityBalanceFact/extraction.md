---
generated:
  by: developer-agent
  at: "2026-08-27T10:08:59+00:00"
  commit: 7bc5038c7faddce153aeda6dc132966e6f2deca0
---

# HHS_SDE_ORA_GTASActivityBalanceFact — Extraction

## Description

SDE mapping that extracts GTAS (Governmentwide Treasury Account Symbol)
activity-balance journal-line detail from Oracle EBS Federal Financials
(`FV_GTAS_ACTIVITY_BALANCES`), filtered incrementally via a Source Qualifier
SQL override (`CREATION_DATE >= TO_DATE('$$LAST_EXTRACT_DATE', ...)`),
through a single Expression transformation (`EXP_GTASACTIVITY`) that derives
`DATASOURCE_NUM_ID` and looks up `PROVIDER_RECIPNT_NAME`, into staging table
`W_GTAS_ACTIVITY_BALANCES_FS`.

`PROVIDER_RECIPNT_NAME` is resolved via a three-way conditional lookup keyed
off `PROVIDER_RECIPNT_ID` (itself passed through from
`FV_GTAS_ACTIVITY_BALANCES.PARENT_AWARD_ID`):
- 7-character id not starting with `075` → `LKP_PROVD_RECP` keyed on
  `SUBSTR(id,2,2)` (lookup source: `FND_FLEX_VALUES_VL` filtered to
  `VALUE_CATEGORY = 'HHS_TP_ELIMINATION_CODE'`).
- id starting with `075` → `LKP_INTRA_HHS_ELI` keyed on `SUBSTR(id,4,4)`
  (lookup source: `W_GTAS_INTRAHHS_D.TP_MAIN_ACT`).
- else → `LKP_PROVD_RECP` keyed on the full id.

## Key Columns

- **No declared unique key in the raw mapping** — the test case's DataCompare
  uses a composite key of `CCID, PERIOD_NUM, SET_OF_BOOKS_ID, JE_HEADER_ID,
  JE_LINE_NUM, AE_HEADER_ID, AE_LINE_NUM` (journal/accounting-event line
  identifiers) since no single natural key is exposed by the source.
- **Derived via Expression**: `DATASOURCE_NUM_ID` = `$$DATASOURCE_NUM_ID`
  (parameterized, no workflow default found) — modeled in the test case as
  `CAST(NULL AS NUMBER)` with `ignoreColumn: true`.
- **Renamed passthrough**: `PROVIDER_RECIPNT_ID` <- source
  `PARENT_AWARD_ID` (not the target's own `PARENT_AWARD_ID`, which is a
  separate passthrough field).
- **Conditional lookup (nested IIF)**: `PROVIDER_RECIPNT_NAME` — see
  Description above for the three-branch logic; modeled in the test case as
  a nested `CASE`/correlated-subquery expression against `LKP_PROVD_RECP` and
  `W_GTAS_INTRAHHS_D`.
- **Unresolved (target-only, not populated)**: `INTEGRATION_ID` — the
  compact summary's `field_lineage` shows `EXP_GTASACTIVITY.out_INTEGRATION_ID`
  with no upstream port expression captured (no `CONNECTOR`/no rule in
  `transformation_logic`); modeled as `CAST(NULL AS VARCHAR(100))` with
  `ignoreColumn: true` per the project's `on_unresolved: leave_blank` policy.
- **Incremental filter parameter**: `$$LAST_EXTRACT_DATE` drives the source
  qualifier's `CREATION_DATE >=` predicate; the test case's `JDBC 2` query
  reproduces this literally (unresolved placeholder, left as-is).
- **Other unused mapping parameters** (not referenced by any field in this
  mapping's `field_lineage`, present in the workflow's variable list but
  inert here): `$$GTAS_CDC_LEDGER`, `$$GTAS_FDA_LEDGER`, `$$GTAS_PSC_LEDGER`,
  `$$GTAS_IHS_LEDGER`, `$$GTAS_FISCAL_YR_CDC_EXT`,
  `$$GTAS_FISCAL_YR_FDA_EXT`, `$$GTAS_FISCAL_YR_IHS_EXT`,
  `$$GTAS_FISCAL_YR_PSC_EXT`, `$$GTAS_ACTBAL_CDC_EXT_DT`,
  `$$GTAS_ACTBAL_FDA_EXT_DT`, `$$GTAS_ACTBAL_IHS_EXT_DT`,
  `$$GTAS_ACTBAL_PSC_EXT_DT`.
