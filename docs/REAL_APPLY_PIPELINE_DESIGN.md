# Real Apply Pipeline Design

Status: **design-only**. This document does not implement, enable, or authorize real apply.

`hermes-agentops apply` must remain disabled until the implementation slices listed in this design are separately reviewed, tested, and merged.

## Purpose

Define the future production mutation pipeline for applying an already-reviewed Hermes AgentOps change to a managed profile. The design converts the existing read-only and sandbox evidence chain into a production sequence, but it does not add mutation code.

## Non-Goals

This design does not authorize:

- source profile mutation;
- runtime state mutation;
- secret value reads;
- business orchestration;
- rollback execution;
- production lock release;
- production audit creation;
- any feature flag that can enable real apply.

## Required Production Pipeline

A future real apply implementation must execute these stages in order. Each stage must emit evidence before the next stage starts.

1. **Input selection**
   - Accept an explicit `change_id` only.
   - Resolve the target agent from `changes/<change_id>/proposal.yaml`.
   - Refuse ambiguous, missing, rejected, or non-verified changes.

2. **Authenticated approval gate**
   - Verify authenticated approval evidence using a reviewed verifier mode.
   - Bind repository, default branch, change ID, agent, diff hash, approver identity, decision, and signing or review time.
   - Treat any rejection, stale approval, missing threshold, or verifier failure as blocking.

3. **Readiness gate**
   - Require an apply-readiness report whose required gates are present, non-blocking, pre-apply, hash-bound, and backed by safe relative evidence paths.
   - Refuse readiness reports that imply authorization by themselves.

4. **Exclusive production lock acquisition**
   - Acquire one repository-scoped production lock for the change.
   - The lock must bind repository, branch, change ID, agent, current head, operator, acquired time, TTL, and recovery owner.
   - Existing active, stale, or recovery-required locks must block unless a reviewed recovery procedure resolves them.

5. **Rollback point creation**
   - Create rollback evidence before mutation.
   - Bind pre-apply Git head, working-tree cleanliness, target profile hash, changed paths, and lock evidence hash.
   - Refuse if the worktree is dirty or the rollback point cannot be independently verified.

6. **Pre-mutation audit start**
   - Emit audit evidence that a real apply attempt has started.
   - The record must include approval, readiness, lock, rollback, operator, command, and pre-head hashes.
   - Failure to write this evidence must preserve the lock and stop before mutation.

7. **Mutation command dispatch**
   - Apply only the reviewed diff for the approved change.
   - The command must be allowlisted, argv-only, non-shell, timeout-bound, and restricted to `profiles/<agent>/`.
   - It must not read secrets, mutate runtime state, invoke Hermes runtime tools, or orchestrate business actions.

8. **Post-apply validation**
   - Run allowlisted validation commands after mutation and before lock release.
   - Require profile validation, schema validation, policy validation, patch/path safety checks, and any change-specific validation gates.
   - Validation failure must enter recovery-required handling and must not release the production lock.

9. **Production audit completion**
   - Record success or failure with post-head, post-profile hash, validation outputs, lock status, rollback status, and recovery decision.
   - Audit must exist for both success and failure paths.

10. **Lock release or preservation**
    - Release the production lock only after successful mutation, successful post-apply validation, and successful completion audit.
    - Preserve the lock and mark recovery-required on unknown state, validation failure, audit failure, timeout, or rollback uncertainty.

## State Model

Allowed future states:

```text
selected
  -> authenticated
  -> ready
  -> locked
  -> rollback_point_created
  -> audit_started
  -> mutation_attempted
  -> post_validated
  -> audit_completed
  -> lock_released
```

Failure transitions:

```text
any_pre_mutation_failure -> failed_closed_no_mutation
mutation_or_post_validation_failure -> recovery_required_lock_preserved
unknown_state -> recovery_required_lock_preserved
rollback_success_after_failure -> recovered_lock_preserved_for_review
```

No state may transition directly from `selected`, `authenticated`, `ready`, or `locked` to `lock_released`.

## Evidence Binding Requirements

Each production record must include hashes or IDs for the previous records it depends on:

- authenticated approval evidence;
- readiness report;
- production lock;
- rollback point;
- structured mutation command;
- post-apply validation;
- production audit;
- recovery decision, if any.

Evidence completeness is not authorization. Authorization exists only when every gate passes in sequence and the future command remains inside its reviewed allowlist.

## Implementation Slices Required Before Enablement

A future implementation must be split into reviewed PRs:

1. production lock lifecycle integration;
2. rollback execution and post-rollback validation;
3. production audit capture for success and failure;
4. production post-apply validation execution;
5. production recovery state machine;
6. disabled real apply skeleton wired to the gates but returning failure;
7. canary-only real apply;
8. non-default explicit real apply, only after canary evidence.

## Design Boundaries

This document is evidence for architecture only. It does not enable `hermes-agentops apply`, does not add mutation code, and does not weaken any existing fail-closed invariant.
