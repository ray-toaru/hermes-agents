# CI Coverage Map

## Purpose

This map records which checks are expected to cover current AgentOps governance artifacts. It is descriptive evidence for reviewers; it is not itself enforcement. GitHub rulesets, branch protection, CODEOWNERS, and workflow required-check settings remain external enforcement.

## Main CI Workflow

Workflow: `.github/workflows/ci.yml`, job `validate`, Python 3.11.

Runs on pull requests, pushes to `main`, and manual dispatch.

Main coverage:

- compile the primary CLI and governance helper scripts;
- `python scripts/hermes-agentops validate-schemas`;
- `python scripts/hermes-agentops validate -v`;
- CODEOWNERS baseline validation;
- canonical example validation for pre-apply plan, apply lock, rollback point, audit record, approval identity, authenticated approval, structured command, post-apply validation, apply lock analysis, apply readiness, real apply readiness, real apply design, production lock lifecycle, production lock skeleton, and production audit-start;
- grouped pytest execution for governance/validators, sandbox/readiness, rollback/audit/recovery, and structured command validation;
- secret and runtime file guard.

The grouped pytest commands are intentionally split to keep subprocess-heavy tests bounded by explicit timeouts.

## Main CI Pytest Groups

| Group | Intent | Test files |
| --- | --- | --- |
| governance and validators | Core validators, approval evidence, changes, and policy-governance records | `tests/test_agentops_common.py`, `tests/test_apply_lock_acquisition.py`, `tests/test_apply_lock_analysis.py`, `tests/test_apply_readiness_report.py`, `tests/test_approval_identity_validator.py`, `tests/test_audit_record_validator.py`, `tests/test_authenticated_approval_validator.py`, `tests/test_authenticated_approval_verifier.py`, `tests/test_change_workflow.py`, `tests/test_governance_validators.py` |
| sandbox and readiness | Sandbox-only evidence, readiness, real-apply design/prototypes, and rejection handling | `tests/test_integrated_sandbox_mutation.py`, `tests/test_policy_strictness.py`, `tests/test_post_apply_validation_sandbox_runner.py`, `tests/test_post_apply_validation_validator.py`, `tests/test_pre_apply_plan_generation.py`, `tests/test_production_apply_lock_lifecycle.py`, `tests/test_production_audit_start.py`, `tests/test_production_lock_skeleton_run.py`, `tests/test_read_only_evidence_chain.py`, `tests/test_real_apply_design_contract.py`, `tests/test_real_apply_lock_prototype.py`, `tests/test_real_apply_readiness_review.py`, `tests/test_rejection_status.py` |
| rollback, audit, recovery | Temporary-repository rollback prototypes, sandbox dry-run, sandbox audit, and sandbox recovery | `tests/test_rollback_point_creator_prototype.py`, `tests/test_rollback_point_validator.py`, `tests/test_sandbox_apply_dry_run.py`, `tests/test_sandbox_mutation_audit.py`, `tests/test_sandbox_recovery_simulation.py` |
| structured command validation | Structured command sandbox runner and validator | `tests/test_structured_command_sandbox_runner.py`, `tests/test_structured_command_validator.py` |

## Path-Scoped Workflows

Path-scoped workflows cover later-stage artifacts without forcing every PR to rerun every specialized test in isolation. They are additive to main CI and should stay fail-closed for their owned artifact paths.

| Workflow | Primary coverage |
| --- | --- |
| `.github/workflows/a22.yml` | `tests/test_production_audit_capture_v2.py` |
| `.github/workflows/c23.yml` | `tests/test_command_catalog.py` |
| `.github/workflows/c24.yml` | `tests/test_post_command_validation.py` |
| `.github/workflows/c25.yml` | `tests/test_governance_stage_gate.py` |
| `.github/workflows/c28.yml` | `tests/test_production_lock_readiness_source.py` |
| `.github/workflows/c29.yml` | `tests/test_closeout_contract.py` |
| `.github/workflows/c30.yml` | `tests/test_recovery_stage_adr.py` |
| `.github/workflows/c31.yml` | `tests/test_stage_readiness_v3.py` |
| `.github/workflows/c34.yml` | `tests/test_github_approval_network_source.py` |
| `.github/workflows/c35.yml` | `tests/test_production_lock_path_dry_run.py` |
| `.github/workflows/c36.yml` | `tests/test_production_audit_closeout_dry_run.py` |
| `.github/workflows/c37.yml` | `tests/test_command_dry_run_validation.py` |
| `.github/workflows/c38.yml` | `tests/test_runtime_adjacent_policy.py` |
| `.github/workflows/c39.yml` | `tests/test_stage_readiness_v4.py` |
| `.github/workflows/c40.yml` | `tests/test_governance_preflight.py` |
| `.github/workflows/c41.yml` | `tests/test_governance_blockers.py` |
| `.github/workflows/c42.yml` | `tests/test_stage_readiness_v5.py`, `tests/test_capability_ledger.py` |
| `.github/workflows/c45.yml` | `tests/test_apply_blocked_scaffold.py` |
| `.github/workflows/c46.yml` | `tests/test_guard_write_path_decision.py` |
| `.github/workflows/c47.yml` | `tests/test_audit_store_decision.py` |
| `.github/workflows/c48.yml` | `tests/test_recovery_runner_decision.py` |
| `.github/workflows/c49.yml` | `tests/test_stage_readiness_v6.py` |
| `.github/workflows/c50.yml` | `tests/test_apply_entrypoint_blocked.py` |
| `.github/workflows/c51.yml` | `tests/test_apply_entrypoint_tree_guard.py` |
| `.github/workflows/c52.yml` | `tests/test_stage_readiness_v7.py` |
| `.github/workflows/c53.yml` | `tests/test_single_cli_apply_blocked.py` |
| `.github/workflows/c54.yml` | `tests/test_stage_readiness_v8.py` |
| `.github/workflows/p6-live-approval-source.yml` | `tests/test_live_github_approval_source.py` |
| `.github/workflows/v12-state-safety.yml` | `tests/test_state_safety_contract.py` |
| `.github/workflows/v15-ledger.yml` | `tests/test_capability_ledger.py` |

## Maintenance Rule

When adding or renaming a test, workflow, governance script, schema, or capability-ledger item, update this map in the same PR or explicitly explain why the change has no CI coverage impact.
