# HHS_SDE_ORA_QuickDemoFact — Test Cases, Dataflows & Caveats

## Test Cases & Dataflows

| Test Case | Dataflow | Container | Folder | Engine | Run ID | Status | Fingerprint |
|---|---|---|---|---|---|---|---|
| `HRD/HHS_SDE_ORA_QuickDemoFact_TestCase.json` | `HHS_SDE_ORA_QuickDemoFact_TestCase` (guid `807e24b2-0ac4-4306-a6b9-36d93182c5e6`) | DevContainer (518) | Dataflow | 168_AN | 330247 | Failed | `sha256:6071b4a550c2134b733c4109295555af1490ad5167e6f85a5ce759db437fdab7` |

`engineName=168_AN`/`folderName=Dataflow` and both `dataSourceName` values (`W_GTAS_ACTIVITY_BALANCES_FS`, `FV_GTAS_ACTIVITY_BALANCES`) were verified live in DevContainer (518) via `list_engines`/`list_folders`/`list_data_sources` before `create_dataflow`.

Report (run 330247): [`Results/HHS_SDE_ORA_QuickDemoFact_TestCase_run330247_report.json`](../../../Results/HHS_SDE_ORA_QuickDemoFact_TestCase_run330247_report.json). Analysis (run 330247): [`Results/HHS_SDE_ORA_QuickDemoFact_TestCase_run330247_analysis.html`](../../../Results/HHS_SDE_ORA_QuickDemoFact_TestCase_run330247_analysis.html).

## Known Caveats

- **This target table is shared with the production `HHS_SDE_ORA_GTASActivityBalanceFact` workflow, which loads a much wider column set at a 9-column grain — this mapping's name and scope suggest it is a demo/tutorial artifact rather than a mapping meant to run against that same production target as a real ETL load. `(CCID, PERIOD_NUM, SET_OF_BOOKS_ID)` used as the DataCompare key here is not the table's true unique grain.**
- **Run 330247 Failed against 0-tolerance thresholds: 9/10 rows matched exactly (including the `ROUND(AMOUNT,2)` computation, 0 mismatches, 0 duplicates), 1 row only-in-source (`CCID=10010, PERIOD_NUM=9, SET_OF_BOOKS_ID=2021, AMOUNT=500000.00`).** Root cause per analysis-agent: an environment/data-freshness defect, not a mapping-logic or test-case-scoping defect. The 9 matched rows are best explained as incidental overlap with the separate production `HHS_SDE_ORA_GTASActivityBalanceFact` load on the same shared target table, not evidence this mapping itself has ever actually run. The `CCID=10010` gap is the same source row already flagged as unloaded in `Results/HHS_SDE_ORA_GTASActivityBalanceFact_TestCase_v2_run330171_analysis.html` (Finding 3, attributed to `$$LAST_EXTRACT_DATE` having no resolvable value) — since this mapping's source qualifier has no filter at all, it would have picked up all 10 rows had it ever actually run. Full breakdown in the analysis report above.
- **Decision needed from the workflow owner (not yet made):** either (a) actually execute this mapping against real data so the target genuinely reflects its output, or (b) if confirmed as a demo/tutorial mapping never meant to write into the shared production target, retarget the test case to wherever it's actually meant to write. No test-case or XML change has been applied — this is recorded as an open decision, not a completed fix.
- **Status is not Validated.** Do not schedule this dataflow in the DataGaps native UI as a trusted check until the retarget-vs-execute decision above is made and a clean re-run confirms a matching `Fingerprint`.
