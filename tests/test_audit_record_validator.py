from __future__ import annotations

import hashlib
import shutil
import subprocess
from pathlib import Path
from typing import Any

import yaml
from agentops_test_utils import run_script

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts" / "check-audit-record"
CHANGE_ID = "20260530T000000Z_agentops_aaaaaaaaaa"


def run_checker(root: Path, record: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return run_script(CHECKER, "--root", str(root), str(record), *args)


def write_yaml(path: Path, data: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return path


def prepare_evidence_root(root: Path) -> Path:
    schemas = root / "schemas"
    schemas.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / "schemas" / "audit-record.schema.json", schemas / "audit-record.schema.json")
    return root


def valid_record() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "audit_record_id": f"{CHANGE_ID}_audit",
        "change_id": CHANGE_ID,
        "agent": "agentops",
        "created_at": "2026-05-30T00:00:00Z",
        "created_by": "operator",
        "mutation_enabled": False,
        "status": "validation_only",
        "git": {
            "head_before": "0" * 40,
            "head_after": "0" * 40,
            "working_tree_clean_before": True,
            "working_tree_clean_after": True,
        },
        "evidence": {
            "pre_apply_plan_sha256": "a" * 64,
            "apply_lock_sha256": "b" * 64,
            "rollback_point_sha256": "c" * 64,
        },
        "commands": [
            {
                "name": "changes_verify",
                "command": f"python scripts/hermes-agentops changes verify {CHANGE_ID} --check-git-clean --check-patch-applicable",
                "command_evidence_type": "recorded_only",
                "command_is_not_execution_authority": True,
                "exit_code": 0,
                "status": "success",
                "output_sha256": "d" * 64,
                "redacted_summary": "Validation completed without secret or runtime mutation.",
            }
        ],
        "boundaries": {
            "no_secret_values_read": True,
            "no_runtime_state_mutated": True,
            "no_profile_files_mutated": True,
            "no_business_actions_executed": True,
            "apply_remained_disabled": True,
        },
        "failure_recovery": {
            "manual_review_required": True,
            "rollback_not_executed_by_validator": True,
            "note": "Recovery remains manual and operator-reviewed.",
        },
    }


def test_audit_record_checker_accepts_valid_record(tmp_path: Path) -> None:
    path = write_yaml(tmp_path / "audit.yaml", valid_record())
    result = run_checker(ROOT, path)
    assert result.returncode == 0, result.stdout + result.stderr


def test_audit_record_checker_rejects_mutation_enabled_true(tmp_path: Path) -> None:
    record = valid_record()
    record["mutation_enabled"] = True
    path = write_yaml(tmp_path / "audit.yaml", record)
    result = run_checker(ROOT, path)
    assert result.returncode == 1
    assert "mutation_enabled" in result.stdout


def test_audit_record_checker_rejects_agent_mismatch(tmp_path: Path) -> None:
    record = valid_record()
    record["agent"] = "otheragent"
    path = write_yaml(tmp_path / "audit.yaml", record)
    result = run_checker(ROOT, path)
    assert result.returncode == 1
    assert "agent" in result.stdout


def test_audit_record_checker_rejects_id_mismatch(tmp_path: Path) -> None:
    record = valid_record()
    record["audit_record_id"] = "20260530T000000Z_agentops_bbbbbbbbbb_audit"
    path = write_yaml(tmp_path / "audit.yaml", record)
    result = run_checker(ROOT, path)
    assert result.returncode == 1
    assert "audit_record_id" in result.stdout


def test_audit_record_checker_rejects_head_mismatch(tmp_path: Path) -> None:
    record = valid_record()
    record["git"]["head_after"] = "1" * 40
    path = write_yaml(tmp_path / "audit.yaml", record)
    result = run_checker(ROOT, path)
    assert result.returncode == 1
    assert "head_before" in result.stdout


def test_audit_record_checker_rejects_dirty_worktree_evidence(tmp_path: Path) -> None:
    record = valid_record()
    record["git"]["working_tree_clean_after"] = False
    path = write_yaml(tmp_path / "audit.yaml", record)
    result = run_checker(ROOT, path)
    assert result.returncode == 1
    assert "clean working tree" in result.stdout


def test_audit_record_checker_rejects_unsafe_command(tmp_path: Path) -> None:
    record = valid_record()
    record["commands"][0]["command"] = "python scripts/check-rollback-point && git push"
    path = write_yaml(tmp_path / "audit.yaml", record)
    result = run_checker(ROOT, path)
    assert result.returncode == 1
    assert "read-only allowlist" in result.stdout


def test_audit_record_checker_rejects_command_execution_authority(tmp_path: Path) -> None:
    record = valid_record()
    record["commands"][0]["command_is_not_execution_authority"] = False
    path = write_yaml(tmp_path / "audit.yaml", record)
    result = run_checker(ROOT, path)
    assert result.returncode == 1
    assert "command_is_not_execution_authority" in result.stdout


def test_audit_record_checker_rejects_non_recorded_command_evidence(tmp_path: Path) -> None:
    record = valid_record()
    record["commands"][0]["command_evidence_type"] = "execution_plan"
    path = write_yaml(tmp_path / "audit.yaml", record)
    result = run_checker(ROOT, path)
    assert result.returncode == 1
    assert "command_evidence_type" in result.stdout


def test_audit_record_checker_rejects_status_exit_code_mismatch(tmp_path: Path) -> None:
    record = valid_record()
    record["commands"][0]["status"] = "success"
    record["commands"][0]["exit_code"] = 2
    path = write_yaml(tmp_path / "audit.yaml", record)
    result = run_checker(ROOT, path)
    assert result.returncode == 1
    assert "exit_code 0" in result.stdout


def test_audit_record_checker_requires_evidence_files(tmp_path: Path) -> None:
    evidence_root = prepare_evidence_root(tmp_path)
    path = write_yaml(tmp_path / "audit.yaml", valid_record())
    result = run_checker(evidence_root, path, "--require-evidence-files")
    assert result.returncode == 1
    assert "required evidence file is missing" in result.stdout


def test_audit_record_checker_binds_existing_evidence_hashes(tmp_path: Path) -> None:
    evidence_root = prepare_evidence_root(tmp_path)
    change_dir = evidence_root / "changes" / CHANGE_ID
    plan_path = change_dir / "pre-apply-plan.yaml"
    lock_path = change_dir / "apply-lock.yaml"
    rollback_path = change_dir / "rollback-point.yaml"
    change_dir.mkdir(parents=True, exist_ok=True)
    plan_path.write_text("plan\n", encoding="utf-8")
    lock_path.write_text("lock\n", encoding="utf-8")
    rollback_path.write_text("rollback\n", encoding="utf-8")

    record = valid_record()
    record["evidence"]["pre_apply_plan_sha256"] = hashlib.sha256(plan_path.read_bytes()).hexdigest()
    record["evidence"]["apply_lock_sha256"] = hashlib.sha256(lock_path.read_bytes()).hexdigest()
    record["evidence"]["rollback_point_sha256"] = hashlib.sha256(rollback_path.read_bytes()).hexdigest()
    record_path = write_yaml(tmp_path / "audit.yaml", record)

    result = run_checker(evidence_root, record_path, "--require-evidence-files")
    assert result.returncode == 0, result.stdout + result.stderr

    record["evidence"]["rollback_point_sha256"] = "e" * 64
    write_yaml(record_path, record)
    result = run_checker(evidence_root, record_path, "--require-evidence-files")
    assert result.returncode == 1
    assert "rollback_point_sha256 does not match" in result.stdout
