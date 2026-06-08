# Project Design

## Status

This is the project-level design entry point for Hermes AgentOps Manager. It describes the intended system as a whole, not only the current version-specific increments.

As of v2.8:

- The repository is public.
- `main` is governed by repository ruleset / PR / CI / CODEOWNERS discipline.
- The current implemented direction is repository governance, evidence validation, and bounded governance-record generation.
- `apply` remains disabled and must remain non-zero until a separately reviewed mutation pipeline exists.
- Validators and generators may read repository governance records and write only explicitly documented governance records under `changes/<change_id>/`.
- Current read-only and sandbox-only evidence layers include rollback-point validation, audit-record validation, approval-identity evidence validation, post-apply validation evidence validation, apply-lock analysis, apply-readiness report validation, signed approval verification, integrated sandbox mutation, sandbox audit capture, sandbox recovery simulation, real-apply readiness review evidence, and the v2.8 design-only real apply package.
- No current script may read real secret values, mutate runtime state, mutate managed profiles, acquire or release real runtime locks, execute rollback, or execute business actions.
- Future runtime-adjacent health, deployment, or repair management is allowed only after a separate design/ADR, read-only-first validation, explicit approval gates, and no Hermes runtime bypass.

## Mission

Hermes AgentOps Manager is a control-plane system for managing Hermes agent lifecycle assets.

Its job is to make agent profile changes reviewable, auditable, reversible, and safe before any future mutation path exists.

## Non-Goals

AgentOps is not:

- a business task scheduler;
- a multi-agent workflow orchestrator;
- a trading, research, or execution decision system;
- a replacement for Hermes provider runtime resolution;
- a replacement for Hermes tool registry or dispatch;
- a secret manager;
- a replacement for Hermes runtime sessions, gateway, cron, containers, or systemd;
- an automatic profile mutation system in the current phase.

Current AgentOps scripts also do not manage runtime sessions, gateway, cron, containers, or systemd units. That is a phase boundary, not a permanent ban on future AgentOps health, deployment, or repair management. Any future runtime-adjacent management must be separately designed, read-only first where possible, explicitly gated, auditable, and must not become business orchestration or bypass Hermes runtime mechanisms.

## Primary Design Boundary

```text
AgentOps manages agents. It does not dispatch agents to do business work.
```

This boundary applies even when a managed profile itself later has business permissions. AgentOps governance permissions do not inherit the managed agent's runtime or business permissions.

## System Responsibilities

AgentOps may:

- declare managed profiles;
- validate profile metadata and governance schemas;
- validate global policy inheritance;
- create and inspect change proposals;
- bind approvals to a change and diff hash;
- validate path scope and patch applicability;
- generate non-mutating pre-apply plans;
- validate apply-lock records without acquiring or releasing locks;
- create constrained apply-lock governance records after a valid pre-apply plan and no blocking lock evidence;
- validate rollback-point evidence records without creating rollback points or executing rollback;
- validate audit records without treating command evidence as execution authority;
- validate approval-identity evidence without treating YAML records or URLs as authentication authority;
- validate post-apply validation evidence without executing apply or rollback;
- analyze repository-wide apply-lock evidence without acquiring, releasing, rewriting, deleting, or repairing locks;
- validate apply-readiness evidence reports without authorizing apply;
- enforce repository process through CI guards and GitHub ruleset / CODEOWNERS configuration;
- propose future health, deployment, or repair management only through explicit design and review.

AgentOps must not:

- apply patches to managed profile files in the current phase;
- mutate runtime directories, sessions, logs, state databases, gateways, cron jobs, containers, or systemd units in the current phase;
- read or display real secret values;
- bypass Hermes runtime/provider/tooling mechanisms;
- treat approval records as cryptographic identity proofs;
- treat pre-apply plans, lock records, rollback points, audit records, post-apply validation records, or readiness reports as execution authority.

## Current Implementation Classes

