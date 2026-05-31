# Hermes AgentOps Manager Architecture

## Purpose

Hermes AgentOps Manager is the repository governance and control-plane layer for managed Hermes agent profiles. It records intended profile changes, policy decisions, approvals, pre-apply plans, and future apply-adjacent governance records.

It is not a Hermes runtime replacement, not a business workflow orchestrator, and not a secret reader.

## Current status model

| Area | Status | Notes |
| --- | --- | --- |
| Profile declaration storage | Implemented | Managed under `profiles/` with schemas, policies, inventory, and CI validation. |
| Change proposals | Implemented | Diff-first records under `changes/<change_id>/`. |
| Approval records | Implemented | Hash-bound approval/rejection records under `changes/<change_id>/approvals/`. |
| Pre-apply plans | Read-only generation implemented | `scripts/generate-pre-apply-plan` creates schema-valid governance records only. |
| Apply locks | Design + read-only validation | Schema and checker exist; no acquisition or release command yet. |
| Apply execution | Blocked | `apply` remains intentionally unimplemented and returns non-zero. |
| Runtime state | Out of scope | Logs, sessions, workspace state, and secret values must not be committed. |

## Architecture layers

### 1. Repository policy layer

Files:

- `policies/global-permissions.yaml`
- `schemas/*.schema.json`
- `.github/CODEOWNERS`
- `.github/workflows/ci.yml`
- GitHub ruleset or branch protection configuration

Responsibilities:

- define global forbidden actions;
- define risk-based approval thresholds;
- validate record structures;
- protect `main` through PR, CI, linear-history, and deletion/force-push rules;
- keep enforcement in GitHub, not only in repository scripts.

### 2. Profile declaration layer

Files:

- `profiles/<agent>/SOUL.md`
- `profiles/<agent>/config.yaml`
- `profiles/<agent>/manifest.yaml`
- `inventory/agents.yaml`

Responsibilities:

- store intended profile declarations;
- forbid real secrets and runtime files;
- ensure each managed profile has required metadata and permission boundaries.

### 3. Change record layer

Files:

- `changes/<change_id>/proposal.yaml`
- `changes/<change_id>/diff.patch`
- `changes/<change_id>/approvals/*.yaml`

Responsibilities:

- keep profile changes diff-first;
- bind proposal and approval records to `diff.patch` by SHA-256;
- validate path scope under `profiles/<agent>/`;
- fail closed on rejection records, malformed records, mismatched hashes, duplicate approvers, and insufficient approvals.

### 4. Pre-apply planning layer

Files:

- `changes/<change_id>/pre-apply-plan.yaml`
- `schemas/pre-apply-plan.schema.json`
- `scripts/generate-pre-apply-plan`
- `scripts/check-pre-apply-plan`

Responsibilities:

- generate a non-mutating plan only after full change verification passes;
- require `mutation_enabled: false`;
- bind the plan to `change_id`, agent, base commit, proposal diff hash, validation gates, rollback expectations, audit intent, and failure recovery behavior;
- keep output constrained to the canonical governance-record path.

### 5. Apply-lock design layer

Files:

- `schemas/apply-lock.schema.json`
- `docs/examples/apply-lock.example.yaml`
- `scripts/check-apply-lock`

Responsibilities:

- define future repository-scoped exclusive lock semantics;
- bind a future lock to `change_id`, `base_commit`, and `pre_apply_plan_sha256`;
- require stale-lock manual inspection before release;
- remain read-only until a future lock-acquisition command is separately reviewed.

## Domain objects

### Agent profile

A managed Hermes profile. The minimum unit of AgentOps governance.

Required profile files:

- `SOUL.md`
- `config.yaml`
- `manifest.yaml`

### Change proposal

A structured request to change one managed profile. It contains risk level, reason, rollback note, validation expectations, and `diff_sha256`.

### Diff patch

The exact Git patch being proposed. It must stay inside `profiles/<agent>/` and match the proposal hash.

### Approval record

A hash-bound decision record. `approve` records count toward the policy threshold; any valid `reject` record blocks verification.

### Pre-apply plan

A generated governance record proving that a verified change has a non-mutating apply-adjacent plan. It is not authorization to mutate.

### Apply lock

A future governance record for concurrency control. At present it is design-only and read-only validated.

## State machine

```text
profile diff
  -> change proposed
  -> approvals collected
  -> verified
  -> pre-apply plan generated
  -> lock designed / future lock acquired
  -> future apply preflight
  -> future apply mutation
  -> post-apply validation
  -> audit and recovery record
```

Current implemented stop point:

```text
pre-apply plan generated
```

Current blocked point:

```text
apply mutation
```

## Safety invariants

- `apply` remains disabled until preflight, lock acquisition, rollback, mutation, post-apply validation, and audit semantics are implemented and reviewed together.
- AgentOps must not read real secret values.
- AgentOps must not commit runtime state, logs, sessions, or workspaces.
- AgentOps must not bypass Hermes runtime provider or tool registry mechanisms.
- AgentOps must not orchestrate business actions.
- All profile mutations must be diff-first and path-scoped.
- All approval decisions must bind to the exact diff hash.
- Any valid rejection blocks verification.
- Pre-apply plans and lock records must use `mutation_enabled: false` until the future mutation phase is separately approved.

## Threat model

| Threat | Control |
| --- | --- |
| Policy drift | Approval thresholds load from policy and are tested. |
| Path escape | Diff parser rejects absolute paths, traversal, malformed headers, ambiguous paths, and out-of-profile paths. |
| Approval replay | Approval records bind `change_id` and `diff_sha256`. |
| Duplicate approvals | Verification rejects duplicate approver identities. |
| Silent rejection bypass | Any valid rejection record fails verification. |
| Stale or mismatched plan | Pre-apply checker enforces cross-field consistency. |
| Lock reuse | Apply-lock checker binds `change_id`, agent, optional plan file hash, and base commit shape. |
| Output-path expansion | Pre-apply generator only writes the canonical plan path. |
| CI-only false confidence | Governance docs distinguish repository guardrails from GitHub ruleset enforcement. |

## Recovery model

Current recovery is Git-first:

- revert the PR that introduced a governance change;
- preserve change records for audit;
- do not delete stale evidence automatically;
- require manual inspection before future stale lock release.

Future apply recovery must additionally record:

- HEAD before mutation;
- HEAD after mutation;
- stdout/stderr and exit codes for each gate;
- rollback action and result;
- post-apply validation result.
