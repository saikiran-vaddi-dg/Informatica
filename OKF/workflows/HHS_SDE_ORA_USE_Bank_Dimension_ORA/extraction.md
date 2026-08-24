---
generated:
  by: developer-agent
  at: "2026-08-24T16:24:35+05:30"
  commit: 7d254ea041b31d565335fb4f92269765b869cff4
---

# HHS_SDE_ORA_USE_Bank_Dimension_ORA — Extraction

## Description

Hardcoded-for-testing copy of `HHS_SDE_ORA_BankDimension` (see
[sibling extraction](../HHS_SDE_ORA_BankDimension/extraction.md) for the full
join/mapplet lineage — the sources, mapplets (`HHS_mplt_BC_ORA_BankDimension`,
`HHS_mplt_SA_ORA_BankDimension`), `Exp_Integration_ID` dedup expression, and
`Filter` transformation are unchanged). This variant exists purely so the
mapping's three `$$` mapping parameters can be exercised without an
environment/session config: `$$LAST_EXTRACT_DATE` is replaced by the literal
`TO_DATE('01/01/2020 00:00:00', 'MM/DD/YYYY HH24:MI:SS')` in the source
qualifier's CDC filter, `$$DATASOURCE_NUM_ID` is replaced by the literal `601`
in the `Exp_Integration_ID` expression, and `$$TENANT_ID` (the fallback value
inside `IIF(ISNULL(INP_TENANT_ID), $$TENANT_ID, INP_TENANT_ID)`) is replaced by
the literal `'DEFAULT'`. Target is the same staging table, `W_BANK_DS`.

## Key Columns

- **Unique/natural key**: `INTEGRATION_ID` = (E|I flag from ACCOUNT_TYPE) || '~' ||
  `BANK_ACCOUNT_ID`, deduped via the same Expression+Filter pair as the base
  workflow.
- **Hardcoded-literal columns (the point of this variant)**: `DATASOURCE_NUM_ID`
  (`601`, was `$$DATASOURCE_NUM_ID`), `TENANT_ID` fallback (`'DEFAULT'`, was
  `$$TENANT_ID`), and the CDC cutoff date (`01/01/2020`, was
  `$$LAST_EXTRACT_DATE`) baked into the source qualifier's `WHERE` clause.
- **Derived-lookup-dependent**: same as the base workflow — `CONTACT_NAME`/
  `PHONE_NUM` via the `HZ_RELATIONSHIPS`/`HZ_PARTIES` contact join,
  `BANK_NAME`/`BANK_TYPE_CODE`/`COUNTRY_CODE`/`STATE_NAME`/`CITY`/
  `STREET_ADDRESS1` via the derived branch view, `COUNTY` (COALESCE fallback
  to `STATE_NAME`).
- **Known quirk (inherited)**: `BANK_BRANCH_CODE` and `BANK_BRANCH_NAME` share
  the same source field — preserved as actual behavior, same as the base
  workflow.
- **No registered data source**: no source named
  `HHS_SDE_ORA_USE_Bank_Dimension_ORA` exists on the platform; the JDBC 2
  ("expected") side of the test case reuses the `HHS_SDE_ORA_BankDimension`
  data source since both point at the same OLTP EBS instance.
