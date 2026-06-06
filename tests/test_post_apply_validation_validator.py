from __future__ import annotations

import hashlib
import shutil
import subprocess
from pathlib import Path
from typing import Any

import yaml
from agentops_test_utils import run_script

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts" / "check-post-apply-validation"
CHANGE_ID = "20260530T000000Z_agentops_aaaaaaaaaa"
EXPECTED_HEAD = "1" * 40


def run_checker(root: Path, record: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return run_script(CHECKER, "--root", str(root), str(record), *args)


def write_yaml(path: Path, data: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return path


def prepare_root(root: Path) -> Path:
    schemas = root / "schemas"
    schemas.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / "schemas" / "post-apply-validation.schema.json", schemas / "post-apply-validation.schema.json")
    return root


def valid_record() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "post_apply_validation_id": f"{CHANGE_ID}_post_apply_validation",
        "change_id": CHANGE_ID,
        "agent": "agentops",
        "created_at": "2026-05-30T00:00:00Z",
        "created_by": "operator",
        "mutation_enabled": False,
        "status": "success",
        "expected_head": EXPECTED_HEAD,
        "actual_head": EXPECTED_HEAD,
        "audit_record_sha256": "a" * 64,
        "validation_commands": [
            {
                "name": "profile_validate",
                "command": "python scripts/hermes-agentops validate agentops",
                "exit_code": 0,
                "status": "success",
                "output_sha256": "b" * 64,
                "redacted_summary": "Profile validation passed.",
            },
            {
                "name": "tests",
                "command": "pytest -q",
                "exit_code": 0,
                "status": "success",
                "output_sha256": "c" * 64,
                "redacted_summary": "Tests passed.",
            },
        ],
        "boundaries": {
            "validator_is_read_only": True,
            "no_secret_values_read": True,
            "no_runtime_state_mutated_by_validator": True,
            "no_business_actions_executed": True,
            "apply_not_performed_by_validator": True,
        },
        "failure_recovery": {
            "manual_review_required": True,
            "rollback_not_executed_by_validator": True,
            "note": "Recovery remains manual.",
        },
    }


def test_post_apply_validation_checker_accepts_valid_record(tmp_path: Path) -> None:
    path = write_yaml(tmp_path / "post.yaml", valid_record())
    result = run_checker(ROOT, path)
    assert result.returncode == 0, result.stdout + result.stderr


def test_post_apply_validation_checker_rejects_mutation_enabled_true(tmp_path: Path) -> None:
    record = valid_record()
    record["mutation_enabled"] = True
    path = write_yaml(tmp_path / "post.yaml", record)
    result = run_checker(ROOT, path)
    assert result.returncode == 1
    assert "mutation_enabled" in result.stdout


def test_post_apply_validation_checker_rejects_agent_mismatch(tmp_path: Path) -> None:
    record = valid_record()
    record["agent"] = "otheragent"
    path = write_yaml(tmp_path / "post.yaml", record)
    result = run_checker(ROOT, path)
    assert result.returncode == 1
    assert "agent" in result.stdout


def test_post_apply_validation_checker_rejects_id_mismatch(tmp_path: Path) -> None:
    record = valid_record()
    record["post_apply_validation_id"] = "20260530T000000Z_agentops_bbbbbbbbbb_post_apply_validation"
    path = write_yaml(tmp_path / "post.yaml", record)
    result = run_checker(ROOT, path)
    assert result.returncode == 1
    assert "post_apply_validation_id" in result.stdout


def test_post_apply_validation_checker_rejects_success_head_mismatch(tmp_path: Path) -> None:
    record = valid_record()
    record["actual_head"] = "2" * 40
    path = write_yaml(tmp_path / "post.yaml", record)
    result = run_checker(ROOT, path)
    assert result.returncode == 1
    assert "actual_head" in result.stdout


def test_post_apply_validation_checker_rejects_success_with_failed_command(tmp_path: Path) -> None:
    record = valid_record()
    record["validation_commands"][0]["status"] = "failed"
    record["validation_commands"][0]["exit_code"] = 1
    path = write_yaml(tmp_path / "post.yaml", record)
    result = run_checker(ROOT, path)
    assert result.returncode == 1
    assert "all validation commands" in result.stdout


def test_post_apply_validation_checker_rejects_failed_with_no_failure_evidence(tmp_path: Path) -> None:
    record = valid_record()
    record["status"] = "failed"
    path = write_yaml(tmp_path / "post.yaml", record)
    result = run_checker(ROOT, path)
    assert result.returncode == 1
    assert "failed post-apply validation" in result.stdout


def test_post_apply_validation_checker_rejects_unsafe_command(tmp_path: Path) -> None:
    record = valid_record()
    record["validation_commands"][0]["command"] = "pytest -q && git push"
    path = write_yaml(tmp_path / "post.yaml", record)
    result = run_checker(ROOT, path)
    assert result.returncode == 1
    assert "read-only validation allowlist" in result.stdout


def test_post_apply_validation_checker_rejects_status_exit_code_mismatch(tmp_path: Path) -> None:
    record = valid_record()
    record["validation_commands"][0]["status"] = "success"
    record["validation_commands"][0]["exit_code"] = 2
    path = write_yaml(tmp_path / "post.yaml", record)
    result = run_checker(ROOT, path)
    assert result.returncode == 1
    assert "exit_code 0" in result.stdout


def test_post_apply_validation_checker_requires_audit_file(tmp_path: Path) -> None:
    evidence_root = prepare_root(tmp_path)
    path = write_yaml(tmp_path / "post.yaml", valid_record())
    result = run_checker(evidence_root, path, "--require-audit-file")
    assert result.returncode == 1
    assert "required audit record file is missing" in result.stdout


def test_post_apply_validation_checker_binds_existing_audit_record(tmp_path: Path) -> None:
    evidence_root = prepare_root(tmp_path)
    audit_path = evidence_root / "changes" / CHANGE_ID / "audit-record.yaml"
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    audit_path.write_text("audit\n", encoding="utf-8")

    record = valid_record()
    record["audit_record_sha256"] = hashlib.sha256(audit_path.read_bytes()).hexdigest()
    record_path = write_yaml(tmp_path / "post.yaml", record)

    result = run_checker(evidence_root, record_path, "--require-audit-file")
    assert result.returncode == 0, result.stdout + result.stderr

    record["audit_record_sha256"] = "d" * 64
    write_yaml(record_path, record)
    result = run_checker(evidence_root, record_path, "--require-audit-file")
    assert result.returncode == 1
    assert "audit_record_sha256 does not match" in result.stdout
