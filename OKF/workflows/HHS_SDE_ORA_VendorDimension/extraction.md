---
generated:
  by: developer-agent
  at: "2026-08-24T15:19:09+05:30"
  commit: ef22da5
---

# HHS_SDE_ORA_VendorDimension — Extraction

## Description

Synthetic demo SDE mapping. Extracts vendor master data from Oracle EBS
`PO_VENDORS`, joined to each vendor's primary pay-site address/phone from
`PO_VENDOR_SITES_ALL` (filtered to `PRIMARY_PAY_SITE_FLAG='Y'`), filtered to
enabled vendors only (`ENABLED_FLAG='Y'`), and loaded into staging table
`W_VENDOR_DS`. All 20 target columns come from a single
`Exp_Vendor_Business_Rules` expression — mostly direct passthroughs, a
handful of `TO_CHAR`/concatenation derivations, one conditional (`COUNTRY`
default to `'USA'` when null), and several hardcoded literal constants. No
mapping variables, no session parameters, no lookups, no router branching,
no SQL override.

## Key Columns

- **Unique/natural key**: `VENDOR_ID` (`TO_CHAR(PO_VENDORS.VENDOR_ID)`);
  `INTEGRATION_ID` (`'VND~' || VENDOR_ID`) is an equivalent derived business
  key.
- **Derived-lookup-dependent (via join)**: `ADDRESS_LINE1`/`CITY`/`STATE`/
  `ZIP`/`PHONE` come from `PO_VENDOR_SITES_ALL`'s primary pay site row,
  joined against `PO_VENDORS`.
- **Conditional**: `COUNTRY` defaults to `'USA'` when source value is null.
- **Hardcoded literals (not parameterized)**: `TENANT_ID` (`'HHS_DEFAULT'`),
  `DATASOURCE_NUM_ID` (`302`), `SRC_EFF_FROM_DT` (`01/01/1900`),
  `ACTIVE_FLG` (`'Y'`) — unlike `HHS_SDE_ORA_BankDimension`, these are plain
  literals in the expression, not `$$`-parameters. Note: `DATASOURCE_NUM_ID`
  has already changed once (`301` -> `302`, commit `ef22da5`, "reassign to
  source system 302") — confirm with the SME whether this literal is stable
  going forward or likely to keep moving.
- **Filters**: `PO_VENDOR_SITES_ALL.PRIMARY_PAY_SITE_FLAG='Y'` (source
  qualifier filter) and `ENABLED_FLAG='Y'` (post-join Filter transformation).
- **Known caveat**: the `JNR_VendorPrimarySite` Joiner's exact join type
  (inner vs outer) isn't captured by `compact_mapping.py`'s
  `transformation_logic` output for this workflow (a tool gap — flagged as
  such, not a workflow ambiguity). The test case assumes an inner join on
  `VENDOR_ID`; confirm against the platform once available.
