# HHS_SDE_ORA_USE_Bank_Dimension_ORA — HRD Mapping

## Test Cases & Dataflows

| Test Case | Dataflow | Environment | Run ID | Status | Fingerprint |
|---|---|---|---|---|---|
| `HRD/HHS_SDE_ORA_USE_Bank_Dimension_ORA_TestCase.json` | `HHS_SDE_ORA_USE_Bank_Dimension_ORA_TestCase` (`381c9463-cd18-4b61-a7af-7b3fd55ce004`) | HHS_Poc_container | 330329 | Failed (environment/data defect — recommendation delivered, awaiting operator action) | pending |

## Known Caveats

- **Sources JDBC/actual side (`W_BANK_DS`)** is the same shared staging table
  as `HHS_SDE_ORA_BankDimension`'s test case — see
  [that workflow's caveats](../HHS_SDE_ORA_BankDimension/hrd_mapping.md) for
  the current known state of that table's data (as of the last run there, it
  held hand-seeded stub rows rather than real mapping output). **Run 330329
  (2026-08-24) found the table completely empty** (0 rows, vs. 4 hand-seeded
  stub rows in the sibling's last run) — see
  `Results/HHS_SDE_ORA_USE_Bank_Dimension_ORA_TestCase_run330329_analysis.html`.
  Classified as an environment/data defect (table not populated by an actual
  mapping run against source EBS data), not a test case or workflow bug — the
  expected side (JDBC 2) returned 4 live rows correctly. Recommended action:
  populate/reload `W_BANK_DS` by running the actual ETL mapping, or confirm/
  restore the table if it was truncated.
- **No dedicated data source for this variant.** The "expected" (JDBC 2) side
  reuses the `HHS_SDE_ORA_BankDimension` data source registration (same OLTP
  EBS connection) since no source named
  `HHS_SDE_ORA_USE_Bank_Dimension_ORA` is registered on the platform — see
  `extraction.md`.
- Test case models the inherited `BANK_BRANCH_CODE`/`BANK_BRANCH_NAME`
  same-source-field quirk as actual behavior, not a defect.
