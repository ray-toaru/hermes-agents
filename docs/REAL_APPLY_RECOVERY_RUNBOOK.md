# Real Apply Recovery Runbook

Status: **design-only**. This document does not implement, enable, or authorize rollback, lock release, or real apply.

## Purpose

Define the future manual and automated recovery rules for a production real apply pipeline. The runbook is conservative: unknown state preserves locks and requires manual review.

## Recovery Principles

1. Preserve evidence before attempting repair.
2. Preserve or mark locks on uncertainty.
3. Never release a lock solely because time elapsed.
4. Never retry mutation without manual review after a partial or unknown outcome.
5. Never execute rollback unless rollback preconditions are proven.
6. Always validate after rollback before any future lock release.
7. Record both failed and successful recovery attempts.

## Recovery Inputs

A future recovery command must require:

- change ID;
- production lock evidence;
- rollback point evidence;
- audit-start evidence, if mutation may have started;
- same-same-sandbox post-apply validation evidence, if available;
- current repository head;
- current target profile hash;
- operator identity;
- manual review reference for non-trivial recovery.

## Failure Classes

| Failure class | Mutation may have occurred? | Required action |
| --- | --- | --- |
| pre-approval failure | No | Do not acquire lock; no recovery required. |
| readiness failure | No | Do not acquire lock; no recovery required. |
| lock acquisition failure | No | Preserve existing lock state; manual review if stale or recovery-required. |
| rollback point failure | No | Preserve lock if acquired; mark recovery-required if lock ownership is uncertain. |
| audit-start failure | No | Preserve lock; manual review before retry. |
| mutation command failure | Maybe | Preserve lock; compare pre/post hashes; require manual review. |
| mutation timeout | Unknown | Preserve lock; mark unknown state; no automatic rollback. |
| post-apply validation failure | Yes | Preserve lock; evaluate rollback preconditions. |
| audit-completion failure | Yes or unknown | Preserve lock; write emergency evidence if possible; manual review. |
| rollback failure | Unknown | Preserve lock; escalate manual recovery. |
| validation after rollback failure | Unknown | Preserve lock; manual recovery required. |

## Rollback Preconditions

A future rollback execution may run only when all are true:

- production lock belongs to the same change and remains active;
- rollback point hash and pre-head are verified;
- current changed paths are limited to the target profile scope;
- no unrelated worktree changes exist;
- audit-start evidence exists if mutation may have started;
- rollback command is allowlisted, argv-only, non-shell, and timeout-bound;
- manual approval exists for rollback unless the implementation slice proves a safe automatic rollback subset.

If any precondition is unknown, rollback must not run automatically.

## Lock Release Rules

A production lock may be released only when:

- the real apply succeeded;
- post-apply validation succeeded;
- production completion audit was written;
- no recovery-required flag exists;
- current repository head and target profile hash match the completion audit;
- the lock release action itself is audited.

A production lock must not be released when:

- mutation state is unknown;
- validation failed;
- audit failed;
- rollback was attempted and not validated;
- stale timeout elapsed without manual recovery;
- an operator wants to unblock another apply but evidence is incomplete.

## Recovery State Machine

```text
failure_detected
  -> classify_failure
  -> preserve_or_mark_lock
  -> collect_current_state
  -> decide_recovery_path
  -> manual_review_required
```

Known safe no-mutation failures may end at:

```text
failed_closed_no_mutation
```

Post-mutation or unknown failures must end at:

```text
recovery_required_lock_preserved
```

Only after verified rollback and validation may the state become:

```text
recovered_pending_manual_lock_release
```

## Operator Checklist

Before any manual recovery action, an operator must confirm:

- evidence hashes match;
- change ID and agent match all records;
- lock owner and repository head are understood;
- no secret or runtime files were read or changed;
- changed paths are restricted to the target profile;
- rollback preconditions are satisfied or explicitly not used;
- the next action is recorded before execution.

## Emergency Evidence

If normal audit writing fails, a future implementation should write emergency evidence to a reviewed recovery location. Emergency evidence must still be schema-validated later and must not be used to authorize lock release by itself.

## Boundaries

This runbook is not an implementation. It does not release locks, execute rollback, mutate profiles, read secrets, mutate runtime state, or authorize business orchestration.
