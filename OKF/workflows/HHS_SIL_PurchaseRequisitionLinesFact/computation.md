---
type: Attested Computation
title: HHS_SIL_PurchaseRequisitionLinesFact_TestCase computation contract
description: Sanctioned DataCompare definition for verifying W_PURCH_RQSTN_LINE_F against a recomputation from W_PURCH_RQSTN_LINE_FS.
resource: "dataops://DevContainer/Dataflow/WorkingSession/HHS_SIL_PurchaseRequisitionLinesFact_TestCase"
tags: [PurchaseRequisitionLinesFact, SIL, computation]
status: draft
runtime: dataops-dataflow
parameters:
  - { name: engineName, type: string, required: true }
  - { name: folderName, type: string, required: true }
computation: /HRD/HHS_SIL_PurchaseRequisitionLinesFact_TestCase.json
executor:
  resource: "dataops://DevContainer/engine/168_AN?dataflow_guid=c9b52ed8-2ca6-4d88-ae88-823003f6564a"
  receipt: [runId, status, differenceCount, reportPath]
attester:
  resource: /references/attesters/datacompare_verify.py
generated: { by: "developer-agent/claude-sonnet-5", at: "2026-08-19T00:00:00+05:30" }
---

# Computation

DataCompare between:
- **JDBC 1 (actual)** — target read of `W_PURCH_RQSTN_LINE_F`.
- **JDBC 2 (expected)** — recomputed rows from `W_PURCH_RQSTN_LINE_FS` via the SCD2 effective-dated dimension joins and date-to-WID conversions.

Full source/mapping/DataCompare definitions live in the file named by `computation` above. This contract is reused by every run of this dataflow; per-run outcomes are not persisted as bundle files (OKF §10.2 — a Receipt is a runtime artifact) and instead live in `Results/HHS_SIL_PurchaseRequisitionLinesFact_TestCase_run330094_report.json`, linked from the workflow concept file's "Test Cases & Dataflows" table.

`attester` runs `datacompare_verify.py <report.json>` against a run's saved report and exits 0 (PASS) or 1 (FAIL).
