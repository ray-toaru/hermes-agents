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

Code constants are fallbacks only. Repository behavior should load and validate policy. Invalid policy must fail closed.

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

### Approval Identity Evidence

`changes/<change_id>/approval-identity.yaml` or equivalent referenced identity evidence.

Purpose:

- bind an approver to identity evidence for a specific `change_id` and approval record;
- preserve provider/method metadata for future authenticated approval gates.

Important limitation:

- current checker validates evidence shape and bindings only;
- URLs or YAML fields are references, not live authentication authority.

### Pre-Apply Plan

`changes/<change_id>/pre-apply-plan.yaml`.

Purpose:

- capture the future apply preconditions after the existing verifier passes;
- bind to change ID, base commit, diff hash, and audit path;
- keep `mutation_enabled: false`.

Important limitation:

- a valid pre-apply plan is not authorization to mutate.

### Apply Lock

`changes/<change_id>/apply-lock.yaml`.

Purpose:

- define future concurrency protection;
- bind lock to `change_id`, pre-apply plan hash, and base commit;
- enforce repository scope and exclusive mode;
- require manual stale-lock review.

Important limitation:

- current checker validates lock records read-only;
- current generator writes a governance record only;
- current system does not acquire or release real locks.

### Apply Lock Analysis Report

A repository-wide read-only report validated by `schemas/apply-lock-analysis.schema.json`.

Purpose:

- classify existing lock records as blocking or non-blocking;
- treat active, expired-active, stale, recovery-required, invalid, and unparsable locks conservatively.

Important limitation:

- report generation is stdout-only;
- it does not acquire, release, rewrite, delete, or repair locks.

### Rollback Point

`changes/<change_id>/rollback-point.yaml`.

Purpose:

- bind future mutation evidence to the pre-apply Git HEAD;
- support Git-first rollback on failure.

Important limitation:

- current checker validates rollback-point evidence only;
- current system does not create rollback points or execute rollback.

### Audit Record

`changes/<change_id>/audit-record.yaml`.

Purpose:

- capture before/after Git HEAD;
- capture command evidence, exit codes, validation output hashes, lock lifecycle references, and recovery actions.

Important limitation:

- current checker validates audit evidence only;
- command strings in current records are not execution authority.

### Post-Apply Validation Evidence

`changes/<change_id>/post-apply-validation.yaml`.

Purpose:

- record validation evidence for a future post-apply phase;
- bind to expected and actual Git HEADs, audit hash, command evidence, and success/failure status.

Important limitation:

- current checker validates evidence only;
- it does not execute apply, validation commands, or rollback.

### Apply Readiness Report

A read-only aggregate report validated by `schemas/apply-readiness-report.schema.json`.

Purpose:

- summarize whether required governance evidence gates are present, missing, blocked, invalid, or future-only;
- make readiness evidence explicit for human review.

Important limitation:

- `apply_authorized` must remain `false`;
- evidence completeness is not execution authority.

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

Approval Identity Evidence
  -> Approval Record by approver / approval hash
  -> Change Proposal by change_id

Pre-Apply Plan
  -> Change Proposal by change_id
  -> verified gate set
  -> base_commit
  -> canonical audit path

Apply Lock
  -> Change Proposal by change_id
  -> Pre-Apply Plan by pre_apply_plan_sha256
  -> base_commit

Apply Lock Analysis Report
  -> Apply Lock records by path/status

Rollback Point
  -> Change Proposal
  -> Pre-Apply Plan
  -> Apply Lock
  -> pre-apply Git HEAD

Audit Record
  -> Change Proposal
  -> Pre-Apply Plan
  -> Apply Lock
  -> Rollback Point
  -> command evidence

Post-Apply Validation Evidence
  -> Change Proposal
  -> Audit Record
  -> expected/actual Git HEADs

Apply Readiness Report
  -> Change Proposal
  -> Approval Identity Evidence
  -> Pre-Apply Plan
  -> Apply Lock Analysis Report
  -> future Apply Lock / Rollback / Audit / Post-Apply evidence slots
```

## Trust Levels

| Entity | Trust Level | Notes |
| --- | --- | --- |
| Schema | Structural authority | Defines valid shape, not operational truth. |
| Policy | Governance authority | Threshold and forbidden-operation source. |
| Proposal | Review input | Must be hash-bound to diff. |
| Approval | Review evidence | Not identity proof. |
| Approval identity | Identity evidence reference | Not live authentication authority. |
| Pre-apply plan | Prepared evidence | Not execution authority. |
| Apply lock | Future concurrency evidence | Current checker/generator do not acquire or release real locks. |
| Apply lock analysis | Blocking evidence summary | Does not mutate locks. |
| Rollback point | Recovery evidence | Current checker does not create rollback points or execute rollback. |
| Audit record | Execution/recovery evidence | Current checker validates evidence only. |
| Post-apply validation | Completion evidence | Current checker does not execute validation. |
| Apply readiness report | Aggregate evidence summary | Must keep `apply_authorized: false`. |
| CI result | Validation evidence | Not a substitute for GitHub ruleset enforcement. |
| Ruleset | Merge enforcement | External GitHub setting; record evidence when changed. |
