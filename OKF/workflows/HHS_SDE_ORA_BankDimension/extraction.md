---
type: Informatica Workflow
title: HHS_SDE_ORA_BankDimension
description: Straight SDE extract-to-staging load of CEBV_BANK_ACCOUNTS into W_BANK_DS; test case reviewed and confirmed, dataflow not yet built.
resource: /Workflows/HHS_SDE_ORA_BankDimension.XML
tags: [BankDimension, SDE, Oracle]
status: draft
generated: { by: "review-agent/claude-sonnet-5", at: "2026-08-17T00:00:00+05:30", commit: "dac58659327a1edee4c9ac1e95f4e82a1db0a8bf" }
verified:
  - { by: "review-agent/claude-sonnet-5", at: "2026-08-17T00:00:00+05:30" }
  - { by: "human:Datagaps", at: "2026-08-19T00:00:00+05:30" }
---

# Description

Straight SDE extract-to-staging load into `W_BANK_DS` — no lookup/update-strategy branching. Source is an INTERNAL/EXTERNAL `UNION ALL` recompute of `CEBV_BANK_ACCOUNTS` joined to a bank/branch hierarchy, filtered by `SYSDATE BETWEEN` effective-date predicates, with a session-level SQL override for `AUX1_CHANGED_ON_DT`. Multi-contact accounts are deduplicated non-deterministically via `REJECT_FLAG`/`ORDER BY BANK_ACCOUNT_ID` (first row wins). Several ports are always-NULL/dead (`INP_TENANT_ID`, `INP_X_CUSTOM`, `INP_COUNTY`, `INP_AUX2-4_CHANGED_ON_DT`, the `EXT_COUNTY` `IIF` branch) — notably, target `TENANT_ID` is wired from the mapplet's always-NULL `EXT_TENANT_ID` output rather than `Exp_Integration_ID`'s computed `TENANT_ID`/`$$TENANT_ID` fallback port, which looks like a bug but is the workflow's actual current behavior.

# Key Columns

- **Unique key**: `INTEGRATION_ID`, `DATASOURCE_NUM_ID`, `SRC_EFF_FROM_DT` (matches `W_BANK_DS`'s `KEYTYPE="PRIMARY KEY"` fields)
- **Derived / lookup-dependent**: `EXT_BANK_BRANCH_CODE` (aliased from branch name), `BANK_CAT_CODE` (vs. account-type literal — distinct fields, don't conflate)
- **Known-dead / always-NULL**: `TENANT_ID` (see Description), `INP_TENANT_ID`, `INP_X_CUSTOM`, `INP_COUNTY`, `INP_AUX2_CHANGED_ON_DT`–`INP_AUX4_CHANGED_ON_DT`

# Known Caveats

- Test case reviewed 2026-08-17 by review-agent and confirmed correct/complete against this description — single JDBC/JDBC/DataCompare shape, 58-column mapping, keys match the target's actual primary key. No draft/correction needed.
- The `REJECT_FLAG`/`ORDER BY BANK_ACCOUNT_ID` dedup for multi-contact accounts is non-deterministic in the source system sense (first row per sort order wins) — a DataCompare mismatch on a deduplicated row isn't automatically a defect; check which row the source actually returned first before concluding the mapping is wrong.
- `TENANT_ID`'s always-NULL wiring (see Description) looks like unreachable/dead logic in the mapping but matches the workflow's real current behavior — don't "fix" it in a test case without confirming with the workflow owner whether this is a known issue or intentional.
- Dataflow build/run blocked on `dataops_mcp` re-authentication — see project memory `project_dataops_mcp_auth_blocker`.

# Test Cases & Dataflows

| Test Case | HRD Mapping | Dataflow | Environment | Latest Run | Status | Fingerprint |
|---|---|---|---|---|---|---|
| [HHS_SDE_ORA_BankDimension_TestCase](/HRD/HHS_SDE_ORA_BankDimension_TestCase.json) | [column mapping](hrd_mapping.md) | not yet built — `dataops_mcp` connector unauthenticated as of this update | — | not yet run | Pending | — (not built yet) |
