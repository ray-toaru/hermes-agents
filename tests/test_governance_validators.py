from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
PLAN_CHECKER = ROOT / "scripts" / "check-pre-apply-plan"
LOCK_CHECKER = ROOT / "scripts" / "check-apply-lock"

CHANGE_ID = "20260530T000000Z_agentops_aaaaaaaaaa"


def run_checker(script: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python", str(script), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def valid_plan() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "plan_id": f"{CHANGE_ID}_preapply",
        "change_id": CHANGE_ID,
        "agent": "agentops",
        "generated_at": "2026-05-30T00:00:00Z",
        "mutation_enabled": False,
        "base_commit": "0" * 40,
        "proposal_diff_sha256": "a" * 64,
        "gates": {
            "policy_valid": True,
            "proposal_valid": True,
            "approvals_valid": True,
            "diff_hash_valid": True,
            "path_scope_valid": True,
            "git_clean_required": True,
            "patch_applicable_required": True,
            "manual_operator_confirmation_required": True,
        },
        "lock": {
            "required": True,
            "scope": "repository",
            "mode": "exclusive",
            "stale_after_seconds": 900,
            "note": "Future apply must acquire one exclusive repository-level lock before mutation.",
        },
        "rollback": {
            "required": True,
            "strategy": "git_first",
            "pre_apply_commit_required": True,
            "note": "Future apply must record HEAD before mutation.",
        },
        "post_apply_validation": {
            "required": True,
            "commands": ["python scripts/hermes-agentops validate-schemas"],
        },
        "audit": {
            "required": True,
            "record_path": f"changes/{CHANGE_ID}/pre-apply-plan.yaml",
            "include_stdout_stderr": True,
            "include_exit_codes": True,
            "include_git_head_before_after": True,
        },
        "failure_recovery": {
            "abort_on_first_failure": True,
            "rollback_on_partial_mutation": True,
            "leave_lock_for_manual_recovery": True,
            "note": "Future apply must fail closed.",
        },
    }


def valid_lock() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "lock_id": f"{CHANGE_ID}_lock",
        "change_id": CHANGE_ID,
        "agent": "agentops",
        "scope": "repository",
        "mode": "exclusive",
        "status": "active",
        "created_at": "2026-05-30T00:00:00Z",
        "created_by": "operator",
        "expires_at": "2026-05-30T00:15:00Z",
        "base_commit": "0" * 40,
        "pre_apply_plan_sha256": "a" * 64,
        "mutation_enabled": False,
        "recovery": {
            "manual_review_required": True,
            "stale_lock_action": "inspect_before_release",
            "note": "Future stale locks must be inspected before release.",
        },
    }


def write_yaml(path: Path, data: dict[str, Any]) -> Path:
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return path


def test_pre_apply_plan_checker_accepts_valid_plan(tmp_path: Path) -> None:
    path = write_yaml(tmp_path / "plan.yaml", valid_plan())
    result = run_checker(PLAN_CHECKER, str(path))
    assert result.returncode == 0, result.stdout + result.stderr


def test_pre_apply_plan_checker_rejects_mutation_enabled_true(tmp_path: Path) -> None:
    plan = valid_plan()
    plan["mutation_enabled"] = True
    path = write_yaml(tmp_path / "plan.yaml", plan)
    result = run_checker(PLAN_CHECKER, str(path))
    assert result.returncode == 1
    assert "mutation_enabled" in result.stdout


def test_pre_apply_plan_checker_rejects_missing_required_gate(tmp_path: Path) -> None:
    plan = valid_plan()
    plan["gates"].pop("policy_valid")
    path = write_yaml(tmp_path / "plan.yaml", plan)
    result = run_checker(PLAN_CHECKER, str(path))
    assert result.returncode == 1
    assert "policy_valid" in result.stdout


def test_pre_apply_plan_checker_rejects_bad_base_commit(tmp_path: Path) -> None:
    plan = valid_plan()
    plan["base_commit"] = "not-a-sha"
    path = write_yaml(tmp_path / "plan.yaml", plan)
    result = run_checker(PLAN_CHECKER, str(path))
    assert result.returncode == 1
    assert "base_commit" in result.stdout


def test_pre_apply_plan_checker_rejects_mismatched_plan_id(tmp_path: Path) -> None:
    plan = valid_plan()
    plan["plan_id"] = "20260530T000000Z_agentops_bbbbbbbbbb_preapply"
    path = write_yaml(tmp_path / "plan.yaml", plan)
    result = run_checker(PLAN_CHECKER, str(path))
    assert result.returncode == 1
    assert "plan_id" in result.stdout


