# Safety Invariants

These invariants are non-negotiable. A change that violates them should be rejected even if it passes schema validation.

## Control-Plane Boundary

AgentOps is a governance/control plane for Hermes agent assets. It must not become a business workflow scheduler or runtime agent dispatcher.

## Runtime Boundary

Current AgentOps scripts must not:

- mutate managed profile files from proposals;
- write runtime state;
- read logs, sessions, state databases, or workspaces as authority for governance mutation;
- restart containers, gateways, cron jobs, or systemd units;
- bypass Hermes provider runtime resolution;
- bypass Hermes tool registry or dispatch.

Future runtime-adjacent health, deployment, or repair management must be introduced through explicit design, read-only-first validation where possible, approval gates for service-affecting actions, and no business orchestration.

## Secret Boundary

Real secret values must never be committed, read, printed, diffed, stored in change records, or included in audit records.

Secret names and references may be governed only as metadata.

## Apply Boundary

`apply` must remain disabled until all future mutation gates are implemented and separately reviewed.

A valid proposal, approval, pre-apply plan, or apply-lock record is not authorization to mutate.

## Record Binding Invariants

- A proposal must bind to `diff.patch` by SHA-256.
- An approval must bind to both `change_id` and `diff_sha256`.
- A pre-apply plan must bind to `change_id`, `base_commit`, diff evidence, and canonical record path.
- An apply lock must bind to `change_id`, `pre_apply_plan_sha256`, and `base_commit`.
- Reusing records across changes is invalid unless every binding still matches.

## Path Safety Invariants

Diff and output paths must fail closed on:

- absolute paths;
- `..` traversal;
- empty path segments;
- backslashes;
- quoted or whitespace paths;
- non-normal paths;
- malformed diff headers;
- paths outside the managed profile scope;
- output paths outside the documented governance record path.

## Approval Invariants

- Approval threshold comes from policy.
- Duplicate approving approvers do not increase approval count.
- Any valid rejection blocks verification.
- Malformed or mismatched approval records make status untrusted.
- Approval records are not authenticated identity proofs.

## Policy Invariants

- Global forbidden operations must be preserved in profile manifests.
- Policy thresholds are single-source for approval counts.
- Policy validation must fail closed on missing, malformed, weak, or unsafe policy values.

## Pre-Apply Plan Invariants

- `mutation_enabled` must remain false.
- Generation must call `changes verify --check-git-clean --check-patch-applicable`.
- Failed verification must write no plan.
- Plan output must be canonical: `changes/<change_id>/pre-apply-plan.yaml`.
- The plan does not authorize apply.

## Apply Lock Invariants

- Current checker is read-only.
- Lock records must be repository-scoped and exclusive.
- `mutation_enabled` must remain false in current lock records.
- Stale locks require manual review before release.
- Lock records do not acquire real runtime/concurrency locks.
- Lock records do not authorize apply.
- Lock record creation must bind to the actual pre-apply plan bytes.
- Existing active, stale, or recovery-required lock records block new lock records.
- Released locks do not block unrelated changes, but same-path overwrite is refused to preserve evidence.

## Repository Enforcement Invariants

- CI guardrails are detection, not enforcement.
- GitHub ruleset / branch protection is the enforcement layer for `main`.
- CODEOWNERS must cover `.github/`, scripts, schemas, policies, docs, profiles, and governance files.
- Ruleset evidence should be updated whenever ruleset settings change.

## Future Mutation Invariants

A future apply implementation must:

1. re-run all verification gates immediately before mutation;
2. acquire a repository-scoped exclusive real lock after governance lock-record checks;
3. record a rollback point before mutation;
4. mutate only expected managed profile paths;
5. run post-apply validation;
6. capture audit evidence;
7. release or preserve lock evidence according to outcome;
8. abort and recover on first failure.
