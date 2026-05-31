# State Machine

## Purpose

This document defines the intended lifecycle for change and future apply records. It prevents a new contributor from treating a later governance record as permission to skip earlier gates.

## Current Change States

### proposed

A change directory exists with `proposal.yaml` and `diff.patch`.

### partially_approved

At least one valid approval exists, but approval threshold is not met.

### approved

Enough unique valid approvals exist, no valid rejection is present, proposal/diff hashes match, and policy threshold is met.

### rejected

A structurally valid, hash-bound rejection exists.

### invalid

Any required record is malformed, mismatched, hash-invalid, duplicated, path-invalid, policy-invalid, or otherwise untrusted.

## Current Evidence States

### verified

Base `changes verify` passes. This means the proposal, diff, approvals, policy, and path scope are trusted enough for non-mutating governance status, but it is not sufficient for pre-apply plan generation or future mutation.

### apply_ready_verified

`changes verify --check-git-clean --check-patch-applicable` passes. This stricter state is required before generating a pre-apply plan and must be re-checked immediately before any future mutation.

### pre_apply_planned

A schema-valid `pre-apply-plan.yaml` was generated after `apply_ready_verified`.

### lock_validated

An apply-lock record validates read-only against schema and cross-field checks.

This is not lock acquisition.

### apply_lock_recorded

A constrained `changes/<change_id>/apply-lock.yaml` governance record was created after validating the canonical pre-apply plan, matching the plan base commit to current `HEAD`, and checking for existing blocking lock records.

This is not apply mutation, real lock acquisition, or lock release.

### lock_analysis_clear

A read-only apply-lock analysis report indicates no blocking lock evidence.

This is not lock acquisition or lock release.

### rollback_point_validated

A rollback-point evidence record validates read-only.

This is not rollback point creation and does not execute rollback.

### audit_record_validated

An audit evidence record validates read-only.

This is not command execution and does not authorize mutation.

### approval_identity_validated

Approval identity evidence validates read-only.

This is not live or cryptographic authentication.

### post_apply_validation_evidence_validated

Post-apply validation evidence validates read-only.

This does not run post-apply validation and cannot be required before apply.

### readiness_report_validated

An apply-readiness evidence report validates and keeps `apply_authorized: false`.

This is not execution authority.

## Future Mutation States

These states are design-only until `apply` exists.

### locked

A future implementation has acquired exactly one repository-scoped exclusive runtime/concurrency lock.

### rollback_point_recorded

A future implementation has recorded the pre-apply Git HEAD and rollback metadata.

### applying

A future implementation is mutating managed profile files.

### applied

Mutation completed and post-apply validation passed.

### failed

A future mutation or post-apply validation failed.

### rolled_back

A future recovery path restored the recorded rollback point and captured evidence.

### audited

A future audit record captured commands, outputs, exit codes, Git HEAD before/after, lock lifecycle, and recovery data.

## Allowed Current Transitions

```text
none -> proposed
proposed -> partially_approved
proposed -> approved
proposed -> rejected
proposed -> invalid
partially_approved -> approved
partially_approved -> rejected
approved -> verified
verified -> apply_ready_verified
apply_ready_verified -> pre_apply_planned
pre_apply_planned -> lock_validated
pre_apply_planned -> apply_lock_recorded
apply_lock_recorded -> lock_analysis_clear
approved / verified / apply_ready_verified / pre_apply_planned -> approval_identity_validated
pre_apply_planned / apply_lock_recorded -> rollback_point_validated
pre_apply_planned / apply_lock_recorded -> audit_record_validated
pre_apply_planned / apply_lock_recorded -> post_apply_validation_evidence_validated
verified / apply_ready_verified / pre_apply_planned / apply_lock_recorded / lock_analysis_clear -> readiness_report_validated
```

All current transitions are non-runtime governance or evidence-validation transitions.

## Forbidden Current Transitions

```text
approved -> applying
verified -> applying
apply_ready_verified -> applying
pre_apply_planned -> applying
lock_validated -> locked
lock_validated -> applying
apply_lock_recorded -> locked
apply_lock_recorded -> applying
lock_analysis_clear -> locked
readiness_report_validated -> locked
readiness_report_validated -> applying
approval -> execution authority
approval_identity -> execution authority
pre_apply_plan -> execution authority
apply_lock_record -> execution authority
apply_lock_analysis -> execution authority
rollback_point -> execution authority
audit_record -> execution authority
post_apply_validation_evidence -> execution authority
readiness_report -> execution authority
```

## Future Apply Transition Sketch

Future apply must use a linear, fail-closed sequence:

```text
approved
  -> verified
  -> apply_ready_verified
  -> approval_identity_validated
  -> pre_apply_planned
  -> apply_lock_recorded
  -> lock_analysis_clear
  -> readiness_report_validated
  -> locked
  -> rollback_point_recorded
  -> applying
  -> applied
  -> audited
```

Failure path:

```text
locked / rollback_point_recorded / applying
  -> failed
  -> rolled_back
  -> audited
```

A future implementation must abort on first failed gate. It must not continue mutation after a failed clean-state check, patch applicability check, lock acquisition, rollback point creation, apply, or post-apply validation.

## State Ownership

| State | Owned by | Current/Future |
| --- | --- | --- |
| proposed | `hermes-agentops changes propose` | current |
| partially_approved | approval records + status view | current |
| approved | `changes verify` threshold logic | current |
| rejected | approval records + status view | current |
| invalid | validators | current |
| verified | base `changes verify` | current |
| apply_ready_verified | `changes verify --check-git-clean --check-patch-applicable` | current strict gate |
| pre_apply_planned | `generate-pre-apply-plan` | current governance write |
| lock_validated | `check-apply-lock` | current read-only |
| apply_lock_recorded | `acquire-apply-lock` | current governance write |
| lock_analysis_clear | `analyze-apply-locks --validate-report` or generated stdout report | current read-only |
| rollback_point_validated | `check-rollback-point` | current read-only |
| audit_record_validated | `check-audit-record` | current read-only |
| approval_identity_validated | `check-approval-identity` | current read-only |
| post_apply_validation_evidence_validated | `check-post-apply-validation` | current read-only |
| readiness_report_validated | `check-apply-readiness` | current read-only |
| locked | future real lock acquisition | future |
| rollback_point_recorded | future rollback module | future |
| applying | future apply module | future |
| applied | future apply module | future |
| failed | future recovery module | future |
| rolled_back | future recovery module | future |
| audited | future audit module | future |
