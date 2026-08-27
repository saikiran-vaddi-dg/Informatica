# HHS_SDE_ORA_GTASActivityBalanceFact — HRD Mapping

## Test Cases & Dataflows

| Test Case | Dataflow | Environment | Run ID | Status | Fingerprint |
|---|---|---|---|---|---|
| `HRD/HHS_SDE_ORA_GTASActivityBalanceFact_TestCase.json` | `HHS_SDE_ORA_GTASActivityBalanceFact_TestCase` (not yet created) | TBD | — | Not yet run | — |

## Known Caveats

- **FDA session only.** This test case covers only the `SQ_FV_GTAS_ACTIVITY_BALANCES_FDA`
  session-level partition override. The `_PSC`, `_CDC`, and `_IHS` overrides
  share identical join/CASE logic for `PROVIDER_RECIPNT_ID` but filter on
  different `$$GTAS_FISCAL_YR_<X>_EXT` parameters and different physical
  partitions — they are not covered here and would need parallel test cases.
- **Unresolved parameter placeholder.** `$$GTAS_FISCAL_YR_FDA_EXT` in the
  expected-side query (`sources[1].query` in the HRD file) has no resolved
  default. It must be substituted with the actual fiscal year loaded into
  `W_GTAS_ACTIVITY_BALANCES_FS` before a run against this test case is
  meaningful — otherwise the expected side returns rows for all fiscal years,
  not the one actually staged.
- **Recreated/corrected test case.** The version of this file committed at
  `bf9c51e` tested the mapping-level default query (dead code — missing 2
  output ports, never executed in production). This file replaces it with the
  session-level `_FDA` override logic actually run in production; see
  `extraction.md` for the full comparison. Prior `Results/` artifacts (if
  any existed) from the old version should not be treated as validating this
  corrected test case.
- No dataflow has been created/run against this file yet — the pipeline's
  build/run/report step is pending in a session with `dataops_mcp` access.
