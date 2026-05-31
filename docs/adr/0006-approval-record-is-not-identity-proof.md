# ADR 0006: Approval Records Are Not Identity Proofs

## Status

Accepted.

## Context

Approval records are YAML governance records stored in the repository. They can bind an approver string to a change ID and diff hash, but they do not cryptographically prove who approved.

## Decision

Approval records are review evidence, not authenticated identity proofs.

Future mutation authority must require an authenticated approval model or equivalent GitHub-reviewed enforcement, not merely the presence of YAML approval records.

## Consequences

- Approval records may satisfy current non-mutating verification thresholds.
- Approval records do not authorize apply.
- Future apply design must revisit authenticated approval identity.
