---
type: Informatica Workflow
title: HHS_SDE_ORA_GTASActivityBalanceFact
description: SDE load of W_GTAS_ACTIVITY_BALANCES_FS from FV_GTAS_ACTIVITY_BALANCES across four fiscal-ledger session partitions; surviving dataflow currently runs the older pre-partition query model.
resource: /Workflows/HHS_SDE_ORA_GTASActivityBalanceFact.XML
tags: [GTAS, ActivityBalance, SDE, Oracle]
status: draft
generated: { by: "developer-agent/claude-sonnet-5", at: "2026-08-17T00:00:00+05:30", commit: "9040975c0746fac4842b7d27a53254677f03db55" }
---

# Description

Builds `W_GTAS_ACTIVITY_BALANCES_FS` from raw source `FV_GTAS_ACTIVITY_BALANCES`. The workflow runs the SAME mapping across FOUR reusable session tasks (`HHS_SDE_ORA_GTASActivityBalanceFact_FDA`/`_PSC`/`_CDC`/`_IHS`) rather than a single pass — each session overrides the source qualifier to read a different physical partition of `FV_GTAS_ACTIVITY_BALANCES` (`P2`/`P23`/`P1`/`P43`) filtered by its own `$$GTAS_FISCAL_YR_<LEDGER>_EXT` mapping variable, and all four load into the same target `W_GTAS_ACTIVITY_BALANCES_FS`. The `TRADING_PARTNER_TYPE`-driven CASE expression that derives `PROVIDER_RECIPNT_ID`/`PROVIDER_RECIPNT_NAME` (looking up `apps.HZ_CUST_ACCOUNTS`, `apps.AP_SUPPLIERS`, `apps.GL_JE_LINES`, then resolving a display name from `FND_FLEX_VALUES_VL` or `W_GTAS_INTRAHHS_D`) lives in the shared mapping logic, but the partition/fiscal-year filtering that selects which rows reach it is applied per-session, not in the mapping's own source-qualifier SQL. Also carries an unresolved Informatica mapping variable, `$$DATASOURCE_NUM_ID` (workflow XML line 403), with no default value.

# Key Columns

- **Unique key**: `CCID`, `JE_HEADER_ID`, `JE_LINE_NUM`, `PERIOD_NUM`
- **Derived / lookup-dependent**: `PROVIDER_RECIPNT_ID`, `PROVIDER_RECIPNT_NAME`
- **Parameterized**: `DATASOURCE_NUM_ID`, `GTAS_FISCAL_YR_FDA_EXT`, `GTAS_FISCAL_YR_PSC_EXT`, `GTAS_FISCAL_YR_CDC_EXT`, `GTAS_FISCAL_YR_IHS_EXT` (see Known Caveats)

# Known Caveats

- **2026-08-19 cleanup**: the user manually removed two duplicate dataflows from the platform (`HHS_SDE_ORA_GTASActivityBalanceFact_TestCase_v3`, guid `86af569f-df83-40ba-92b2-e02fdb443c1b`, and `HHS_SDE_ORA_GTASActivityBalanceFact_ProviderRecipnt_Validation`, guid `9c648798-a39d-4463-9de8-33298d26b5a9`) and renamed the surviving one (formerly `_v2`, guid `9ea17989-6e31-43e2-9f34-a4ed516d7461`) to the clean `HHS_SDE_ORA_GTASActivityBalanceFact_TestCase` name, now in folder `Dataflow/WorkingSession`. **Important**: the surviving dataflow is the older "_v2" query model, not the revised "_v3" one — it (a) has no fiscal-year/period filter at all (reads the whole unpartitioned `FV_GTAS_ACTIVITY_BALANCES` stub in one pass), and (b) joins `HZ_CUST_ACCOUNTS`/`AP_SUPPLIERS` on `TRADING_PARTNER_ID` alone, without first checking `TRADING_PARTNER_TYPE = 'C'`/`'S'` the way the real mapping's CASE expression does. If the goal was to keep the more-correct 4-CTE model, that logic needs to be re-applied to this surviving dataflow via `update_data_flow` — right now the name looks clean but the query underneath is the earlier, less accurate one.
- `DATASOURCE_NUM_ID` on the DataOps side is still a placeholder parameter (`$[DATASOURCE_NUM_ID]` = `0`) substituting for the unresolved `$$DATASOURCE_NUM_ID` mapping variable. Run 329920's analysis found the real fact table value is `12` (every target row shows `DATASOURCE_NUM_ID: 12.0000000000`) — the parameter itself still needs correcting to `12` via `update_data_flow` before results are trusted. See run 329920 analysis, Finding 1.
- `apps.HZ_CUST_ACCOUNTS`, `apps.AP_SUPPLIERS`, `apps.GL_JE_LINES` are empty stub tables in the current environment — causes `PROVIDER_RECIPNT_ID`/`NAME` to be blank for any row needing those lookups. Confirmed in run 329920. See run 329920 analysis, Finding 2.
- CCID 10010 (`PERIOD_YEAR` 2024) appeared only in the recomputed dataset, not the loaded fact table, in run 329920 — that run's JDBC 2 query modeled the mapping as a single un-partitioned pass over `FV_GTAS_ACTIVITY_BALANCES`, matching this surviving dataflow's actual (v2) model, not the true 4-session/4-partition structure. See run 329920 analysis, Finding 3.
- The JDBC 2 query originally used Oracle `PARTITION(P2/P23/P1/P43)` hints to mirror production's physical per-ledger partitions. Confirmed BROKEN in this environment: the first build attempt failed with `ORA-14501: object is not partitioned` — the DevContainer's `FV_GTAS_ACTIVITY_BALANCES` is an unpartitioned 10-row stub table. The hints were removed from the test case (see inline SQL comments in `HRD/HHS_SDE_ORA_GTASActivityBalanceFact_TestCase.json`); this environment cannot fully validate the per-ledger split model until a properly partitioned or ledger-tagged source is available.
- `engineName` (`168_AN`) and `folderName` (`Dataflow/WorkingSession`) are confirmed valid against DevContainer (containerId `518`) as of the 2026-08-19 folder move.

# Test Cases & Dataflows

| Test Case | Computation Contract | Dataflow | Environment | Latest Run | Status | Fingerprint |
|---|---|---|---|---|---|---|
| [HHS_SDE_ORA_GTASActivityBalanceFact_TestCase](/HRD/HHS_SDE_ORA_GTASActivityBalanceFact_TestCase.json) | [computation](computation.md) | HHS_SDE_ORA_GTASActivityBalanceFact_TestCase (DevContainer, folder `Dataflow/WorkingSession`, engine `168_AN`, guid `9ea17989-6e31-43e2-9f34-a4ed516d7461`) | DevContainer | run 329920 (2026-08-13) — [report](/Results/HHS_SDE_ORA_GTASActivityBalanceFact_TestCase_v2_run329920_report.json) / [analysis](/Results/HHS_SDE_ORA_GTASActivityBalanceFact_TestCase_v2_run329920_analysis.html) | Failed | not computed (predates drift-check fingerprinting; hash on next confirmed fix) |
