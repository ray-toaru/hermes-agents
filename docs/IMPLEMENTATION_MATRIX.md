# Implementation Matrix

This matrix is a compact governance index. Detailed per-artifact paths are tracked in `docs/examples/capability-ledger.yaml`; this file records the current implementation state and the remaining blockers before any real managed-state change.

## Current Evidence Baseline

| Area | Primary Evidence | Current Status | Boundary |
| --- | --- | --- | --- |
| Repository governance scope | `README.md`, `AGENTS.md`, `docs/ARCHITECTURE.md`, `scripts/hermes-agentops` | Implemented | Governance/control-plane only; no Hermes runtime execution |
| Profile, inventory, policy, and schema validation | `scripts/hermes-agentops validate`, `validate-schemas`, `policy check`, `schemas/*.json`, `policies/global-permissions.yaml` | Implemented | Validation does not grant apply authority |
| Change and approval evidence chain | `scripts/hermes-agentops changes verify`, approval schemas, signed/captured GitHub approval verifiers, GitHub source collector | Read-only implemented | Evidence remains non-authorizing and fail-closed |
| Planning and lock governance records | pre-apply plan, apply-lock records, lock analysis, production lock lifecycle/skeleton/readiness source, lock path dry-run | Governance and read-only adapters implemented | No production lock acquire/release/write path is enabled |
| Audit governance records | audit-start contract, audit closeout contracts, audit closeout dry-run, sandbox audit capture | Contract/stdout/sandbox implemented | No production audit store write pipeline is enabled |
| Command and recovery governance | command catalog, post-command validation, command dry-run validation, recovery runner decision, sandbox recovery simulation | Contract/deferred/sandbox implemented | No command execution or recovery runner is enabled |
| Runtime-adjacent policy | `docs/RUNTIME_ADJACENT_POLICY.md`, runtime-adjacent schema/tests | Policy implemented | Runtime logs, sessions, gateway, containers, cron, and protected values remain out of scope |
| Governance preflight and blocker taxonomy | `scripts/run-governance-preflight`, governance preflight/blocker schemas and tests | Read-only implemented | Emits blocked reports only |
| Apply blocked report path | `scripts/run-apply-blocked-scaffold`, `scripts/run-apply-entrypoint-blocked`, apply blocked report schema/tests | Implemented | Always non-zero; cannot authorize managed-state change |
| Single CLI blocked entrypoint | `scripts/hermes-agentops`, `scripts/hermes-agentops-core`, `tests/test_single_cli_apply_blocked.py` | Hard-disabled entrypoint implemented | `hermes-agentops apply` returns structured blocked output and remains non-zero |
| Readiness reviews | readiness v3-v8 schemas/examples/tests | Deferred reviews implemented | next stage, apply authorization, and real implementation remain disallowed |
| Sandbox-only mutation experiments | sandbox apply dry-run, integrated sandbox mutation, sandbox audit, sandbox recovery simulation | Sandbox-only implemented | Temporary workspace only; not production authority |
| Historical design packages | real apply design, readiness v2, production lock lifecycle design, state safety, closeout/tracking docs | Design/prototype implemented | Design evidence does not enable real mutation |

## Known Gaps Before Any Real Mutation

| Gap | Why It Blocks Mutation | Required Next Evidence |
| --- | --- | --- |
| Integrated real lock lifecycle | Real production lock acquisition and release are not integrated with the hard-disabled apply entrypoint | Separate lock write-path implementation ADR and tests after current deferred gates converge |
| Rollback execution and validation | Rollback point records and command catalog contracts exist, but no reviewed recovery runner is enabled | Separate runner implementation ADR, post-run validation, and failure handling evidence |
| Production mutation audit capture | Production audit records are not written by any real apply pipeline | Audit store implementation ADR and success/failure capture tests |
| Runtime-adjacent operations | Runtime logs, sessions, gateway, containers, cron, and protected values remain out of scope | Separate runtime-adjacent ADRs and policies before any access is considered |
| Legacy compatibility assertions | Some tests still accept legacy text alongside structured blocked reports | Migrate old text checks to schema-based blocked report assertions |

## Maintenance Rule

Any future PR that changes behavior, safety boundaries, schema semantics, or lifecycle state must update this matrix or the capability ledger in the same PR. A row may not claim `Implemented` unless it names evidence and at least one test or explicit manual verification command.
