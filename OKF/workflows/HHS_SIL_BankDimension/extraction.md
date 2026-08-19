---
type: Informatica Workflow
title: HHS_SIL_BankDimension
description: Builds the W_BANK_D dimension from W_BANK_DS via seven W_CODE_D category lookups and effective-dated W_USER_D audit-user resolution.
resource: /Workflows/HHS_SIL_BankDimension.XML
tags: [BankDimension, SIL, Oracle]
status: draft
generated: { by: "developer-agent/claude-sonnet-5", at: "2026-08-19T13:48:57+05:30", commit: "5588d347452d72377df7bc83d96c59aeea6beb03" }
---

# Description

Builds the `W_BANK_D` dimension from the `W_BANK_DS` staging table. For each of seven code categories (`BANK`, `BANK_TYPE`, `BANK_CAT`, `COUNTRY`, `STATE`, `SWIFT`, `BANK_BRANCH`) it looks up `W_CODE_D` by `(CATEGORY, LANGUAGE_CODE = 'E', SOURCE_CODE, DATASOURCE_NUM_ID)` and applies a COALESCE-style fallback: master code/name if the lookup hits, `'<Master Code Not Found>'` if the source code exists but no master row matches, else `'<Source Code Not Supplied>'`. `CREATED_BY_WID`/`CHANGED_BY_WID` are resolved via an effective-dated subquery against `W_USER_D` (`EFFECTIVE_FROM_DT <= created/changed date <= EFFECTIVE_TO_DT`). The target read (JDBC 1) filters `CURRENT_FLG = 'Y' AND DELETE_FLG = 'N'`.

# Key Columns

- **Unique key**: `INTEGRATION_ID`, `DATASOURCE_NUM_ID`
- **Derived / lookup-dependent**: `BANK_KEY_CODE`/`BANK_NAME`, `BANK_TYPE_CODE`/`BANK_TYPE_NAME`, `BANK_CAT_CODE`/`BANK_CAT_NAME`, `COUNTRY_CODE`/`COUNTRY_NAME`, `STATE_CODE`/`STATE_NAME`, `SWIFT_CODE`/`SWIFT_NAME`, `BANK_HIER_CODE`/`BANK_HIER_NAME`, `BANK_BRANCH_CODE`/`BANK_BRANCH_NAME` (all via `W_CODE_D` lookup), `CREATED_BY_WID`, `CHANGED_BY_WID` (effective-dated `W_USER_D` lookup)
- **Filter-sensitive**: `CURRENT_FLG`, `DELETE_FLG` (target read requires `'Y'`/`'N'` respectively — see Known Caveats)

# Known Caveats

- Run 330093 failed with "Only In B: 10 (100%)" — the target read (JDBC 1, `WHERE CURRENT_FLG = 'Y' AND DELETE_FLG = 'N'`) returned 0 rows. Root-caused to `POC.W_BANK_D` having `DELETE_FLG = 'Y'` on all 10 stub rows (should be `'N'` for active rows) — an environment/data defect, not a query or test-case bug. Corrective `UPDATE POC.W_BANK_D SET DELETE_FLG = 'N' WHERE DELETE_FLG = 'Y'` was handed to the user in `fix_remaining_blockers.sql`; re-run pending confirmation it was executed.
- Separately, `W_BANK_D`/`W_USER_D`'s stub rows have `EFFECTIVE_FROM_DT == EFFECTIVE_TO_DT`, which makes the effective-dated `CREATED_BY_WID`/`CHANGED_BY_WID` lookups always miss (this is a systemic stub-data defect affecting every SCD2-joined dimension in this environment, not unique to this workflow). Corrective `UPDATE ... SET EFFECTIVE_TO_DT = DATE '9999-12-31' WHERE EFFECTIVE_TO_DT = EFFECTIVE_FROM_DT` for `W_USER_D` (among others) was included in the same `fix_remaining_blockers.sql`.
- `engineName` (`168_AN`) and `folderName` (`Dataflow/WorkingSession`) are confirmed valid against DevContainer (containerId `518`) as of the 2026-08-19 folder move.

# Test Cases & Dataflows

| Test Case | Computation Contract | Dataflow | Environment | Latest Run | Status | Fingerprint |
|---|---|---|---|---|---|---|
| [HHS_SIL_BankDimension_TestCase](/HRD/HHS_SIL_BankDimension_TestCase.json) | [computation](computation.md) | HHS_SIL_BankDimension_TestCase (DevContainer, folder `Dataflow/WorkingSession`, engine `168_AN`, guid `05d13c0e-dc13-40be-a00c-636bab22e4ca`) | DevContainer | run 330093 (2026-08-19) — no report persisted; see Known Caveats for root cause | Failed | not computed (fix not yet applied; hash on next confirmed re-run) |
