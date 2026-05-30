# hermes-agents

Hermes agents lifecycle-management repository.

This repository is the declaration and governance layer for Hermes AgentOps Manager and managed Hermes agent profiles.

## Purpose

This repository stores:

- AgentOps governance documents
- managed Hermes profile declarations
- templates
- schemas
- policies
- CI checks
- change proposal records

It does not store runtime state, real secrets, logs, sessions, or business execution state.

## Hard Boundaries

- AgentOps manages agents; it does not orchestrate business tasks.
- A Hermes profile is the minimum managed unit.
- Critical changes must be diff-first.
- Real secret values must never be committed.
- Hermes runtime mechanisms must not be bypassed.

## Repository Workflow

All development agents must use:

```text
Issue → branch → pull request → CI → review → merge
```

No direct feature work should be pushed to `main`.

## Initial Governance

See:

- `AGENTS.md`
- `CONTRIBUTING.md`
- `.github/pull_request_template.md`
- `.github/ISSUE_TEMPLATE/task.yml`
