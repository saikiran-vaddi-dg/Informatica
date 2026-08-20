---
description: Pull the latest changes on the current branch, then for every file in Workflows/ (or just one file, if given a name as an argument) run review-agent (review workflow, draft a test case, review the draft), developer-agent (create the reviewed test case), then developer-agent again to build the corresponding DataOps dataflow, run it, and save/analyze the results.
argument-hint: "[WorkflowName]"
---

Do the following, in order:

## 1. Sync from git

Run `git pull` in this project's working copy (fast-forwards the current branch from its tracked remote — never assume a specific branch/remote name). If there are local uncommitted changes that would block the pull, stop and tell the user — do not stash or discard anything automatically.

After a successful pull, ensure the required folder layout exists — create whichever of these are missing (a fresh clone won't have them yet): `Workflows/`, `HRD/`, `Results/`, `OKF/workflows/`. If `OKF/index.md` doesn't exist yet, create it as the bundle-root index (`okf_version: "0.2"` frontmatter, a short description, and a link to `workflows/index.md`); if `OKF/workflows/index.md` doesn't exist yet, create it too (`okf_version: "0.2"` frontmatter and a bare `# Workflows` heading) so developer-agent has somewhere to append per-workflow entries later. This is additive only (never deletes or overwrites existing files) so it needs no confirmation.

Also ensure the harness-neutral pipeline file exists in the target repo, so this pipeline is usable from any AI coding agent that reads the `AGENTS.md` convention (Copilot, Cursor, Codex, and 20+ others — not just Claude Code) — copy it from this plugin's `templates/` directory only if the destination doesn't already exist (never overwrite a file the user may have customized):
- `templates/AGENTS.md` → `AGENTS.md` (repo root) — the canonical, harness-neutral process description. No per-tool wrapper files needed: `AGENTS.md` is read natively by the major coding agents.
- `templates/vscode-mcp.json` → `.vscode/mcp.json`, only if missing — MCP server configuration is the one piece that genuinely isn't standardized across tools yet (Claude Code uses this plugin's own `.mcp.json`; VS Code-based agents read `.vscode/mcp.json`'s `servers` key instead). Placeholder URL; the user still edits it before use.

## 2. Enumerate workflow files

If `$ARGUMENTS` is non-empty, treat it as a workflow name (with or without the `.XML` extension) and scope to just that single file in `Workflows/` — verify it actually exists there (Glob) before proceeding, and stop with an error if it doesn't. Otherwise, list every file currently in `Workflows/` (e.g. via Glob `Workflows/**/*`) — this is the authoritative list to iterate over, don't assume file names from memory.

## 3. Per-file pipeline

For each file found in step 2, run this pipeline for that single file:

0. **Skip check.** Before invoking any agent, check `OKF/workflows/<WorkflowName>/` for this file:
   - Does `extraction.md` exist, and is its `generated.at` frontmatter *not* stale (not older than `git log -1 --format=%cI` on the workflow XML)?
   - Does `hrd_mapping.md`'s Test Cases & Dataflows table have a row for this workflow with Status = `Passed`?
   - Does that row's `Fingerprint` still match the live dataflow (same drift check developer-agent uses in its "Apply confirmed fixes" step — call `get_data_flow_definition` and hash it)?

   If all three hold, this file is already fully processed and unchanged — skip straight to reporting it as "already up to date" in step 4's summary, and move to the next file. Only proceed to steps 1-4 below if any of these don't hold (missing/stale OKF entry, no Passed run yet, or drift detected) — new files, previously Failed/Pending files, and drifted files always get reprocessed.
1. Invoke the `review-agent` subagent (via the Agent tool), scoped explicitly to that one workflow file. Point it at the file and let it follow its own documented process (`plugin/agents/review-agent.md`) rather than restating the steps yourself — in particular, don't tell it to "read the XML" directly; its own Pass 1 already decides between the `compact_mapping.py` preprocessing summary and a raw read (or a diff-scoped review off an existing OKF concept file), and paraphrasing the task can override that and force an unnecessary full raw read. It reviews the workflow's actual logic, drafts a test case (scenarios/inputs/expected results), reviews its own draft for completeness against the workflow, and reports the reviewed draft — or, if a correct test case already exists for that workflow, reports that explicitly instead.
2. If review-agent produced a reviewed draft (new or corrected), invoke the `developer-agent` subagent with that draft to create/fix the file in `HRD/`.
3. If review-agent reported existing coverage as already correct, skip step 2 for that file and treat its existing test case as the input to step 4.
4. Invoke `developer-agent` again to build the corresponding dataflow on the DataOps platform from that test case. It will ask you which container/project and what the dataflow should actually do (implement the ETL vs. validate/reconcile) — answer per-file, since this command does not default those. Per its own instructions, developer-agent then also runs the dataflow, downloads the DataCompare report, saves the report plus an analysis writeup to `Results/` automatically, and commits + pushes the `HRD/` and `Results/` files to the current branch's tracked remote — it does not stop after creation. It only pauses again if it hits a genuine blocker (name collision, unresolved parameter, missing prerequisite, or a push conflict).

Process files strictly one at a time, in sync — finish the full pipeline (review → test case → dataflow → run → save → analyze → push) for one file before starting the next. Do not fan out multiple files' Agent tool calls in the same message. This keeps step 4's per-file questions and any blocker pauses attributable to a single file at a time instead of interleaving across files.

## 4. Next steps

Once all files have gone through the pipeline (or been skipped): report a per-file summary — for skipped files, just "already up to date (Passed, no drift) — validated, run via DataGaps native UI going forward"; for processed files, workflow → test case created/fixed/already-covered → dataflow created/run/report saved/pushed, with container/id, run outcome, commit hash, and Results/ file paths (include developer-agent's validated/native-UI note for any file that reached Passed with no drift).
