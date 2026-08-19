# Workflows

One folder per Informatica workflow that has generated content, grouped below by SDE/SIL. Each workflow folder holds up to three concept files plus its own `index.md` (pure navigation, no frontmatter):

* `extraction.md` — `type: Informatica Workflow`. Carries `type`, `description`, `resource` (the source XML), `tags`, `status`, and a `generated` provenance block, followed by `# Description`, `# Key Columns`, `# Known Caveats`, and `# Test Cases & Dataflows` sections. Check `generated.at` against the workflow XML's last commit time before trusting it — if the XML changed since, treat it as stale and regenerate rather than reading it as current.
* `hrd_mapping.md` — `type: XML-to-HRD Mapping`, present once a workflow's HRD test case is reviewed. A column-by-column table tracing each target column's derivation from the workflow's transformation logic (source ports, joins, dead ports, literals) to the HRD test case's expected-side query. Pilot pattern (started with `HHS_SDE_ORA_BankDimension`) — not yet generated for every workflow.
* `computation.md` — `type: Attested Computation`, present once a workflow has a built dataflow. The reusable contract: `runtime`, `computation` (its HRD test-case definition), `executor`, and `attester` (a deterministic script under `references/attesters/`). Created once and doesn't change per run.

A workflow not yet generated at all has no folder — read its XML under `/Workflows/` directly.

Per-run outcomes are **not** persisted as bundle files — OKF §10.2 defines a Receipt as a runtime artifact, not bundle content, so a run's evidence lives only in `Results/<DataflowName>_run<runId>_report.json`/`_analysis.html`, outside `OKF/`. Each workflow's `extraction.md` "Test Cases & Dataflows" table links straight to those files for the latest run, and root-cause detail for a failure is recorded in that file's own "Known Caveats" section. Per OKF §10.6, `verified` (does the definition still match policy) and attestation (did this run execute the sanctioned way) stay distinct: the contract's own `verified`/`attester` fields cover the former; the latter happens by running `attester.resource` against a run's report at consumption time, not by pre-recording a verdict in the bundle.

## SDE (Source Dependent Extract)

* [HHS_SDE_ORA_GTASActivityBalanceFact](HHS_SDE_ORA_GTASActivityBalanceFact/index.md) - has a generated test case, dataflow, and run (status: draft — see Known Caveats)
* HHS_SDE_ORA_ProgramActivity_Dimension - not yet generated, read `/Workflows/HHS_SDE_ORA_ProgramActivity_Dimension.XML` directly
* [HHS_SDE_ORA_BankDimension](HHS_SDE_ORA_BankDimension/index.md) - test case reviewed and confirmed; has an XML-to-HRD column mapping; dataflow not yet built (`dataops_mcp` unauthenticated)
* HHS_SDE_ORA_PurchaseRequisitionLinesFact - not yet generated, read `/Workflows/HHS_SDE_ORA_PurchaseRequisitionLinesFact.XML` directly

## SIL (Source Independent Load)

* [HHS_SIL_BankDimension](HHS_SIL_BankDimension/index.md) - has a generated test case, dataflow, and run (status: draft — Failed, see Known Caveats)
* HHS_SIL_GTASActivityBalanceFact - not yet generated, read `/Workflows/HHS_SIL_GTASActivityBalanceFact.XML` directly
* HHS_SIL_ProgramActivity_Dimension - not yet generated, read `/Workflows/HHS_SIL_ProgramActivity_Dimension.XML` directly
* [HHS_SIL_PurchaseRequisitionLinesFact](HHS_SIL_PurchaseRequisitionLinesFact/index.md) - has a generated test case, dataflow, and run (status: draft — Failed, see Known Caveats)
