# Production Audit Capture Design

Status: **design/prototype-only**. This document does not write production audit records.

`hermes-agentops apply` remains disabled. The v2.11 slice defines the future production audit-start contract so later implementation PRs can be reviewed against explicit pre-mutation audit and lock-preservation rules.

## Purpose

Production audit capture must make a real apply attempt accountable before any mutation happens. The audit-start record is the future first production audit record. It binds the operator, repository head, change ID, agent, approval evidence, readiness evidence, lock evidence, rollback evidence, and structured mutation command evidence before mutation dispatch.

This design is not an audit writer. It is a contract for what a future writer must prove before mutation can begin.

## Audit-Start Must Precede Mutation

audit-start must occur before mutation. A future implementation must refuse mutation dispatch unless audit-start evidence has been successfully written and hash-bound to the same change and lock attempt.

The future sequence is:

```text
authenticated approval
  -> readiness
  -> production lock acquired or preserved skeleton evidence
  -> rollback point evidence
  -> structured mutation command evidence
  -> audit-start evidence written
  -> mutation dispatch may be considered by a later implementation
```

v2.11 stops before the final step. It does not dispatch mutation.

## Failure Policy

audit-start write failure preserves the lock. If the future audit-start writer cannot persist evidence, the implementation must stop before mutation and preserve the production lock for manual review.

Missing audit-start evidence blocks mutation. Unknown state preserves the lock. Retry requires manual review.

## Required Evidence Binding

A future audit-start record must bind:

- repository and default branch;
- current Git head;
- change ID and agent;
- operator identity;
- authenticated approval evidence hash;
- readiness report hash;
- production lock lifecycle contract hash;
- production lock skeleton or future production lock evidence hash;
- rollback point evidence hash;
- structured mutation command evidence hash;
- pre-mutation profile hash.

Evidence completeness is not authorization. It is a precondition for future production audit and recovery decisions.

## Release Boundary

A future production lock may not be released merely because audit-start exists. Completion audit, post-apply validation, recovery decision, and lock lifecycle release eligibility remain separate gates.

## Attack Review

### Attack: Treat audit-start evidence as permission to mutate

Rejected. Audit-start is accountability evidence, not authorization. It must be followed by separately reviewed mutation dispatch, validation, completion audit, and recovery handling.

### Attack: Continue mutation when audit-start write fails

Rejected. Audit-start write failure preserves the lock and blocks mutation.

### Attack: Release lock after audit-start because the attempt is recorded

Rejected. Audit-start alone is never release-eligible. Release requires completion audit, post-apply validation success, and recovery-not-required evidence.

### Attack: Use v2.11 to create production audit records

Rejected. v2.11 is design/prototype-only and does not write production audit records.

## Current Boundary

This slice does not enable apply, does not write production audit records, does not dispatch mutation, does not release production locks, does not mutate profiles, does not execute rollback, does not read secret values, does not mutate runtime state, and does not orchestrate business work.
