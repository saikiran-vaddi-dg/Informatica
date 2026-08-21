---
name: dataflow-environment-config
description: Defines where dataflow build defaults (container, engine, folder, purpose) and $$ parameter/mapping-variable resolution rules live for this project — a user-editable dataops.config.yaml instead of hardcoded agent instructions. Use whenever developer-agent needs to know which container/engine/folder to build a dataflow in, what the dataflow should do, or how to resolve a $$ mapping variable's value, before asking the user.
metadata:
  author: Datagaps
  version: 1.0.0
  category: configuration
  tags: [dataflow, container, engine, configuration, parameters]
---

# Dataflow Environment Config

## Why this exists

Which DataOps container/engine/folder a new dataflow gets built in, and how a workflow's `$$` mapping variables should resolve, are project- and environment-specific facts — they change per deployment, not per workflow. Baking them into `developer-agent.md`'s prose would mean editing shared plugin instructions every time a team's environment changes, and would force the agent to ask the same question on every single run. This skill instead points at one user-editable data file, `dataops.config.yaml`, that lives in the target repo (alongside `AGENTS.md`, `HRD/`, `OKF/`) — not inside the plugin — so any user of this pipeline can set their own defaults without touching agent instructions at all.

## The config file

`dataops.config.yaml` at the repo root. If it doesn't exist yet, create it with empty defaults (below) rather than failing — an empty/missing file just means "nothing configured yet, ask the user."

```yaml
version: 1

dataflow:
  container: ""        # DataOps container/project new dataflows get created in
  engine: ""
  folder: "Dataflow"
  # What a newly built dataflow should do:
  #   validation    - a DataCompare-style actual-vs-expected reconciliation check (default)
  #   implement_etl - actually implement the workflow's ETL logic itself
  purpose: validation

# How to resolve a $$ mapping variable / session parameter when the workflow
# itself doesn't supply a usable value:
#   prompt  - always ask the user
#   default - use the variable's own DEFAULTVALUE from the workflow XML, if present (default if unset)
parameter_defaults:
  resolution: default
  overrides: {}
    # $$DATA_ACT_REPORTING_PERIOD: "202401"
  # What to do if resolution above still finds nothing (no override, no
  # workflow DEFAULTVALUE either):
  #   prompt       - ask the user
  #   leave_blank  - use an empty value and flag it in the test case's
  #                  _notes for review, rather than blocking on a question (default if unset)
  on_unresolved: leave_blank

# Per-workflow overrides, keyed by workflow file stem (without .XML), for
# cases where one workflow needs a different container/engine/folder/purpose
# than the project default above.
workflow_overrides: {}
  # HHS_SIL_ProgramActivity_Dimension:
  #   container: "some-other-container"
```

## Resolution order

For **container / engine / folder / purpose**, when building or updating a dataflow for `<WorkflowName>`:
1. `workflow_overrides.<WorkflowName>.<field>`, if set.
2. `dataflow.<field>` (the project default), if set (non-empty string).
3. Otherwise: ask the user. This only happens for a field neither level configured — with `container`/`engine`/`folder`/`purpose` all set at the project-default level, this project's pipeline should never actually reach this step.

For a **`$$` mapping variable or session parameter** with no usable value from the workflow itself:
1. `parameter_defaults.overrides.<$$VarName>`, if present — use it directly, no prompt.
2. If `parameter_defaults.resolution: default` — use the variable's own `DEFAULTVALUE` from the workflow XML (visible in the compact summary's `mapping_variables`), if it has one.
3. If still unresolved: follow `parameter_defaults.on_unresolved` — `leave_blank` uses an empty value and records it in the test case's `_notes` for the user to review later, without blocking on a question; `prompt` asks the user instead.

## Closing the loop: persist new answers

Whenever step 3 above (container/engine/folder/purpose) actually required asking the user because neither config level had a value, offer to write the answer back into `dataops.config.yaml` before moving on — as a `workflow_overrides.<WorkflowName>` entry if the user said it's specific to this workflow, or into the top-level `dataflow` section if they said it's a project-wide default. Ask which scope they mean rather than guessing. This is what makes the config actually save future runs from re-asking — a skill that only reads and never writes back would just move the same repeated question one file over.

Never overwrite an existing non-empty value in this file without the user's confirmation — treat it the same as any other project file the user may have hand-edited.

## When invoked from developer-agent

developer-agent's dataflow build step should read `dataops.config.yaml` (creating it with empty defaults if missing) before asking the container/engine/folder/purpose question, and again before resolving any `$$` parameter it can't derive from the workflow itself. With this project's current config (container/engine/folder/purpose all set, `on_unresolved: leave_blank`), this pipeline should build straight through without asking any of these — the safety gates in developer-agent.md's own instructions (real blockers like a name collision, an analysis-agent fix recommendation, live-dataflow drift, a push conflict) are a separate, deliberately-untouched category and still pause regardless of this config.
