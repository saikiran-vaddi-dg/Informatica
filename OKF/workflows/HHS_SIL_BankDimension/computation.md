---
type: Attested Computation
title: HHS_SIL_BankDimension_TestCase computation contract
description: Sanctioned DataCompare definition for verifying W_BANK_D against a recomputation from W_BANK_DS.
resource: "dataops://DevContainer/Dataflow/WorkingSession/HHS_SIL_BankDimension_TestCase"
tags: [BankDimension, SIL, computation]
status: draft
runtime: dataops-dataflow
parameters:
  - { name: engineName, type: string, required: true }
  - { name: folderName, type: string, required: true }
computation: /HRD/HHS_SIL_BankDimension_TestCase.json
executor:
  resource: "dataops://DevContainer/engine/168_AN?dataflow_guid=05d13c0e-dc13-40be-a00c-636bab22e4ca"
  receipt: [runId, status, differenceCount]
attester:
  resource: /references/attesters/datacompare_verify.py
generated: { by: "developer-agent/claude-sonnet-5", at: "2026-08-19T00:00:00+05:30" }
---

# Computation

DataCompare between:
- **JDBC 1 (actual)** — target read of `W_BANK_D`, filtered `WHERE CURRENT_FLG = 'Y' AND DELETE_FLG = 'N'`.
- **JDBC 2 (expected)** — recomputed `W_BANK_D` rows from `W_BANK_DS` via the seven `W_CODE_D` category lookups and the effective-dated `W_USER_D` audit-user resolution.

Full source/mapping/DataCompare definitions live in the file named by `computation` above. This contract is reused by every run of this dataflow; per-run outcomes are not persisted as bundle files (OKF §10.2 — a Receipt is a runtime artifact) and instead would live under `Results/`, linked from the workflow concept file's "Test Cases & Dataflows" table. No report was persisted for run 330093, so there is nothing under `Results/` for it yet — see the workflow concept file's Known Caveats.

`attester` runs `datacompare_verify.py <report.json>` against a run's saved report. No report was persisted for run 330093, so the attester has not yet been exercised against a real receipt for this contract.
