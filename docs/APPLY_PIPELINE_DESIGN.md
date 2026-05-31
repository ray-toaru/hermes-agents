# Apply Pipeline Design

## Status

This is the project-level design for a future apply pipeline. It is not an implementation plan for enabling `apply` immediately.

Current status: `apply` is disabled and must remain non-zero.

## Pipeline Summary

A future apply must be a linear, fail-closed pipeline:

```text
policy/schema validation
  -> change verification
  -> approval verification
  -> clean-state and patch applicability
  -> pre-apply plan generation
  -> lock acquisition
  -> rollback point creation
  -> mutation
  -> post-apply validation
  -> audit record
  -> lock release or preserved failure evidence
```

## Phase Table

| Phase | Current Status | Mutation? | Notes |
| --- | --- | --- | --- |
| Policy/schema validation | implemented | no | Validates policy, schema, profile metadata. |
| Change verification | implemented | no | Verifies proposal, diff, approvals, path scope, hashes. |
| Git clean check | implemented dry-run | no | Currently optional verifier gate; future apply must require. |
| Patch applicability | implemented dry-run | no | Uses `git apply --check`; no patch application. |
| Pre-apply plan schema | implemented | no | `mutation_enabled: false`. |
| Pre-apply plan generation | implemented governance write | governance record only | Writes canonical `changes/<id>/pre-apply-plan.yaml`. |
| Apply-lock schema/checker | implemented read-only | no | Validates lock contract only. |
| Lock acquisition | not implemented | future | Must be repository-scoped and exclusive first. |
| Rollback point creation | not implemented | future | Must record pre-apply Git HEAD. |
| Patch mutation | disabled | future | Must be separate from dry-run. |
| Post-apply validation | not implemented | future | Must validate profile and governance state after mutation. |
| Audit record | not implemented | future | Must capture commands, outputs, exit codes, Git HEADs, lock lifecycle. |
| Lock release/recovery | not implemented | future | Must preserve failure evidence when needed. |

## Required Future Apply Gates

A future mutation command must fail closed unless all are true:

1. Repository ruleset / PR flow has already accepted the change that introduced the apply implementation.
2. Policy validates.
3. Schemas validate.
4. Change proposal validates.
5. `diff.patch` hash matches proposal.
6. Approval records validate and meet policy threshold.
7. No valid rejection is present.
8. All paths remain under the managed profile scope.
9. Target profile worktree is clean.
10. Patch applicability succeeds immediately before mutation.
11. Pre-apply plan exists, validates, and binds to current base commit and diff evidence.
12. Operator confirms the plan.
13. Repository-scoped exclusive lock is acquired.
14. Rollback point is recorded.
15. Patch is applied only to expected profile paths.
16. Post-apply profile validation succeeds.
17. Audit record is written.
18. Lock is released on success or preserved with failure evidence on failure.

## Prohibited Shortcuts

A future implementation must not:

- treat approval records as identity proof;
- treat plan generation as apply authorization;
- treat lock validation as lock acquisition;
- skip Git clean checks because a plan exists;
- skip patch applicability because it passed earlier;
- apply without rollback point;
- apply without audit record;
- delete stale lock evidence automatically;
- mutate runtime state or execute business actions.

## Failure Handling

The pipeline must abort on first failure. If failure occurs before mutation, no rollback is needed beyond preserving evidence.

If failure occurs after mutation starts, future implementation must:

1. stop further mutation;
2. preserve lock and audit evidence;
3. roll back to the recorded rollback point where possible;
4. run validation after rollback;
5. record success/failure of rollback;
6. require manual review before any retry.

## Minimal Future Implementation Order

Do not jump directly to mutation. Implement in this order:

1. authenticated approval identity design;
2. repository-wide clean-state policy;
3. lock acquisition/release design with read-only tests first;
4. rollback point schema and validator;
5. audit record schema and validator;
6. sandboxed apply dry-run integration tests;
7. post-apply validation design;
8. mutation implementation behind explicit non-default command;
9. failure recovery tests;
10. ruleset and CODEOWNERS review of the whole pipeline.
