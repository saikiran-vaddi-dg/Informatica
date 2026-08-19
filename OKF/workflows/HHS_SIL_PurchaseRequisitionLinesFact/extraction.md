---
type: Informatica Workflow
title: HHS_SIL_PurchaseRequisitionLinesFact
description: Builds W_PURCH_RQSTN_LINE_F from W_PURCH_RQSTN_LINE_FS via SCD2 effective-dated joins across roughly fourteen dimension aliases.
resource: /Workflows/HHS_SIL_PurchaseRequisitionLinesFact.XML
tags: [PurchaseRequisitionLinesFact, SIL, Oracle]
status: draft
generated: { by: "developer-agent/claude-sonnet-5", at: "2026-08-19T13:48:57+05:30", commit: "5588d347452d72377df7bc83d96c59aeea6beb03" }
---

# Description

Builds `W_PURCH_RQSTN_LINE_F` from the `W_PURCH_RQSTN_LINE_FS` staging table. Every `*_WID` column is resolved via an SCD2 effective-dated `LEFT JOIN` against its dimension (`W_EMPLOYEE_D` for `REQUESTOR_WID`, `W_PARTY_ORG_D` for `SUPPLIER_WID`, `W_PRODUCT_D`/`W_INVENTORY_PRODUCT_D`/`W_SUPPLIER_PRODUCT_D`, `W_BUSN_LOCATION_D` three times aliased for plant/receipt/storage location, `W_INT_ORG_D` three times aliased for inventory org/requisition org/operating unit, `W_STATUS_D`/`W_XACT_TYPE_D` (undated) for approval/cycle/fulfillment status and transaction types, `W_SUPPLIER_ACCOUNT_D`, `W_USER_D` twice for created/changed-by), each falling back to `0` via `NVL(...,0)` when unmatched. Date columns (`SUBMITTED_ON_DT`, `APPROVED_ON_DT`, etc.) are converted to `YYYYMMDD`/`HH24MISS` integer WIDs via `TO_CHAR`. `UOM_CODE` resolves through `W_CODE_D` (`CATEGORY = 'UOM'`) with a `'<Source Code Not Supplied>'` fallback.

# Key Columns

- **Unique key**: `INTEGRATION_ID`, `DATASOURCE_NUM_ID`
- **Derived / lookup-dependent (SCD2 effective-dated)**: `REQUESTOR_WID`, `SUPPLIER_WID`, `PRODUCT_WID`, `INVENTORY_PROD_WID`, `SUPPLIER_PROD_WID`, `PLANT_LOC_WID`, `INVENTORY_ORG_WID`, `RCPT_LOC_WID`, `STORAGE_LOC_WID`, `RQSTN_ORG_WID`, `OPERATING_UNIT_ORG_WID`, `SUPPLIER_ACCOUNT_WID`, `CREATED_BY_WID`, `CHANGED_BY_WID`
- **Derived / lookup-dependent (undated)**: `APPROVAL_STATUS_WID`, `CYCLE_STATUS_WID`, `XACT_TYPE_WID`, `LINE_TYPE_WID`, `FULFILLMENT_STATUS_WID`, `PO_CREATION_METHOD_WID`, `UOM_CODE`
- **Date-to-WID conversions**: `SUBMITTED_ON_DT_WID`/`_TM_WID`, `RESUBMITTED_ON_DT_WID`/`_TM_WID`, `APPROVED_ON_DT_WID`/`_TM_WID`, `ORDERED_ON_DT_WID`, `RECEIVED_ON_DT_WID`, `NEEDED_BY_DT_WID`/`_TM_WID`, `DUE_ON_DT_WID`, `CREATED_ON_TM_WID`, `PO_SUBMIT_ON_DT_WID`/`_TM_WID`, `PO_APPROVED_ON_DT_WID`/`_TM_WID`

# Known Caveats

- Run 330094 failed with `Difference : 10 (A:100%, B:100%)` — all keys matched but nearly every `*_WID`/date-WID column mismatched. Two distinct root causes, both environment/data defects (see linked report for full detail):
  1. Every SCD2 dimension table referenced here has `EFFECTIVE_FROM_DT == EFFECTIVE_TO_DT`, making the standard `date >= EFFECTIVE_FROM_DT AND date < EFFECTIVE_TO_DT` join always empty — every effective-dated lookup falls back to `NVL(...,0)`. Partial fix (`EFFECTIVE_TO_DT = DATE '9999-12-31'`) provided in `fix_remaining_blockers.sql` for `W_EMPLOYEE_D`, `W_PARTY_ORG_D`, `W_PRODUCT_D`, `W_INVENTORY_PRODUCT_D`, `W_SUPPLIER_PRODUCT_D`, `W_BUSN_LOCATION_D`, `W_INT_ORG_D`, `W_SUPPLIER_ACCOUNT_D`, `W_USER_D`.
  2. The target `W_PURCH_RQSTN_LINE_F`'s own stub data holds generic sequential placeholders (`1, 2, 3...10`) in every `*_WID`/`*_DT_WID` column rather than values consistent with the actual join/date-conversion logic — this is **not** addressed by the `EFFECTIVE_TO_DT` fix above and needs the target table's stub data regenerated to match real computed values before this test case can pass.
- `engineName` (`168_AN`) and `folderName` (`Dataflow/WorkingSession`) are confirmed valid against DevContainer (containerId `518`) as of the 2026-08-19 folder move.

# Test Cases & Dataflows

| Test Case | Computation Contract | Dataflow | Environment | Latest Run | Status | Fingerprint |
|---|---|---|---|---|---|---|
| [HHS_SIL_PurchaseRequisitionLinesFact_TestCase](/HRD/HHS_SIL_PurchaseRequisitionLinesFact_TestCase.json) | [computation](computation.md) | HHS_SIL_PurchaseRequisitionLinesFact_TestCase (DevContainer, folder `Dataflow/WorkingSession`, engine `168_AN`, guid `c9b52ed8-2ca6-4d88-ae88-823003f6564a`) | DevContainer | run 330094 (2026-08-19) — [report](/Results/HHS_SIL_PurchaseRequisitionLinesFact_TestCase_run330094_report.json) | Failed | not computed (fix not yet applied; hash on next confirmed re-run) |
