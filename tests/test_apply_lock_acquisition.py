from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path
from typing import Any

import yaml

from test_change_workflow import init_git_profile, prepare_root, write_change
from agentops_test_utils import run_script
from apply_blocked_helpers import assert_apply_blocked_report

ROOT = Path(__file__).resolve().parents[1]
ACQUIRE = ROOT / "scripts" / "acquire-apply-lock"
CHECK_LOCK = ROOT / "scripts" / "check-apply-lock"
CLI = ROOT / "scripts" / "hermes-agentops"
CHANGE_ID = "20260530T000000Z_agentops_aaaaaaaaaa"


def run_acquire(root: Path, change_id: str = CHANGE_ID, *args: str) -> subprocess.CompletedProcess[str]:
    return run_script(ACQUIRE, change_id, "--root", str(root), *args)


def git_head(root: Path) -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()


def write_yaml(path: Path, data: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return path


def valid_plan(root: Path, change_id: str = CHANGE_ID, *, base_commit: str | None = None) -> dict[str, Any]:
    if base_commit is None:
        base_commit = git_head(root)
    return {
        "schema_version": 1,
        "plan_id": f"{change_id}_preapply",
        "change_id": change_id,
        "agent": "agentops",
        "generated_at": "2026-05-30T00:00:00Z",
        "mutation_enabled": False,
        "base_commit": base_commit,
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
            "record_path": f"changes/{change_id}/pre-apply-plan.yaml",
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


def write_plan(root: Path, change_id: str = CHANGE_ID, *, base_commit: str | None = None) -> Path:
    return write_yaml(root / "changes" / change_id / "pre-apply-plan.yaml", valid_plan(root, change_id, base_commit=base_commit))


def valid_lock(root: Path, change_id: str, *, status: str = "active", expires_at: str = "2026-05-30T00:15:00Z") -> dict[str, Any]:
    plan_path = root / "changes" / change_id / "pre-apply-plan.yaml"
    plan_hash = hashlib.sha256(plan_path.read_bytes()).hexdigest() if plan_path.exists() else "a" * 64
    return {
        "schema_version": 1,
        "lock_id": f"{change_id}_lock",
        "change_id": change_id,
        "agent": "agentops",
        "scope": "repository",
        "mode": "exclusive",
        "status": status,
        "created_at": "2026-05-30T00:00:00Z",
        "created_by": "operator",
        "expires_at": expires_at,
        "base_commit": git_head(root),
        "pre_apply_plan_sha256": plan_hash,
        "mutation_enabled": False,
        "recovery": {
            "manual_review_required": True,
            "stale_lock_action": "inspect_before_release",
            "note": "Future stale locks must be inspected before release.",
        },
    }


def prepare_change_with_plan(tmp_path: Path) -> tuple[Path, str, Path]:
    root = prepare_root(tmp_path)
    init_git_profile(root)
    change_id = write_change(root)
    plan_path = write_plan(root, change_id)
    return root, change_id, plan_path


def test_acquire_apply_lock_writes_valid_canonical_lock(tmp_path: Path) -> None:
    root, change_id, plan_path = prepare_change_with_plan(tmp_path)

    result = run_acquire(root, change_id, "--created-by", "pytest")
    assert result.returncode == 0, result.stdout + result.stderr

    lock_path = root / "changes" / change_id / "apply-lock.yaml"
    assert lock_path.exists()
    lock = yaml.safe_load(lock_path.read_text(encoding="utf-8"))
    assert lock["status"] == "active"
    assert lock["mutation_enabled"] is False
    assert lock["change_id"] == change_id
    assert lock["agent"] == "agentops"
    assert lock["base_commit"] == git_head(root)
    assert lock["pre_apply_plan_sha256"] == hashlib.sha256(plan_path.read_bytes()).hexdigest()

    check = run_script(CHECK_LOCK, "--root", str(root), str(lock_path), "--require-plan-file")
    assert check.returncode == 0, check.stdout + check.stderr


def test_acquire_apply_lock_requires_plan(tmp_path: Path) -> None:
    root = prepare_root(tmp_path)
    init_git_profile(root)
    change_id = write_change(root)

    result = run_acquire(root, change_id)
    assert result.returncode == 2
    assert "missing pre-apply plan" in result.stdout
    assert not (root / "changes" / change_id / "apply-lock.yaml").exists()


def test_acquire_apply_lock_rejects_invalid_plan(tmp_path: Path) -> None:
    root, change_id, _ = prepare_change_with_plan(tmp_path)
    plan_path = root / "changes" / change_id / "pre-apply-plan.yaml"
    plan = yaml.safe_load(plan_path.read_text(encoding="utf-8"))
    plan["agent"] = "otheragent"
    write_yaml(plan_path, plan)

    result = run_acquire(root, change_id)
    assert result.returncode == 2
    assert "invalid pre-apply plan" in result.stdout
    assert not (root / "changes" / change_id / "apply-lock.yaml").exists()


def test_acquire_apply_lock_rejects_stale_base_commit(tmp_path: Path) -> None:
    root, change_id, _ = prepare_change_with_plan(tmp_path)
    plan_path = root / "changes" / change_id / "pre-apply-plan.yaml"
    plan = yaml.safe_load(plan_path.read_text(encoding="utf-8"))
    plan["base_commit"] = "1" * 40
    write_yaml(plan_path, plan)

    result = run_acquire(root, change_id)
    assert result.returncode == 2
    assert "base_commit" in result.stdout
    assert not (root / "changes" / change_id / "apply-lock.yaml").exists()


def test_acquire_apply_lock_rejects_existing_active_lock(tmp_path: Path) -> None:
    root, change_id, _ = prepare_change_with_plan(tmp_path)
    other_id = "20260530T000001Z_agentops_bbbbbbbbbb"
    write_yaml(root / "changes" / other_id / "apply-lock.yaml", valid_lock(root, other_id, status="active", expires_at="2999-01-01T00:00:00Z"))

    result = run_acquire(root, change_id)
    assert result.returncode == 2
    assert "existing active lock blocks" in result.stdout
    assert not (root / "changes" / change_id / "apply-lock.yaml").exists()


def test_acquire_apply_lock_treats_expired_active_lock_as_blocking_stale(tmp_path: Path) -> None:
    root, change_id, _ = prepare_change_with_plan(tmp_path)
    other_id = "20260530T000001Z_agentops_bbbbbbbbbb"
    write_yaml(root / "changes" / other_id / "apply-lock.yaml", valid_lock(root, other_id, status="active", expires_at="2000-01-01T00:00:00Z"))

    result = run_acquire(root, change_id)
    assert result.returncode == 2
    assert "stale" in result.stdout
    assert not (root / "changes" / change_id / "apply-lock.yaml").exists()


def test_acquire_apply_lock_rejects_existing_recovery_required_lock(tmp_path: Path) -> None:
    root, change_id, _ = prepare_change_with_plan(tmp_path)
    other_id = "20260530T000001Z_agentops_bbbbbbbbbb"
    write_yaml(root / "changes" / other_id / "apply-lock.yaml", valid_lock(root, other_id, status="recovery_required"))

    result = run_acquire(root, change_id)
    assert result.returncode == 2
    assert "recovery_required" in result.stdout
    assert not (root / "changes" / change_id / "apply-lock.yaml").exists()


def test_acquire_apply_lock_ignores_existing_released_lock(tmp_path: Path) -> None:
    root, change_id, _ = prepare_change_with_plan(tmp_path)
    other_id = "20260530T000001Z_agentops_bbbbbbbbbb"
    write_yaml(root / "changes" / other_id / "apply-lock.yaml", valid_lock(root, other_id, status="released"))

    result = run_acquire(root, change_id)
    assert result.returncode == 0, result.stdout + result.stderr
    assert (root / "changes" / change_id / "apply-lock.yaml").exists()


def test_acquire_apply_lock_refuses_existing_output(tmp_path: Path) -> None:
    root, change_id, _ = prepare_change_with_plan(tmp_path)
    write_yaml(root / "changes" / change_id / "apply-lock.yaml", valid_lock(root, change_id, status="released"))

    result = run_acquire(root, change_id)
    assert result.returncode == 2
    assert "already exists" in result.stdout


def test_acquire_apply_lock_requires_minimum_expiry(tmp_path: Path) -> None:
    root, change_id, _ = prepare_change_with_plan(tmp_path)

    result = run_acquire(root, change_id, "--expires-in-seconds", "10")
    assert result.returncode == 2
    assert "at least 60" in result.stdout


def test_apply_remains_disabled_after_lock_acquisition_feature(tmp_path: Path) -> None:
    root = prepare_root(tmp_path)
    result = run_script(CLI, "--root", str(root), "apply", CHANGE_ID)
    assert result.returncode == 1
    assert_apply_blocked_report(result, change_id=CHANGE_ID)
