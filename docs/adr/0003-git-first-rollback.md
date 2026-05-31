# ADR 0003: Use a Git-First Rollback Model

## Status

Accepted for future apply design.

## Context

Managed profile declarations are repository files. A future apply path must be able to recover from failed mutation or failed post-apply validation.

Runtime state, logs, sessions, secrets, and containers are outside the current AgentOps mutation scope.

## Decision

Future apply must record the pre-apply Git HEAD and use a Git-first rollback model for repository-managed files.

Rollback evidence must include before/after Git HEAD, commands, outputs, exit codes, and validation results.

## Consequences

- Future apply cannot start without a rollback point.
- Recovery must preserve evidence before cleanup.
- Git rollback does not cover external runtime state; current AgentOps must not mutate that state.
