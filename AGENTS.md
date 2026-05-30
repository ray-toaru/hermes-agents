# Development Agent Protocol

This repository may be modified by multiple development agents. Every agent must follow this protocol.

## Role

Agents working in this repository are development contributors. They are not runtime orchestrators for Hermes agents.

## Mandatory Workflow

```text
Issue → branch → pull request → CI → review → merge
```

Agents must not push feature work directly to `main`.

## Required Evidence

Every non-trivial change must include:

- goal
- non-goal
- evidence source
- affected files
- risk level
- tests performed
- rollback plan
- attack/review notes when design-sensitive

Evidence priority:

1. official Hermes source
2. official Hermes documentation
3. official tests
4. actual local/CI run result
5. explicitly labeled engineering inference

## Forbidden Actions

Agents must not:

- commit real secrets
- commit `.env`, `state.db`, logs, sessions, workspace data, or runtime cache
- bypass Hermes provider runtime resolution
- bypass Hermes tools registry/dispatch
- convert AgentOps into a business orchestration layer
- claim tests passed without recorded evidence
- implement automatic `apply` without approval workflow, file locking, rollback point, and validation gates

## Critical Files

Changes to these files require extra care and explicit PR explanation:

- `profiles/agentops/SOUL.md`
- `scripts/hermes-agentops`
- `schemas/`
- `policies/`
- `.github/workflows/`
- `AGENTS.md`
- `CONTRIBUTING.md`

## Design Convergence Rule

A design point is not considered stable until it survives multiple attack/review rounds without changing.
