# Live GitHub Approval Verifier Design

Status: design-only and fail-closed.

The current authenticated approval verifier supports local fixture records and signed local attestations. The `live_github` mode intentionally returns non-zero until a separately reviewed integration binds GitHub review data to the existing authenticated approval evidence contract.

## Required bindings

A future read-only implementation must bind all of the following before it can emit verified evidence:

- repository full name and default branch
- pull request number and head SHA
- reviewed diff hash
- reviewer identity
- reviewer permission at review time
- review decision and timestamp
- rejection state
- verification timestamp

## Non-goals

This design does not enable apply, mutate profiles, read secret values, mutate runtime state, acquire or release locks, write production audit records, execute rollback, or perform business orchestration.

## Current behavior

`verify-authenticated-approval --mode live_github` must fail closed and emit no evidence. This preserves the existing invariant that authenticated approval evidence is not execution authority.

## Next implementation slice

The next slice may add a read-only adapter interface and local fixtures for GitHub API response shapes. That slice must still keep `live_github` fail-closed unless repository, review, permission, rejection, and diff bindings are all present and validated.
