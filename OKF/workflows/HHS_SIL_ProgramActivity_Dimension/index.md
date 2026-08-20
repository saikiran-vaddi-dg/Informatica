# HHS_SIL_ProgramActivity_Dimension

SCD-1 upsert load of dimension `WC_PROGRAM_ACTIVITY_D` from staging `WC_PROGRAM_ACTIVITY_DS`, resolving `LEDGER_WID` (via `W_LEDGER_D`) and six `PRC_*_BY_WID` user columns (via six `W_USER_D` aliases) in the source-qualifier SQL override.

- [Workflow logic (Description, Key Columns)](extraction.md)
- [Test cases, dataflows & caveats](hrd_mapping.md)
