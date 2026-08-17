---
type: Informatica Workflow
title: HHS_SDE_ORA_GTASActivityBalanceFact
resource: /Workflows/HHS_SDE_ORA_GTASActivityBalanceFact.XML
tags: [GTAS, ActivityBalance, SDE, Oracle]
generated: { by: "developer-agent", at: "2026-08-17T10:08:30+05:30" }
---

# Description

Builds `W_GTAS_ACTIVITY_BALANCES_FS` from raw source `FV_GTAS_ACTIVITY_BALANCES`. Derives `PROVIDER_RECIPNT_ID`/`PROVIDER_RECIPNT_NAME` per row via a `TRADING_PARTNER_TYPE`-driven CASE expression that looks up `apps.HZ_CUST_ACCOUNTS`, `apps.AP_SUPPLIERS`, and `apps.GL_JE_LINES`, then resolves a display name from `FND_FLEX_VALUES_VL` or `W_GTAS_INTRAHHS_D`. Also carries an unresolved Informatica mapping variable, `$$DATASOURCE_NUM_ID` (workflow XML line 403), with no default value.

# Key Columns

- **Unique key**: `CCID`, `JE_HEADER_ID`, `JE_LINE_NUM`, `PERIOD_NUM`
- **Derived / lookup-dependent**: `PROVIDER_RECIPNT_ID`, `PROVIDER_RECIPNT_NAME`
- **Parameterized**: `DATASOURCE_NUM_ID` (see Known Caveats)

# Test Cases & Dataflows

| Test Case | Dataflow | Environment | Latest Run | Status |
|---|---|---|---|---|
| [HHS_SDE_ORA_GTASActivityBalanceFact_TestCase](/HRD/HHS_SDE_ORA_GTASActivityBalanceFact_TestCase.json) | HHS_SDE_ORA_GTASActivityBalanceFact_TestCase_v2 (DevContainer, folder `Dataflow`, engine `168_AN`) | DevContainer | run 329920 (2026-08-13) — [report](/Results/HHS_SDE_ORA_GTASActivityBalanceFact_TestCase_v2_run329920_report.json) / [analysis](/Results/HHS_SDE_ORA_GTASActivityBalanceFact_TestCase_v2_run329920_analysis.html) | Failed |

# Known Caveats

- `DATASOURCE_NUM_ID` is currently a placeholder DataOps parameter (`$[DATASOURCE_NUM_ID]` = `0`) substituting for the unresolved `$$DATASOURCE_NUM_ID` mapping variable — the real fact table value is `12`. Must be corrected before results are trusted. See run 329920 analysis, Finding 1.
- `apps.HZ_CUST_ACCOUNTS`, `apps.AP_SUPPLIERS`, `apps.GL_JE_LINES` are empty stub tables in the current environment — causes `PROVIDER_RECIPNT_ID`/`NAME` to be blank for any row needing those lookups. See run 329920 analysis, Finding 2.
- CCID 10010 (`PERIOD_YEAR` 2024) appears only in the recomputed dataset, not the loaded fact table — possibly a real ETL load gap, unconfirmed against spec. See run 329920 analysis, Finding 3.
