# Roadmap

## Current Position

As of v2.0, Hermes AgentOps Manager is a repository governance and evidence-validation control plane.

Implemented capabilities are intentionally limited to:

- profile, policy, schema, and change validation;
- approval and diff hash binding;
- strict dry-run gates for clean worktree and patch applicability;
- canonical pre-apply plan governance-record generation;
- canonical apply-lock governance-record generation;
- read-only validators for rollback point, audit record, approval identity, post-apply validation, apply-lock analysis, and apply-readiness reports;
- sandboxed apply dry-run that applies patches only inside temporary sandboxes and leaves source profiles unchanged.

`apply` remains disabled. Real locks, profile mutation, rollback execution, runtime management, secret reading, and business orchestration remain out of scope.

## Near-Term Priorities

### P0: Keep project-level documentation current

Every behavior-changing PR must update project-level docs when it changes implementation status, safety invariants, lifecycle states, or future-vs-current boundaries.

### P1: Review and harden evidence semantics

Status: implemented for the current evidence records.

Before adding mutation, review existing records for ambiguity:

- readiness reports must never imply apply authorization;
- approval identity evidence must not be mistaken for live authentication;
- audit command strings must not become execution authority;
- lock analysis must not become lock release authority.

### P2: Add read-only integration tests

Status: implemented for the current evidence chain.

Create end-to-end tests that assemble a full evidence chain in a temporary repository without mutating managed profiles:

1. change proposal;
2. approval records;
3. apply-ready verification;
4. pre-apply plan;
5. apply-lock governance record;
6. apply-lock analysis;
7. readiness report.

The current chain is expected to stop before mutation. If an active governance lock is present, readiness may validate as `blocked`, not complete.

### P3: Design future mutation prerequisites as ADRs

Status: baseline ADRs added for future mutation prerequisites.

Do not implement mutation until these are reviewed:

1. authenticated approval verification against live GitHub or signed evidence;
2. structured command evidence for execution-adjacent records;
3. real repository lock acquisition/release, TTL, and stale recovery;
4. rollback point creation and Git object existence checks;
5. post-apply validation execution;
6. audit capture for mutation and recovery;
7. failure recovery and retry rules.

Baseline ADRs:

- `docs/adr/0008-authenticated-approval-required-for-mutation.md`;
- `docs/adr/0009-structured-command-evidence-before-execution.md`;
- `docs/adr/0010-real-lock-and-rollback-point-before-mutation.md`;
- `docs/adr/0011-post-apply-validation-audit-and-recovery.md`.

### P4: Sandboxed apply dry-run only

Status: implemented as a standalone sandbox dry-run command. It does not enable `hermes-agentops apply`.

Sandboxed dry-run may create temporary repositories and apply candidate patches inside those temporary repositories only. It must not mutate managed repository profiles or runtime state.

### P5: Explicit non-default mutation command

Status: not ready to implement. See `docs/P5_MUTATION_READINESS_REVIEW.md`.

A real mutation command remains blocked until the ADR 0008-0011 prerequisites are implemented and validated as separate fail-closed slices.

Only after those prerequisite slices converge, consider an explicit non-default mutation command. It must be separately reviewed and remain fail-closed behind all gates.

## Always Out of Scope for This Track

- business task routing;
- trading or research execution decisions;
- bypassing Hermes provider resolution or tool registry;
- reading real secret values;
- mutating runtime sessions, logs, state databases, gateway, cron, containers, or systemd without a separate runtime-adjacent design.
