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
- Automatic `apply` remains intentionally unimplemented until the full preflight, locking, rollback, post-apply validation, and audit model is reviewed.

## Repository Workflow

All development agents must use:

```text
Issue → branch → pull request → CI → review → merge
```

No direct feature work should be pushed to `main`.

## Design Entry Points

Start here for system-level context:

- `docs/agentops-architecture.md` — overall architecture, domain model, state machine, invariants, threat model, and recovery model.
- `docs/agentops-adr.md` — already-converged architecture decisions.
- `docs/agentops-future-apply-pipeline.md` — future apply pipeline prerequisites; design-only, not authorization to implement mutation.
- `docs/repository-governance-baseline.md` — CODEOWNERS, CI guardrails, and GitHub ruleset/branch protection expectations.

Version-specific notes:

- `docs/v1.1-pre-apply-safety-design.md`
- `docs/v1.2-pre-apply-plan-generation.md`
- `docs/v1.3-apply-lock-design.md`

## Initial Governance

See:

- `AGENTS.md`
- `CONTRIBUTING.md`
- `.github/pull_request_template.md`
- `.github/ISSUE_TEMPLATE/task.yml`
