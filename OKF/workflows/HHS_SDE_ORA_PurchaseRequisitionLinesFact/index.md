# HHS_SDE_ORA_PurchaseRequisitionLinesFact

Single-mapping Oracle EBS Purchasing requisition-line extract load from `PO_REQUISITION_LINES_ALL` (joined with `PO_REQUISITION_HEADERS_ALL`, `PO_LINE_LOCATIONS_ALL`, `PO_LINES_ALL`, `PO_HEADERS_ALL`, `PO_RELEASES_ALL`) into staging table `W_PURCH_RQSTN_LINE_FS`, via the `mplt_BC_ORA_PurchaseRequisitionLinesFact`/`mplt_SA_ORA_PurchaseRequisitionLinesFact` mapplets.

- [Workflow logic (Description, Key Columns)](extraction.md)
- [Test cases, dataflows & caveats](hrd_mapping.md)
