# Operations and Recovery

## Purpose

This document defines operational handling for CI failures, ruleset issues, stale PRs, invalid records, and future apply recovery.

## CI Failure Handling

Do not guess.

Required process:

1. Identify PR head SHA.
2. Fetch workflow run, job, and failing step.
3. Read logs before patching.
4. Patch the root cause, not just the failing assertion.
5. If logs are truncated, add diagnostics or reproduce with the same command locally before changing behavior.
6. Keep production behavior unchanged when the failure is test-environment-only.
7. Document root cause in PR comments or body when non-obvious.

## Ruleset / Branch Protection Handling

Ruleset is the enforcement layer for `main`; CI is a detection layer.

When ruleset changes:

1. Export or screenshot settings where feasible.
2. Record evidence in governance docs.
3. Verify the real required status check name. For this repository, the CI job name is `validate`.
4. Avoid requiring non-existent checks.
5. In single-owner mode, avoid self-approval deadlock unless an explicit bypass model is intended.
6. Use a low-risk smoke-test PR after changes.

## Stale PR Handling

A stale PR is one whose branch predates current main and would reintroduce older behavior or duplicate already-merged work.

Handling:

1. Compare the PR's intent with current main.
2. If the work is superseded, comment with the reason.
3. Close without merge.
4. Do not rebase old branches if rebasing would recreate outdated implementation.
5. Preserve audit trail in the PR conversation.

## Invalid Change Records

If `changes verify` fails:

1. Treat the change as untrusted.
2. Do not generate a pre-apply plan.
3. Do not add approvals until structural issues are fixed.
4. Fix policy/schema/hash/path issues first.
5. Re-run verification after each fix.

## Dirty Worktree

If Git clean check fails:

1. Inspect profile-local modifications.
2. Decide whether they belong in a separate proposal.
3. Do not apply or generate a plan over unmanaged changes.
4. Restore or commit through PR before retrying.

## Patch Not Applicable

If patch applicability fails:

1. Treat stored diff as stale relative to current repository state.
2. Recreate the change proposal from current diff.
3. Do not edit `diff.patch` manually without regenerating hash-bound records.
4. Require new approvals if diff hash changes.

## Pre-Apply Plan Mismatch

If a pre-apply plan fails validation or cross-field checks:

1. Delete or supersede the invalid plan through PR review.
2. Re-run `changes verify`.
3. Regenerate the plan.
4. Preserve old invalid evidence where useful for audit.

## Apply Lock Problems

Current system validates lock records read-only. It does not acquire or release locks.

If a lock record fails validation:

1. Do not treat it as a valid concurrency guard.
2. Check change ID, agent, base commit, plan hash, timestamp ordering, lock ID, and stale-lock policy.
3. If `--require-plan-file` is used, verify the canonical pre-apply plan exists and hash matches.

Future stale-lock recovery must require manual inspection before release.

## Secret or Runtime File Detected

If CI detects secret/runtime files:

1. Stop the PR.
2. Remove the file from the branch.
3. Rotate any exposed secret if real values were committed.
4. Add/update `.gitignore` or guard tests if the pattern was missing.
5. Do not continue until CI passes.

## Future Partial Apply Failure

Not implemented. When future apply exists, partial failure must:

1. stop all further mutation;
2. preserve lock evidence;
3. preserve stdout/stderr and exit codes;
4. restore from rollback point where possible;
5. run post-rollback validation;
6. record audit evidence;
7. require manual review before retry.

## Recovery Principle

Prefer evidence preservation over automatic cleanup. Automatic deletion of stale locks, failed plans, or partial audit evidence can erase the facts needed for safe recovery.
