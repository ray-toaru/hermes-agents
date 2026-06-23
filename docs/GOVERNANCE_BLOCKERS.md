# Governance Blockers

The governance blocker taxonomy standardizes machine-readable reasons emitted by read-only preflight reports.

The taxonomy is not authority to resolve a blocker. It maps each blocker code to a review category and the current resolution class.

Current resolution classes:

- `fix_input`: repair malformed or incomplete local evidence.
- `manual_review`: human review is required before any later-stage decision.
- `separate_adr`: a new ADR/policy is required before the capability can advance.
- `defer_next_stage`: the project remains in the current governance stage.

Boundary: blocker taxonomy does not authorize apply, mutation, lock release, audit writes, command execution, runtime access, or protected value reads.
