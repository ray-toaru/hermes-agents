# Future Apply Pipeline Design

## Status

Future design only. `apply` remains intentionally unimplemented.

## Required phases before mutation

A future apply implementation must execute these phases in order and fail closed on any error:

1. Load policy and schemas.
2. Verify `changes/<change_id>/proposal.yaml` and `diff.patch`.
3. Verify all approval records and reject if any valid rejection exists.
4. Require sufficient approvals for the risk level.
5. Recompute and compare diff SHA-256.
6. Validate diff path scope under `profiles/<agent>/`.
7. Require clean Git state for the target profile.
8. Require patch applicability immediately before mutation.
9. Load and validate `pre-apply-plan.yaml`.
10. Bind plan fields to the change record.
11. Acquire a repository-scoped exclusive lock.
12. Record pre-apply HEAD.
13. Apply the patch.
14. Run post-apply validation.
15. Record audit data.
16. Release or mark lock based on outcome.
17. Provide Git-first rollback evidence if any mutation partially fails.

## Minimum implementation requirements

- The apply command must not read real secret values.
- The apply command must not mutate runtime state.
- The apply command must not execute business actions.
- The apply command must not bypass Hermes runtime provider or tool registry semantics.
- The apply command must refuse if a lock is active.
- The apply command must refuse if `pre_apply_plan_sha256` does not match the actual plan file.
- The apply command must refuse if HEAD has changed since planning unless a new plan is generated.
- The apply command must produce an audit record with stdout/stderr, exit codes, and Git HEAD before/after.

## Current blockers

Before `apply` can be considered, the repository still needs:

- a reviewed lock acquisition command;
- a reviewed lock release/recovery command;
- an audit record schema and validator;
- a rollback record schema and validator;
- tests for interruption and partial failure behavior;
- documented operator confirmation semantics;
- a final review that confirms no runtime/secret/business boundaries are crossed.

## Non-goal

This document does not authorize implementation of mutation. It only defines prerequisites for a future design review.