def test_pre_apply_plan_checker_rejects_agent_mismatch(tmp_path: Path) -> None:
    plan = valid_plan()
    plan["agent"] = "otheragent"
    path = write_yaml(tmp_path / "plan.yaml", plan)
    result = run_checker(PLAN_CHECKER, str(path))
    assert result.returncode == 1
    assert "agent" in result.stdout


def test_pre_apply_plan_checker_rejects_wrong_audit_path(tmp_path: Path) -> None:
    plan = valid_plan()
    plan["audit"]["record_path"] = "changes/other/pre-apply-plan.yaml"
    path = write_yaml(tmp_path / "plan.yaml", plan)
    result = run_checker(PLAN_CHECKER, str(path))
    assert result.returncode == 1
    assert "audit.record_path" in result.stdout


def test_apply_lock_checker_accepts_valid_lock(tmp_path: Path) -> None:
    path = write_yaml(tmp_path / "lock.yaml", valid_lock())
    result = run_checker(LOCK_CHECKER, str(path))
    assert result.returncode == 0, result.stdout + result.stderr


def test_apply_lock_checker_rejects_timestamp_order(tmp_path: Path) -> None:
    lock = valid_lock()
    lock["expires_at"] = lock["created_at"]
    path = write_yaml(tmp_path / "lock.yaml", lock)
    result = run_checker(LOCK_CHECKER, str(path))
    assert result.returncode == 1
    assert "expires_at" in result.stdout


def test_apply_lock_checker_rejects_lock_id_mismatch(tmp_path: Path) -> None:
    lock = valid_lock()
    lock["lock_id"] = "20260530T000000Z_agentops_bbbbbbbbbb_lock"
    path = write_yaml(tmp_path / "lock.yaml", lock)
    result = run_checker(LOCK_CHECKER, str(path))
    assert result.returncode == 1
    assert "lock_id" in result.stdout


def test_apply_lock_checker_rejects_agent_mismatch(tmp_path: Path) -> None:
    lock = valid_lock()
    lock["agent"] = "otheragent"
    path = write_yaml(tmp_path / "lock.yaml", lock)
    result = run_checker(LOCK_CHECKER, str(path))
    assert result.returncode == 1
    assert "agent" in result.stdout


def test_apply_lock_checker_rejects_mutation_enabled_true(tmp_path: Path) -> None:
    lock = valid_lock()
    lock["mutation_enabled"] = True
    path = write_yaml(tmp_path / "lock.yaml", lock)
    result = run_checker(LOCK_CHECKER, str(path))
    assert result.returncode == 1
    assert "mutation_enabled" in result.stdout


def test_apply_lock_checker_rejects_non_exclusive_mode(tmp_path: Path) -> None:
    lock = valid_lock()
    lock["mode"] = "shared"
    path = write_yaml(tmp_path / "lock.yaml", lock)
    result = run_checker(LOCK_CHECKER, str(path))
    assert result.returncode == 1
    assert "mode" in result.stdout


def test_apply_lock_checker_rejects_bad_hash_format(tmp_path: Path) -> None:
    lock = valid_lock()
    lock["pre_apply_plan_sha256"] = "not-a-hash"
    path = write_yaml(tmp_path / "lock.yaml", lock)
    result = run_checker(LOCK_CHECKER, str(path))
    assert result.returncode == 1
    assert "pre_apply_plan_sha256" in result.stdout


def test_apply_lock_checker_can_require_existing_plan_file() -> None:
    lock = valid_lock()
    path = write_yaml(Path("/tmp") / "missing-plan-lock.yaml", lock)
    result = run_checker(LOCK_CHECKER, str(path), "--require-plan-file")
    assert result.returncode == 1
    assert "required pre-apply plan file is missing" in result.stdout


def test_apply_lock_checker_binds_existing_plan_hash(tmp_path: Path) -> None:
    change_dir = ROOT / "changes" / CHANGE_ID
    plan_path = change_dir / "pre-apply-plan.yaml"
    lock = valid_lock()
    try:
        change_dir.mkdir(parents=True, exist_ok=True)
        plan_path.write_text("test-plan\n", encoding="utf-8")
        lock["pre_apply_plan_sha256"] = hashlib.sha256(plan_path.read_bytes()).hexdigest()
        path = write_yaml(tmp_path / "lock.yaml", lock)
        result = run_checker(LOCK_CHECKER, str(path), "--require-plan-file")
        assert result.returncode == 0, result.stdout + result.stderr

        lock["pre_apply_plan_sha256"] = "b" * 64
        write_yaml(path, lock)
        result = run_checker(LOCK_CHECKER, str(path), "--require-plan-file")
        assert result.returncode == 1
        assert "pre_apply_plan_sha256 does not match" in result.stdout
    finally:
        if plan_path.exists():
            plan_path.unlink()
        if change_dir.exists():
            try:
                change_dir.rmdir()
            except OSError:
                pass
