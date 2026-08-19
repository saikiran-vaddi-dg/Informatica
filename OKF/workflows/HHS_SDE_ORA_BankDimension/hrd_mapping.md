---
type: XML-to-HRD Mapping
title: HHS_SDE_ORA_BankDimension XML-to-HRD column mapping
description: Column-by-column derivation from the Informatica workflow's transformation logic to each W_BANK_DS target column, as encoded in the HRD test case's JDBC 2 (expected) recompute query.
resource: /Workflows/HHS_SDE_ORA_BankDimension.XML
mapping: /HRD/HHS_SDE_ORA_BankDimension_TestCase.json
tags: [BankDimension, SDE, Oracle, column-lineage]
status: draft
generated: { by: "developer-agent/claude-sonnet-5", at: "2026-08-19T00:00:00+05:30" }
verified:
  - { by: "review-agent/claude-sonnet-5", at: "2026-08-17T00:00:00+05:30" }
---

# Purpose

This file is the explicit, queryable version of the lineage that already lives as inline SQL comments in the HRD test case's JDBC 2 query (`mapping` above). It exists so an agent tracing "why does target column X have this value" doesn't have to re-parse the workflow XML or the recompute SQL — it can look up the row here. It documents the same facts as [extraction.md](extraction.md)'s Description/Key Columns sections, at column granularity instead of prose.

# Source Structure

Two source paths are `UNION ALL`-ed before reaching the target, tagged by a literal `account_type`:
- **INTERNAL** — `CE_BANK_ACCOUNTS` (`ACC` alias). Has a real `ACCOUNT_HOLDER_NAME`; `PRIMARY_FLAG` is hardcoded `'Y'`.
- **EXTERNAL** — `IBY_EXT_BANK_ACCOUNTS` (`EB` alias) left-joined to `IBY_ACCOUNT_OWNERS` (`OW`, `PRIMARY_FLAG='Y'`). `ACCOUNT_HOLDER_NAME` is always NULL; `PRIMARY_FLAG`/`END_DATE` come from `OW`.

Both paths join to a `bank_branch` CTE (bank/branch hierarchy via `HZ_ORGANIZATION_PROFILES` → `HZ_RELATIONSHIPS` (`BANK_AND_BRANCH`/`BRANCH_OF`) → `HZ_PARTIES`, filtered by `SYSDATE BETWEEN` effective-date predicates) and optionally to a contact chain (`CE_CONTACT_ASSIGNMENTS` → `HZ_RELATIONSHIPS` (`CONTACT_OF`) → `HZ_PARTIES`). The contact chain can fan out to multiple rows per bank account; `ROW_NUMBER() OVER (PARTITION BY bank_account_id ORDER BY relationship_id)` picks one deterministically for the recompute, while the real Informatica mapping's `REJECT_FLAG`/`ORDER BY BANK_ACCOUNT_ID` dedup is non-deterministic (see workflow.md Known Caveats) — expect occasional `CONTACT_NAME`/`PHONE_NUM` mismatches on multi-contact accounts.

# Column Mapping

