# Repository Governance

## Purpose

This repository is the declaration and governance layer for Hermes AgentOps Manager and managed Hermes profiles.

## Source of Truth Split

- GitHub: declarations, templates, schemas, policies, docs, tests, and change records
- Local runtime: state database, logs, sessions, workspaces, and runtime cache
- Secret storage: real secret values outside this repository

## Development Flow

All development should use:

```text
Issue -> branch -> pull request -> CI -> review -> merge
```

## Branches

Allowed branch prefixes:

- `bootstrap/*`
- `feature/*`
- `fix/*`
- `docs/*`
- `schema/*`
- `policy/*`
- `ci/*`

## PR Requirements

Each PR should include:

- goal
- non-goal
- evidence
- risk level
- changed files
- tests
- rollback
- review notes for design-sensitive changes

## Main Protection Target

After the bootstrap PR is merged, `main` should be protected:

- require pull request before merging
- require status checks
- require conversation resolution
- avoid direct feature pushes

## AgentOps Boundary

AgentOps manages Hermes agent lifecycle assets. It should not become a task routing layer or workflow orchestration layer for managed profiles.
