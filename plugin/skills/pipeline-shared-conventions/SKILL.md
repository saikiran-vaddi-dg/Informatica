---
name: pipeline-shared-conventions
description: Full explanation behind two conventions shared across review-agent, developer-agent, orchestrator-agent, and process-workflows in this Informatica DataOps pipeline — why MCP tools don't propagate to Agent-tool subagents, and why only extraction.md (not index.md) carries OKF frontmatter. Each agent's own instructions already state the short actionable rule; invoke this skill only when you need the full "why" behind one of them, e.g. to explain a blocker to the user or to debug why a lookup unexpectedly failed.
---

# Pipeline shared conventions

## MCP tools don't propagate to Agent-tool subagents

Any agent invoked via the `Agent` tool (review-agent, developer-agent, or orchestrator-agent, whether spawned by `/process-workflows` or by another agent) runs in a subagent context where MCP server tools (`dataops_mcp_...`) are **never reachable**, even via `ToolSearch`, regardless of what's authenticated in the session that spawned it and regardless of what the subagent's own declared tool list says. This is a platform-level isolation, not something specific to one agent's configuration — no Agent-tool-spawned subagent gets MCP tools.

Consequences:
- **developer-agent never calls a `dataops_mcp` tool, period** — not metadata lookups, not `create_dataflow`/`run_dataflow`, not `get_data_flow_definition`, not `download_data_compare_report`. Whoever invokes developer-agent for a build/run step (the top-level session running `/process-workflows`, or a user's direct request) owns the *entire* build → run → poll → report → analyze-handoff sequence itself, since it's the only party with real platform access, and hands developer-agent the **finished outcome** in one consolidated prompt — dataflow/run id, per-component status and report data, the definition hash, and (for a Failed run) analysis-agent's classification. developer-agent's job is to record that outcome to `Results/`/`OKF/` and push, not to discover it.
- This also covers `analysis-agent`: developer-agent has no `Agent` tool at all, so it can never invoke analysis-agent itself. That handoff is the same caller's job, on a Failed run, *before* it calls developer-agent — not something to delegate down.
- Do not fall back to a tool-by-tool relay ("call X for me, here's the result, what's next?") as a workaround — every relay turn reloads developer-agent's full context for a decision it has no new information to make (it has no MCP tools to react differently with). If you don't yet have the full outcome to hand over, keep making the platform calls yourself until you do, then invoke developer-agent exactly once for the step.
- If a subagent needs `dataops_mcp` and wasn't given a finished outcome to record, the right move is to say so plainly and stop — not to guess at names, not to attempt the call anyway, and not to silently work around it by asking a peer subagent to try (that peer is equally isolated and will just fail the same way).
- The one case this doesn't apply: an agent invoked directly in the main session (not via `Agent`) does have normal MCP access, since it isn't a spawned subagent at all.

## OKF per-workflow frontmatter: only `extraction.md` carries `generated`

Per §8 of the OKF spec, only a bundle-root `index.md` may carry frontmatter. `OKF/workflows/<WorkflowName>/index.md` is a per-workflow file, not the bundle root (that's `OKF/index.md`), so it carries no frontmatter at all — just a short summary and links to `extraction.md` and `hrd_mapping.md`.

`extraction.md` is therefore the one file in that folder that owns the `generated: { by, at, commit }` block, where `commit` is `git rev-parse HEAD` at the time of writing. This is what makes it the staleness marker for the whole concept folder: compare `generated.at` (or resolve `generated.commit` for a diff-scoped review) against `git log -1 --format=%cI` on the workflow's own XML file to decide whether the folder's summary can be trusted as-is or needs a re-review.
