# Project Status

## Current Baseline

Hermes AgentOps Manager is a repository-backed governance and evidence-validation control plane for managed Hermes agent profiles. It manages declarations, policies, schemas, proposals, approval evidence, readiness evidence, and non-authorizing governance records.

It is not a Hermes runtime, gateway, cron manager, business-work scheduler, deployment runner, or secret reader. `hermes-agentops apply` remains hard-disabled and must keep returning a non-zero blocked result until separately reviewed mutation gates are implemented.

The current capability baseline is represented by:

- `docs/IMPLEMENTATION_MATRIX.md` for compact state and remaining blockers;
- `docs/examples/capability-ledger.yaml` for per-capability artifact paths;
- `docs/ROADMAP.md` for ordered next slices;
- `docs/SAFETY_INVARIANTS.md` for non-negotiable boundaries.

## Implemented Capability Classes

### Governance and Validation

Implemented:

- profile, inventory, policy, and schema validation;
- change proposal and approval-record verification;
- diff hash binding and profile path-scope checks;
- CODEOWNERS and repository-governance baseline checks;
- blocked `apply` entrypoint and structured blocked-report scaffolding.

Boundary: validation evidence does not authorize mutation.

### Read-Only Evidence

Implemented:

- pre-apply plan validation and generation as governance evidence;
- apply-lock governance record validation;
- rollback point, audit record, approval identity, post-apply validation, apply-lock analysis, apply-readiness, authenticated approval, live GitHub approval source, production lock readiness source, governance preflight, and governance blocker evidence checks.

Boundary: read-only evidence may explain readiness or blockers, but it must not acquire locks, release locks, write production audit records, execute rollback, or mutate profiles.

### Sandbox-Only Evidence

Implemented:

- sandbox apply dry-run inside temporary workspaces;
- integrated sandbox mutation evidence pipeline;
- sandbox mutation audit capture;
- sandbox recovery simulation;
- structured command sandbox validation.

Boundary: sandbox commands may mutate only temporary repositories or temporary workspaces created for the run. They must not mutate managed repository profiles or runtime state.

### Design/Prototype-Only Evidence

Implemented:

- real apply pipeline design package;
- production lock lifecycle contract;
- disabled production lock skeleton evidence;
- production audit-start contract;
- audit store, guard write path, recovery runner, runtime-adjacent policy, and staged readiness decision records.

Boundary: design/prototype artifacts define contracts for later review. They do not enable production writes.

## Deferred or Blocked Capability Classes

Still blocked before any real managed-state mutation:

1. integrated production lock acquisition/release and failure preservation;
2. production audit store writes for start, success, failure, closeout, and recovery outcomes;
3. rollback execution and post-run validation;
4. production post-apply validation wired to mutation outcomes;
5. runtime-adjacent reads or writes involving sessions, logs, state databases, gateway, cron, containers, systemd, or protected values;
6. any non-default real mutation command.

Legacy text assertions around blocked apply output should continue migrating to schema-based structured blocked-report assertions.

## Next Safe Implementation Slices

The next safe slices remain non-mutating:

1. keep project status, implementation matrix, capability ledger, roadmap, and CI coverage map in sync;
2. migrate remaining legacy blocked-output assertions to structured schema assertions;
3. harden disabled production lock acquire/preserve skeleton without writing production locks;
4. implement production audit capture only as contract/stdout/read-only dry-run evidence until audit-store design converges;
5. harden post-apply validation contracts and recovery decisions without executing rollback or mutation.

## Review Rule

A PR may claim a capability is implemented only when it names:

- evidence artifacts;
- tests or explicit manual verification commands;
- current boundary class: implemented, read-only, sandbox-only, design/prototype-only, deferred, or blocked;
- rollback plan;
- attack/review notes for safety-sensitive changes.