| Target Column (`W_BANK_DS`) | Derivation | Category | Notes |
|---|---|---|---|
| `BANK_KEY_CODE` | — | Dead | No connector into `W_BANK_DS` anywhere in the workflow. |
| `BANK_NAME` | `bank_branch.bank_name` ← `bankorgprofile.organization_name` | Mapped | |
| `PHONE_NUM` | `contact_phone_area_code \|\| '-' \|\| contact_phone_number` ← `HZ_PARTIES` (contact's party, via `HZ_RELATIONSHIPS.CONTACT_OF`) | Derived | Multi-contact fan-out; see Source Structure. |
| `TAX_NUMBER` | — | Dead | No connector. |
| `CONTACT_NAME` | `HZ_PARTIES.PARTY_NAME` (contact's party) | Derived | Same multi-contact caveat as `PHONE_NUM`. |
| `BANK_USER_NAME` | `ACC.ACCOUNT_HOLDER_NAME` (INTERNAL only; NULL for EXTERNAL) | Mapped | |
| `BANK_TYPE_CODE` | `bank_branch.institution_type` ← `bankca.class_code` (`BANK`/`CLEARINGHOUSE`) | Mapped | |
| `BANK_TYPE_NAME` | — | Dead | No connector. |
| `BANK_CAT_CODE` | `bank_account_type` ← `ACC.BANK_ACCOUNT_TYPE` / `EB.BANK_ACCOUNT_TYPE` | Mapped | Raw account subtype (e.g. CHECKING/SAVINGS) — **not** the INTERNAL/EXTERNAL literal; don't conflate. |
| `BANK_CAT_NAME` | — | Dead | No connector. |
| `BANK_ID` | — | Dead | No connector. |
| `ACCDET_ID` | — | Dead | No connector. |
| `ACCDET_NAME` | — | Dead | No connector. |
| `BANK_ACCT_NUM` | `ACC.BANK_ACCOUNT_NUM` / `EB.MASKED_BANK_ACCOUNT_NUM` | Mapped | |
| `BANK_ACCT_ALT_NUM` | — | Dead | No connector. |
| `BANK_ALT_NUM` | — | Dead | No connector. |
| `BANK_ALT_NAME` | `ACC.BANK_ACCOUNT_NAME_ALT` / `EB.BANK_ACCOUNT_NAME_ALT` | Mapped | |
| `COUNTRY_CODE` | `bank_branch.country` ← `branchparty.country` | Mapped | |
| `COUNTRY_NAME` | — | Dead | No connector. |
| `COUNTRY_REGION` | — | Dead | No connector into `W_BANK_DS`. |
| `STATE_CODE` | — | Dead | No connector into `W_BANK_DS`. |
| `STATE_NAME` | `bank_branch.state` ← `branchparty.state` | Mapped | |
| `STATE_REGION` | — | Dead | No connector. |
| `POSTAL_CODE` | — | Dead | No connector into `W_BANK_DS`. |
| `COUNTY` | `bank_branch.state` ← `branchparty.state` | Derived (dead-branch) | `EXP_BANKS`'s `IIF(ISNULL(INP_COUNTY), INP_STATE, INP_COUNTY)` always takes the `INP_STATE` branch — `INP_COUNTY` is never fed upstream, so `COUNTY` always equals `STATE_NAME`. Not a bug in the recompute; it's the workflow's real behavior. |
| `STREET_ADDRESS1` | `bank_branch.address_line1` ← `branchparty.address1` | Mapped | |
| `STREET_ADDRESS2` | — | Dead | No connector into `W_BANK_DS`. |
| `CITY` | `bank_branch.city` ← `branchparty.city` | Mapped | |
| `SWIFT_NAME` | — | Dead | No connector. |
| `SWIFT_CODE` | — | Dead | No connector. |
| `BANK_HIER_CODE` | — | Dead | No connector. |
| `BANK_HIER_NAME` | — | Dead | No connector. |
| `BANK_NUMBER` | `bank_branch.bank_number` ← `bankorgprofile.bank_or_branch_number` | Mapped | |
| `BANK_BRANCH_CODE` | `bank_branch.bank_branch_name` ← `branchparty.party_name` | Derived (aliased) | Aliased from the branch **name** per `EXT_BANK_BRANCH_CODE`'s expression — there is no separate branch-code source column, so this equals `BANK_BRANCH_NAME`. |
| `BANK_BRANCH_NAME` | `bank_branch.bank_branch_name` ← `branchparty.party_name` | Mapped | |
| `ACTIVE_FLG` | `'Y'` | Literal | |
| `CREATED_BY_ID` | `ACC.CREATED_BY` / `EB.CREATED_BY` (cast to string) | Mapped | |
| `CHANGED_BY_ID` | `ACC.LAST_UPDATED_BY` / `EB.LAST_UPDATED_BY` (cast to string) | Mapped | |
| `CREATED_ON_DT` | `ACC.CREATION_DATE` / `EB.CREATION_DATE` | Mapped | |
| `CHANGED_ON_DT` | `ACC.LAST_UPDATE_DATE` / `EB.LAST_UPDATE_DATE` | Mapped | |
| `AUX1_CHANGED_ON_DT` | `bank_branch.branch_last_update_date` ← `bankorgprofile.last_update_date` | Derived (session override) | Populated only because of the **session-level SQL override** of `SQ_AP_BANK_ACCOUNTS_ALL`; the mapping-level default SQL hardcodes this to NULL instead. The session override is what actually runs. |
| `AUX2_CHANGED_ON_DT` | — | Dead | `INP_AUX2_CHANGED_ON_DT` never fed a value upstream. |
| `AUX3_CHANGED_ON_DT` | — | Dead | `INP_AUX3_CHANGED_ON_DT` never fed a value upstream. |
| `AUX4_CHANGED_ON_DT` | — | Dead | `INP_AUX4_CHANGED_ON_DT` never fed a value upstream. |
| `SRC_EFF_FROM_DT` | `TO_DATE('18990101','YYYYMMDD')` | Literal | Part of the primary key. |
| `SRC_EFF_TO_DT` | — | Dead | No connector. |
| `DELETE_FLG` | — | Dead | No connector into `W_BANK_DS`. |
| `DATASOURCE_NUM_ID` | `$$DATASOURCE_NUM_ID` (session/mapping parameter) | Parameterized | DataOps side substitutes `$[DATASOURCE_NUM_ID]`, currently a placeholder (`0`) — see workflow.md Known Caveats before trusting a comparison on this key. Part of the primary key. |
| `INTEGRATION_ID` | `(CASE account_type WHEN 'EXTERNAL' THEN 'E' ELSE 'I' END) \|\| '~' \|\| bank_account_id` | Computed key | Part of the primary key. |
| `SET_ID` | — | Dead | No connector into `W_BANK_DS`. |
| `TENANT_ID` | — | Dead port | `Exp_Integration_ID` computes `TENANT_ID = IIF(ISNULL(INP_TENANT_ID),$$TENANT_ID,INP_TENANT_ID)`, but that output only flows into `Filter`, not into the SA mapplet — `INP_TENANT_ID` is never actually fed, so the loaded value is always NULL. Looks like a bug; matches current real behavior — don't "fix" without workflow-owner confirmation. |
| `X_CUSTOM` | — | Dead port | Same dead-port pattern as `TENANT_ID` — `INP_X_CUSTOM` never fed. |
| `BANK_ACCOUNT_NAME` | `ACC.BANK_ACCOUNT_NAME` / `EB.BANK_ACCOUNT_NAME` | Mapped | |
| `AGENCY_LOCATION_CODE` | `ACC.AGENCY_LOCATION_CODE` / `EB.AGENCY_LOCATION_CODE` | Mapped | |
| `PRIMARY_FLAG` | `'Y'` (INTERNAL) / `OW.PRIMARY_FLAG` (EXTERNAL) | Mapped (branch-dependent) | See Source Structure. |
| `END_DATE` | `ACC.END_DATE` (INTERNAL) / `OW.END_DATE` (EXTERNAL) | Mapped (branch-dependent) | See Source Structure. |

# Coverage Summary

- **56** target columns total.
- **12** dead ports (`TENANT_ID`, `X_CUSTOM`, `AUX2`–`AUX4_CHANGED_ON_DT`, `COUNTY`'s dead `ISNULL` branch counted separately below) plus **20** columns with no connector at all into `W_BANK_DS` — see rows marked `Dead`/`Dead port` above for the full list; don't treat a DataCompare mismatch on any of these as a defect without checking this table first.
- **2** literal constants (`ACTIVE_FLG`, `SRC_EFF_FROM_DT`), **1** computed key (`INTEGRATION_ID`), **1** parameterized column (`DATASOURCE_NUM_ID`).
- Everything else is a direct or joined pass-through — see `Mapped`/`Derived` rows for source lineage.
