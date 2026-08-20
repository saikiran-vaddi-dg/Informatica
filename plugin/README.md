# coding-agent

A Claude Code plugin that reviews Informatica workflows, generates/maintains DataCompare-shaped test cases, builds and runs the corresponding DataOps dataflow, and analyzes results — end to end, with a confirm-before-fix gate.

## Works beyond Claude Code

The pipeline logic itself (review → draft/fix test case → build & run dataflow → analyze/classify → confirm → push) isn't Claude-specific — only the packaging (subagents, a Skill, a slash command) is. Rather than hand-building a separate adapter per tool, this plugin relies on **`AGENTS.md`** — the cross-tool standard for repo-level agent instructions, now read natively by GitHub Copilot, Cursor, OpenAI Codex, Gemini CLI, Aider, Windsurf, Zed, Devin, and 20+ other agents (Claude Code reads it too, alongside its native `CLAUDE.md`).

The first time `/process-workflows` or `developer-agent` runs in a target repo, it installs (additively, never overwriting an existing file):

| File (in the target repo) | Purpose |
|---|---|
| `AGENTS.md` | Canonical, harness-neutral description of the pipeline (folder layout, phases, test case schema, hard rules) — the single file any compliant agent needs to pick up the whole process. |
| `.vscode/mcp.json` | The one thing that genuinely isn't standardized yet: MCP server configuration. Claude Code uses this plugin's own `.mcp.json`; VS Code-based agents (Copilot, others) read `.vscode/mcp.json`'s `servers` key instead. Same placeholder URL, edit before use. |

Source templates live in this plugin's `templates/` directory. Claude Code users keep the existing subagent/skill/slash-command experience unchanged; any other `AGENTS.md`-compliant agent gets the same process directly from that one file. **Caveat**: a single-agent harness running off `AGENTS.md` alone executes all phases in one continuous context rather than Claude Code's isolated per-subagent scoping — `AGENTS.md` is written to be self-contained per phase to compensate, but expect less strict separation between review/build/analyze than Claude Code's dedicated subagents give you. This hasn't yet been verified against a live Copilot (or other) run — only built to its documented conventions.

## What's included

- **Agents**: `review-agent` (drafts/corrects test coverage), `developer-agent` (builds/runs/fixes/pushes), `analysis-agent` (classifies failures, recommends fixes, writes a charted HTML report), `orchestrator-agent` (single entry point that routes an ad-hoc request to whichever of the above applies — see its "Known limitation" section: MCP tools don't propagate to Agent-tool subagents, so build/run/apply-fix steps requiring `dataops_mcp` must still be run at the top level or via `/process-workflows`, not through this agent).
- **Command**: `/process-workflows` — pulls the latest changes on the current branch, then runs the full pipeline for every file in `Workflows/`, one file at a time.
- **Skill**: `test-case-generation` — the canonical schema/worked-example for the DataCompare test case JSON format.
- **Tool**: `tools/compact_mapping.py` — the first-pass read for any workflow: a deterministic Stage1+Stage2 compaction pipeline (vendored from this repo's `etl_mapping_compaction_api/`) that turns a PowerCenter export into a per-mapping JSON summary — topological flow, target-field lineage traced to its real transformation rule, resolved sources (including ones that only exist inside a referenced mapplet), shared-mapplet dedup, and a rule-based complexity tier + recommended review effort. Typically 95-99% smaller than the raw XML. Persists each summary right next to its source file — `Workflows/<WorkflowName>.summary.json` (or `<WorkflowName>.<MappingName>.summary.json` when a file has more than one mapping) — so it's committed to git alongside the XML and any clone/teammate gets it without reprocessing; a re-run skips reprocessing once that summary's own recorded hash matches the file's current hash. Only the mapplet dedup cache and a raw-XML archive (machine-local, regenerable, gitignored) live under the target project's own `.cache/`. It doesn't parse Mapping Variables or session-level per-partition SQL overrides — read the raw workflow XML directly for those, or for anything else it doesn't capture.
- **Templates**: `templates/` — the harness-neutral `AGENTS.md` and `vscode-mcp.json`, installed into the target repo the first time the pipeline runs there (see "Works beyond Claude Code" above).

## Prerequisites (per developer/machine)

1. **Python 3** on PATH, to run `tools/compact_mapping.py` (standard library only — no extra packages needed).
2. **Project folder layout.** The target repo must have (or will have created for it) these top-level folders:
   - `Workflows/` — Informatica workflow XML exports
   - `HRD/` — Human Readable Definition test cases (`<WorkflowName>_TestCase.json`)
   - `Results/` — dataflow run reports + analysis HTML
   - `OKF/` — per-workflow context summaries (`OKF/index.md` bundle root, `OKF/workflows/index.md` category index, and `OKF/workflows/<WorkflowName>/{index.md,extraction.md,hrd_mapping.md}` per workflow)
3. **`dataops_mcp` MCP server.** A `.mcp.json` is bundled with this plugin pointing at placeholder values — edit both before use:
   ```json
   { "mcpServers": { "dataops_mcp": { "type": "http", "url": "https://<your-dataops-instance>/mcp", "oauth": { "clientId": "<your-oauth-client-id>" } } } }
   ```
   Credentials are never bundled — after pointing it at your instance, authenticate via `/mcp` (interactive OAuth) before running `/process-workflows` or invoking `developer-agent`.
   Running under GitHub Copilot in VS Code instead? Point `.vscode/mcp.json` (installed into the target repo per "Works beyond Claude Code" above) at the same instance, or configure the server directly under the target repo's Settings → Copilot → MCP servers if using Copilot's cloud coding agent.
4. **Git branch/remote.** The pipeline always operates on whatever branch is currently checked out and its tracked remote — it never assumes a specific branch or remote name. Just check out the branch you want it to pull/push against before running it.

## Install

`.claude-plugin/` lives inside this `plugin/` folder, not at the repo root — this repo also doubles as a live Informatica project (`Workflows/`, `HRD/`, `Results/`, `OKF/` at the repo root) used to develop and dogfood the plugin. Point `/plugin marketplace add` at the `plugin/` folder itself, not the repo root:

```
/plugin marketplace add <path-or-git-url>/plugin
/plugin install coding-agent
```

The folder is fully self-contained (no reference anywhere under `plugin/` to anything outside it), so it can also be copied or published as its own standalone repository if a host doesn't support pointing at a subdirectory — in that case `plugin/` becomes the new repo root and the command above drops the `/plugin` suffix.
