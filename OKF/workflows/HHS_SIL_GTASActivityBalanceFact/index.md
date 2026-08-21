# HHS_SIL_GTASActivityBalanceFact

SIL enrichment load of fact `W_GTAS_ACTIVITY_BALANCES_F` from staging `W_GTAS_ACTIVITY_BALANCES_FS`, resolving five dimension surrogate keys (`GL_ACCOUNT_WID`, `MCAL_PERIOD_WID`, `LEDGER_WID`, `GL_JE_SOURCE_WID`, `GL_JE_CATEGORY_WID`) via joins in the source-qualifier SQL override.

- [Workflow logic (Description, Key Columns)](extraction.md)
- [Test cases, dataflows & caveats](hrd_mapping.md)
