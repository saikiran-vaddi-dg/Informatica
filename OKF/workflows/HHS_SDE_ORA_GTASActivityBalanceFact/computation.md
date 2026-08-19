---
type: Attested Computation
title: HHS_SDE_ORA_GTASActivityBalanceFact_TestCase computation contract
description: Sanctioned DataCompare definition for verifying W_GTAS_ACTIVITY_BALANCES_FS against a recomputation of FV_GTAS_ACTIVITY_BALANCES.
resource: "dataops://DevContainer/Dataflow/WorkingSession/HHS_SDE_ORA_GTASActivityBalanceFact_TestCase"
tags: [GTAS, ActivityBalance, SDE, computation]
status: draft
runtime: dataops-dataflow
parameters:
  - { name: engineName, type: string, required: true }
  - { name: folderName, type: string, required: true }
  - { name: DATASOURCE_NUM_ID, type: string, required: true }
computation: /HRD/HHS_SDE_ORA_GTASActivityBalanceFact_TestCase.json
executor:
  resource: "dataops://DevContainer/engine/168_AN?dataflow_guid=9ea17989-6e31-43e2-9f34-a4ed516d7461"
  receipt: [runId, status, differenceCount, reportPath, analysisPath]
attester:
  resource: /references/attesters/datacompare_verify.py
generated: { by: "developer-agent/claude-sonnet-5", at: "2026-08-19T00:00:00+05:30" }
---

# Computation

DataCompare between:
- **JDBC 1 (actual)** — `W_GTAS_ACTIVITY_BALANCES_FS` as loaded by the workflow.
- **JDBC 2 (expected)** — a recomputed query over `FV_GTAS_ACTIVITY_BALANCES`.

Full source/mapping/DataCompare definitions live in the file named by `computation` above. This contract is reused by every run of this dataflow; per-run outcomes are not persisted as bundle files (OKF §10.2 — a Receipt is a runtime artifact) and instead live in `Results/HHS_SDE_ORA_GTASActivityBalanceFact_TestCase_v2_run329920_report.json`/`_analysis.html`, linked from the workflow concept file's "Test Cases & Dataflows" table.

`attester` runs `datacompare_verify.py <report.json>` against a run's saved report and exits 0 (PASS) or 1 (FAIL); it does not itself know which report belongs to which run — the caller supplies that via `executor.receipt.reportPath`.
