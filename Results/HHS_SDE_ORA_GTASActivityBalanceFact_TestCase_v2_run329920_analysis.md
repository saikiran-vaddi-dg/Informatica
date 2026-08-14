# Analysis: HHS_SDE_ORA_GTASActivityBalanceFact_TestCase_v2 — Run 329920

## Scope
- Dataflow: `HHS_SDE_ORA_GTASActivityBalanceFact_TestCase_v2` (guid `9ea17989-6e31-43e2-9f34-a4ed516d7461`), container `DevContainer`, folder `Dataflow`, engine `168_AN`.
- Built from `TestCases/HHS_SDE_ORA_GTASActivityBalanceFact_TestCase.json` against the `HHS_SDE_ORA_GTASActivityBalanceFact` Informatica workflow logic.
- Run executed via `run_dataflow` (dataFlowRunId 329920, run date 2026-08-13 11:29:01) and its DataCompare report pulled via `download_data_compare_report`. Raw report saved alongside this file as `HHS_SDE_ORA_GTASActivityBalanceFact_TestCase_v2_run329920_report.json`.
- Cross-referenced against `TestCases/HHS_SDE_ORA_GTASActivityBalanceFact_missing_tables.sql` to explain root cause of one finding.

## Summary
- **Status: Failed.**
- Dataset A (`JDBC_1`, loaded fact table `W_GTAS_ACTIVITY_BALANCES_FS`): 9 rows.
- Dataset B (`JDBC_2`, recomputed from raw source `FV_GTAS_ACTIVITY_BALANCES` + lookups): 10 rows.
- Matched rows: 0. Differing rows: 9 (100% of A, 90% of B). Only-in-B: 1 row (10%).
- Column-wise mismatch counts: `DATASOURCE_NUM_ID` 9, `PROVIDER_RECIPNT_ID` 5, `PROVIDER_RECIPNT_NAME` 5.

## Findings

### 1. DATASOURCE_NUM_ID mismatch on all 9 rows — known artifact, not a real defect
Every compared row shows `A: 12.0000000000` vs `B: 0E-10`. This is caused by an unresolved Informatica mapping variable: the source workflow XML (`Workflows/HHS_SDE_ORA_GTASActivityBalanceFact.XML:403`) declares `$$DATASOURCE_NUM_ID` with no default value. When the dataflow was built, this was parameterized as a DataOps dataflow parameter (`$[DATASOURCE_NUM_ID]`) set to a placeholder value of `0`, since the real runtime value wasn't available. The real fact table has `12`.
**Action needed:** update the dataflow parameter to the real `DATASOURCE_NUM_ID` value (from the Informatica session parameter file) via `update_data_flow`, then re-run — this will eliminate all 9 of these mismatches if no other issue exists on this column.

### 2. PROVIDER_RECIPNT_ID / PROVIDER_RECIPNT_NAME blank for 5 rows (CCID 10001–10005) — genuine data gap
| CCID | Expected (A) | Got (B) |
|---|---|---|
| 10001 | `1200` / DEPARTMENT OF ENERGY | *(blank)* |
| 10002 | `1400` / DEPARTMENT OF JUSTICE | *(blank)* |
| 10003 | `1900` / DEPARTMENT OF STATE | *(blank)* |
| 10004 | `0751234` / CDC | *(blank)* |
| 10005 | `0121500` / DEPARTMENT OF AGRICULTURE | *(blank)* |

Root cause, confirmed by reading `TestCases/HHS_SDE_ORA_GTASActivityBalanceFact_missing_tables.sql`: the JDBC_2 query's `PROVIDER_RECIPNT_ID` CASE logic depends on LEFT JOINs into `apps.HZ_CUST_ACCOUNTS`, `apps.AP_SUPPLIERS`, and `apps.GL_JE_LINES`. That script creates these three tables **empty** (stub DDL only, no data rows) — so every join returns NULL, and the CASE expression falls through to blank for any row whose `TRADING_PARTNER_TYPE` needs one of those lookups (`'C'`, `'S'`, `'M'`, or `'O'` with a length match). Rows 10006–10009 were unaffected: 10006 uses `TRADING_PARTNER_TYPE = 'B'` (a direct concatenation needing no lookup) and matched; 10007–10009 are legitimately NULL on both sides.

**Action needed:** populate `apps.HZ_CUST_ACCOUNTS`, `apps.AP_SUPPLIERS`, and `apps.GL_JE_LINES` with reference rows whose keys (`CUST_ACCOUNT_ID`/`VENDOR_ID`/`JE_HEADER_ID`+`JE_LINE_NUM`) match the `TRADING_PARTNER_ID`/`JE_HEADER_ID`/`JE_LINE_NUM` values used by test rows 10001–10005, then re-run to confirm the lookup logic itself is correct.

### 3. Row only in dataset B: CCID 10010, PERIOD_YEAR 2024 — possible ETL load gap
This row is derivable from the raw source (`FV_GTAS_ACTIVITY_BALANCES`) but does not exist in the already-loaded fact table (`W_GTAS_ACTIVITY_BALANCES_FS`). Since A represents "already loaded" and B represents "should exist per source + transform logic," this is a candidate real ETL gap — the row may not have been processed yet, or a filter (e.g. on `PERIOD_YEAR`) is excluding 2024 data from this fact load. Needs confirmation of whether 2024-period rows are in scope.

## Gaps
- No live DataOps job history beyond this single run was queried — only run 329920 was analyzed.
- Whether `PERIOD_YEAR = 2024` should be in scope for this fact table load was not verified against any spec/requirements doc — flagged as a question, not a confirmed defect.
- The correct real value for `DATASOURCE_NUM_ID` was not available in this repo (checked `Workflows/` and `TestCases/`); it must come from an external Informatica session parameter file.
