# ADR 0011: Post-Apply Validation, Audit, and Recovery Are Mandatory Mutation Gates

## Status

Accepted for future apply design.

## Context

Current post-apply validation and audit records are evidence validators. They do not run apply, validation, rollback, audit capture, or recovery.

Future mutation may partially modify managed profile files, fail validation, or leave uncertain repository state. Without mandatory post-apply validation, audit capture, and failure recovery, the system would be hard to trust or repair.

## Decision

A future mutation command must run post-apply validation immediately after mutation and before lock release.

Post-apply validation must:

- validate schemas;
- validate managed profiles;
- validate policy;
- validate the resulting Git/worktree state;
- validate that only expected managed profile paths changed;
- capture output hashes and redacted summaries;
- fail closed on any unexpected result.

A future mutation command must capture an audit record for both success and failure paths.

Audit capture must include:

- change ID;
- authenticated operator;
- authenticated approval evidence reference;
- base commit;
- head before mutation;
- head after mutation;
- lock lifecycle evidence;
- rollback point evidence;
- structured command evidence;
- validation results;
- failure and recovery actions.

If mutation or validation fails, the future command must:

1. stop further mutation;
2. preserve lock and audit evidence;
3. attempt rollback only if rollback preconditions are satisfied;
4. validate rollback result;
5. record rollback success or failure;
6. leave the lock in recovery-required state when uncertainty remains;
7. require manual review before retry.

## Consequences

- A future apply command must not release a lock before audit capture and post-apply validation are complete.
- A future apply command must not silently retry after failure.
- Recovery is part of the mutation design, not an afterthought.
- This ADR does not implement post-apply validation execution, audit capture, rollback, or retry logic.
