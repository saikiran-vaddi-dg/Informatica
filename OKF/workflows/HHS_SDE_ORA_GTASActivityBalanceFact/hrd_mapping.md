# HHS_SDE_ORA_GTASActivityBalanceFact — Test Cases, Dataflows & Caveats

## Test Cases & Dataflows

| Test Case | Dataflow | Container | Folder | Engine | Run ID | Status | Fingerprint |
|---|---|---|---|---|---|---|---|
| `HRD/HHS_SDE_ORA_GTASActivityBalanceFact_TestCase.json` | `HHS_SDE_ORA_GTASActivityBalanceFact_TestCase_v2` (guid `c094116a-4687-4eb3-968f-50062281a005`) | DevContainer (518) | Dataflow | 168_AN | 330171 | Failed | `sha256:0b0ca5bfdc819bff6ee472cdbb73d7c4b5102f92bd75601c90398dbf96d5ffca` |

Report: [`Results/HHS_SDE_ORA_GTASActivityBalanceFact_TestCase_v2_run330171_report.json`](../../../Results/HHS_SDE_ORA_GTASActivityBalanceFact_TestCase_v2_run330171_report.json). Analysis: [`Results/HHS_SDE_ORA_GTASActivityBalanceFact_TestCase_v2_run330171_analysis.html`](../../../Results/HHS_SDE_ORA_GTASActivityBalanceFact_TestCase_v2_run330171_analysis.html).

Note: a second, differently-shaped dataflow named `HHS_SDE_ORA_GTASActivityBalanceFact_TestCase` (no `_v2` suffix) already exists in the same container under folder `WorkingSession` from a prior investigation. It is **not** tracked by this table/row — its logic was inspected only as supporting evidence for the caveat below and it was not built, run, or modified by this pipeline.

## Known Caveats

- **Run 330171 Failed against 0-tolerance DataCompare thresholds** — this is a real reconciliation failure, not a technical/setup error. Full breakdown in the analysis report above.
- **XML-vs-production discrepancy on `INTEGRATION_ID` (confirmed)** — the currently committed workflow XML's empty `EXPRESSION` attribute for `out_INTEGRATION_ID` does not match live target data: the real target holds values shaped `<JE_HEADER_ID>~<JE_LINE_NUM>` (e.g. `5001~1`), not `NULL`. Recommend re-exporting/reconciling the production mapping for this port. See analysis report for evidence.
- **XML-vs-production discrepancy on `PROVIDER_RECIPNT_ID` / `PROVIDER_RECIPNT_NAME` (confirmed)** — the XML's documented `PARENT_AWARD_ID`-passthrough / `LKP_PROVD_RECP`/`LKP_INTRA_HHS_ELI` lookup logic does not reproduce live target values (e.g. target ID `1200`/name `DEPARTMENT OF ENERGY` vs. this test case's computed `PAW0001`/blank). The pattern instead resembles a richer `TRADING_PARTNER_TYPE`-keyed lookup already present in the pre-existing `HHS_SDE_ORA_GTASActivityBalanceFact_TestCase` dataflow in `DevContainer/WorkingSession` (built in an earlier session, not part of this pipeline's tracked row above). Needs user/SME reconciliation of which side is authoritative — not something this pipeline should silently patch into either the XML or the test case.
- **1 only-in-source row (CCID=10010)** — plausibly explained by this run being a full-table comparison (the `:LAST_EXTRACT_DATE` bind was removed because it isn't valid on this platform and no real value was known) against a target that was actually last loaded under the real incremental filter; not treated as a defect.
- **Placeholder/unresolved values still present by design**: `DATASOURCE_NUM_ID` is `ignoreColumn: true` and always `NULL` in this test case (driven by unresolved `$$DATASOURCE_NUM_ID` at runtime), and JDBC 2 now runs as a full extract with no incremental filter — see `HRD/HHS_SDE_ORA_GTASActivityBalanceFact_TestCase.json`'s `_notes` for detail.
- **Status is not Validated.** Because the run Failed and two genuine XML-vs-production discrepancies are outstanding, this dataflow has not cleared this pipeline's validation bar. Do not schedule it in the DataGaps native UI as a trusted check until the discrepancies above are resolved and a clean re-run confirms a matching `Fingerprint`.
