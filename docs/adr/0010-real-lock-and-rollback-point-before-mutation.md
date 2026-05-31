# ADR 0010: Real Lock Acquisition and Rollback Point Creation Must Precede Mutation

## Status

Accepted for future apply design.

## Context

Current apply-lock records are governance evidence only. They do not acquire, release, repair, or override real locks. Current rollback-point records are evidence validation contracts only; they do not create rollback points or execute rollback.

Future mutation needs both concurrency safety and recovery evidence before any managed profile file changes.

## Decision

A future mutation command must acquire exactly one repository-scoped exclusive lock before mutation.

The lock implementation must:

- be atomic for the repository scope;
- bind to `change_id`, authenticated operator, base commit, pre-apply plan hash, and acquisition time;
- include a TTL;
- treat expired active locks as blocking until manual review;
- preserve failure evidence;
- release only after successful post-apply validation and audit capture;
- preserve the lock or mark recovery-required if mutation, rollback, validation, or audit capture fails.

After lock acquisition and before mutation, the future command must create a rollback point.

Rollback point creation must:

- record the pre-apply Git `HEAD`;
- prove referenced Git objects exist locally;
- bind to the acquired lock and pre-apply plan hash;
- record clean working tree evidence;
- fail closed if the repository state has changed since plan generation;
- avoid reading secrets or mutating runtime state.

## Consequences

- Apply-lock governance records are not real locks.
- Apply-lock analysis is only a preflight input; it does not release or override locks.
- Future mutation must stop if a real lock cannot be acquired atomically.
- Future mutation must stop if a rollback point cannot be created and verified.
- This ADR does not implement real lock acquisition, release, rollback-point creation, or rollback execution.
