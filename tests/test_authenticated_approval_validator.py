from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any

import yaml
from agentops_test_utils import run_script

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts" / "check-authenticated-approval"
CHANGE_ID = "20260530T000000Z_agentops_aaaaaaaaaa"
DIFF_SHA = "b" * 64


def run_checker(root: Path, record: Path) -> subprocess.CompletedProcess[str]:
    return run_script(CHECKER, "--root", str(root), str(record))


def write_yaml(path: Path, data: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return path


def prepare_root(root: Path) -> Path:
    schemas = root / "schemas"
    schemas.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / "schemas" / "authenticated-approval.schema.json", schemas / "authenticated-approval.schema.json")
    return root


def valid_record() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "authenticated_approval_id": f"{CHANGE_ID}_authenticated_approval",
        "change_id": CHANGE_ID,
        "agent": "agentops",
        "repository": {
            "provider": "github",
            "full_name": "ray-toaru/hermes-agents",
            "default_branch": "main",
        },
        "diff_sha256": DIFF_SHA,
        "required_approvals": 1,
        "verified_approvals": [
            {
                "approver": "operator",
                "decision": "approve",
                "approved_at": "2026-05-30T00:01:00Z",
                "identity_provider": "github",
                "identity_subject": "operator",
                "permission": "write",
                "evidence_kind": "pull_request_review",
                "evidence_ref": "https://github.example.local/ray-toaru/hermes-agents/pull/0#pullrequestreview-0",
                "diff_sha256": DIFF_SHA,
                "verified": True,
            }
        ],
        "rejections_present": False,
        "verified_at": "2026-05-30T00:02:00Z",
        "verified_by": "fixture-contract-only",
        "verifier_mode": "fixture_contract_only",
        "mutation_enabled": False,
        "apply_authorized": False,
        "status": "verified_not_authorized",
        "assertions": {
            "repository_bound": True,
            "change_id_bound": True,
            "diff_hash_bound": True,
            "approval_threshold_met": True,
            "no_rejections_present": True,
            "all_approvals_verified": True,
            "does_not_authorize_apply": True,
            "does_not_mutate_profiles_or_runtime": True,
            "does_not_read_secret_values": True,
            "business_orchestration_not_authorized": True,
        },
    }


def test_authenticated_approval_checker_accepts_valid_record(tmp_path: Path) -> None:
    path = write_yaml(tmp_path / "auth.yaml", valid_record())
    result = run_checker(ROOT, path)
    assert result.returncode == 0, result.stdout + result.stderr


def test_authenticated_approval_checker_rejects_apply_authorized_true(tmp_path: Path) -> None:
    record = valid_record()
    record["apply_authorized"] = True
    path = write_yaml(tmp_path / "auth.yaml", record)
    result = run_checker(ROOT, path)
    assert result.returncode == 1
    assert "apply_authorized" in result.stdout


def test_authenticated_approval_checker_rejects_mutation_enabled_true(tmp_path: Path) -> None:
    record = valid_record()
    record["mutation_enabled"] = True
    path = write_yaml(tmp_path / "auth.yaml", record)
    result = run_checker(ROOT, path)
    assert result.returncode == 1
    assert "mutation_enabled" in result.stdout


def test_authenticated_approval_checker_rejects_unmet_threshold(tmp_path: Path) -> None:
    record = valid_record()
    record["required_approvals"] = 2
    path = write_yaml(tmp_path / "auth.yaml", record)
    result = run_checker(ROOT, path)
    assert result.returncode == 1
    assert "required_approvals" in result.stdout


def test_authenticated_approval_checker_rejects_rejections_present(tmp_path: Path) -> None:
    record = valid_record()
    record["rejections_present"] = True
    path = write_yaml(tmp_path / "auth.yaml", record)
    result = run_checker(ROOT, path)
    assert result.returncode == 1
    assert "rejections_present" in result.stdout


def test_authenticated_approval_checker_rejects_unverified_approval(tmp_path: Path) -> None:
    record = valid_record()
    record["verified_approvals"][0]["verified"] = False
    path = write_yaml(tmp_path / "auth.yaml", record)
    result = run_checker(ROOT, path)
    assert result.returncode == 1
    assert "verified" in result.stdout


def test_authenticated_approval_checker_rejects_diff_hash_mismatch(tmp_path: Path) -> None:
    record = valid_record()
    record["verified_approvals"][0]["diff_sha256"] = "c" * 64
    path = write_yaml(tmp_path / "auth.yaml", record)
    result = run_checker(ROOT, path)
    assert result.returncode == 1
    assert "diff_sha256" in result.stdout


def test_authenticated_approval_checker_rejects_duplicate_approver(tmp_path: Path) -> None:
    record = valid_record()
    record["verified_approvals"].append(dict(record["verified_approvals"][0]))
    path = write_yaml(tmp_path / "auth.yaml", record)
    result = run_checker(ROOT, path)
    assert result.returncode == 1
    assert "duplicate" in result.stdout


def test_authenticated_approval_checker_rejects_approval_after_verification(tmp_path: Path) -> None:
    record = valid_record()
    record["verified_approvals"][0]["approved_at"] = "2026-05-30T00:03:00Z"
    path = write_yaml(tmp_path / "auth.yaml", record)
    result = run_checker(ROOT, path)
    assert result.returncode == 1
    assert "approved_at" in result.stdout


def test_authenticated_approval_checker_can_run_against_copied_schema(tmp_path: Path) -> None:
    root = prepare_root(tmp_path / "repo")
    path = write_yaml(tmp_path / "auth.yaml", valid_record())
    result = run_checker(root, path)
    assert result.returncode == 0, result.stdout + result.stderr
