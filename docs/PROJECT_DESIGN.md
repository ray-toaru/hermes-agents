# Project Design

## Status

This is the project-level design entry point for Hermes AgentOps Manager. It describes the intended system as a whole, not only the current version-specific increments.

As of the current design baseline:

- The repository is public.
- `main` is governed by repository ruleset / PR / CI / CODEOWNERS discipline.
- The current implemented direction is pre-apply governance and validation.
- `apply` remains disabled.
- Validators and generators are allowed to read repository governance records and write only explicitly documented governance records under `changes/<change_id>/`.
- No script may read real secret values, mutate runtime state, mutate managed profiles, or execute business actions.

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
- a runtime session, gateway, cron, or container manager;
- an automatic profile mutation system in the current phase.

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
- document future rollback, audit, and post-apply requirements;
- enforce repository process through CI guards and GitHub ruleset / CODEOWNERS configuration.

AgentOps must not:

- apply patches to managed profile files in the current phase;
- mutate runtime directories, sessions, logs, state databases, gateways, cron jobs, containers, or systemd units;
- read or display real secret values;
- bypass Hermes runtime/provider/tooling mechanisms;
- treat approval records as cryptographic identity proofs;
- treat pre-apply plans or lock records as execution authority.

## Current Implementation Classes

| Area | Status | Notes |
| --- | --- | --- |
| Repository governance | Implemented | PR flow, CODEOWNERS, CI guard, ruleset evidence. |
| Profile declaration | Implemented | Manifest/config/SOUL governance assets. |
| Policy validation | Implemented | Global forbidden operations and risk thresholds. |
| Change records | Implemented | Proposal, diff, approvals, verify, list/show/diff. |
| Dry-run gates | Implemented | Optional Git clean and patch applicability checks. |
| Pre-apply plan schema | Implemented read-only | Schema and example validate the future contract. |
| Pre-apply plan generation | Implemented governance write | Writes only canonical `changes/<id>/pre-apply-plan.yaml`. |
| Apply-lock schema/checker | Implemented read-only | Validates lock records; does not acquire or release locks. |
| Apply-lock record generation | Implemented governance write | Writes canonical `changes/<id>/apply-lock.yaml`; does not release or delete locks. |
| Real lock acquisition/release | Not implemented | Future mutation prerequisite. |
| Rollback point creation | Not implemented | Future mutation prerequisite. |
| Audit record capture | Not implemented | Future mutation prerequisite. |
| Post-apply validation | Not implemented | Future mutation prerequisite. |
| Apply mutation | Disabled | Must remain non-zero until all gates converge. |

## Design Principles

1. **Fail closed.** Invalid policy, schema, proposal, approval, path, hash, plan, or lock evidence blocks progress.
2. **Bind records cryptographically where practical.** Diff hashes, plan hashes, base commits, and change IDs prevent record reuse.
3. **Separate records from authority.** A valid record is review evidence, not permission to mutate.
4. **Prefer read-only validators before mutation.** Every future mutation step must first have a schema, example, validator, tests, and attack review.
5. **Keep governance writes narrow.** Current writes may create governance records under `changes/<change_id>/`; they must not write managed profiles or runtime state.
6. **Use GitHub enforcement for branch safety.** CI guards detect repository drift, but rulesets / branch protection enforce merge discipline.
7. **Preserve Hermes runtime boundary.** AgentOps governs repository assets and must not replace Hermes runtime semantics.

## Required Reading Order for New Agents

1. `README.md`
2. `docs/PROJECT_DESIGN.md`
3. `docs/ARCHITECTURE.md`
4. `docs/DOMAIN_MODEL.md`
5. `docs/STATE_MACHINE.md`
6. `docs/SAFETY_INVARIANTS.md`
7. `docs/THREAT_MODEL.md`
8. `docs/APPLY_PIPELINE_DESIGN.md`
9. `docs/OPERATIONS_AND_RECOVERY.md`
10. `docs/adr/*.md`

After that, read the version-specific documents only for detailed history and rationale.

## Evolution Rule

Do not implement `apply` by adding one large mutation PR. Future apply must be assembled as a sequence of separately reviewed, test-covered gates. A gate is eligible for mutation only after its schema, validator, tests, operational recovery behavior, and threat review have converged.
