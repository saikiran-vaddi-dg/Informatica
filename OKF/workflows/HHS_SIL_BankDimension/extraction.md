---
generated:
  by: developer-agent
  at: "2026-08-25T19:19:22+05:30"
  commit: 31c7269
---

# HHS_SIL_BankDimension — Extraction

## Description

SIL mapping that loads the `W_BANK_D` dimension from staging table
`W_BANK_DS`. Each staging row is self-looked-up against `W_BANK_D` (via
`Lkp_W_BANK_D`, keyed on `DATASOURCE_NUM_ID`/`INTEGRATION_ID`/
`SRC_EFF_FROM_DT`) to classify it as insert/update/reject/soft-delete;
no-op rows are filtered out. ~49 descriptive attribute columns pass through
unchanged via mapplet `mplt_SIL_BankDimension`. `DELETE_FLG` is computed
from the row classification, and `BANK_KEY_CODE` is resolved via a
master-code lookup fallback (`mplt_SIL_BankDimension_CodeLookup` →
`LKP_BANK_CODE`).

## Key Columns

- **Unique/natural key**: composite `DATASOURCE_NUM_ID` + `INTEGRATION_ID`
  + `SRC_EFF_FROM_DT`, used both as the self-lookup key against `W_BANK_D`
  and as the test-case comparison key.
- **Straight passthrough (49 columns)**: descriptive attributes carried
  unchanged from `W_BANK_DS` to `W_BANK_D` through
  `mplt_SIL_BankDimension` — covered by this workflow's test case. See
  `HRD/HHS_SIL_BankDimension_TestCase.json` for the full column list.
- **Row-classification/action-derived (excluded from this test case)**:
  `DELETE_FLG` (derived from insert/update/reject/soft-delete
  classification via `Lkp_W_BANK_D`).
- **Lookup-derived (excluded from this test case, tool gap)**:
  `BANK_KEY_CODE` — resolved via `mplt_SIL_BankDimension_CodeLookup`'s
  internal lookup(s) feeding `LKP_BANK_CODE`. `compact_mapping.py`'s
  `transformation_logic` output does not surface this mapplet's internal
  lookup logic (a tool gap, not a workflow ambiguity) — cannot be
  validated end-to-end until fixed.
- **SCD2/audit/surrogate (excluded from this test case, tool gap for the
  SCD2 portion)**: `ROW_WID`, `EFFECTIVE_FROM_DT`, `EFFECTIVE_TO_DT`,
  `CURRENT_FLG`, `ETL_PROC_WID`, `CREATED_BY_WID`, `CHANGED_BY_WID`,
  `W_INSERT_DT`, `W_UPDATE_DT`. The SCD2 date/flag derivation lives in
  `Exp_Scd2_Dates`, which has **no `transformation_logic` entry at all**
  in `compact_mapping.py`'s output for this workflow (a tool gap) — these
  columns cannot be validated end-to-end until fixed.
- **Known tool gaps (compact_mapping.py)**: (1) internal lookup(s) inside
  `mplt_SIL_BankDimension_CodeLookup` feeding `LKP_BANK_CODE` are not
  surfaced in `transformation_logic`; (2) `Exp_Scd2_Dates` has no
  `transformation_logic` entry at all. Both flagged by review-agent; do
  not attempt to work around either via raw-XML fallback — fix the
  compaction tool instead.
