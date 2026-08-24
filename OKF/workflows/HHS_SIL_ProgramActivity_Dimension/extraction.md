---
generated:
  by: developer-agent
  at: "2026-08-20T00:00:00+05:30"
  commit: d892839ef5cba00d6cff618888fca67276744756
---

# HHS_SIL_ProgramActivity_Dimension — Workflow Logic

## Description

`HHS_SIL_ProgramActivity_Dimension` is an SCD-1 upsert load of dimension `WC_PROGRAM_ACTIVITY_D` from staging `WC_PROGRAM_ACTIVITY_DS`. The source-qualifier SQL override left-joins `WC_PROGRAM_ACTIVITY_DS` to `W_LEDGER_D` (on `LEDGER_ID=INTEGRATION_ID` + `DATASOURCE_NUM_ID`, filtered `DELETE_FLG='N'`) to resolve `LEDGER_WID`, and to `W_USER_D` six times (aliased, each on `INTEGRATION_ID`+`DATASOURCE_NUM_ID`+`CURRENT_FLG='Y'`) to resolve the six `PRC_HDR/DTL/ALLOC_CHANGED/CREATED_BY_WID` columns. `EXPTRANS` derives six `CMS_PRC_*_BY_ID` columns via `IIF(LEDGER_WID=2, <source _ID column>, NULL)` — populated only for ledger 2. A self-lookup (`LKP_WC_PROGRAM_ACTIVITY_D`, keyed on `INTEGRATION_ID`+`DATASOURCE_NUM_ID` against the target) feeds a router sending unmatched rows to Insert (new `ROW_WID` from `SEQ_WC_PROGRAM_ACTIVITY_D`) and changed rows (any of the three `*_CHANGED_ON_DT` differing) to Update; unchanged rows drop. GL-segment (1-30 LOW/HIGH), treasury/fund/allocation, and `PROGRAM_ACTIVITY_RPT_*`/`CFRS_TREASURY_SYMBOL` columns are straight passthroughs.

The workflow's second mapping, `HHS_SIL_DATA_ACT_CONTROL_DUMMY`, is a trivial 1:1 copy of `WC_FBIS_DATA_ACT_CONTROL` (tier simple/template-only) with an unused `$$DATA_ACT_REPORTING_PERIOD` mapping variable — no business logic to test, not covered by the accompanying test case (see [hrd_mapping.md](hrd_mapping.md)).

## Key Columns

- **Natural/unique key**: `INTEGRATION_ID` + `DATASOURCE_NUM_ID` (composite, matching the self-lookup's own join condition).
- **Derived-lookup-dependent**: `LEDGER_WID` (← `W_LEDGER_D` self-lookup, `DELETE_FLG='N'`), the six `PRC_*_BY_WID` columns (← `W_USER_D`, `CURRENT_FLG='Y'`), and the six `CMS_PRC_*_BY_ID` columns (derived from the `LEDGER_WID=2` branch — a derived value feeding a further branch).
- **Parameterized/out-of-scope**: `ETL_PROC_WID` (via mapplet `MPLT_GET_ETL_PROC_WID` against `W_PARAM_G`), `ROW_WID` (sequence-generated), `W_INSERT_DT`/`W_UPDATE_DT` (`SESSSTARTTIME`), and the router's INSERT/UPDATE/no-op branching (a run-to-run CDC concern, not testable via a single-snapshot compare).
