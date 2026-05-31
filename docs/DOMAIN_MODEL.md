# Domain Model

## Core Entities

### Agent Profile

A managed Hermes profile stored under `profiles/<agent>/`.

Required files:

- `SOUL.md`
- `config.yaml`
- `manifest.yaml`

AgentOps treats these as governed repository assets. It does not run the profile or inherit the profile's runtime permissions.

### Inventory Entry

A record in `inventory/agents.yaml` that points to a managed profile.

Purpose:

- enumerate managed agents;
- provide a stable profile directory and manifest reference.

### Manifest

Governance metadata for one profile.

Purpose:

- define profile identity;
- declare runtime references;
- declare permissions and forbidden operations;
- preserve global forbidden operations from policy.

### Global Policy

`policies/global-permissions.yaml`.

Purpose:

- define non-negotiable forbidden operations;
- define risk approval thresholds;
- define critical path patterns.

Code constants are fallbacks only. Repository behavior should load and validate policy.

### Change Proposal

`changes/<change_id>/proposal.yaml`.

Purpose:

- declare a proposed change to one agent profile;
- bind to `diff.patch` through `diff_sha256`;
- declare risk level and required approvals from policy;
- capture reason, validation notes, and rollback strategy.

### Diff Patch

`changes/<change_id>/diff.patch`.

Purpose:

- store the exact patch under review;
- provide the hash input for proposal and approval binding.

Safety properties:

- paths must remain under `profiles/<agent>/`;
- absolute, traversal, non-normal, quoted, backslash, whitespace, and malformed paths are rejected;
- patch applicability is a dry-run check only.

### Approval Record

`changes/<change_id>/approvals/*.yaml`.

Purpose:

- capture a human review decision for one change and one diff hash;
- record acknowledgements that secrets were not reviewed, apply is not automatic, and business orchestration is not authorized.

Important limitation:

- approval records are not cryptographic identity proofs;
- they are governance evidence only;
- future authenticated approval design is still required before mutation.

### Pre-Apply Plan

`changes/<change_id>/pre-apply-plan.yaml`.

Purpose:

- capture the future apply preconditions after the existing verifier passes;
- bind to change ID, base commit, diff hash, and audit path;
- keep `mutation_enabled: false`.

Important limitation:

- a valid pre-apply plan is not authorization to mutate.

### Apply Lock

A future governance record described by `schemas/apply-lock.schema.json`.

Purpose:

- define future concurrency protection;
- bind lock to `change_id`, pre-apply plan hash, and base commit;
- enforce repository scope and exclusive mode;
- require manual stale-lock review.

Important limitation:

- current checker validates lock records read-only;
- current system does not acquire or release locks.

### Rollback Point

Future record, not implemented.

Purpose:

- bind a future mutation attempt to the pre-apply Git HEAD;
- support Git-first rollback on failure.

### Audit Record

Future record, not implemented.

Purpose:

- capture before/after Git HEAD;
- capture commands, stdout/stderr, exit codes, validation output, lock lifecycle, and recovery actions.

### Runtime State

Logs, sessions, workspaces, state databases, gateways, cron jobs, containers, and other runtime artifacts.

Status:

- outside this repository;
- must not be committed;
- must not be mutated by current AgentOps scripts.

### Secret Reference

A name or reference to a secret required by a profile.

Status:

- references may be governed;
- real secret values must never be read, printed, or committed.

## Record Binding Graph

```text
Agent Profile
  <- Inventory Entry
  <- Manifest

Change Proposal
  -> Agent Profile
  -> Diff Patch by diff_sha256
  -> Policy risk threshold

Approval Record
  -> Change Proposal by change_id
  -> Diff Patch by diff_sha256

Pre-Apply Plan
  -> Change Proposal by change_id
  -> verified gate set
  -> base_commit
  -> canonical audit path

Apply Lock
  -> Change Proposal by change_id
  -> Pre-Apply Plan by pre_apply_plan_sha256
  -> base_commit

Future Audit Record
  -> Change Proposal
  -> Pre-Apply Plan
  -> Apply Lock
  -> Rollback Point
```

## Trust Levels

| Entity | Trust Level | Notes |
| --- | --- | --- |
| Schema | Structural authority | Defines valid shape, not operational truth. |
| Policy | Governance authority | Threshold and forbidden-operation source. |
| Proposal | Review input | Must be hash-bound to diff. |
| Approval | Review evidence | Not identity proof. |
| Pre-apply plan | Prepared evidence | Not execution authority. |
| Apply lock | Future concurrency evidence | Current checker is read-only. |
| CI result | Validation evidence | Not a substitute for GitHub ruleset enforcement. |
| Ruleset | Merge enforcement | External GitHub setting; record evidence when changed. |