| Area | Status | Notes |
| --- | --- | --- |
| Repository governance | Implemented | PR flow, CODEOWNERS, CI guard, ruleset evidence. |
| Profile declaration | Implemented | Manifest/config/SOUL governance assets. |
| Policy validation | Implemented | Global forbidden operations and risk thresholds; invalid policy fails closed. |
| Change records | Implemented | Proposal, diff, approvals, verify, list/show/diff. |
| Dry-run gates | Implemented | Optional Git clean and patch applicability checks; strict mode is required before plan generation and any future mutation. |
| Pre-apply plan schema | Implemented read-only | Schema and example validate the future contract. |
| Pre-apply plan generation | Implemented governance write | Writes only canonical `changes/<id>/pre-apply-plan.yaml`. |
| Apply-lock schema/checker | Implemented read-only | Validates lock records; does not acquire or release locks. |
| Apply-lock record generation | Implemented governance write | Writes canonical `changes/<id>/apply-lock.yaml`; does not acquire, release, rewrite, delete, or repair real locks. |
| Rollback point schema/checker | Implemented read-only | Validates rollback-point evidence; does not create rollback points or execute rollback. |
| Audit record schema/checker | Implemented read-only | Validates audit evidence; command strings are evidence only and not execution authority. |
| Approval identity schema/checker | Implemented read-only | Validates identity evidence references; does not authenticate live reviewer permissions. |
| Post-apply validation schema/checker | Implemented read-only | Validates post-apply validation evidence; does not execute apply or rollback. |
| Apply-lock analysis | Implemented read-only | Reports blocking lock evidence to stdout only; does not write reports or mutate locks. |
| Apply-readiness report | Implemented read-only | Aggregates evidence gates; `apply_authorized` remains `false`. |
| Real apply design package | Implemented design-only | Pipeline design, threat model, recovery runbook, schema, checker, and tests exist; no mutation code or feature flag. |
| Runtime-adjacent health/deployment/repair management | Not implemented | Future design only; must not bypass Hermes runtime or become business orchestration. |
| Real lock acquisition/release | Not implemented | Future mutation prerequisite. |
| Rollback point creation | Not implemented | Future mutation prerequisite distinct from the current read-only checker. |
| Patch mutation | Disabled | Must remain non-zero until all gates converge. |

## Design Principles

1. **Fail closed.** Invalid policy, schema, proposal, approval, path, hash, plan, lock, rollback, audit, identity, post-apply, analysis, or readiness evidence blocks progress.
2. **Bind records cryptographically where practical.** Diff hashes, plan hashes, lock hashes, audit hashes, evidence hashes, base commits, and change IDs reduce record reuse risk.
3. **Separate records from authority.** A valid record is review evidence, not permission to mutate.
4. **Prefer read-only validators before mutation.** Every future mutation step must first have a schema, example, validator, tests, and attack review.
5. **Keep governance writes narrow.** Current writes may create explicitly documented governance records under `changes/<change_id>/`; they must not write managed profiles or runtime state.
6. **Use GitHub enforcement for branch safety.** CI guards detect repository drift, but rulesets / branch protection enforce merge discipline.
7. **Preserve Hermes runtime boundary.** AgentOps governs repository assets and must not replace Hermes runtime semantics.
8. **Keep runtime-adjacent management explicit.** Health, deployment, and repair management may evolve only through design-gated, auditable, non-business orchestration paths.

## Required Reading Order for New Agents

1. `README.md`
2. `docs/EVIDENCE_BASELINE.md`
3. `docs/PROJECT_DESIGN.md`
4. `docs/ARCHITECTURE.md`
5. `docs/DOMAIN_MODEL.md`
6. `docs/STATE_MACHINE.md`
7. `docs/SAFETY_INVARIANTS.md`
8. `docs/THREAT_MODEL.md`
9. `docs/APPLY_PIPELINE_DESIGN.md`
10. `docs/OPERATIONS_AND_RECOVERY.md`
11. `docs/ROADMAP.md`
12. `docs/adr/*.md`

After that, read the version-specific documents only for detailed history and rationale.

## Evolution Rule

Do not implement `apply` by adding one large mutation PR. Future apply must be assembled as a sequence of separately reviewed, test-covered gates. A gate is eligible for mutation only after its schema, validator, tests, operational recovery behavior, and threat review have converged.
