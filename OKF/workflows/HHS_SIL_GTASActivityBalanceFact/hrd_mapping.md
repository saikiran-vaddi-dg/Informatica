# HHS_SIL_GTASActivityBalanceFact — Test Cases, Dataflows & Caveats

## Test Cases & Dataflows

| Test Case | Dataflow | Container | Folder | Engine | Run ID | Status | Fingerprint |
|---|---|---|---|---|---|---|---|
| `HRD/HHS_SIL_GTASActivityBalanceFact_TestCase.json` | `HHS_SIL_GTASActivityBalanceFact_TestCase` (id `36047d64-13d5-4850-8e54-8ecaeed3d0d7`) | HHS_client_Poc_container | Dataflow | 168_AN | 330422 | Failed (corrected, not yet re-run) | `1de9efea9ef730af0a106dcc32d08f04eaea0787fa7186473e72093d4af1fc2b` (HRD file sha256; pending confirmation against live definition after re-run) |

## Known Caveats

- **`MCAL_PERIOD_WID` always blank (run 330422)** — classified as an environment/data defect, not a test case defect. `W_MCAL_PERIOD_D` population needs external verification. See [analysis](../../../Results/HHS_SIL_GTASActivityBalanceFact_TestCase_run330422_analysis.html).
- **"Only In B": 9 rows (run 330422)** — expected fact-vs-staging timing gap, not a defect.
- **`AMOUNT` mismatch on 2/4 differing rows (run 330422)** — tentatively an environment/data defect (possible decimal precision); needs further verification, not a test case fix.
- **Duplicate keys under the composite unique key (run 330422) — FIXED, pending re-run verification.** `GL_ACCOUNT_WID` and `LEDGER_WID` were dropped from `uniqueKeyColumn=true` in `HRD/HHS_SIL_GTASActivityBalanceFact_TestCase.json`'s DataCompare 3 columnMappings, since they are derived dimension-lookup columns, not part of the real business key. Remaining unique key: `JE_HEADER_ID`, `JE_LINE_NUM`, `RECORD_CATEGORY`, `BALANCE_TYPE`, `AE_HEADER_ID`, `AE_LINE_NUM`, `DATASOURCE_NUM_ID`.
- **Real target table PK/unique constraint still UNCONFIRMED.** No tool was available to query Oracle constraint metadata directly this session; the composite key above (original and corrected) is inferred from the fact's grain, not verified against the actual DB constraint. Needs SME/DBA confirmation.
- **`MCAL_PERIOD_WID` join direction corrected vs. a prior deleted draft.** The real `SQ_W_GTAS_ACTIVITY_BALANCES_FS` SQL override joins `PERIOD_YEAR=MCAL_YEAR` and `PERIOD_NUM=MCAL_PERIOD` (no swap); an earlier draft had this backwards.
- **`GL_ACCOUNT_WID` subquery corrected** to include `a.CURRENT_FLG='Y'`, present in the real join but missing from a prior draft.
- **`ETL_PROC_WID`, `TP_OPDIV`, `TP_LEDGER_WID`, `W_INSERT_DT`, `W_UPDATE_DT` deliberately excluded** (`ignoreColumn`) — session-timestamp/mapping-parameter driven, or resolved via the 5-level IIF/lookup cascade in `HHS_mplt_SIL_GTAS_Get_TP_Ledger_WID`, not practical to reproduce as a flat SQL expression.
