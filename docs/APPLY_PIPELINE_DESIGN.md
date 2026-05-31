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
  -> strict clean-state and patch applicability verification
  -> pre-apply plan generation
  -> lock acquisition record generation
  -> future real lock acquisition
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
| Git clean check | implemented dry-run | no | Optional for base verify; required by plan generation and future apply. |
| Patch applicability | implemented dry-run | no | Optional for base verify; required by plan generation and future apply; uses `git apply --check`. |
| Apply-ready verification | implemented strict gate | no | `changes verify --check-git-clean --check-patch-applicable`. |
| Pre-apply plan schema | implemented | no | `mutation_enabled: false`. |
| Pre-apply plan generation | implemented governance write | governance record only | Writes canonical `changes/<id>/pre-apply-plan.yaml` only after apply-ready verification. |
| Apply-lock schema/checker | implemented read-only | no | Validates lock contract only. |
| Apply-lock record generation | implemented governance write | governance record only | Writes canonical `changes/<id>/apply-lock.yaml` after valid plan and no blocking lock. |
| Real lock acquisition | not implemented | future | Future runtime/concurrency primitive; must be reviewed separately. |
| Rollback point creation | not implemented | future | Must record pre-apply Git HEAD. |
| Patch mutation | disabled | future | Must be separate from dry-run. |
| Runtime-adjacent health/deployment/repair management | not implemented | future | Requires separate design; cannot bypass Hermes runtime or become business orchestration. |
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
13. Apply-lock governance record is created and bound to the actual plan bytes.
14. A future real repository-scoped exclusive lock is acquired.
15. Rollback point is recorded.
16. Patch is applied only to expected profile paths.
17. Post-apply profile validation succeeds.
18. Audit record is written.
19. Lock is released on success or preserved with failure evidence on failure.

## Prohibited Shortcuts

A future implementation must not:

- treat approval records as identity proof;
- treat plan generation as apply authorization;
- treat lock validation or lock-record generation as mutation authority;
- skip Git clean checks because a plan exists;
- skip patch applicability because it passed earlier;
- apply without rollback point;
- apply without audit record;
- delete stale lock evidence automatically;
- mutate runtime state or execute business actions;
- introduce runtime-adjacent management by silently expanding validators, plan generation, or lock validation.

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

Runtime-adjacent health, deployment, or repair management should be designed as a separate track unless it is strictly required by the apply pipeline. It must begin read-only where possible and must not become business task routing.
