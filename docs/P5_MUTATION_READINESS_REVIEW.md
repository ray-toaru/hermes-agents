# P5 Mutation Readiness Review

## Decision

Do not implement a real mutation command yet.

P0-P4 have converged for the current read-only and sandboxed track, but P5 requires more than a non-default flag. A command that mutates managed profiles would still violate the accepted ADR baseline because the required mutation prerequisites are documented but not implemented.

`hermes-agentops apply` must remain disabled until the blocking prerequisites below are implemented, tested, reviewed, and integrated into a fail-closed pipeline.

## Current Implemented Boundary

Implemented capabilities are limited to:

- governance record validation;
- approval and diff hash binding;
- strict dry-run checks for clean worktree and patch applicability;
- pre-apply plan governance-record generation;
- apply-lock governance-record generation;
- read-only evidence validators;
- read-only evidence-chain integration tests;
- sandboxed patch application inside temporary directories only;
- temporary-repository authenticated approval verifier fixtures and read-only signed approval attestation verification;
- structured command evidence validation;
- validation-only structured command sandbox execution;
- temporary-repository atomic real apply lock prototype;
- temporary-repository rollback point creator prototype;
- sandbox-only post-apply validation runner prototype;
- integrated sandbox-only mutation pipeline that composes authenticated approval, readiness, temporary lock, rollback point, same-sandbox patch application, and post-apply validation evidence without source profile mutation;
- sandbox mutation audit capture that records integrated sandbox success/failure evidence without creating production audit records;
- sandbox recovery simulation that records fail-closed recovery decisions without releasing locks or executing rollback.

None of these capabilities authorize or perform real mutation.

## Blocking Prerequisites

| Prerequisite | ADR | Current State | Required Before Mutation |
| --- | --- | --- | --- |
| Authenticated approval verification | ADR 0008 | Approval YAML and identity evidence exist; authenticated approval evidence contract exists; fixture verifier exists; signed-attestation verifier exists for local Ed25519 evidence and reviewed public trust roots; integrated sandbox pipeline consumes authenticated approval evidence; `live_github` still fails closed. | Implement `live_github` separately if direct GitHub review verification is required before real mutation. |
| Structured command evidence and dispatch | ADR 0009 | Audit command strings are recorded-only evidence; structured command evidence contract exists; validation-only sandbox runner exists, but no mutation, rollback, or audit-capture runner exists. | Add reviewed allowlisted dispatch for mutation-adjacent classes only after lock, rollback, audit, and recovery prerequisites converge. |
| Real repository-scoped exclusive lock | ADR 0010 | Apply-lock files are governance records only; temporary-repo atomic lock prototype exists, but it is not integrated with apply. | Integrate atomic lock acquisition/release with the future mutation pipeline, including failure preservation and recovery-required state. |
| Rollback point creation | ADR 0010 | Rollback-point governance records can be validated; temporary-repo rollback point creator prototype exists, but it is not integrated with apply and does not execute rollback. | Integrate rollback point creation before mutation, including Git object existence, clean-state binding, and failure-safe evidence persistence. |
| Post-apply validation execution | ADR 0011 | Post-apply validation evidence can be validated; the standalone sandbox-only runner exists, and the integrated sandbox pipeline performs same-sandbox patch application and validation after temporary rollback-point evidence creation, but it is not real apply and does not release locks. | Execute post-apply checks after real mutation and before real lock release; fail closed on any unexpected result. |
| Mutation audit capture | ADR 0011 | Existing audit records are validation-only evidence; sandbox mutation audit capture now records integrated sandbox success/failure evidence and hashes, but does not create production audit records. | Capture production success and failure audit records with structured command evidence, heads, lock lifecycle, rollback evidence, validation outputs, and recovery state. |
| Failure recovery and retry rules | ADR 0011 | Sandbox recovery simulation records no-recovery, validation-failed, lock, rollback, audit-write, and unknown-state outcomes without releasing locks or executing rollback. Production recovery remains unimplemented. | Preserve real locks on uncertainty, attempt rollback only when preconditions hold, validate rollback, and require manual review before retry. |

