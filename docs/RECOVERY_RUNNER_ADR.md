# Recovery Runner ADR

Status: deferred.

This ADR records prerequisites for any future recovery runner. Current implementation remains dry-run only: no command execution, state change, guard release, or runtime access is allowed.

Required before reconsideration:

- reviewed command catalog binding
- rollback point binding
- audit closeout binding
- post-command validation binding
- manual review before any runnable implementation
