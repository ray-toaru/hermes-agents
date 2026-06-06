# Implementation Matrix

This matrix binds project claims to concrete implementation evidence. It is a governance artifact, not execution authority. All rows must preserve the current invariant: `hermes-agentops apply` remains disabled and no managed profile or runtime mutation is authorized by evidence completeness alone.

## Current Evidence Baseline

| Claim | Implementation Evidence | Test Evidence | Current Status | Boundary |
| --- | --- | --- | --- | --- |
| Repository manages AgentOps governance records, not Hermes runtime execution | `README.md`, `AGENTS.md`, `docs/ARCHITECTURE.md`, `scripts/hermes-agentops` | `tests/test_change_workflow.py::test_apply_remains_disabled` | Implemented | No business orchestration or runtime mutation |
| Profile, inventory, policy, schema validation exists | `scripts/hermes-agentops validate`, `validate-schemas`, `policy check`; `schemas/*.json`; `policies/global-permissions.yaml` | `tests/test_change_workflow.py`, `tests/test_governance_validators.py`, `tests/test_policy_strictness.py` | Implemented | Validation does not authorize apply |
| Change proposal and approval records are hash-bound to reviewed diff | `scripts/hermes-agentops changes verify` | `tests/test_change_workflow.py` | Implemented | YAML approvals are governance records, not identity proof |
| Git clean and patch applicability gates are strict dry-run checks | `scripts/hermes-agentops changes verify --check-git-clean --check-patch-applicable` | `tests/test_change_workflow.py::test_git_clean_gate_rejects_dirty_profile`, `::test_patch_applicability_gate_*` | Implemented | Uses `git apply --check`; does not apply patch |
| Pre-apply plan generation writes a canonical governance record | `scripts/generate-pre-apply-plan`; `schemas/pre-apply-plan.schema.json` | `tests/test_pre_apply_plan_generation.py` | Implemented | Plan is not execution authority |
| Apply-lock governance record generation exists | `scripts/acquire-apply-lock`; `schemas/apply-lock.schema.json` | `tests/test_apply_lock_acquisition.py` | Implemented | Governance lock is not real mutation lock |
| Apply-lock analysis is read-only | `scripts/analyze-apply-locks`; `schemas/apply-lock-analysis.schema.json` | `tests/test_apply_lock_analysis.py` | Implemented | Analysis cannot release or repair locks |
| Read-only evidence validators exist for rollback, audit, approval identity, post-apply validation, structured command, and readiness reports | `scripts/check-*`; `schemas/*` | `tests/test_*_validator.py`, `tests/test_read_only_evidence_chain.py` | Implemented | Record shape and hash binding only |
| Authenticated approval verifier contract exists | `scripts/verify-authenticated-approval`; `schemas/authenticated-approval.schema.json` | `tests/test_authenticated_approval_verifier.py` | Implemented for fixture and signed-attestation modes | Evidence remains `apply_authorized: false`; `live_github` fails closed |
| Signed approval attestation verification exists | `scripts/verify-authenticated-approval --mode signed_attestation`; `schemas/signed-approval-attestation.schema.json`; `schemas/trusted-approval-signers.schema.json` | `tests/test_authenticated_approval_verifier.py::test_signed_attestation_verifier_*` | Read-only implemented | Public trust roots and signed evidence do not authorize apply |
| Structured validation command sandbox exists | `scripts/run-structured-command-sandbox`; `schemas/structured-command*.schema.json` | `tests/test_structured_command_sandbox_runner.py` | Validation-only implemented | No mutation, rollback, audit capture, or business commands |
| Real lock prototype exists for temporary repositories | `scripts/real-apply-lock-prototype`; `schemas/real-apply-lock.schema.json` | `tests/test_real_apply_lock_prototype.py` | Prototype implemented | Not integrated with `apply`; temporary repo only |
| Rollback point creator prototype exists | `scripts/create-rollback-point-prototype`; `schemas/rollback-point-created.schema.json` | `tests/test_rollback_point_creator_prototype.py` | Prototype implemented | Does not execute rollback |
| Sandbox post-apply validation exists | `scripts/run-post-apply-validation-sandbox`; `schemas/post-apply-validation-run.schema.json` | `tests/test_post_apply_validation_sandbox_runner.py` | Sandbox-only implemented | Mutates temporary workspace only |
| Sandbox apply dry-run exists | `scripts/sandbox-apply-dry-run` | `tests/test_sandbox_apply_dry_run.py` | Sandbox-only implemented | Does not acquire real lock or mutate source profiles |
| Shared subprocess execution has a hard timeout | `scripts/agentops_common.py::run_command`; migrated command call sites in CLI/sandbox/prototype scripts | `tests/test_agentops_common.py` | Implemented | Timeout is a fail-closed command failure, not retry authority |
| Internal script dispatch for reviewed AgentOps Python entry points exists | `scripts/agentops_common.py::run_python_script_main`, `::run_internal_python_command`; sandbox-only runners use internal dispatch for repository scripts | `tests/test_agentops_common.py`, `tests/test_post_apply_validation_sandbox_runner.py`, `tests/test_structured_command_sandbox_runner.py`, `tests/agentops_test_utils.py` | Implemented | Internal dispatch is not shell execution, not record-provided mutation authority, and not apply authorization |
| Test harness avoids repeated child Python cold starts | `tests/agentops_test_utils.py`, `tests/conftest.py` | `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q --basetemp=/tmp/agentops-pytest` | Implemented | Test harness change does not weaken runtime safety boundaries |
| Real mutation command exists | `scripts/hermes-agentops apply` | `tests/test_change_workflow.py::test_apply_remains_disabled` | Not implemented | Must stay disabled until prerequisite ADRs converge |

## Known Gaps Before Any Real Mutation

| Gap | Why It Blocks Mutation | Required Next Evidence |
| --- | --- | --- |
| Live GitHub approval verification | Signed attestations now cover a non-fixture authenticated path, but direct GitHub review verification is still absent | Read-only `live_github` verifier with repository, PR/review, diff, approver, permission, rejection, and time binding |
| Integrated real lock lifecycle | Governance lock files and temporary prototypes do not protect a live apply pipeline | Reviewed lock acquisition/release/recovery integration with preservation on uncertainty |
| Rollback execution and validation | Rollback point records do not roll back anything | Failure simulation, rollback command registry, post-rollback validation, and audit evidence |
| Mutation audit capture | Current audit records are validation-only evidence | Structured command capture around sandbox mutation before any real mutation |
| Integrated sandbox mutation pipeline | Existing sandbox pieces are standalone | A pipeline that combines authenticated approval evidence, lock, rollback point, sandbox mutation, post-apply validation, audit, and recovery simulation without source mutation |
| Runtime-adjacent operations | Current scope intentionally excludes runtime logs, sessions, gateway, containers, cron, secrets | Separate runtime-adjacent ADRs and policies |

## Maintenance Rule

Any future PR that changes behavior, safety boundaries, schema semantics, or lifecycle state must update this matrix in the same PR. A row may not claim `Implemented` unless it names script/schema evidence and at least one test or explicit manual verification command.
