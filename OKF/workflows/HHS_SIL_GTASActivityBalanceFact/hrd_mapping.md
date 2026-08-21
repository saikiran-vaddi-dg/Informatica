# HHS_SIL_GTASActivityBalanceFact — Test Cases, Dataflows & Caveats

## Test Cases & Dataflows

| Test Case | Dataflow | Container | Folder | Engine | Run ID | Status | Fingerprint |
|---|---|---|---|---|---|---|---|
| `HRD/HHS_SIL_GTASActivityBalanceFact_TestCase.json` | *(not yet created)* | Base | Dataflow | 168_AN | — | Not yet built/run | — |

## Known Caveats

- **Build/run blocked this session.** No `dataops_mcp` tools were available in this session (the connector requires re-authorization) so `create_dataflow`/`run_dataflow` were not attempted. The test case JSON exists at `HRD/HHS_SIL_GTASActivityBalanceFact_TestCase.json` and is ready to build once the connector is authorized.
- **`engineName=168_AN`, `folderName=Dataflow`, `container=Base` are project defaults from `dataops.config.yaml`, not yet confirmed against the live container.** Verify via `list_engines`/`list_folders`/`list_data_sources` — including whether the target container's `W_GTAS_ACTIVITY_BALANCES_FS` connection also exposes `W_GL_ACCOUNT_D`, `W_MCAL_PERIOD_D`, `W_LEDGER_D`, `W_GL_JE_SOURCES_D`, `W_GL_JE_CATEGORIES_D` for JDBC 2's correlated subqueries — before `create_dataflow` is called.
- **Possible dataflow name collision.** The SDE-layer sibling test case for the same underlying tables (`HHS_SDE_ORA_GTASActivityBalanceFact_TestCase`) hit a name collision in the target container that required a `_v2` suffix (see `OKF/workflows/HHS_SDE_ORA_GTASActivityBalanceFact/hrd_mapping.md`). Check `list_dataflows` for an existing `HHS_SIL_GTASActivityBalanceFact_TestCase` before creating.
- **`MCAL_PERIOD_WID` join reproduces an apparent naming swap as-is** — the deployed rule joins staging's `PERIOD_YEAR` to the dimension's `MCAL_PERIOD` column and staging's `PERIOD_NUM` to the dimension's `MCAL_YEAR` column. This is reproduced faithfully because it is the deployed rule under test, not corrected to what "looks right."
- **Compaction-tool gap suspected, not a workflow defect:** the compact summary's printed SQL override text for the staging→fact source qualifier appears truncated relative to `field_lineage`, which lists roughly 15 more passthrough fields than the printed SQL shows. Treat this as a tooling gap worth fixing in the compaction tool itself; do not silently guess additional columns into the test case query to compensate.
- **Two reusable mapplets (`MPLT_GET_ETL_PROC_WID`, `HHS_mplt_SIL_GTAS_Get_TP_Ledger_WID`) drive `ETL_PROC_WID`/`TP_OPDIV`/`TP_LEDGER_WID`** but their internal logic isn't visible in the compact summary, so these three columns are `ignoreColumn: true` in the test case rather than reproduced/guessed.
- **9-column composite unique key is inferred from the fact's grain**, not from an explicit `KEYTYPE` in the workflow XML (none declared beyond "NOT A KEY"). Prefer the real target table PK/unique constraint if it can be confirmed.
