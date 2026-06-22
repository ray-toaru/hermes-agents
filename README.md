# hermes-agents

Hermes agents lifecycle-management repository.

This repository is the declaration and governance layer for Hermes AgentOps Manager and managed Hermes agent profiles.

## Start Here

New development agents should read these project-level design documents before changing code, schemas, or governance records:

- `docs/EVIDENCE_BASELINE.md` — upstream Hermes evidence and derived AgentOps constraints.
- `docs/PROJECT_DESIGN.md` — project goals, non-goals, system boundary, and current implementation status.
- `docs/ARCHITECTURE.md` — layers, components, and responsibility boundaries.
- `docs/DOMAIN_MODEL.md` — core records and how they bind to each other.
- `docs/STATE_MACHINE.md` — change/apply lifecycle states and allowed transitions.
- `docs/SAFETY_INVARIANTS.md` — non-negotiable safety rules.
- `docs/THREAT_MODEL.md` — attacker model and mitigations.
- `docs/APPLY_PIPELINE_DESIGN.md` — complete future apply pipeline, including which phases are implemented, read-only, design-only, or blocked.
- `docs/REAL_APPLY_PIPELINE_DESIGN.md`, `docs/REAL_APPLY_THREAT_MODEL.md`, and `docs/REAL_APPLY_RECOVERY_RUNBOOK.md` — v2.8 design-only real apply package; these do not enable apply.
- `docs/PRODUCTION_LOCK_LIFECYCLE_DESIGN.md` — v2.9 design/prototype-only production lock lifecycle contract; this does not release production locks.
- `docs/v2.10-production-lock-skeleton.md` — v2.10 disabled production lock acquire/preserve skeleton; this does not write lock files.
- `docs/PRODUCTION_AUDIT_CAPTURE_DESIGN.md` — v2.11 design/prototype-only production audit-start contract; this does not write production audit records.
- `docs/OPERATIONS_AND_RECOVERY.md` — CI, ruleset, stale PR, stale lock, and future recovery handling.

Architecture decisions that should not be repeatedly reopened are recorded under `docs/adr/`.

## Purpose

This repository stores:

- AgentOps governance documents
- managed Hermes profile declarations
- templates
- schemas
- policies
- CI checks
- change proposal records
- pre-apply governance records
- apply-lock design records

It does not store runtime state, real secrets, logs, sessions, or business execution state.

## Hard Boundaries

- AgentOps manages agents; it does not orchestrate business tasks.
- A Hermes profile is the minimum managed unit.
- Critical changes must be diff-first.
- Real secret values must never be committed or read by AgentOps.
- Hermes runtime mechanisms must not be bypassed.
- Current scripts do not mutate managed profiles or runtime state.
- Future runtime-adjacent health, deployment, or repair management requires a separate design, approval gates, and no Hermes runtime bypass.
- `apply` remains disabled until the full gated mutation pipeline is implemented and reviewed.

## Repository Workflow

All development agents must use:

```text
Issue → branch → pull request → CI → review → merge
```

No direct feature work should be pushed to `main`.

## Governance

See:

- `AGENTS.md`
- `CONTRIBUTING.md`
- `.github/pull_request_template.md`
- `.github/ISSUE_TEMPLATE/task.yml`
- `.github/CODEOWNERS`
- `docs/repository-governance-baseline.md`
