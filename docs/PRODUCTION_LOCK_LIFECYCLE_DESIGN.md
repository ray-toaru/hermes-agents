# Production Lock Lifecycle Design

Status: **design/prototype-only**. This document does not implement real apply and does not release production locks.

`hermes-agentops apply` remains disabled. The v2.9 slice defines the future production lock lifecycle contract so later implementation PRs can be reviewed against explicit release and preservation rules.

## Purpose

The production apply lock is the future exclusive guard around a real apply attempt. Its job is to prevent concurrent mutation, bind a mutation attempt to reviewed evidence, and preserve ambiguous or failed states for manual recovery.

This design is not a production lock implementation. It records the states, transitions, evidence bindings, and non-release rules that a future implementation must satisfy.

## Lifecycle States

The future lifecycle is modeled as:

```text
not_acquired
  -> acquired
  -> rollback_bound
  -> audit_started
  -> mutation_attempted
  -> post_validated
  -> audit_completed
  -> release_eligible
  -> released
```

Failure transitions go to:

```text
recovery_required
  -> preserved_for_review
```

unknown state preserves the lock. Validation failure preserves the lock. Audit failure preserves the lock. Timeout preserves the lock. Retry is blocked until manual review.

## Release Rule

A future lock release is allowed only from `release_eligible`. To become release-eligible, a future implementation must prove:

1. authenticated approval evidence passed;
2. readiness evidence passed;
3. production lock evidence exists;
4. rollback point evidence exists;
5. production audit-start evidence exists before mutation;
6. the reviewed mutation command succeeded;
7. post-apply validation succeeded after mutation;
8. production completion audit exists;
9. recovery is not required.

No state other than `release_eligible` may release a lock. `recovery_required` and `preserved_for_review` explicitly forbid release.

## Preservation Rule

The lock must be preserved when any of these occur:

- mutation failure;
- post-apply validation failure;
- production audit write failure;
- rollback uncertainty;
- timeout;
- operator interruption;
- unknown state;
- missing evidence hash;
- stale lock whose owner/outcome cannot be proven.

Preserved locks require manual review before retry or release. The future recovery process must produce explicit evidence before any state changes.

## Evidence Binding

A production lock record must bind:

- repository and branch;
- change ID and agent;
- operator and recovery owner;
- current Git head;
- authenticated approval evidence hash;
- readiness report hash;
- rollback point hash once created;
- audit-start and audit-completion hashes;
- post-apply validation hash;
- recovery decision hash if recovery is required.

Completeness of evidence is not authorization. It is only a prerequisite for future release decisions.

## Attack Review

### Attack: Release the lock after an unknown failure to unblock later changes

Rejected. Unknown state preserves the lock and requires manual review.

### Attack: Treat a successful sandbox lock prototype as a production lock

Rejected. Sandbox and temporary-repository locks demonstrate sequencing only. Production lifecycle ownership, audit binding, and recovery preservation remain future implementation work.

### Attack: Let audit failure release the lock because mutation already succeeded

Rejected. Release requires successful completion audit. Audit failure preserves the lock.

### Attack: Add a release helper before real apply exists

Rejected. v2.9 is design/prototype-only. It does not release production locks and does not add production release code.

## Current Boundary

This slice does not enable apply, does not mutate profiles, does not execute rollback, does not create production audit records, does not read secret values, does not mutate runtime state, and does not orchestrate business work.
