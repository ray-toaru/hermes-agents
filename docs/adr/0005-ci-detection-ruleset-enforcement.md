# ADR 0005: CI is Detection; Ruleset is Enforcement

## Status

Accepted.

## Context

Repository scripts can check CODEOWNERS, schemas, policies, examples, tests, and forbidden files. But CI cannot force a maintainer to use PR review or prevent a direct push by itself.

GitHub rulesets or branch protection provide the actual merge enforcement layer.

## Decision

Treat CI as deterministic detection and GitHub rulesets / branch protection as enforcement.

Repository documentation must not claim CI guardrails are equivalent to protected branch or ruleset enforcement.

## Consequences

- Ruleset evidence should be recorded when settings change.
- Required status check names must match real CI jobs.
- CODEOWNERS and CI guards support review, but ruleset configuration is required to enforce the workflow.
