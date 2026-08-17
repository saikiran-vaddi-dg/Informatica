---
okf_version: "0.2"
---

# Workflows

Each entry is a concept file summarizing an Informatica workflow: what it does, its key columns, and every test case/dataflow/run built for it (see [Test Cases & Dataflows](workflows/HHS_SDE_ORA_GTASActivityBalanceFact.md) for the table shape). Check the concept file's `generated.at` against the workflow XML's last commit time before trusting it — if the XML changed since, treat the concept file as stale and regenerate it rather than reading it as current.

## SDE (Source Dependent Extract)

- [HHS_SDE_ORA_GTASActivityBalanceFact](workflows/HHS_SDE_ORA_GTASActivityBalanceFact.md) — has a generated test case, dataflow, and run
- HHS_SDE_ORA_ProgramActivity_Dimension — *not yet generated, read `/Workflows/HHS_SDE_ORA_ProgramActivity_Dimension.XML` directly*
- HHS_SDE_ORA_BankDimension — *not yet generated, read `/Workflows/HHS_SDE_ORA_BankDimension.XML` directly*
- HHS_SDE_ORA_PurchaseRequisitionLinesFact — *not yet generated, read `/Workflows/HHS_SDE_ORA_PurchaseRequisitionLinesFact.XML` directly*

## SIL (Source Independent Load)

- HHS_SIL_BankDimension — *not yet generated, read `/Workflows/HHS_SIL_BankDimension.XML` directly*
- HHS_SIL_GTASActivityBalanceFact — *not yet generated, read `/Workflows/HHS_SIL_GTASActivityBalanceFact.XML` directly*
- HHS_SIL_ProgramActivity_Dimension — *not yet generated, read `/Workflows/HHS_SIL_ProgramActivity_Dimension.XML` directly*
- HHS_SIL_PurchaseRequisitionLinesFact — *not yet generated, read `/Workflows/HHS_SIL_PurchaseRequisitionLinesFact.XML` directly*
