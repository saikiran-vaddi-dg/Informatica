---
type: Informatica Workflow
title: HHS_SDE_ORA_GTASActivityBalanceFact
resource: /Workflows/HHS_SDE_ORA_GTASActivityBalanceFact.XML
tags: [GTAS, ActivityBalance, SDE, Oracle]
generated: { by: "developer-agent", at: "2026-08-17T00:00:00+05:30", commit: "9040975c0746fac4842b7d27a53254677f03db55" }
---

# Description

Builds `W_GTAS_ACTIVITY_BALANCES_FS` from raw source `FV_GTAS_ACTIVITY_BALANCES`. The workflow runs the SAME mapping across FOUR reusable session tasks (`HHS_SDE_ORA_GTASActivityBalanceFact_FDA`/`_PSC`/`_CDC`/`_IHS`) rather than a single pass — each session overrides the source qualifier to read a different physical partition of `FV_GTAS_ACTIVITY_BALANCES` (`P2`/`P23`/`P1`/`P43`) filtered by its own `$$GTAS_FISCAL_YR_<LEDGER>_EXT` mapping variable, and all four load into the same target `W_GTAS_ACTIVITY_BALANCES_FS`. The `TRADING_PARTNER_TYPE`-driven CASE expression that derives `PROVIDER_RECIPNT_ID`/`PROVIDER_RECIPNT_NAME` (looking up `apps.HZ_CUST_ACCOUNTS`, `apps.AP_SUPPLIERS`, `apps.GL_JE_LINES`, then resolving a display name from `FND_FLEX_VALUES_VL` or `W_GTAS_INTRAHHS_D`) lives in the shared mapping logic, but the partition/fiscal-year filtering that selects which rows reach it is applied per-session, not in the mapping's own source-qualifier SQL. Also carries an unresolved Informatica mapping variable, `$$DATASOURCE_NUM_ID` (workflow XML line 403), with no default value.

# Key Columns

- **Unique key**: `CCID`, `JE_HEADER_ID`, `JE_LINE_NUM`, `PERIOD_NUM`
- **Derived / lookup-dependent**: `PROVIDER_RECIPNT_ID`, `PROVIDER_RECIPNT_NAME`
- **Parameterized**: `DATASOURCE_NUM_ID`, `GTAS_FISCAL_YR_FDA_EXT`, `GTAS_FISCAL_YR_PSC_EXT`, `GTAS_FISCAL_YR_CDC_EXT`, `GTAS_FISCAL_YR_IHS_EXT` (see Known Caveats)

# Test Cases & Dataflows

| Test Case | Dataflow | Environment | Latest Run | Status | Fingerprint |
|---|---|---|---|---|---|
| [HHS_SDE_ORA_GTASActivityBalanceFact_TestCase](/HRD/HHS_SDE_ORA_GTASActivityBalanceFact_TestCase.json) | HHS_SDE_ORA_GTASActivityBalanceFact_TestCase_v2 (DevContainer, folder `Dataflow`, engine `168_AN`) | DevContainer | run 329920 (2026-08-13) — [report](/Results/HHS_SDE_ORA_GTASActivityBalanceFact_TestCase_v2_run329920_report.json) / [analysis](/Results/HHS_SDE_ORA_GTASActivityBalanceFact_TestCase_v2_run329920_analysis.html) | Failed | not computed (predates drift-check fingerprinting; hash on next confirmed fix) |
| [HHS_SDE_ORA_GTASActivityBalanceFact_TestCase](/HRD/HHS_SDE_ORA_GTASActivityBalanceFact_TestCase.json) (revised, 4-CTE union model) | HHS_SDE_ORA_GTASActivityBalanceFact_TestCase_v3 (DevContainer, folder `Dataflow`, engine `168_AN`, guid `86af569f-df83-40ba-92b2-e02fdb443c1b`) | DevContainer | run 330090 (2026-08-19) — [report](/Results/HHS_SDE_ORA_GTASActivityBalanceFact_TestCase_v3_run330090_report.json) / [analysis](/Results/HHS_SDE_ORA_GTASActivityBalanceFact_TestCase_v3_run330090_analysis.html) | Failed (mechanics-only — dataset B empty due to placeholder fiscal-year params, no logic validated yet) | not computed (parameters not yet corrected; hash on next confirmed fix) |

# Known Caveats

- `DATASOURCE_NUM_ID` on the DataOps side is still a placeholder parameter (`$[DATASOURCE_NUM_ID]` = `0`) substituting for the unresolved `$$DATASOURCE_NUM_ID` mapping variable. Run 330090 confirmed the real fact table value is `12` (every target row shows `DATASOURCE_NUM_ID: 12.0000000000`) — the parameter itself still needs correcting to `12` via `update_data_flow` before results are trusted. See run 329920 analysis, Finding 1; run 330090 analysis, Finding 2.
- `apps.HZ_CUST_ACCOUNTS`, `apps.AP_SUPPLIERS`, `apps.GL_JE_LINES` are empty stub tables in the current environment — causes `PROVIDER_RECIPNT_ID`/`NAME` to be blank for any row needing those lookups. Confirmed in run 329920; unconfirmed either way in run 330090 since dataset B was empty. See run 329920 analysis, Finding 2.
- CCID 10010 (`PERIOD_YEAR` 2024) appeared only in the recomputed dataset, not the loaded fact table, in run 329920 — that run's JDBC 2 query modeled the mapping as a single un-partitioned pass over `FV_GTAS_ACTIVITY_BALANCES`, not the actual 4-session/4-partition structure now understood. Still unconfirmed as of run 330090 (dataset B was empty there too, for an unrelated reason — see fiscal-year caveat below). Needs re-checking once dataset B returns real rows. See run 329920 analysis, Finding 3.
- The revised test case's four `$[GTAS_FISCAL_YR_<LEDGER>_EXT]` parameters (FDA/PSC/CDC/IHS) are currently PLACEHOLDERS defaulting to `0`, matching no real `PERIOD_YEAR` — same pattern as `DATASOURCE_NUM_ID` above. Confirmed as the cause of run 330090 returning 0 rows for dataset B (100% "Only in A"). Real per-ledger fiscal-year values need to be resolved (e.g. from the Informatica parameter file referenced by the session, `$PMSourceFileDir\REDACTED_FOLDER_SDE.HHS_SDE_ORA_GTASActivityBalanceFact.txt`) before any new run's results can be trusted. See run 330090 analysis, Finding 1.
- The JDBC 2 query originally used Oracle `PARTITION(P2/P23/P1/P43)` hints to mirror production's physical per-ledger partitions. Confirmed BROKEN in this environment: the first build attempt failed with `ORA-14501: object is not partitioned` — the DevContainer's `FV_GTAS_ACTIVITY_BALANCES` is an unpartitioned 10-row stub table. The hints were removed from the test case (see inline SQL comments in `HRD/HHS_SDE_ORA_GTASActivityBalanceFact_TestCase.json`); the four CTEs now differ only by their fiscal-year filter, not by physical partition, so this environment cannot fully validate the per-ledger split model until a properly partitioned or ledger-tagged source is available.
- `engineName` (`168_AN`) and `folderName` (`Dataflow`) are confirmed valid against DevContainer (containerId `518`) as of run 330090's build (`list_engines`/`list_folders` both resolved cleanly).
