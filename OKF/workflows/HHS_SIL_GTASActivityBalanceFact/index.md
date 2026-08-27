# HHS_SIL_GTASActivityBalanceFact

Loads fact `W_GTAS_ACTIVITY_BALANCES_F` from staging `W_GTAS_ACTIVITY_BALANCES_FS`, resolving dimension surrogate keys (`GL_ACCOUNT_WID`, `MCAL_PERIOD_WID`, `LEDGER_WID`, `GL_JE_SOURCE_WID`, `GL_JE_CATEGORY_WID`) via joins in the source-qualifier SQL override, plus mapplet-derived `ETL_PROC_WID` and `TP_OPDIV`/`TP_LEDGER_WID`.

- [Workflow logic (Description, Key Columns)](extraction.md)
- [Test cases, dataflows & caveats](hrd_mapping.md)
