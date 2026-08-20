# HHS_SIL_ProgramActivity_Dimension — Test Cases, Dataflows & Caveats

## Test Cases & Dataflows

| Test Case | Dataflow | Container | Folder | Engine | Run ID | Status | Fingerprint |
|---|---|---|---|---|---|---|---|
| `HRD/HHS_SIL_ProgramActivity_Dimension_TestCase.json` | *(not yet created)* | *(TBD)* | Dataflow | 168_AN | — | Not yet built/run | — |

## Known Caveats

- **Build/run blocked this session.** `dataops_mcp_68` requires re-authorization (token expired) as of this session, so `create_dataflow`/`run_dataflow` were not attempted. The test case JSON exists at `HRD/HHS_SIL_ProgramActivity_Dimension_TestCase.json` and is ready to build once the user re-authorizes the connector.
- **`engineName=168_AN`, `folderName=Dataflow`, and both `dataSourceName` values (`WC_PROGRAM_ACTIVITY_D`, `WC_PROGRAM_ACTIVITY_DS`) are unconfirmed.** They were carried over from prior test cases in this project (see the test case's `_notes`) and must be re-verified via `list_engines`/`list_folders`/`list_data_sources` — including whether the `WC_PROGRAM_ACTIVITY_DS` connection also exposes `W_LEDGER_D`/`W_USER_D` for the join — before `create_dataflow` is called.
- **Router INSERT/UPDATE/no-op branching not covered.** This is a run-to-run CDC concern, not verifiable via a single-snapshot DataCompare. Recommend running the eventual test after a full/initial load so every row is on the INSERT path.
- **`CMS_PRC_*_BY_ID` population depends on `LEDGER_WID` literally equal to 2** (hardcoded, environment-specific). Confirm test data includes at least one row mapping to `LEDGER_WID=2`, else that branch will pass vacuously.
- **`HHS_SIL_DATA_ACT_CONTROL_DUMMY` (workflow's 2nd mapping) is intentionally not covered** — trivial same-table passthrough with no testable business logic beyond an unreferenced `$$DATA_ACT_REPORTING_PERIOD` mapping variable.
- **Genuine potential mapping defect flagged (not a test bug), to investigate once run:** `PROGRAM_ACTIVITY_RPT_KEY`, `PROGRAM_ACTIVITY_RPT_KEY_DESC`, `CFRS_TREASURY_SYMBOL`, and the six raw `*_BY_ID` columns do not literally appear in the `SQ_WC_PROGRAM_ACTIVITY_DS` SQL override's SELECT list (only in JOIN ON predicates, for the `*_BY_ID` columns), even though field lineage traces them as passthrough through this same SQ. The test case's expected query includes them as real `WC_PROGRAM_ACTIVITY_DS` staging columns (the intended/should-be behavior); if the deployed override truly omits them, actual values may come back NULL/misaligned and the DataCompare should surface that as a mismatch. If the eventual run fails specifically on these columns, treat this as the likely explanation.
