# AGENTS.md — Informatica Workflow Test & Validation Pipeline

This file is the harness-neutral source of truth for this pipeline. Any AI coding
agent working in this repository (Claude Code, GitHub Copilot, or any other
agent that reads `AGENTS.md`) should follow it, regardless of which tool is
driving.

## Folder layout

- `Workflows/` — Informatica PowerCenter workflow XML exports (source of truth for ETL logic).
- `HRD/` — Human Readable Definition test cases, one `<WorkflowName>_TestCase.json`
  per workflow (DataCompare-shaped dataflow definitions — schema below).
- `Results/` — dataflow run reports (`*_report.json`) and analysis writeups (`*_analysis.html`).
- `OKF/` — per-workflow context summaries: `OKF/index.md` (bundle root, the
  only place frontmatter belongs on an `index.md` per §8 of the OKF spec),
  `OKF/workflows/index.md` (category index, no frontmatter), and one folder
  per workflow, `OKF/workflows/<WorkflowName>/`, containing `index.md` (no
  frontmatter — just a short summary + links), `extraction.md` (the concept
  file: `generated: {by,at,commit}` frontmatter plus Description/Key Columns
  from reading the workflow logic), and `hrd_mapping.md` (Test Cases &
  Dataflows table + Known Caveats) — persisted notes so the full XML doesn't
  need re-reading every time a workflow is revisited.

## Tools this pipeline needs

- A DataOps MCP server (commonly named `dataops_mcp`) exposing `create_dataflow`,
  `run_dataflow`, `get_data_flow_run_status`, `download_data_compare_report`,
  `list_engines`, `list_folders`, `list_data_sources`, `update_data_flow`,
  `get_data_flow_definition`, etc. This is the **only** connection to the
  DataOps/Informatica platform — there is no direct Informatica connection
  anywhere in this pipeline; workflow logic comes only from the XML in
  `Workflows/`.
- `tools/compact_mapping.py <path-to-workflow.xml>` — a dependency-free Python 3
  script that compacts a workflow XML into a per-mapping JSON summary (typically
  95-99% smaller): topological flow, target-field lineage, resolved sources,
  a complexity tier, Mapping Variables (`$$` parameters), and any session-level
  per-partition SQL/filter overrides. Read the raw XML only for something this
  summary still leaves ambiguous.

## Pipeline phases (run per workflow file, one at a time — finish one before starting the next)

### Phase 1 — Review
Read the workflow XML (or its compacted summary / an existing, non-stale
`OKF/workflows/<Name>/extraction.md` — its `generated.at` frontmatter is the
staleness marker, per §8 of the OKF spec only a bundle-root `index.md` may
carry frontmatter, so the per-workflow `index.md` stays frontmatter-free)
and identify what needs testing: the
source query and any session-level overrides, every transformation branch
(CASE/IIF/lookup) that produces materially different output, and the target
table/load strategy.

Draft (or correct) the test case using the schema below. Self-review before
treating it as done: does every meaningful branch have a scenario, is the
"expected" side independently derived rather than a copy of "actual", are key
columns and thresholds grounded in the workflow's real logic. If existing
`HRD/` coverage is already correct, say so instead of redrafting.

### Phase 2 — Build & run
Write the reviewed test case to `HRD/<WorkflowName>_TestCase.json`. Build the
corresponding dataflow through the MCP platform tools, reusing the test case
JSON's sources/mappings — resolve engine/folder/data-source names against the
target container rather than assuming they transfer as-is.

Ask the operator (never guess) which container to build in, and whether the
dataflow should implement the ETL logic itself or validate/reconcile an
existing target. Pause only on genuine blockers: a name collision, an
unresolved parameter with no known value, or a missing prerequisite.

Once created: run it, poll to a terminal state, download the DataCompare
report to `Results/`, and write a charted HTML analysis to
`Results/<Name>_run<id>_analysis.html` using the fixed skeleton at
`templates/analysis_report_template.html` — fill in its `{{TOKEN}}`
placeholders rather than regenerating the CSS/page structure from scratch
each run.

### Phase 3 — Analyze & classify
Classify every failure as exactly one of:

- **Test case defect** — the HRD file itself is wrong; state exactly what
  field(s) to change.
- **Environment/data defect** — the test case and workflow logic are correct,
  but a dependency (reference data, unresolved parameter, stale source) is
  wrong.
- **Genuine workflow/ETL bug** — the underlying Informatica logic itself is
  wrong. Never paper over this by loosening the test case.

Present the classification and a recommended fix, and wait for explicit
operator confirmation before changing anything.

### Phase 4 — Apply & persist
Once confirmed: check for drift first — hash the live dataflow definition and
compare it to the `Fingerprint` recorded in
`OKF/workflows/<WorkflowName>/hrd_mapping.md` for that dataflow. If it
differs, stop and ask which side is correct before changing anything.

Apply only the confirmed classification's fix, re-run to confirm it actually
resolves the failure, and refresh the `Fingerprint`.

Update `OKF/workflows/<WorkflowName>/`: `extraction.md` (Description, Key
Columns, plus `generated: {by, at, commit}` frontmatter — the staleness
marker; `commit` is `git rev-parse HEAD` at the time of writing), `hrd_mapping.md`
(a Test Cases & Dataflows table — one row per test case/dataflow/run, with
`Fingerprint` — and Known Caveats), and `index.md` (no frontmatter — per §8 of
the OKF spec only a bundle-root `index.md` gets that exemption — just a short
summary and links to the other two files). Once a row reaches `Passed` with a
confirmed, non-drifted `Fingerprint`, mark it **Validated** in `hrd_mapping.md` — that dataflow
should be scheduled/run from the DataOps platform's own UI from then on, not
re-validated by an AI agent on every visit.

### Phase 5 — Push
Commit the specific `HRD/`, `Results/`, `OKF/` (and `Workflows/`, if it
changed) files this run touched, and push to the current branch's tracked
remote. Never force-push, rewrite history, or push to a different branch than
the one checked out. Stop and report if the push conflicts.

## DataCompare test case schema (`HRD/*.json`)

One dataflow definition per workflow:

- `sources[]` — two JDBC datasets: an **actual** dataset (the workflow's real
  logic/target) and an **expected** dataset (the same business rule,
  independently derived — never a copy of the actual query).
- `mappings[]` — one DataCompare component per scenario group, comparing the
  two sources column-by-column with explicit `uniqueKeyColumn`s and
  thresholds (default `"0"` / strict — any mismatch fails, unless a scenario
  explicitly documents why it tolerates drift).

For the full field reference and a worked example, see the
`test-case-generation` reference shipped with this pipeline's Claude Code
plugin (`plugin/skills/test-case-generation/SKILL.md`), or an existing file in
`HRD/` in this repo.

## Hard rules (apply regardless of which agent/tool is driving)

- Never guess container, scope, engine, or folder — ask the operator.
- Never apply a recommended fix without explicit operator confirmation.
- Never force-push, rewrite history, or push to a branch other than the one
  checked out.
- Never treat "expected" as a copy of "actual" in a test case — it must be
  independently derived, or the test proves nothing.
- Process one workflow file at a time, start to finish, before starting the
  next.
- Don't waste tokens: read each file once per task, fetch platform metadata
  (engines/folders/data sources) once per container and reuse it, never call
  the same tool with the same arguments twice expecting a different result,
  and use the fixed `templates/analysis_report_template.html` skeleton for
  every analysis report instead of regenerating its boilerplate.
