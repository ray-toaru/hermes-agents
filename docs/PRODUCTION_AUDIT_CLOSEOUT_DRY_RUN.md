# Production Audit Closeout Dry-Run

Status: stdout-only adapter.

`build-production-audit-closeout-dry-run` builds success or failure closeout candidates using the existing production audit closeout schema. It validates the candidate before printing it to stdout.

The adapter does not write audit records, does not update an audit store, does not release locks, and does not authorize apply. Failure outcomes require a failure reference and keep the same conservative guard fields as success outcomes.
