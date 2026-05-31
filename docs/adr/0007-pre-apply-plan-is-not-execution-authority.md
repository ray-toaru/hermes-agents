# ADR 0007: Pre-Apply Plans and Lock Records Are Not Execution Authority

## Status

Accepted.

## Context

The project now has pre-apply plan generation and apply-lock validation. These records are useful to design and validate future mutation gates.

A future contributor could mistakenly treat these records as permission to apply changes.

## Decision

A valid pre-apply plan or apply-lock record is evidence only. It does not authorize mutation.

Current plan and lock records require `mutation_enabled: false`; current checkers remain non-mutating.

## Consequences

- Future apply must be a separate implementation with explicit lock acquisition, rollback, mutation, post-apply validation, and audit.
- Plan generation and lock validation must remain safe to run in CI.
- Any PR that treats plan/lock validity as apply authorization violates this ADR.
