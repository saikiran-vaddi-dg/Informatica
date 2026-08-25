---
name: pipeline-shared-conventions
description: Full explanation behind two conventions shared across review-agent, developer-agent, orchestrator-agent, and process-workflows in this Informatica DataOps pipeline — why MCP tools don't propagate to Agent-tool subagents, and why only extraction.md (not index.md) carries OKF frontmatter. Each agent's own instructions already state the short actionable rule; invoke this skill only when you need the full "why" behind one of them, e.g. to explain a blocker to the user or to debug why a lookup unexpectedly failed.
---

# Pipeline shared conventions

## MCP tools don't propagate to Agent-tool subagents

Any agent invoked via the `Agent` tool (review-agent, developer-agent, or orchestrator-agent, whether spawned by `/process-workflows` or by another agent) runs in a subagent context where MCP server tools (`dataops_mcp_...`) are **never reachable**, even via `ToolSearch`, regardless of what's authenticated in the session that spawned it and regardless of what the subagent's own declared tool list says. This is a platform-level isolation, not something specific to one agent's configuration — no Agent-tool-spawned subagent gets MCP tools.

Consequences:
- Whoever spawns developer-agent for a build/run step must resolve platform metadata (`list_engines`/`list_folders`/`list_data_sources`, container-specific values) in their own session first, and pass the resolved values concretely in developer-agent's prompt. developer-agent uses those values as-is; it does not attempt its own platform lookups.
- If a subagent needs `dataops_mcp` and wasn't given resolved values, the right move is to say so plainly and stop — not to guess at names, not to retry the lookup expecting a different result, and not to silently work around it by asking a peer subagent to try (that peer is equally isolated and will just fail the same way).
- The one case this doesn't apply: an agent invoked directly in the main session (not via `Agent`) does have normal MCP access, since it isn't a spawned subagent at all.

## OKF per-workflow frontmatter: only `extraction.md` carries `generated`

Per §8 of the OKF spec, only a bundle-root `index.md` may carry frontmatter. `OKF/workflows/<WorkflowName>/index.md` is a per-workflow file, not the bundle root (that's `OKF/index.md`), so it carries no frontmatter at all — just a short summary and links to `extraction.md` and `hrd_mapping.md`.

`extraction.md` is therefore the one file in that folder that owns the `generated: { by, at, commit }` block, where `commit` is `git rev-parse HEAD` at the time of writing. This is what makes it the staleness marker for the whole concept folder: compare `generated.at` (or resolve `generated.commit` for a diff-scoped review) against `git log -1 --format=%cI` on the workflow's own XML file to decide whether the folder's summary can be trusted as-is or needs a re-review.
