# HHS_SIL_GTASActivityBalanceFact — Test Cases, Dataflows & Caveats

## Test Cases & Dataflows

| Test Case | Dataflow | Container | Folder | Engine | Run ID | Status | Fingerprint |
|---|---|---|---|---|---|---|---|
| `HRD/HHS_SIL_GTASActivityBalanceFact_TestCase.json` | `HHS_SIL_GTASActivityBalanceFact_TestCase` (id `36047d64-13d5-4850-8e54-8ecaeed3d0d7`) | HHS_client_Poc_container | Dataflow | 168_AN | 330424 | Failed (final) | `1de9efea9ef730af0a106dcc32d08f04eaea0787fa7186473e72093d4af1fc2b` (HRD file sha256; confirmed against live definition — composite-key fix pushed via update_data_flow matches this file) |

## Known Caveats

- **Failed (final) — needs SME/DBA verification before this dataflow can pass.** The composite-key fix (dropping `GL_ACCOUNT_WID`/`LEDGER_WID` from `uniqueKeyColumn=true`) was applied, pushed to the live dataflow, and re-run (330424) with an identical failure signature to run 330422. This confirms the duplicate-key symptom is not caused by the key definition but stems from the same underlying environment/data issue as the other two findings below. No further automated fix is possible from this pipeline; the workflow needs the following external verification:
  - `MCAL_PERIOD_WID` always blank — `W_MCAL_PERIOD_D` population/registration in container `HHS_client_Poc_container` needs SME/DBA verification.
  - `AMOUNT` mismatch on 2/4 differing rows — decimal precision root cause needs SME/DBA verification.
  - See [run 330422 analysis](../../../Results/HHS_SIL_GTASActivityBalanceFact_TestCase_run330422_analysis.html) (classification still applies to run 330424 — identical failure signature) and [run 330424 report](../../../Results/HHS_SIL_GTASActivityBalanceFact_TestCase_run330424_report.json).
- **"Only In B": 9 rows** — expected fact-vs-staging timing gap, not a defect.
- **Real target table PK/unique constraint still UNCONFIRMED.** No tool was available to query Oracle constraint metadata directly; the composite key in `HRD/HHS_SIL_GTASActivityBalanceFact_TestCase.json` is inferred from the fact's grain, not verified against the actual DB constraint. Needs SME/DBA confirmation.
- **`MCAL_PERIOD_WID` join direction corrected vs. a prior deleted draft.** The real `SQ_W_GTAS_ACTIVITY_BALANCES_FS` SQL override joins `PERIOD_YEAR=MCAL_YEAR` and `PERIOD_NUM=MCAL_PERIOD` (no swap); an earlier draft had this backwards.
- **`GL_ACCOUNT_WID` subquery corrected** to include `a.CURRENT_FLG='Y'`, present in the real join but missing from a prior draft.
- **`ETL_PROC_WID`, `TP_OPDIV`, `TP_LEDGER_WID`, `W_INSERT_DT`, `W_UPDATE_DT` deliberately excluded** (`ignoreColumn`) — session-timestamp/mapping-parameter driven, or resolved via the 5-level IIF/lookup cascade in `HHS_mplt_SIL_GTAS_Get_TP_Ledger_WID`, not practical to reproduce as a flat SQL expression.
