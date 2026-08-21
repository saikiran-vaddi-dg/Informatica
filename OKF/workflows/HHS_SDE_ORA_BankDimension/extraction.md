---
generated:
  by: developer-agent
  at: "2026-08-21T14:06:39+05:30"
  commit: 11e8719dfbc0797fba734ef345915b5ea7cef90c
---

# HHS_SDE_ORA_BankDimension — Workflow Logic

## Description

HHS_SDE_ORA_BankDimension (SDE layer) extracts bank/account/branch data from Oracle EBS (`HZ_PARTIES`, `CEBV_BANK_ACCOUNTS`, `CEBV_BANK_BRANCHES`) through a 17-join SQL override embedded in the reusable mapplet `HHS_mplt_BC_ORA_BankDimension`, computes a natural key via the `Exp_Integration_ID` expression, filters to `REJECT_FLAG = 'I'` (validated inserts only), then passes through the reusable staging mapplet `HHS_mplt_SA_ORA_BankDimension` into the `W_BANK_DS` staging table. It is a straight extract-to-stage load with no lookups or router branching at the top mapping level; all business logic lives inside the two reusable mapplets.

Of the target's key computed columns (test case not yet run, see [hrd_mapping.md](hrd_mapping.md)):

- Unique/natural key: `ACCDET_ID` (bank account ID, source-PK passthrough) — used in place of `INTEGRATION_ID` for this test case because the `Exp_Integration_ID` formula is not exposed in the current compact summary.
- Derived/lookup-dependent (logic lives inside `HHS_mplt_BC_ORA_BankDimension`'s SQL override, not independently confirmed): `BANK_CAT_NAME`/`CODE`, `BANK_TYPE_NAME`/`CODE`, `BANK_USER_NAME`, `BANK_HIER_NAME`/`CODE`, `COUNTRY_NAME`, `AGENCY_LOCATION_CODE`, `X_CUSTOM`.
- Parameterized (constant per run, not row logic): `$$DATASOURCE_NUM_ID` (decimal, no default) -> `DATASOURCE_NUM_ID`; `$$TENANT_ID` (string, default `DEFAULT`) -> `TENANT_ID`.

## Key Columns

- **Unique/natural key**: `ACCDET_ID` (bank account ID, source-PK passthrough) — substituted for `INTEGRATION_ID` in the test case since `Exp_Integration_ID`'s port formula is not captured by the current compaction tooling.
- **Derived / lookup-dependent** (via `HHS_mplt_BC_ORA_BankDimension`'s 17-join SQL override, not independently confirmed against the actual override text): `BANK_CAT_NAME`, `BANK_CAT_CODE`, `BANK_TYPE_NAME`, `BANK_TYPE_CODE`, `BANK_USER_NAME`, `BANK_HIER_NAME`, `BANK_HIER_CODE`, `COUNTRY_NAME`, `AGENCY_LOCATION_CODE`, `X_CUSTOM`.
- **Parameterized (mapping variables)**: `$$DATASOURCE_NUM_ID` (decimal, no default) -> `DATASOURCE_NUM_ID`; `$$TENANT_ID` (string, default `DEFAULT`) -> `TENANT_ID`.
- **Filter**: `REJECT_FLAG = 'I'` (validated inserts only) — assumed satisfied by construction on the expected/source side, not independently verified against the mapplet's actual dedup/reject logic.
- **Known gap**: `field_lineage` covers 47 of 56 target fields; the remaining 9 are presumed standard OBIA ETL audit/system columns not traced by the current tooling. See [hrd_mapping.md](hrd_mapping.md#known-caveats) for the full list of compaction-tool gaps and unverified placeholders.

This is a first full review of this workflow (no prior `generated.commit` exists to diff against).