## Attack Review

### Attack: Add `--i-understand` and call `git apply` directly

Rejected. A non-default flag is not a substitute for authenticated approvals, atomic locks, rollback evidence, post-apply validation, audit capture, and recovery rules.

### Attack: Reuse sandbox dry-run as apply

Rejected. The sandbox command intentionally copies data to a temporary directory and proves source profiles remain unchanged. Treating it as mutation would discard the safety property it was created to test.

### Attack: Treat readiness report completeness as authorization

Rejected. Readiness reports require `apply_authorized: false`; blocked readiness can be valid evidence, but it still cannot authorize mutation.

### Attack: Trust YAML approvals because CI passed

Rejected. CI validation proves record shape and consistency, not live reviewer identity or current permission.

### Attack: Release stale or expired locks automatically

Rejected. ADR 0010 requires expired active locks to remain blocking until manual review.

### Attack: Treat rollback point creation as rollback execution

Rejected. The rollback point creator only emits pre-mutation evidence bound to an active lock and clean Git state. It does not execute rollback, release locks, authorize apply, or mutate managed profiles.

### Attack: Treat sandbox post-apply validation as real post-apply validation

Rejected. The sandbox post-apply validation runner mutates only a temporary copied workspace, emits evidence, and proves source profiles remain unchanged. It does not run after real apply, release locks, create audit records, or authorize mutation.


### Attack: Treat integrated sandbox pipeline as real apply

Rejected. The integrated pipeline intentionally copies governance inputs into a throwaway temporary workspace and proves source `profiles/` remain unchanged. Its temporary lock and rollback evidence prove sequencing only; they do not protect source mutation, release production locks, execute rollback, create production audit records, or authorize apply.

### Attack: Treat sandbox mutation audit as production audit

Rejected. Sandbox audit records require `sandbox_only: true`, `production_audit: false`, `mutation_enabled: false`, and `apply_authorized: false`. They record integrated sandbox evidence only and cannot replace future production audit capture.

### Attack: Treat sandbox recovery simulation as rollback or lock release

Rejected. Recovery simulation records require `rollback_executed: false`, `lock_release_allowed: false`, `lock_release_performed: false`, and `retry_allowed_without_manual_review: false`. Unknown states must fail closed and require manual review.

## Required Implementation Slices Before Real Mutation

These should be separate reviewed PRs before any mutation command exists:

1. **Authenticated approval verifier**: read-only signed-attestation verifier is implemented; live GitHub verification remains a separate optional slice before real mutation if direct GitHub review checks are required.
2. **Structured command schema**: schema and validator for execution-adjacent command records; no command execution yet.
3. **Command registry and validation-only runner**: allowlisted argv-only runner for validation commands in a temporary workspace; still no mutation.
4. **Atomic real lock prototype**: repository-scoped lock acquisition/release in a temporary test repository, with stale/recovery behavior; no profile mutation.
5. **Rollback point creator**: create and validate rollback evidence in a temporary repository; no rollback execution yet.
6. **Post-apply validation runner**: run validation commands after sandbox mutation and capture structured evidence.
7. **Audit capture pipeline**: sandbox mutation audit capture is implemented; production audit capture remains future work.
8. **Recovery simulation**: sandbox recovery simulation is implemented; production rollback execution, post-rollback validation, and real lock release remain future work.
9. **Integrated sandbox mutation pipeline**: implemented sandbox-only in v2.4 and extended with audit and recovery evidence in v2.5-v2.6.
10. **Final non-default mutation proposal**: only after audit and recovery converge, consider a real mutation command behind explicit non-default invocation and fail-closed gates.

## Current P5 Status

P5 is not ready for implementation. The correct current outcome is to keep `hermes-agentops apply` disabled and continue with prerequisite implementation slices.

## Non-Goals

This review does not:

- implement or enable real `apply`;
- mutate managed profiles;
- acquire or release real locks in the apply pipeline;
- execute rollback;
- execute post-apply validation as part of real mutation;
- read real secret values;
- mutate runtime state;
- route or orchestrate business tasks.
