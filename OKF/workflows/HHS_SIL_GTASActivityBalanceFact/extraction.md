---
generated:
  by: developer-agent
  at: "2026-08-27T00:00:00+05:30"
  commit: 16abef5323826e129dd4d7d4392227b7d9fa2ff8
---

# HHS_SIL_GTASActivityBalanceFact — Workflow Logic

## Description

`HHS_SIL_GTASActivityBalanceFact` loads fact `W_GTAS_ACTIVITY_BALANCES_F` from staging table `W_GTAS_ACTIVITY_BALANCES_FS`, resolving dimension surrogate keys (`GL_ACCOUNT_WID`, `MCAL_PERIOD_WID`, `LEDGER_WID`, `GL_JE_SOURCE_WID`, `GL_JE_CATEGORY_WID`) via LEFT OUTER JOINs against `W_GL_ACCOUNT_D` (filtered to `CURRENT_FLG='Y'`), `W_MCAL_PERIOD_D`, `W_LEDGER_D`, `W_GL_JE_SOURCES_D`, `W_GL_JE_CATEGORIES_D` in the source-qualifier SQL override. `ETL_PROC_WID` is resolved via mapplet `MPLT_GET_ETL_PROC_WID` (`IIF($$ETL_PROC_WID = 0, LKP_ETL_PROC_WID, $$ETL_PROC_WID)`). `TP_OPDIV`/`TP_LEDGER_WID` are resolved via mapplet `HHS_mplt_SIL_GTAS_Get_TP_Ledger_WID`, a 5-pass fuzzy trading-partner-to-OPDIV mapping cascade. `DELETE_FLG` is hardcoded `'N'`; `W_INSERT_DT`/`W_UPDATE_DT` are `SESSSTARTTIME`. Two sessions exist (`_FDA`, `_PSC`) targeting distinct Oracle table partitions with otherwise identical SQL.

## Key Columns

- **Natural/unique key**: composite of `JE_HEADER_ID`, `JE_LINE_NUM`, `AE_HEADER_ID`, `AE_LINE_NUM`, `BALANCE_TYPE`, `RECORD_CATEGORY`, `GL_ACCOUNT_WID`, `LEDGER_WID`, `DATASOURCE_NUM_ID` — inferred from the fact's grain (should be confirmed against the target table's real PK/unique constraint).
- **Derived-lookup-dependent**: `GL_ACCOUNT_WID` (← `W_GL_ACCOUNT_D`, `CURRENT_FLG='Y'`), `MCAL_PERIOD_WID` (← `W_MCAL_PERIOD_D` on `PERIOD_YEAR=MCAL_YEAR` + `PERIOD_NUM=MCAL_PERIOD`), `LEDGER_WID` (← `W_LEDGER_D`), `GL_JE_SOURCE_WID` (← `W_GL_JE_SOURCES_D`), `GL_JE_CATEGORY_WID` (← `W_GL_JE_CATEGORIES_D`).
- **Parameterized/out-of-scope**: `ETL_PROC_WID` (mapplet `MPLT_GET_ETL_PROC_WID` against `W_PARAM_G`), `TP_OPDIV`/`TP_LEDGER_WID` (5-level IIF/lookup cascade in `HHS_mplt_SIL_GTAS_Get_TP_Ledger_WID`, not practical to reproduce as a flat SQL expression), `W_INSERT_DT`/`W_UPDATE_DT` (`SESSSTARTTIME`), `DELETE_FLG` (hardcoded `'N'`).
