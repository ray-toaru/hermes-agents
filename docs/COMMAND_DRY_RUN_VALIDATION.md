# Command Dry-Run Validation

Status: blocked-output harness.

`build-command-dry-run-validation` reads a command catalog and emits a `post-command-validation` record for a selected entry. The emitted record is always blocked, with `state_changed: false`, `guard_released: false`, and `followup_required: true`.

The harness does not execute catalog entries, dispatch commands, change managed state, release guards, or authorize apply.
