from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

import yaml

from test_change_workflow import init_git_profile, run_agentops
from agentops_test_utils import run_script
from apply_blocked_helpers import assert_apply_blocked_report

ROOT = Path(__file__).resolve().parents[1]
LOCK_SCRIPT = ROOT / "scripts" / "real-apply-lock-prototype"
ROLLBACK_SCRIPT = ROOT / "scripts" / "create-rollback-point-prototype"
CHANGE_ID = "20260530T000000Z_agentops_aaaaaaaaaa"
PLAN_HASH = "d" * 64


def run_lock(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return run_script(LOCK_SCRIPT, "--root", str(root), *args)


def run_creator(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return run_script(
        ROLLBACK_SCRIPT,
        CHANGE_ID,
        "--root",
        str(root),
        "--operator",
        "operator",
        "--pre-apply-plan-sha256",
        PLAN_HASH,
        *args,
    )


def acquire(root: Path, *, operator: str = "operator", plan_hash: str = PLAN_HASH) -> subprocess.CompletedProcess[str]:
    return run_lock(root, "acquire", CHANGE_ID, "--operator", operator, "--pre-apply-plan-sha256", plan_hash)


def hash_tree(path: Path) -> str:
    digest = hashlib.sha256()
    for file_path in sorted(item for item in path.rglob("*") if item.is_file()):
        digest.update(file_path.relative_to(path).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(file_path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def test_creates_rollback_point_evidence_for_active_matching_lock(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    init_git_profile(root)
    before = hash_tree(root / "profiles")
    assert acquire(root).returncode == 0

    result = run_creator(root)
    assert result.returncode == 0, result.stdout + result.stderr
    evidence = yaml.safe_load(result.stdout)
    assert evidence["change_id"] == CHANGE_ID
    assert evidence["operator"] == "operator"
    assert evidence["real_apply_lock"]["status"] == "active"
    assert evidence["real_apply_lock"]["recovery_required"] is False
    assert evidence["head"]["object_exists"] is True
    assert evidence["head"]["matches_lock_base_commit"] is True
    assert evidence["working_tree"]["clean"] is True
    assert evidence["rollback_executed"] is False
    assert evidence["mutation_enabled"] is False
    assert evidence["apply_authorized"] is False
    assert hash_tree(root / "profiles") == before

    apply_attempt = run_agentops(root, "apply", CHANGE_ID)
    assert apply_attempt.returncode == 1
    assert_apply_blocked_report(apply_attempt, change_id=CHANGE_ID)


def test_fails_closed_without_lock(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    init_git_profile(root)

    result = run_creator(root)
    assert result.returncode == 2
    assert "real apply lock is missing" in result.stderr
    assert result.stdout == ""


def test_fails_closed_for_recovery_required_lock(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    init_git_profile(root)
    assert acquire(root).returncode == 0
    marked = run_lock(root, "mark-recovery", CHANGE_ID, "--operator", "operator")
    assert marked.returncode == 0, marked.stdout + marked.stderr

    result = run_creator(root)
    assert result.returncode == 2
    assert "lock status must be active" in result.stderr or "recovery-required" in result.stderr
    assert (root / ".hermes-agentops" / "locks" / "real-apply.lock").exists()


def test_fails_closed_on_change_id_mismatch(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    init_git_profile(root)
    other_change = "20260530T000000Z_agentops_bbbbbbbbbb"
    assert run_lock(root, "acquire", other_change, "--operator", "operator", "--pre-apply-plan-sha256", PLAN_HASH).returncode == 0

    result = run_creator(root)
    assert result.returncode == 2
    assert "lock change_id mismatch" in result.stderr


def test_fails_closed_on_operator_mismatch(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    init_git_profile(root)
    assert acquire(root, operator="other").returncode == 0

    result = run_creator(root)
    assert result.returncode == 2
    assert "lock operator mismatch" in result.stderr


def test_fails_closed_on_plan_hash_mismatch(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    init_git_profile(root)
    assert acquire(root, plan_hash="e" * 64).returncode == 0

    result = run_creator(root)
    assert result.returncode == 2
    assert "lock pre_apply_plan_sha256 mismatch" in result.stderr


def test_fails_closed_if_working_tree_dirty(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    init_git_profile(root)
    assert acquire(root).returncode == 0
    (root / "profiles" / "agentops" / "SOUL.md").write_text("dirty\n", encoding="utf-8")

    result = run_creator(root)
    assert result.returncode == 2
    assert "working tree is dirty" in result.stderr


def test_fails_closed_if_current_head_differs_from_lock_base(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    init_git_profile(root)
    assert acquire(root).returncode == 0
    extra = root / "profiles" / "agentops" / "extra.md"
    extra.write_text("new committed file\n", encoding="utf-8")
    subprocess.run(["git", "add", "profiles/agentops/extra.md"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-m", "advance head"], cwd=root, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    result = run_creator(root)
    assert result.returncode == 2
    assert "current HEAD differs from lock base_commit" in result.stderr


def test_fails_closed_if_lock_base_commit_object_is_missing(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    init_git_profile(root)
    assert acquire(root).returncode == 0
    lock_path = root / ".hermes-agentops" / "locks" / "real-apply.lock"
    record = yaml.safe_load(lock_path.read_text(encoding="utf-8"))
    record["base_commit"] = "f" * 40
    lock_path.write_text(yaml.safe_dump(record, sort_keys=False), encoding="utf-8")

    result = run_creator(root)
    assert result.returncode == 2
    assert "lock base_commit object does not exist locally" in result.stderr


def test_ignores_only_lock_governance_file_for_clean_check(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    init_git_profile(root)
    assert acquire(root).returncode == 0

    result = run_creator(root)
    assert result.returncode == 0, result.stdout + result.stderr
    evidence = yaml.safe_load(result.stdout)
    assert evidence["working_tree"]["ignored_governance_paths"] == [".hermes-agentops/locks/real-apply.lock"]
