# ADR 0008: Mutation Requires Authenticated Approval Verification

## Status

Accepted for future apply design.

## Context

Current approval records and approval identity evidence are repository governance evidence. They bind approver strings, change IDs, diff hashes, and external references, but they do not perform live authentication or prove current reviewer authority.

Future mutation would change managed agent profiles. Treating YAML approval records or evidence URLs as final authority would allow stale, forged, copied, or de-authorized approvals to authorize mutation.

## Decision

A future mutation command must verify approval authority through one of these reviewed mechanisms before mutation:

1. live GitHub review evidence from the repository hosting the change;
2. cryptographically signed approval attestations whose trust roots are explicitly configured and reviewed;
3. an equivalent repository-enforced mechanism documented in a later ADR.

The future verifier must bind authenticated approval evidence to:

- repository identity;
- pull request or change identifier;
- exact `change_id`;
- exact `diff_sha256`;
- approver identity;
- approval decision;
- time of approval;
- required policy threshold.

The verifier must fail closed if evidence is missing, stale, unverifiable, permission-inconsistent, hash-mismatched, rejected, duplicated, or not bound to the current diff.

Current `approval-identity.yaml` evidence remains useful input, but it is not live authentication authority.

## Consequences

- Future apply cannot rely only on YAML approval records.
- Future apply cannot rely only on evidence URLs stored in the repository.
- Review threshold calculation must use authenticated identities, not only strings from files.
- If GitHub API access is unavailable or inconclusive, mutation must fail closed.
- This ADR does not implement live approval verification.
