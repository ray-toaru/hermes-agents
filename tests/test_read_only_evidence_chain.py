from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path
from typing import Any

import yaml

from test_change_workflow import init_git_profile, prepare_root, run_agentops, run_verify, write_change
from agentops_test_utils import run_script

ROOT = Path(__file__).resolve().parents[1]
GENERATE_PLAN = ROOT / "scripts" / "generate-pre-apply-plan"
ACQUIRE_LOCK = ROOT / "scripts" / "acquire-apply-lock"
ANALYZE_LOCKS = ROOT / "scripts" / "analyze-apply-locks"
CHECK_APPROVAL_IDENTITY = ROOT / "scripts" / "check-approval-identity"
CHECK_READINESS = ROOT / "scripts" / "check-apply-readiness"
NOW = "2026-05-30T00:00:00Z"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_yaml(path: Path, data: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return path


def run_agentops_script(script: Path, root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return run_script(script, *args, "--root", str(root))


def build_approval_identity(root: Path, change_id: str, approver: str) -> Path:
    approval_path = root / "changes" / change_id / "approvals" / f"01_{approver}_approve.yaml"
    proposal = yaml.safe_load((root / "changes" / change_id / "proposal.yaml").read_text(encoding="utf-8"))
    record = {
        "schema_version": 1,
        "identity_evidence_id": f"{change_id}_{approver}_identity",
        "change_id": change_id,
        "agent": "agentops",
        "approver": approver,
        "created_at": NOW,
        "created_by": approver,
        "mutation_enabled": False,
        "identity_method": "github_review",
        "external_identity": {
            "provider": "github",
            "subject": approver,
            "evidence_url": "https://github.example.local/ray-toaru/hermes-agents/pull/0#pullrequestreview-0",
            "verified_by": "pytest-reference-only",
        },
        "approval_record_sha256": sha256_file(approval_path),
        "diff_sha256": proposal["diff_sha256"],
        "assertions": {
            "reviewed_diff": True,
            "approver_matches_external_identity": True,
            "approval_record_bound_to_diff": True,
            "identity_evidence_is_not_secret": True,
            "does_not_authorize_apply": True,
            "live_authentication_not_performed": True,
            "identity_evidence_does_not_grant_approval_authority": True,
            "business_orchestration_not_authorized": True,
        },
    }
    return write_yaml(root / "changes" / change_id / "approval-identity.yaml", record)


def build_readiness_report(root: Path, change_id: str, approval_identity_path: Path, lock_analysis_path: Path) -> Path:
    proposal_path = root / "changes" / change_id / "proposal.yaml"
    plan_path = root / "changes" / change_id / "pre-apply-plan.yaml"
    gates = [
        {
            "name": "change_verify",
            "phase": "pre_apply",
            "required_before_apply": True,
            "status": "present",
            "blocking": False,
            "evidence_path": f"changes/{change_id}/proposal.yaml",
            "evidence_sha256": sha256_file(proposal_path),
            "note": "Strict change verification passed before plan generation.",
        },
        {
            "name": "approval_identity",
            "phase": "pre_apply",
            "required_before_apply": True,
            "status": "present",
            "blocking": False,
            "evidence_path": f"changes/{change_id}/approval-identity.yaml",
            "evidence_sha256": sha256_file(approval_identity_path),
            "note": "Identity evidence is reference-only and not live authentication authority.",
        },
        {
            "name": "pre_apply_plan",
            "phase": "pre_apply",
            "required_before_apply": True,
            "status": "present",
            "blocking": False,
            "evidence_path": f"changes/{change_id}/pre-apply-plan.yaml",
            "evidence_sha256": sha256_file(plan_path),
            "note": "Pre-apply plan is governance evidence only.",
        },
        {
            "name": "apply_lock_analysis",
            "phase": "pre_apply",
            "required_before_apply": True,
            "status": "blocked",
            "blocking": True,
            "evidence_path": f"changes/{change_id}/apply-lock-analysis.yaml",
            "evidence_sha256": sha256_file(lock_analysis_path),
            "note": "The generated governance lock is active; readiness is blocked, not authorized.",
        },
        {
            "name": "apply_lock_record",
            "phase": "future_apply",
            "required_before_apply": False,
            "status": "future_only",
            "blocking": False,
            "evidence_path": f"changes/{change_id}/apply-lock.yaml",
            "evidence_sha256": None,
            "note": "Governance record exists, but real lock acquisition is future-only.",
        },
        {
            "name": "rollback_point",
            "phase": "future_apply",
            "required_before_apply": False,
            "status": "future_only",
            "blocking": False,
            "evidence_path": f"changes/{change_id}/rollback-point.yaml",
            "evidence_sha256": None,
            "note": "Rollback point creation is future-only.",
        },
        {
            "name": "audit_record",
            "phase": "future_apply",
            "required_before_apply": False,
            "status": "future_only",
            "blocking": False,
            "evidence_path": f"changes/{change_id}/audit-record.yaml",
            "evidence_sha256": None,
            "note": "Mutation audit capture is future-only.",
        },
        {
            "name": "post_apply_validation",
            "phase": "post_apply",
            "required_before_apply": False,
            "status": "future_only",
            "blocking": False,
            "evidence_path": f"changes/{change_id}/post-apply-validation.yaml",
            "evidence_sha256": None,
            "note": "Post-apply validation is not a pre-apply authorization gate.",
        },
    ]
    report = {
        "schema_version": 1,
        "readiness_report_id": f"{change_id}_readiness",
        "change_id": change_id,
        "agent": "agentops",
        "generated_at": NOW,
        "generated_by": "pytest-read-only-integration",
        "mutation_enabled": False,
        "apply_authorized": False,
        "status": "blocked",
        "gate_count": len(gates),
        "blocking_count": 1,
        "gates": gates,
        "boundaries": {
            "report_is_read_only": True,
            "does_not_authorize_apply": True,
            "does_not_acquire_or_release_locks": True,
            "does_not_mutate_profiles_or_runtime": True,
            "does_not_read_secret_values": True,
            "does_not_execute_rollback": True,
            "does_not_orchestrate_business_tasks": True,
        },
        "summary": {
            "human_review_required": True,
            "note": "Evidence chain assembled; active governance lock blocks readiness and apply remains disabled.",
        },
    }
    return write_yaml(root / "changes" / change_id / "apply-readiness.yaml", report)


def test_read_only_evidence_chain_blocks_before_mutation(tmp_path: Path) -> None:
    root = prepare_root(tmp_path)
    init_git_profile(root)
    before_profile = (root / "profiles" / "agentops" / "SOUL.md").read_text(encoding="utf-8")
    change_id = write_change(root, approvals=[("reviewer-1", "approve")])

    verify = run_verify(root, change_id, "--check-git-clean", "--check-patch-applicable")
    assert verify.returncode == 0, verify.stdout + verify.stderr

    plan = run_agentops_script(GENERATE_PLAN, root, change_id)
    assert plan.returncode == 0, plan.stdout + plan.stderr
    assert (root / "changes" / change_id / "pre-apply-plan.yaml").exists()

    lock = run_agentops_script(ACQUIRE_LOCK, root, change_id, "--created-by", "pytest")
    assert lock.returncode == 0, lock.stdout + lock.stderr
    assert (root / "changes" / change_id / "apply-lock.yaml").exists()

    analysis = run_agentops_script(ANALYZE_LOCKS, root, "--now", NOW)
    assert analysis.returncode == 0, analysis.stdout + analysis.stderr
    lock_analysis_path = root / "changes" / change_id / "apply-lock-analysis.yaml"
    lock_analysis_path.write_text(analysis.stdout, encoding="utf-8")
    analysis_report = yaml.safe_load(analysis.stdout)
    assert analysis_report["blocking_count"] == 1
    assert analysis_report["summary"]["does_not_release_locks"] is True

    approval_identity_path = build_approval_identity(root, change_id, "reviewer-1")
    approval_identity = run_agentops_script(CHECK_APPROVAL_IDENTITY, root, str(approval_identity_path), "--require-approval-file")
    assert approval_identity.returncode == 0, approval_identity.stdout + approval_identity.stderr

    readiness_path = build_readiness_report(root, change_id, approval_identity_path, lock_analysis_path)
    readiness = run_agentops_script(CHECK_READINESS, root, str(readiness_path), "--require-evidence-files")
    assert readiness.returncode == 0, readiness.stdout + readiness.stderr
    readiness_report = yaml.safe_load(readiness_path.read_text(encoding="utf-8"))
    assert readiness_report["apply_authorized"] is False
    assert readiness_report["status"] == "blocked"

    apply_attempt = run_agentops(root, "apply", change_id)
    assert apply_attempt.returncode == 1
    assert "intentionally not implemented" in apply_attempt.stdout
    assert (root / "profiles" / "agentops" / "SOUL.md").read_text(encoding="utf-8") == before_profile
