# ADR 0004: First Lock Model is Repository-Scoped and Exclusive

## Status

Accepted for future apply design.

## Context

Concurrent apply attempts can race and corrupt repository state. Per-agent locks look attractive but may miss shared files, policies, schemas, or governance records.

## Decision

The first future apply implementation must use one repository-scoped exclusive lock.

Narrower lock scopes may be considered only after the repository-wide path is proven safe.

## Consequences

- Lock records require repository scope and exclusive mode.
- A future apply command must acquire exactly one effective lock before mutation.
- Stale lock release must require manual review to preserve forensic evidence.
