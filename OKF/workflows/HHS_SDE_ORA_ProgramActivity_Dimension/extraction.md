---
generated:
  by: developer-agent
  at: "2026-08-26T10:07:37+00:00"
  commit: 196145549162777b6eeea2144c7a623531313a15
---

# HHS_SDE_ORA_ProgramActivity_Dimension — Extraction

## Description

SDE mapping that extracts Treasury program-activity/reporting-code data from
Oracle EBS Federal Financials (`FV_FACTS_PRC_HDR` header outer-joined to
`FV_FACTS_PRC_DTL` detail, outer-joined to `FV_DACT_PRC_ALLOCATION` allocation)
via a single Source Qualifier SQL override, through one Expression
transformation (`EXP_WC_PROGRAM_ACTIVITY_DS_Integration_Id`) that derives the
composite `INTEGRATION_ID`, `LEDGER_ID`, and the six audit `_BY_ID` columns,
into staging table `WC_PROGRAM_ACTIVITY_DS`.

`PROGRAM_ACTIVITY_RPT_CODE`/`PROGRAM_ACTIVITY_RPT_DESC` are conditional: when
`FV_FACTS_PRC_DTL.ALLOCATED_FLAG = 'Y'` they come from the allocation table
(`FV_DACT_PRC_ALLOCATION.PROGRAM_ACTIVITY_RPT_CODE`/`_DESC`), otherwise from
the detail table's own `REPORTING_CODE`/`REPORTING_DESC`.

## Key Columns

- **Unique/natural key**: `INTEGRATION_ID` = `TO_CHAR(PRC_HEADER_ID) || '~' ||
  TO_CHAR(PRC_DETAIL_ID) || '~' || TO_CHAR(PRC_ALLOC_ID)`.
- **Conditional (CASE)**: `PROGRAM_ACTIVITY_RPT_CODE`/`PROGRAM_ACTIVITY_RPT_DESC`
  — sourced from `FV_DACT_PRC_ALLOCATION` when `ALLOCATED_FLAG = 'Y'`, else from
  `FV_FACTS_PRC_DTL.REPORTING_CODE`/`REPORTING_DESC`.
- **Derived via Expression, traced to raw SQ/CONNECTOR**: `LEDGER_ID` =
  `TO_CHAR(SET_OF_BOOKS_ID)` (HDR); `PRC_HDR_CHANGED_BY_ID` =
  `TO_CHAR(LAST_UPDATED_BY)` (HDR); `PRC_HDR_CREATED_BY_ID` =
  `TO_CHAR(CREATED_BY)` (HDR); `PRC_DTL_CHANGED_BY_ID` =
  `TO_CHAR(LAST_UPDATED_BY)` (DTL, aliased `LAST_UPDATED_BY1` in the SQ);
  `PRC_DTL_CREATED_BY_ID` = `TO_CHAR(CREATED_BY)` (DTL, `CREATED_BY1`);
  `PRC_ALLOC_CHANGED_BY_ID` = `TO_CHAR(LAST_UPDATED_BY)` (ALLOC,
  `LAST_UPDATED_BY2`); `PRC_ALLOC_CREATED_BY_ID` = `TO_CHAR(CREATED_BY)`
  (ALLOC, `CREATED_BY2`). All seven confirmed directly against the raw XML's
  `CONNECTOR` elements into `EXP_WC_PROGRAM_ACTIVITY_DS_Integration_Id`
  (`INP_LEDGER_ID` <- `SET_OF_BOOKS_ID`; the six `INP_PRC_*_BY_ID` ports <-
  `LAST_UPDATED_BY`/`CREATED_BY`/`LAST_UPDATED_BY1`/`CREATED_BY1`/
  `LAST_UPDATED_BY2`/`CREATED_BY2`), not just inferred by naming analogy.
- **Segments**: `SEGMENT1..30_LOW`/`SEGMENT1..30_HIGH` — direct passthrough
  from `FV_FACTS_PRC_DTL`.
- **Parameterized, unresolved**: `DATASOURCE_NUM_ID` (`$$DATASOURCE_NUM_ID`,
  no workflow default and no `dataops.config.yaml` override found) — modeled
  in the test case as `CAST(NULL AS NUMBER)` with `ignoreColumn: true`, per
  the project's `on_unresolved: leave_blank` policy.
- **Excluded from the test case (target-only, not populated by this
  mapping)**: `CFRS_TREASURY_SYMBOL` (target field 87) and `FILE_NAME`
  (target field 88) — both exist in `WC_PROGRAM_ACTIVITY_DS`'s target
  definition but have no `CONNECTOR` from
  `EXP_WC_PROGRAM_ACTIVITY_DS_Integration_Id` or any source in the raw XML.
  This accounts for the compact-summary's reported 88-vs-90 target-field
  discrepancy (`field_lineage` traces 88 of 90 `TARGETFIELD`s; the other two
  are these audit/unused columns, confirmed by absence of any connector,
  not a compaction-tool gap).
