# Production Lock Path Dry-Run Adapter

Status: read-only adapter.

`collect-production-lock-readiness-source` computes the expected production lock identity for a change and commit, reads at most one repository-relative lock record, and emits the existing production lock readiness source contract.

The adapter never creates, updates, acquires, or releases a lock. Missing records are reported as `not_acquired`. Mismatched commit, owner, lock id, or unsafe lock-root input fails closed.
