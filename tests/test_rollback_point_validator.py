from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts" / "check-rollback-point"
CHANGE_ID = "20260530T000000Z_agentops_aaaaaaaaaa"


def run_checker(root: Path, record: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python", str(CHECKER), "--root", str(root), str(record), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def write_yaml(path: Path, data: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return path


def valid_record() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "rollback_point_id": f"{CHANGE_ID}_rollback",
        "change_id": CHANGE_ID,
        "agent": "agentops",
        "created_at": "2026-05-30T00:00:00Z",
        "created_by": "operator",
        "mutation_enabled": False,
        "strategy": "git_first",
        "pre_apply_commit": "0" * 40,
        "current_head": "0" * 40,
        "pre_apply_plan_sha256": "a" * 64,
        "apply_lock_sha256": "b" * 64,
        "recovery": {
            "manual_review_required": True,
            "rollback_command": "git revert or reset by operator",
            "post_rollback_validation_required": True,
            "note": "Future rollback must be operator-reviewed.",
        },
    }


def test_rollback_point_checker_accepts_valid_record(tmp_path: Path) -> None:
    path = write_yaml(tmp_path / "rollback.yaml", valid_record())
    result = run_checker(ROOT, path)
    assert result.returncode == 0, result.stdout + result.stderr


def test_rollback_point_checker_rejects_mutation_enabled_true(tmp_path: Path) -> None:
    record = valid_record()
    record["mutation_enabled"] = True
    path = write_yaml(tmp_path / "rollback.yaml", record)
    result = run_checker(ROOT, path)
    assert result.returncode == 1
    assert "mutation_enabled" in result.stdout


def test_rollback_point_checker_rejects_agent_mismatch(tmp_path: Path) -> None:
    record = valid_record()
    record["agent"] = "otheragent"
    path = write_yaml(tmp_path / "rollback.yaml", record)
    result = run_checker(ROOT, path)
    assert result.returncode == 1
    assert "agent" in result.stdout


def test_rollback_point_checker_rejects_id_mismatch(tmp_path: Path) -> None:
    record = valid_record()
    record["rollback_point_id"] = "20260530T000000Z_agentops_bbbbbbbbbb_rollback"
    path = write_yaml(tmp_path / "rollback.yaml", record)
    result = run_checker(ROOT, path)
    assert result.returncode == 1
    assert "rollback_point_id" in result.stdout


def test_rollback_point_checker_rejects_bad_commit(tmp_path: Path) -> None:
    record = valid_record()
    record["pre_apply_commit"] = "not-a-sha"
    path = write_yaml(tmp_path / "rollback.yaml", record)
    result = run_checker(ROOT, path)
    assert result.returncode == 1
    assert "pre_apply_commit" in result.stdout


def test_rollback_point_checker_rejects_head_mismatch(tmp_path: Path) -> None:
    record = valid_record()
    record["current_head"] = "1" * 40
    path = write_yaml(tmp_path / "rollback.yaml", record)
    result = run_checker(ROOT, path)
    assert result.returncode == 1
    assert "pre_apply_commit" in result.stdout


def test_rollback_point_checker_rejects_bad_plan_hash(tmp_path: Path) -> None:
    record = valid_record()
    record["pre_apply_plan_sha256"] = "not-a-hash"
    path = write_yaml(tmp_path / "rollback.yaml", record)
    result = run_checker(ROOT, path)
    assert result.returncode == 1
    assert "pre_apply_plan_sha256" in result.stdout


def test_rollback_point_checker_requires_evidence_files(tmp_path: Path) -> None:
    path = write_yaml(tmp_path / "rollback.yaml", valid_record())
    result = run_checker(tmp_path, path, "--require-evidence-files")
    assert result.returncode == 1
    assert "required pre-apply plan file is missing" in result.stdout
    assert "required apply lock file is missing" in result.stdout


def test_rollback_point_checker_binds_existing_evidence_hashes(tmp_path: Path) -> None:
    change_dir = tmp_path / "changes" / CHANGE_ID
    plan_path = change_dir / "pre-apply-plan.yaml"
    lock_path = change_dir / "apply-lock.yaml"
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text("plan\n", encoding="utf-8")
    lock_path.write_text("lock\n", encoding="utf-8")
    record = valid_record()
    record["pre_apply_plan_sha256"] = hashlib.sha256(plan_path.read_bytes()).hexdigest()
    record["apply_lock_sha256"] = hashlib.sha256(lock_path.read_bytes()).hexdigest()
    record_path = write_yaml(tmp_path / "rollback.yaml", record)

    result = run_checker(tmp_path, record_path, "--require-evidence-files")
    assert result.returncode == 0, result.stdout + result.stderr

    record["apply_lock_sha256"] = "c" * 64
    write_yaml(record_path, record)
    result = run_checker(tmp_path, record_path, "--require-evidence-files")
    assert result.returncode == 1
    assert "apply_lock_sha256 does not match" in result.stdout
