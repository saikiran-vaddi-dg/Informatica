---
generated:
  by: developer-agent
  at: "2026-08-21T00:00:00+05:30"
  commit: bade1b72eef7f7363065c0b446d6f22b5a83b67a
---

# HHS_SIL_GTASActivityBalanceFact — Workflow Logic

## Description

`HHS_SIL_GTASActivityBalanceFact` is a SIL mapping enriching staging table `W_GTAS_ACTIVITY_BALANCES_FS` into fact `W_GTAS_ACTIVITY_BALANCES_F`. A source-qualifier SQL override resolves five dimension surrogate keys via five `LEFT OUTER JOIN`s: `GL_ACCOUNT_WID` (← `W_GL_ACCOUNT_D` on `CCID`/`DATASOURCE_NUM_ID`, `CURRENT_FLG='Y'`), `MCAL_PERIOD_WID` (← `W_MCAL_PERIOD_D` on `PERIOD_YEAR`/`PERIOD_NUM`/`DATASOURCE_NUM_ID`), `LEDGER_WID` (← `W_LEDGER_D` on `SET_OF_BOOKS_ID`/`DATASOURCE_NUM_ID`), `GL_JE_SOURCE_WID` (← `W_GL_JE_SOURCES_D` on `JE_SOURCE`), and `GL_JE_CATEGORY_WID` (← `W_GL_JE_CATEGORIES_D` on `JE_CATEGORY`). Roughly 35 fields (trading-partner attributes, JE/AE header/line identifiers, dollar amounts, PIID/FAIN/URI/DOC_NUM award identifiers, provider/recipient info, etc.) pass through unchanged. `ETL_PROC_WID`, `TP_OPDIV`, and `TP_LEDGER_WID` are derived inside two reusable mapplets (`MPLT_GET_ETL_PROC_WID`, `HHS_mplt_SIL_GTAS_Get_TP_Ledger_WID`) whose internal logic is not visible in the compact summary.

Compaction tool tier: **complex**.

## Key Columns

- **Natural/unique key**: no target field in the workflow XML declares a `KEYTYPE` other than "NOT A KEY"; the fact's grain is inferred as the composite `JE_HEADER_ID` + `JE_LINE_NUM` + `AE_HEADER_ID` + `AE_LINE_NUM` + `BALANCE_TYPE` + `RECORD_CATEGORY` + `GL_ACCOUNT_WID` + `LEDGER_WID` + `DATASOURCE_NUM_ID`.
- **Derived-lookup-dependent**: `GL_ACCOUNT_WID` (← `W_GL_ACCOUNT_D`), `MCAL_PERIOD_WID` (← `W_MCAL_PERIOD_D`), `LEDGER_WID` (← `W_LEDGER_D`), `GL_JE_SOURCE_WID` (← `W_GL_JE_SOURCES_D`), `GL_JE_CATEGORY_WID` (← `W_GL_JE_CATEGORIES_D`) — all five resolved via correlated subqueries/joins in the source-qualifier SQL override.
- **Mapplet-derived / out-of-scope for a single-snapshot compare**: `ETL_PROC_WID` (via `MPLT_GET_ETL_PROC_WID`), `TP_OPDIV` and `TP_LEDGER_WID` (via `HHS_mplt_SIL_GTAS_Get_TP_Ledger_WID`) — internal mapplet logic not visible in the compact summary, and `W_INSERT_DT`/`W_UPDATE_DT` (session timestamps).
