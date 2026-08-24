---
generated:
  by: developer-agent
  at: "2026-08-20T11:27:41+05:30"
  commit: 3d75b1ec2bce1ee5922a1657fd7f2f114716032f
---

# HHS_SDE_ORA_PurchaseRequisitionLinesFact — Workflow Logic

## Description

Single-mapping workflow `HHS_SDE_ORA_PurchaseRequisitionLinesFact`: extracts the purchase requisition lines information from Oracle EBS Purchasing source tables (`PO_REQUISITION_LINES_ALL` joined to `PO_REQUISITION_HEADERS_ALL`, `PO_LINE_LOCATIONS_ALL`, `PO_LINES_ALL`, `PO_HEADERS_ALL`, `PO_RELEASES_ALL`, plus `PO_DOC_STYLE_HEADERS`) into staging table `W_PURCH_RQSTN_LINE_FS`. The mapping-level flow is: `mplt_BC_ORA_PurchaseRequisitionLinesFact` (business-component extraction/joins, incl. `SQ_BCI_PURCH_RQLNS` source qualifier and its own `INTEGRATION_ID`/`DATASOURCE_NUM_ID` output ports) -> `Exp_W_PURCH_RQSTN_LINE_FS_Integration_Id` / `X_CUSTOM` expressions -> `mplt_SA_ORA_PurchaseRequisitionLinesFact` (source-adapter derivations) -> `MPLT_CURCY_CONVERSION_RATES_All` -> `LOC_TO_DOC` expression -> target `W_PURCH_RQSTN_LINE_FS`. Modified by Sridevi on 5/5/15 for release 4.0; can be run on an incremental basis via mapping variables `$$LAST_EXTRACT_DATE`/`$$INITIAL_EXTRACT_DATE`.

Of the target's key computed columns (validated in the accompanying test case, see [hrd_mapping.md](hrd_mapping.md)):

- `INTEGRATION_ID` = `TO_CHAR(REQUISITION_LINE_ID)` (`mplt_BC_ORA_PurchaseRequisitionLinesFact.SQ_BCI_PURCH_RQLNS` output expression, confirmed non-empty unlike GTAS's analogous port).
- `DATASOURCE_NUM_ID` = mapping variable `$$DATASOURCE_NUM_ID` (unresolved runtime parameter, same pattern as GTAS).
- `LINE_AMT` / `CANCELLED_LINE_AMT` = `MATCHING_BASIS`-branched: when `MATCHING_BASIS = 'AMOUNT'`, `LINE_AMT` is the requisition line's `AMOUNT` directly and `CANCELLED_LINE_AMT` is `NULL`; otherwise both are computed as `NVL(CURRENCY_UNIT_PRICE, UNIT_PRICE) * QUANTITY` (resp. `* QUANTITY_CANCELLED`).
- `PO_APPROVED_ON_DT` = `PO_LINE_LOCATIONS_ALL.APPROVED_DATE` only when `APPROVED_FLAG = 'Y'`, else `NULL`.
- `PO_SUBMIT_ON_DT` / `PO_CREATION_METHOD_ID` / `PO_REVISIONS` = branched on whether the line location has a `PO_RELEASE_ID`: if `NULL`, sourced from `PO_HEADERS_ALL` (`SUBMIT_DATE`/`DOCUMENT_CREATION_METHOD`/`REVISION_NUM`); if present, sourced from the corresponding `PO_RELEASES_ALL` columns instead.
- `STD_COST_AMT`/`UNIT_STD_COST` (currency-converted standard cost via `MPLT_CURCY_CONVERSION_RATES_All` + `LOC_TO_DOC` + a standard-cost lookup against `W_STANDARD_COST_G`) — not yet traced/tested this session, see Known Caveats.

## Key Columns

- **Declared target `PRIMARY KEY`**: `DATASOURCE_NUM_ID`, `INTEGRATION_ID`, `X_CUSTOM` (all three declared `KEYTYPE="PRIMARY KEY"` in the XML's `TARGETFIELD` list). Of these, only `INTEGRATION_ID` (`TO_CHAR(REQUISITION_LINE_ID)`) actually varies per row within a run; `DATASOURCE_NUM_ID` is a static mapping-parameter value and `X_CUSTOM` is hardcoded `'0'`.
- **Derived / branch-dependent**: `LINE_AMT`, `CANCELLED_LINE_AMT`, `CANCELLED_LINE_QTY` (via `MATCHING_BASIS`); `PO_APPROVED_ON_DT` (via `PLL.APPROVED_FLAG`); `PO_SUBMIT_ON_DT`, `PO_CREATION_METHOD_ID`, `PO_REVISIONS` (via `PLL.PO_RELEASE_ID IS NULL`, header-vs-release source).
- **Parameterized (mapping variables, unresolved at design time)**: `DATASOURCE_NUM_ID` (`$$DATASOURCE_NUM_ID`), source qualifier incremental filter (`$$LAST_EXTRACT_DATE`, `$$INITIAL_EXTRACT_DATE`).
- **Not yet traced (follow-up)**: `STD_COST_AMT`/`UNIT_STD_COST` currency-converted standard cost chain — see [hrd_mapping.md](hrd_mapping.md#known-caveats).
