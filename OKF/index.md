---
okf_version: "0.2"
---

# Informatica DataOps Knowledge Bundle

This bundle holds AI-consumable context for this project's Informatica workflows, so agents can work from a cheap summary instead of re-reading raw workflow XML on every pass.

* [workflows/](workflows/index.md) - one folder per Informatica workflow, grouped by SDE/SIL, holding up to three concept files (extraction, HRD mapping, computation contract) cross-linked to its test case(s) and dataflow(s)
* [log.md](log.md) - chronological history of what changed in this bundle and why

**Path convention**: this bundle lives inside a larger repository (per OKF §3), and its concept files link out to sibling directories that sit outside `OKF/` — `Workflows/` (source XML), `HRD/` (test case definitions), `Results/` (run reports). A bundle-relative path beginning with `/` normally resolves from this bundle's own root per OKF §6.2, but `/Workflows/...`, `/HRD/...`, and `/Results/...` references in this bundle are an intentional producer extension: they resolve from the repository root instead, since those directories are not children of `OKF/`. Paths beginning with `/references/` or `/workflows/` (lowercase) follow the standard bundle-root-relative rule.
