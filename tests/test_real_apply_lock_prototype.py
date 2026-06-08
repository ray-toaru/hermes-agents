from __future__ import annotations

import subprocess
from pathlib import Path

import yaml

from test_change_workflow import init_git_profile
from agentops_test_utils import run_script

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "real-apply-lock-prototype"
CHANGE_ID = "20260530T000000Z_agentops_aaaaaaaaaa"
PLAN_HASH = "c" * 64


def run_lock(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return run_script(SCRIPT, "--root", str(root), *args)


def hash_tree(path: Path) -> str:
    digest = __import__("hashlib").sha256()
    for file_path in sorted(item for item in path.rglob("*") if item.is_file()):
        digest.update(file_path.relative_to(path).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(file_path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def acquire(root: Path, operator: str = "operator", ttl: int = 900) -> subprocess.CompletedProcess[str]:
    return run_lock(root, "acquire", CHANGE_ID, "--operator", operator, "--pre-apply-plan-sha256", PLAN_HASH, "--ttl-seconds", str(ttl))


def test_acquire_and_release_lock_without_profile_mutation(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    init_git_profile(root)
    before = hash_tree(root / "profiles")

    result = acquire(root)
    assert result.returncode == 0, result.stdout + result.stderr
    record = yaml.safe_load(result.stdout)
    assert record["change_id"] == CHANGE_ID
    assert record["operator"] == "operator"
    assert record["status"] == "active"
    assert record["mutation_enabled"] is False
    assert record["apply_authorized"] is False
    assert (root / ".hermes-agentops" / "locks" / "real-apply.lock").exists()
    assert hash_tree(root / "profiles") == before

    released = run_lock(root, "release", CHANGE_ID, "--operator", "operator")
    assert released.returncode == 0, released.stdout + released.stderr
    release_record = yaml.safe_load(released.stdout)
    assert release_record["status"] == "released"
    assert not (root / ".hermes-agentops" / "locks" / "real-apply.lock").exists()
    assert hash_tree(root / "profiles") == before


def test_second_acquire_is_blocked(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    init_git_profile(root)
    assert acquire(root).returncode == 0

    blocked = acquire(root, operator="other")
    assert blocked.returncode == 2
    assert "existing active lock blocks acquisition" in blocked.stderr


def test_expired_lock_still_blocks_acquire(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    init_git_profile(root)
    assert acquire(root, ttl=1).returncode == 0
    lock_path = root / ".hermes-agentops" / "locks" / "real-apply.lock"
    record = yaml.safe_load(lock_path.read_text(encoding="utf-8"))
    record["acquired_at"] = "2026-01-01T00:00:00Z"
    record["expires_at"] = "2026-01-01T00:00:01Z"
    lock_path.write_text(yaml.safe_dump(record, sort_keys=False), encoding="utf-8")

    blocked = acquire(root, operator="other")
    assert blocked.returncode == 2
    assert "existing expired lock blocks acquisition" in blocked.stderr
    assert lock_path.exists()


def test_release_requires_matching_owner(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    init_git_profile(root)
    assert acquire(root, operator="operator").returncode == 0

    wrong = run_lock(root, "release", CHANGE_ID, "--operator", "other")
    assert wrong.returncode == 2
    assert "ownership mismatch" in wrong.stderr
    assert (root / ".hermes-agentops" / "locks" / "real-apply.lock").exists()


def test_recovery_required_lock_is_preserved(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    init_git_profile(root)
    assert acquire(root, operator="operator").returncode == 0

    marked = run_lock(root, "mark-recovery", CHANGE_ID, "--operator", "operator")
    assert marked.returncode == 0, marked.stdout + marked.stderr
    record = yaml.safe_load(marked.stdout)
    assert record["status"] == "recovery_required"
    assert record["recovery_required"] is True

    release = run_lock(root, "release", CHANGE_ID, "--operator", "operator")
    assert release.returncode == 2
    assert "recovery-required lock is preserved" in release.stderr
    assert (root / ".hermes-agentops" / "locks" / "real-apply.lock").exists()


def test_inspect_validates_existing_lock(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    init_git_profile(root)
    assert acquire(root).returncode == 0

    inspected = run_lock(root, "inspect")
    assert inspected.returncode == 0, inspected.stdout + inspected.stderr
    record = yaml.safe_load(inspected.stdout)
    assert record["status"] == "active"
    assert record["boundaries"]["expired_locks_do_not_auto_release"] is True
