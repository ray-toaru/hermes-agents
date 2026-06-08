# Roadmap

## Current Position

As of v2.9, Hermes AgentOps Manager is a repository governance and evidence-validation control plane with an integrated sandbox-only mutation evidence pipeline, sandbox mutation audit capture, sandbox recovery simulation, a structured real-apply readiness review, a design-only real apply package, a design/prototype-only production lock lifecycle contract, and grouped CI test execution for the current sandbox-heavy suite.

Implemented capabilities are intentionally limited to:

- profile, policy, schema, and change validation;
- approval and diff hash binding;
- strict dry-run gates for clean worktree and patch applicability;
- canonical pre-apply plan governance-record generation;
- canonical apply-lock governance-record generation;
- read-only validators for rollback point, audit record, approval identity, post-apply validation, apply-lock analysis, and apply-readiness reports;
- sandboxed apply dry-run that applies patches only inside temporary sandboxes and leaves source profiles unchanged;
- read-only signed approval attestation verification for authenticated approval evidence;
- integrated sandbox-only mutation pipeline that composes authenticated approval, readiness, temporary lock, rollback point, and post-apply validation evidence without source mutation;
- sandbox mutation audit capture for integrated sandbox success/failure evidence without creating production audit records;
- sandbox recovery simulation for success, failure, and unknown-state outcomes without releasing locks or executing rollback;
- structured P5 real-apply readiness review evidence that permits design-only work while keeping implementation and enablement blocked;
- design-only real apply pipeline, threat model, recovery runbook, and machine-checkable design contract evidence that still keeps `apply` disabled;
- design/prototype-only production lock lifecycle contract evidence that defines release eligibility and lock preservation rules without implementing release.

`apply` remains disabled. Production lock release, profile mutation, rollback execution, runtime management, secret reading, and business orchestration remain out of scope.

## Near-Term Priorities

### P0: Keep project-level documentation current

Every behavior-changing PR must update project-level docs when it changes implementation status, safety invariants, lifecycle states, or future-vs-current boundaries.


### P0.5: Maintainability, fail-closed subprocess hardening, and test harness stability

Status: implemented for the current subprocess-heavy scripts and test harness. See `docs/v2.1-maintainability-and-timeouts.md`, `docs/v2.2-test-harness-and-internal-dispatch.md`, and `docs/IMPLEMENTATION_MATRIX.md`.

The current slices add a shared script helper, centralize argv-only subprocess execution with hard timeouts, provide in-process dispatch for reviewed repository-internal Python entry points, and reduce repeated child Python cold starts in tests. This does not enable real apply. Remaining validator helper deduplication should be handled as a separate mechanical cleanup.

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

1. authenticated approval verification against signed evidence is implemented read-only; live GitHub remains optional and fail-closed;
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

### P3.5: Integrated sandbox mutation pipeline

Status: implemented sandbox-only in v2.4. See `docs/v2.4-integrated-sandbox-mutation-pipeline.md`.

The pipeline composes authenticated approval verification, readiness, temporary lock acquisition, rollback point evidence, and post-apply validation inside a temporary workspace only. Sandbox mutation audit capture was added in v2.5 and sandbox recovery simulation was added in v2.6. Real apply remains disabled.

### P3.6: Sandbox mutation audit capture

Status: implemented sandbox-only in v2.5. See `docs/v2.5-sandbox-mutation-audit-capture.md`.

Sandbox mutation audit capture consumes integrated sandbox run evidence and emits read-only audit records for success and failure paths. It writes to stdout only, does not write production audit records, and cannot authorize apply.

### P3.7: Sandbox recovery simulation

Status: implemented sandbox-only in v2.6. See `docs/v2.6-sandbox-recovery-simulation.md`.

Recovery simulation consumes sandbox mutation audit evidence and records fail-closed recovery decisions. It does not release locks, execute rollback, retry, authorize apply, or mutate source profiles. Unknown states fail closed.

### P4: Sandboxed apply dry-run only

Status: implemented as a standalone sandbox dry-run command. It does not enable `hermes-agentops apply`.

Sandboxed dry-run may create temporary repositories and apply candidate patches inside those temporary repositories only. It must not mutate managed repository profiles or runtime state.

### P4.5: Real apply readiness review v2

Status: implemented in v2.7. See `docs/P5_REAL_APPLY_READINESS_REVIEW_V2.md`, `docs/v2.7-real-apply-readiness-review.md`, and `docs/examples/p5-real-apply-readiness-review-v2.yaml`.

The review concludes that the project is ready for a design-only real apply PR, but not ready to implement or enable real apply. `apply` remains disabled.


### P4.6: Real apply design package

Status: implemented design-only in v2.8. See `docs/REAL_APPLY_PIPELINE_DESIGN.md`, `docs/REAL_APPLY_THREAT_MODEL.md`, `docs/REAL_APPLY_RECOVERY_RUNBOOK.md`, `docs/v2.8-real-apply-design.md`, and `docs/examples/real-apply-design-contract.yaml`.

The design package defines the future production pipeline, threat model, and recovery runbook, and validates that the design remains non-authorizing. It does not implement mutation, does not add feature flags, and verifies that `hermes-agentops apply` still fails closed.

### P4.7: Production lock lifecycle contract

Status: implemented design/prototype-only in v2.9. See `docs/PRODUCTION_LOCK_LIFECYCLE_DESIGN.md`, `docs/v2.9-production-lock-lifecycle.md`, and `docs/examples/production-apply-lock-lifecycle.yaml`.

The contract defines future production lock states, release eligibility, preservation rules, and required evidence bindings. It does not implement real apply, does not release production locks, and verifies that `apply` remains disabled.

### P5: Explicit non-default mutation command

Status: not ready to implement. Signed approval attestation verification, integrated sandbox mutation, sandbox audit, sandbox recovery simulation, and P5 review evidence are now implemented, but real mutation remains blocked. See `docs/P5_MUTATION_READINESS_REVIEW.md` and `docs/P5_REAL_APPLY_READINESS_REVIEW_V2.md`.

A real mutation command remains blocked until the ADR 0008-0011 prerequisites are implemented and validated as separate fail-closed slices.

The design-only real apply package and production lock lifecycle contract now exist. The next safe steps are prerequisite production implementation slices that still keep `apply` disabled: disabled lock acquire/preserve skeleton, rollback execution design/validation, production audit capture, production post-apply validation, and production recovery state machine. Only after those slices and canary evidence converge, consider an explicit non-default mutation command. It must be separately reviewed and remain fail-closed behind all gates.

## Always Out of Scope for This Track

- business task routing;
- trading or research execution decisions;
- bypassing Hermes provider resolution or tool registry;
- reading real secret values;
- mutating runtime sessions, logs, state databases, gateway, cron, containers, or systemd without a separate runtime-adjacent design.
