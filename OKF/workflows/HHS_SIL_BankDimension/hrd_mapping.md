# HHS_SIL_BankDimension — HRD Mapping

## Test Cases & Dataflows

| Test Case | Dataflow | Environment | Run ID | Status | Fingerprint |
|---|---|---|---|---|---|
| `HRD/HHS_SIL_BankDimension_TestCase.json` | `HHS_SIL_BankDimension_TestCase` (`f58d08f7-9649-4266-8a9e-2a328645a883`) | `HHS_Poc_container` (id 525) / engine `168_AN` (livyServerId 983) / folder `Dataflow` | 330357 | Passed | `f58d08f7-9649-4266-8a9e-2a328645a883` @ run330357 (dataflowId + run timestamp basis only — `get_data_flow_definition` was unreachable this session (dataops_mcp tools don't propagate to this Agent-tool subagent), so no content-hash fingerprint could be computed; compute the real hash next time `get_data_flow_definition` is reachable) |

## Known Caveats

- **Two `compact_mapping.py` tool gaps affect this workflow's test-case
  coverage** (see `extraction.md`): (1) `mplt_SIL_BankDimension_CodeLookup`'s
  internal lookup(s) feeding `LKP_BANK_CODE` aren't surfaced in
  `transformation_logic`, so `BANK_KEY_CODE` is excluded from this test
  case; (2) `Exp_Scd2_Dates` (SCD2 date/flag derivation) has no
  `transformation_logic` entry at all, so all SCD2/audit/surrogate columns
  are excluded. Fix the compaction tool rather than falling back to raw
  XML for these.
- Test case scope is intentionally limited to the 49 confirmed
  straight-passthrough attribute columns, comparing `W_BANK_D` (current
  rows, `CURRENT_FLG='Y'`) against `W_BANK_DS` staging, keyed on
  `DATASOURCE_NUM_ID` + `INTEGRATION_ID` + `SRC_EFF_FROM_DT`. `BANK_KEY_CODE`,
  `DELETE_FLG`, and all SCD2/audit/surrogate columns are excluded as
  row-classification/action-derived or dependent on the tool gaps above.
- The target table `W_BANK_D` did not exist in the Oracle environment prior
  to this run. The user (via SQL Developer, connected as the `sh` user) ran
  a `CREATE TABLE` DDL script and a seed `INSERT ... SELECT FROM W_BANK_DS`
  script — both generated from the workflow's real `TARGETFIELD`
  definitions — to stand up the table before run 330357 could succeed. The
  seeded SCD2/audit columns (`ROW_WID`, `BANK_KEY_CODE`, `CURRENT_FLG`,
  `DELETE_FLG`, etc.) are placeholder values copied from staging, not real
  ETL output. This Passed result therefore validates only that the 49
  passthrough attribute columns land correctly end-to-end against real
  Oracle data — it does **not** validate the workflow's
  row-classification/SCD2/lookup logic, which remains blocked on the two
  `compact_mapping.py` coverage gaps above.
- Run 330357's full DataCompare report could not be downloaded via
  `download_data_compare_report` (connector unavailable this session — see
  `Results/HHS_SIL_BankDimension_TestCase_run330357_report.json`, which is
  a repository-query-derived substitute, not the downloaded report). The
  Passed status and 13/13 match are confirmed from `t_df_run`/
  `t_df_component_run`, but the full row/column-level report should be
  re-downloaded once the connector is reconnected.
