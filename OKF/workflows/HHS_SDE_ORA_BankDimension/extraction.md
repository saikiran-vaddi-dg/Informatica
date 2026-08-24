---
generated:
  by: developer-agent
  at: "2026-08-24T10:48:30+05:30"
  commit: f8fefb09224960e7450c7586e6b88f30f1582825
---

# HHS_SDE_ORA_BankDimension — Extraction

## Description

SDE mapping that extracts bank/branch/account data from Oracle EBS
(`CE_BANK_ACCOUNTS` internal accounts `UNION ALL` `IBY_EXT_BANK_ACCOUNTS`/
`IBY_ACCOUNT_OWNERS` external accounts, joined to a branch view derived from
`HZ_ORGANIZATION_PROFILES`/`HZ_CODE_ASSIGNMENTS`/`HZ_PARTIES`/`HZ_RELATIONSHIPS`,
plus an outer-joined primary contact via `CE_CONTACT_ASSIGNMENTS`) into staging
table `W_BANK_DS`. An incremental CDC filter (`$$LAST_EXTRACT_DATE`) and a
sequential-variable-port dedup (on a derived `INTEGRATION_ID`) guard against the
contact-join fan-out producing duplicate rows.

## Key Columns

- **Unique/natural key**: `INTEGRATION_ID` = (E|I flag from ACCOUNT_TYPE) || '~' ||
  `BANK_ACCOUNT_ID`, deduped via the Expression+Filter pair.
- **Derived-lookup-dependent**: `CONTACT_NAME`/`PHONE_NUM` (via the
  `HZ_RELATIONSHIPS`/`HZ_PARTIES` contact join), `BANK_NAME`/`BANK_TYPE_CODE`/
  `COUNTRY_CODE`/`STATE_NAME`/`CITY`/`STREET_ADDRESS1` (via the derived branch
  view), `COUNTY` (COALESCE fallback to `STATE_NAME`).
- **Parameterized**: `DATASOURCE_NUM_ID` (`$$DATASOURCE_NUM_ID`), `TENANT_ID`
  (`$$TENANT_ID` fallback when source tenant is null).
- **Known quirk**: `BANK_BRANCH_CODE` and `BANK_BRANCH_NAME` share the same
  source field — likely unintentional, preserved in the test case as actual
  behavior.
- **Always-NULL in this SDE**: `ACCDET_NAME`/`ID`, `BANK_ID`, `BANK_CAT_NAME`,
  `BANK_TYPE_NAME`, `TAX_NUMBER`, `SRC_EFF_TO_DT`, `BANK_HIER_NAME`/`CODE`,
  `SWIFT_NAME`/`CODE`, `COUNTRY_NAME`, `BANK_ALT_NUM`, `BANK_ACCT_ALT_NUM`.
- **Unresolved**: `X_CUSTOM`, `AUX1..4_CHANGED_ON_DT` origin not traceable past
  the mapplet boundary.
