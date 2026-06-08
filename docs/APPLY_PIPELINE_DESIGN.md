# Apply Pipeline Design

## Status

This is the project-level design for a future apply pipeline. It is not an implementation plan for enabling `apply` immediately.

Current status: `apply` is disabled and must remain non-zero.

As of v2.8, detailed design-only real apply assets live in `docs/REAL_APPLY_PIPELINE_DESIGN.md`, `docs/REAL_APPLY_THREAT_MODEL.md`, and `docs/REAL_APPLY_RECOVERY_RUNBOOK.md`. This document remains the project-level baseline; the v2.8 documents refine the future production pipeline without implementing it.

The repository has several implemented read-only evidence layers, sandbox-only evidence layers, and constrained governance-record generators. These records improve reviewability, but none of them authorize mutation.

## Pipeline Summary

A future apply must be a linear, fail-closed pipeline:

```text
policy/schema validation
  -> change verification
  -> approval verification
  -> strict clean-state and patch applicability verification
  -> pre-apply plan generation
  -> apply-lock record generation
  -> apply-lock analysis
  -> apply-readiness evidence report
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
| Policy/schema validation | implemented | no | Validates policy, schema, profile metadata. Invalid policy fails closed. |
| Change verification | implemented | no | Verifies proposal, diff, approvals, path scope, hashes. |
| Git clean check | implemented dry-run | no | Optional for base verify; required by plan generation and future apply. |
| Patch applicability | implemented dry-run | no | Optional for base verify; required by plan generation and future apply; uses `git apply --check`. |
| Apply-ready verification | implemented strict gate | no | `changes verify --check-git-clean --check-patch-applicable`. |
| Pre-apply plan schema | implemented | no | `mutation_enabled: false`. |
| Pre-apply plan generation | implemented governance write | governance record only | Writes canonical `changes/<id>/pre-apply-plan.yaml` only after apply-ready verification. |
| Apply-lock schema/checker | implemented read-only | no | Validates lock contract only. |
| Apply-lock record generation | implemented governance write | governance record only | Writes canonical `changes/<id>/apply-lock.yaml` after valid plan and no blocking lock evidence. |
| Apply-lock analysis | implemented read-only | no | Reports blocking lock evidence to stdout only; does not acquire/release/repair locks or write reports. |
| Apply-readiness report | implemented read-only | no | Aggregates evidence gates; `apply_authorized: false` is mandatory. |
| Rollback point schema/checker | implemented read-only | no | Validates rollback-point evidence only; does not create rollback points or execute rollback. |
| Audit record schema/checker | implemented read-only | no | Validates audit evidence only; command evidence is not execution authority. |
| Approval identity schema/checker | implemented read-only | no | Validates identity evidence references only; does not authenticate live identity. |
| Post-apply validation schema/checker | implemented read-only | no | Validates post-apply validation evidence only; does not execute apply or rollback. |
| Real lock acquisition | not implemented | future | Future runtime/concurrency primitive; must be reviewed separately. |
| Rollback point creation | not implemented | future | Must record pre-apply Git HEAD and prove referenced commits exist. |
| Patch mutation | disabled | future | Must be separate from dry-run. |
| Runtime-adjacent health/deployment/repair management | not implemented | future | Requires separate design; cannot bypass Hermes runtime or become business orchestration. |
| Lock release/recovery | not implemented | future | Must preserve failure evidence when needed. |

## Required Future Apply Gates

A future mutation command must fail closed unless all are true:

1. Repository ruleset / PR flow has already accepted the change that introduced the apply implementation.
2. Policy validates.
3. Schemas validate.
4. Change proposal validates.
5. `diff.patch` hash matches proposal.
6. Approval records validate and meet policy threshold.
7. Approval identity is verified against live or cryptographically signed evidence, not only YAML references.
8. No valid rejection is present.
9. All paths remain under the managed profile scope.
10. Target profile worktree is clean.
11. Patch applicability succeeds immediately before mutation.
12. Pre-apply plan exists, validates, and binds to current base commit and diff evidence.
13. Operator confirms the plan.
14. Apply-lock governance record is created and bound to the actual plan bytes.
15. Apply-lock analysis shows no blocking active, expired-active, stale, recovery-required, or invalid lock evidence.
16. Apply-readiness evidence report validates and still states `apply_authorized: false`; authorization must come from the future apply command's own reviewed gates, not from the report.
17. A future real repository-scoped exclusive lock is acquired atomically.
18. Rollback point is recorded and referenced Git objects are proven present.
19. Patch is applied only to expected profile paths.
20. Post-apply profile validation succeeds.
21. Audit record is written from structured evidence, not trusted shell-like strings.
22. Lock is released on success or preserved with failure evidence on failure.

## Prohibited Shortcuts

A future implementation must not:

- treat approval records as identity proof;
- treat approval identity YAML or URLs as live authentication proof;
- treat plan generation as apply authorization;
- treat lock validation, lock-record generation, lock analysis, or readiness reports as mutation authority;
- skip Git clean checks because a plan exists;
- skip patch applicability because it passed earlier;
- apply without a real acquired lock;
- apply without rollback point creation;
- apply without audit record capture;
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

1. project-level docs and roadmap kept current with implementation state;
2. authenticated approval identity design using live GitHub or cryptographically signed evidence;
3. structured command evidence design to replace shell-like command strings for execution-adjacent records;
4. repository-wide clean-state policy for future mutation;
5. real lock acquisition/release design with read-only tests first;
6. rollback point creation design, including Git object existence checks;
7. sandboxed apply dry-run integration tests;
8. post-apply validation execution design;
9. audit capture design for mutation and recovery;
10. mutation implementation behind explicit non-default command;
11. failure recovery tests;
12. ruleset and CODEOWNERS review of the whole pipeline.

Runtime-adjacent health, deployment, or repair management should be designed as a separate track unless it is strictly required by the apply pipeline. It must begin read-only where possible and must not become business task routing.
