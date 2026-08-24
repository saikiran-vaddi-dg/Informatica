---
generated:
  by: developer-agent
  at: "2026-08-20T17:08:35+05:30"
  commit: 3d75b1ec2bce1ee5922a1657fd7f2f114716032f
---

# HHS_SDE_ORA_QuickDemoFact — Workflow Logic

## Description

Single-mapping workflow `HHS_SDE_ORA_QuickDemoFact`: source `FV_GTAS_ACTIVITY_BALANCES` (Oracle, no schema-qualification attribute set beyond `DBDNAME="OLTP"`) flows through `SQ_FV_GTAS_ACTIVITY_BALANCES` -> `EXP_QUICKDEMO` -> target `W_GTAS_ACTIVITY_BALANCES_FS`. Only 4 columns are carried, all straight passthrough except one computed column:

- `CCID`, `PERIOD_NUM`, `SET_OF_BOOKS_ID` — passthrough, no transformation.
- `AMOUNT` = `ROUND(AMOUNT, 2)` (`EXPRESSIONTYPE="GENERAL"` in `EXP_QUICKDEMO`).

No source qualifier filter, no incremental logic, no mapping variables, no lookups — this is the simplest mapping in the repo so far. The workflow itself is a single `Session` task (`HHS_SDE_ORA_QuickDemoFact_PSC`) run on-demand, `Treat source rows as = Insert`.

The target, `W_GTAS_ACTIVITY_BALANCES_FS`, is the exact same physical table loaded by the full production `HHS_SDE_ORA_GTASActivityBalanceFact` workflow (see [../HHS_SDE_ORA_GTASActivityBalanceFact/extraction.md](../HHS_SDE_ORA_GTASActivityBalanceFact/extraction.md)), which carries 43 target columns at a 9-column composite grain. This mapping only populates 4 of those 43 columns and declares no grain/key at all. Combined with the workflow's own name ("QuickDemo"), this strongly suggests a demo/tutorial artifact rather than a mapping intended to run as a real ETL load against that shared production target — see [hrd_mapping.md](hrd_mapping.md#known-caveats) for the full caveat and how this shaped the dataflow built against it.

## Key Columns

- **Unique/natural key**: none declared — no `TARGETFIELD` in this XML declares anything other than `KEYTYPE="NOT A KEY"`, and unlike the sibling production workflow, this mapping does not even carry the full 9-column composite grain (`JE_HEADER_ID`, `JE_LINE_NUM`, `AE_HEADER_ID`, `AE_LINE_NUM`, `BALANCE_TYPE`, `RECORD_CATEGORY` are all absent from this mapping's 4-column scope).
- **Straight passthrough**: `CCID`, `PERIOD_NUM`, `SET_OF_BOOKS_ID`.
- **Derived**: `AMOUNT` = `ROUND(AMOUNT, 2)`.
- **No parameters, no lookups, no incremental filter** — the simplest mapping among the workflows processed so far.
