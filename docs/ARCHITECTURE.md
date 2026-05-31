# Architecture

## Overview

Hermes AgentOps Manager is organized as a repository-backed governance/control plane.

```text
GitHub ruleset / CODEOWNERS / CI
        |
Repository governance files
        |
Schemas + policies
        |
Profile declarations
        |
Change records
        |
Pre-apply plans
        |
Apply-lock records
        |
Future apply pipeline (disabled)
```

The system intentionally stops before runtime mutation. Current scripts validate records, generate governance records, and check consistency. They do not mutate managed profiles or runtime state.

## Layers

### 1. Repository Enforcement Layer

Components:

- GitHub ruleset or branch protection
- `.github/CODEOWNERS`
- PR review and conversation resolution
- `.github/workflows/ci.yml`
- `scripts/check-codeowners`

Responsibility:

- enforce PR-first workflow;
- require real CI status checks;
- require owner review where configured;
- prevent force-push / deletion / non-reviewed main changes.

CI guardrails are not equivalent to GitHub enforcement. They detect repository drift; rulesets and branch protection enforce merge policy.

### 2. Governance Metadata Layer

Components:

- `README.md`
- `AGENTS.md`
- `CONTRIBUTING.md`
- `docs/`
- `.github/ISSUE_TEMPLATE/`
- `.github/pull_request_template.md`

Responsibility:

- define process, non-goals, design decisions, and review expectations.

### 3. Policy and Schema Layer

Components:

- `policies/global-permissions.yaml`
- `schemas/manifest.schema.json`
- `schemas/change-proposal.schema.json`
- `schemas/approval-record.schema.json`
- `schemas/pre-apply-plan.schema.json`
- `schemas/apply-lock.schema.json`

Responsibility:

- define structural record contracts;
- define global forbidden operations;
- define risk approval thresholds;
- define critical path patterns;
- keep policy as the single source for thresholds.

### 4. Profile Declaration Layer

Components:

- `inventory/agents.yaml`
- `profiles/<agent>/SOUL.md`
- `profiles/<agent>/config.yaml`
- `profiles/<agent>/manifest.yaml`

Responsibility:

- declare managed agent profiles;
- keep runtime-sensitive files out of Git;
- store references and metadata, not secret values or runtime state.

### 5. Change Record Layer

Components:

- `changes/<change_id>/proposal.yaml`
- `changes/<change_id>/diff.patch`
- `changes/<change_id>/approvals/*.yaml`
- `scripts/hermes-agentops`

Responsibility:

- capture a proposed profile diff;
- bind proposal to diff hash;
- bind approval records to change ID and diff hash;
- validate approvals, rejections, path scope, policy, and patch applicability.

### 6. Pre-Apply Planning Layer

Components:

- `changes/<change_id>/pre-apply-plan.yaml`
- `scripts/generate-pre-apply-plan`
- `scripts/check-pre-apply-plan`
- `docs/examples/pre-apply-plan.example.yaml`

Responsibility:

- generate a schema-valid plan only after existing verification succeeds;
- keep `mutation_enabled: false`;
- write only the canonical governance record path;
- validate plan cross-field consistency.

### 7. Apply-Lock Design Layer

Components:

- `docs/examples/apply-lock.example.yaml`
- `scripts/check-apply-lock`
- `schemas/apply-lock.schema.json`

Responsibility:

- define future lock semantics;
- validate lock records read-only;
- require repository-scoped exclusive locks;
- bind lock to change ID, plan hash, and base commit;
- require stale-lock manual inspection.

### 8. Future Mutation Layer

Current status: disabled.

Future responsibilities, when implemented:

- acquire lock;
- record rollback point;
- apply patch;
- validate post-apply state;
- write audit record;
- release lock;
- recover or roll back on failure.

No current code may assume this layer exists.

## Boundary with Hermes Runtime

AgentOps repository governance must not replace or bypass Hermes runtime components. In particular, AgentOps does not:

- resolve model providers;
- dispatch Hermes tools;
- manage Hermes session storage;
- manage gateway, cron, container, or systemd runtime;
- read runtime state databases;
- read `.env` or secret values.

AgentOps may validate that a profile declares references consistently, but it must not interpret itself as the runtime authority for those references.

## Dependency Direction

Allowed direction:

```text
scripts read schemas/policies/profiles/changes/docs examples
scripts write changes/<change_id>/ governance records only when explicitly designed
CI runs scripts
GitHub rulesets enforce merge policy
```

Forbidden direction:

```text
validators -> profile mutation
validators -> runtime mutation
plans -> apply authority
locks -> mutation authority
approvals -> identity proof
AgentOps -> business action execution
```
