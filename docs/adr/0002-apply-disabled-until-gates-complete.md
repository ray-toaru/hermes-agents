# ADR 0002: Apply Remains Disabled Until the Full Gate Set Exists

## Status

Accepted.

## Context

The project is moving toward a future ability to apply reviewed profile changes. Mutation is high risk because it can change managed agents, create partial state, lose rollback evidence, or be mistaken for business execution authority.

The repository already has read-only and governance-write building blocks: change records, approval records, dry-run verification, pre-apply plans, and apply-lock validation.

## Decision

`apply` remains disabled and non-zero until the full apply pipeline exists and has converged through review.

Required future gates include policy validation, schema validation, approval threshold validation, rejection blocking, diff hash binding, path scope checks, clean-state checks, patch applicability, pre-apply plan validation, operator confirmation, repository-scoped exclusive lock acquisition, rollback point creation, mutation, post-apply validation, audit record capture, and lock release or preserved failure evidence.

## Consequences

- A valid approval record does not authorize mutation.
- A valid pre-apply plan does not authorize mutation.
- A valid apply-lock record does not acquire a lock.
- Future apply must be introduced incrementally, not as a single large mutation PR.
