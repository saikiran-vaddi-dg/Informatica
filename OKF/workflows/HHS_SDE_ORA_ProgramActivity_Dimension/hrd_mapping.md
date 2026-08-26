# HHS_SDE_ORA_ProgramActivity_Dimension — HRD Mapping

## Test Cases & Dataflows

| Test Case | Dataflow | Environment | Run ID | Status | Fingerprint |
|---|---|---|---|---|---|
| [HHS_SDE_ORA_ProgramActivity_Dimension_TestCase](../../../HRD/HHS_SDE_ORA_ProgramActivity_Dimension_TestCase.json) | HHS_SDE_ORA_ProgramActivity_Dimension_TestCase (`08c9c67d-89c2-495d-8f61-3b7f9a0ddb0f`) | HHS_Poc_container / 168_AN / Dataflow | 330410 | Failed (environment/data defect) | `93b6989b477ec48584a5d779179b8d24` (md5) |

## Known Caveats

- **JDBC 2 (expected side) source schemas appear empty/unloaded in this POC Oracle instance.** The query (`FDABI.FV_FACTS_PRC_HDR HDR LEFT JOIN FDABI.FV_FACTS_PRC_DTL DTL ... LEFT JOIN FV.FV_DACT_PRC_ALLOCATION ALLOC ...`) is an unfiltered LEFT JOIN chain driven from `FDABI.FV_FACTS_PRC_HDR`; run 330410 read 0 rows from it while the actual/staging side (`WC_PROGRAM_ACTIVITY_DS`) had 4 rows already populated, producing a 100% "Only In A" DataCompare failure. Per `Results/HHS_SDE_ORA_ProgramActivity_Dimension_TestCase_run330410_analysis.html` (analysis-agent), this is classified as an **environment/data defect**, not a test-case or workflow-logic defect — under LEFT JOIN semantics, 0 rows with no WHERE clause can only mean the driving table itself is empty/inaccessible as seen by the connection, most likely because `FDABI`/`FV` schemas were never loaded with representative data in this POC instance (or the data source's connection targets a different Oracle instance/schema than whatever originally fed the staging table).
- **Recommended action (outside this pipeline's scope):** verify `FDABI.FV_FACTS_PRC_HDR`'s actual row count via that connection, then either populate `FDABI.FV_FACTS_PRC_HDR` / `FDABI.FV_FACTS_PRC_DTL` / `FV.FV_DACT_PRC_ALLOCATION` with representative data, or repoint the `FV_FACTS_PRC_HDR` data source's connection at the instance/schema that actually holds this data. No change was made to `HRD/HHS_SDE_ORA_ProgramActivity_Dimension_TestCase.json` or the dataflow to work around this — the schema-qualification fix (`FDABI.`/`FV.` prefixes) applied earlier in this run was a genuine correction (it resolved a real ORA-00942) and is retained; only the *emptiness* of the resulting driving table is unresolved and is external to this pipeline.
- This caveat stays until the environment fix is made and this dataflow is re-run to confirm rows now flow through — at that point this bullet should be removed/rewritten, not appended to.
