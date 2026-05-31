# AgentOps Architecture Decision Records

This document captures already-converged decisions so future agents do not have to reconstruct them from chat history or individual PRs.

## ADR-001: AgentOps is a governance/control plane

Decision: AgentOps manages declarations, policies, change records, approvals, and apply-adjacent governance records. It does not replace Hermes runtime, read secrets, mutate runtime state, or execute business workflows.

Reason: Combining governance and business execution would blur safety boundaries and make future apply review harder.

Status: accepted.

## ADR-002: Profile is the minimum managed unit

Decision: Managed declarations live under `profiles/<agent>/`; change diffs must stay inside one profile scope.

Reason: Profile-level scope gives a clear ownership, approval, and rollback boundary.

Status: accepted.

## ADR-003: Diff-first change records

Decision: Proposed profile changes are represented as `diff.patch` plus a schema-valid `proposal.yaml` that binds to the patch hash.

Reason: Reviewers must be able to inspect exact intended mutations before any future apply path exists.

Status: accepted.

## ADR-004: Policy-driven approval thresholds

Decision: Required approvals are loaded from `policies/global-permissions.yaml`; code constants are only conservative defaults for missing policy files.

Reason: Duplicated policy thresholds create drift and inconsistent review gates.

Status: accepted.

## ADR-005: Conservative diff path support

Decision: Reject absolute paths, traversal, malformed headers, quoted or whitespace paths, backslashes, and non-normal paths.

Reason: Before mutation exists, conservative rejection is safer than partial support for ambiguous Git path encodings.

Status: accepted.

## ADR-006: Valid rejection blocks verification

Decision: Any valid rejection record makes `changes verify` fail.

Reason: A rejected change must not become apply-adjacent through approval count alone.

Status: accepted.

## ADR-007: Pre-apply plan before apply

Decision: Introduce a schema-valid, non-mutating `pre-apply-plan.yaml` before any apply implementation.

Reason: Future mutation needs a reviewed contract for gates, rollback, audit, lock expectations, and failure behavior.

Status: accepted.

## ADR-008: Fixed output boundary for generated plans

Decision: `generate-pre-apply-plan` may only write `changes/<change_id>/pre-apply-plan.yaml`.

Reason: An arbitrary output path would expand mutation surface beyond the documented governance record location.

Status: accepted.

## ADR-009: Repository-scoped exclusive lock first

Decision: The first lock contract is repository-scoped and exclusive.

Reason: Per-agent or per-path locks could miss shared files and introduce unsafe concurrency before the simple case is proven.

Status: accepted.

## ADR-010: Stale lock evidence must not be erased automatically

Decision: Stale locks require manual inspection before release.

Reason: Automatically deleting stale locks could erase evidence of partial mutation or interrupted recovery.

Status: accepted.

## ADR-011: GitHub enforcement complements repository guardrails

Decision: CI scripts and docs are guardrails; GitHub rulesets or branch protection enforce merge policy.

Reason: Repository files alone cannot prevent direct admin/bypass operations or require PR checks.

Status: accepted.
