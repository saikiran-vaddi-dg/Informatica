# HHS_SDE_ORA_USE_Bank_Dimension_ORA — HRD Mapping

## Test Cases & Dataflows

| Test Case | Dataflow | Environment | Run ID | Status | Fingerprint |
|---|---|---|---|---|---|
| `HRD/HHS_SDE_ORA_USE_Bank_Dimension_ORA_TestCase.json` | `HHS_SDE_ORA_USE_Bank_Dimension_ORA_TestCase` (`381c9463-cd18-4b61-a7af-7b3fd55ce004`) | HHS_Poc_container | 330335 | Failed (environment/data defect — `W_BANK_DS` still empty, recommendation delivered, awaiting operator action) | `sha256:7029ec458ced84732c4060d954dcdbb61d4de671ff88d2a2a6d82da456586e3b` (see caveat below — proxy hash) |

## Known Caveats

- **Fingerprint is a proxy, not a live-definition hash.** `get_data_flow_definition`
  was not reachable this session — `dataops_mcp` required authentication that
  could not be completed non-interactively — so the recorded Fingerprint
  above is a SHA-256 of `HRD/HHS_SDE_ORA_USE_Bank_Dimension_ORA_TestCase.json`
  as deployed via `update_data_flow`, not the live definition returned by the
  platform. Treat step 3's future drift check as best-effort until a session
  with live `dataops_mcp` access fetches `get_data_flow_definition` for
  dataflowId `381c9463-cd18-4b61-a7af-7b3fd55ce004` and this row's Fingerprint
  is recomputed from that.
- **Sources JDBC/actual side (`W_BANK_DS`)** is the same shared staging table
  as `HHS_SDE_ORA_BankDimension`'s test case — see
  [that workflow's caveats](../HHS_SDE_ORA_BankDimension/hrd_mapping.md) for
  the current known state of that table's data. **Run 330335 (2026-08-24)
  again found the table completely empty** (0 rows vs. 8 expected-side rows
  from JDBC 2), the same unresolved state as run 330329 before the test case
  fix — see
  `Results/HHS_SDE_ORA_USE_Bank_Dimension_ORA_TestCase_run330335_analysis.html`.
  Classified as an environment/data defect (table not populated by an actual
  mapping run against source EBS data), not a test case or workflow bug — the
  expected side (JDBC 2) correctly returned all 8 live rows including the
  corrected `ACTIVE_FLG` lifecycle values (`Y`/`P`/`N`). Recommended action:
  populate/reload `W_BANK_DS` by running the actual ETL mapping, or confirm/
  restore the table if it was truncated. This is a pipeline-blocking
  environment defect outside this repo's automation scope — no further
  AI-driven run will pass until an operator addresses it.
- **No dedicated data source for this variant.** The "expected" (JDBC 2) side
  reuses the `HHS_SDE_ORA_BankDimension` data source registration (same OLTP
  EBS connection) since no source named
  `HHS_SDE_ORA_USE_Bank_Dimension_ORA` is registered on the platform — see
  `extraction.md`.
- Test case models the inherited `BANK_BRANCH_CODE`/`BANK_BRANCH_NAME`
  same-source-field quirk as actual behavior, not a defect.
- **`ACTIVE_FLG` lifecycle correction validated (2026-08-24, run 330335).**
  The upstream workflow moved `EXT_ACTIVE_FLAG` from a hardcoded `'Y'` to a
  3-way lifecycle rule keyed on `END_DATE` (see `extraction.md`'s Key Columns
  section). `HRD/HHS_SDE_ORA_USE_Bank_Dimension_ORA_TestCase.json`'s JDBC 2
  expected-side query was corrected to match (`CASE WHEN END_DATE IS NULL
  THEN 'Y' WHEN END_DATE > SYSDATE THEN 'Y' WHEN END_DATE > (SYSDATE - 90)
  THEN 'P' ELSE 'N' END AS ACTIVE_FLG`), pushed via `update_data_flow`, and
  re-run as 330335 — the JDBC 2 query in
  `Results/HHS_SDE_ORA_USE_Bank_Dimension_ORA_TestCase_run330335_report.json`
  confirms the corrected expression is live and producing the expected `Y`/
  `P`/`N` values against real EBS data. The run still fails, but solely on
  the unrelated `W_BANK_DS` empty-table environment defect above, not on
  this expression.
