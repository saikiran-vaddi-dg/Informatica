# HHS_SDE_ORA_BankDimension — HRD Mapping

## Test Cases & Dataflows

| Test Case | Dataflow | Environment | Run ID | Status | Fingerprint |
|---|---|---|---|---|---|
| `HRD/HHS_SDE_ORA_BankDimension_TestCase.json` | `HHS_SDE_ORA_BankDimension_TestCase` (dataflowId `e017c2a3-e738-4194-97ae-6bde6e04ae58`) | `HHS_Poc_container` (containerId 525), engine `168_AN`, folder `Dataflow` | 330302 | Failed | `sha256:ac5255bd8ab334bd5adf5bfa913dfdbb5f61db2ca37e2371d3ce271fe1a46d41` (see caveat below — proxy hash) |

## Known Caveats

- **Fingerprint is a proxy, not a live-definition hash.** `get_data_flow_definition`
  is not reachable from this developer-agent subagent session (same MCP
  propagation limitation as create/run), so the recorded Fingerprint above is
  a SHA-256 of `HRD/HHS_SDE_ORA_BankDimension_TestCase.json` as built, not the
  deployed dataflow definition returned by the platform. Treat step 3's future
  drift check as best-effort until the orchestrator (or a session with live
  `dataops_mcp` access) fetches `get_data_flow_definition` for dataflowId
  `e017c2a3-e738-4194-97ae-6bde6e04ae58` and this row's Fingerprint is
  recomputed from that.
- **Fingerprint now stale relative to the local HRD file.** The Fingerprint
  above was computed from `HRD/HHS_SDE_ORA_BankDimension_TestCase.json`
  before the `passComponentIfDuplicatesExist` edit noted below; it no longer
  matches the current file's hash, and (per the point above) never matched
  the live deployed definition either since it was never pushed via
  `update_data_flow`. Recompute once this dataflow is actually rebuilt/
  updated on the platform against real `W_BANK_DS` data.
- **Run 330302 failed — classified, recommendation delivered, partially applied; do not treat as validated.**
  `analysis-agent` (`Results/HHS_SDE_ORA_BankDimension_TestCase_run330302_analysis.html`)
  classified every failure symptom (duplicated `INTEGRATION_ID` keys `E~6001`/
  `I~5001` in Dataset A, 12 of 13 blank derived/lookup columns in A, the
  `SRC_EFF_FROM_DT` mismatch) as **environment/data defects**: `W_BANK_DS`
  currently holds hand-seeded stub rows, not the output of an actual
  `HHS_SDE_ORA_BankDimension` mapping run against source EBS data. No test
  case defect and no genuine workflow/ETL bug was found. One item
  (`PHONE_NUM` for `I~5001`) needs re-verification after a clean reload
  before it can be fully closed out.
  - **Applied**: the one optional test-case hardening recommendation —
    `passComponentIfDuplicatesExist` changed from `ENABLED` to `DISABLED` in
    `HRD/HHS_SDE_ORA_BankDimension_TestCase.json`'s DataCompare config, since
    `INTEGRATION_ID` is a strict unique key and this had been masking the
    duplicate signal. This is a local test-case edit only — it was not
    pushed to the live dataflow via `update_data_flow` and the dataflow was
    not re-run, per the environment-defect classification below.
  - **Not applied / out of pipeline scope**: the 4 environment/data-defect
    items (duplicate stub rows, blank derived columns, `SRC_EFF_FROM_DT`,
    `PHONE_NUM`) all require someone to actually run the
    `HHS_SDE_ORA_BankDimension` mapping against source EBS data to reload
    `W_BANK_DS` with real output — this pipeline cannot and should not
    attempt that reload. Re-running the dataflow today would still fail
    against the same stub data, so no re-run was attempted. Status remains
    `Failed` until that external reload happens and this dataflow is
    re-run.
- Test case models the SDE's known quirk of `BANK_BRANCH_CODE` and
  `BANK_BRANCH_NAME` sharing the same source field as actual behavior, not a
  defect — see `extraction.md`.
- `X_CUSTOM` and `AUX1..4_CHANGED_ON_DT` origin is unresolved past the
  mapplet boundary (see `extraction.md`); not covered by this test case.
