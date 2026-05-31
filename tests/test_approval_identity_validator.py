from __future__ import annotations

import hashlib
import shutil
import subprocess
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts" / "check-approval-identity"
CHANGE_ID = "20260530T000000Z_agentops_aaaaaaaaaa"
APPROVER = "operator"
DIFF_SHA = "b" * 64


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


def prepare_root(root: Path) -> Path:
    schemas = root / "schemas"
    schemas.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / "schemas" / "approval-identity.schema.json", schemas / "approval-identity.schema.json")
    return root


def approval_record() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "change_id": CHANGE_ID,
        "decision": "approve",
        "approver": APPROVER,
        "created_at": "2026-05-30T00:00:00Z",
        "comment": "Reviewed.",
        "diff_sha256": DIFF_SHA,
        "acknowledgements": {
            "reviewed_diff": True,
            "understands_apply_not_automatic": True,
            "secret_values_not_reviewed": True,
            "business_orchestration_not_authorized": True,
        },
    }


def valid_record() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "identity_evidence_id": f"{CHANGE_ID}_{APPROVER}_identity",
        "change_id": CHANGE_ID,
        "agent": "agentops",
        "approver": APPROVER,
        "created_at": "2026-05-30T00:00:00Z",
        "created_by": APPROVER,
        "mutation_enabled": False,
        "identity_method": "github_review",
        "external_identity": {
            "provider": "github",
            "subject": APPROVER,
            "evidence_url": "https://github.example.local/ray-toaru/hermes-agents/pull/0#pullrequestreview-0",
            "verified_by": "human-review",
        },
        "approval_record_sha256": "a" * 64,
        "diff_sha256": DIFF_SHA,
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


def test_approval_identity_checker_accepts_valid_record(tmp_path: Path) -> None:
    path = write_yaml(tmp_path / "identity.yaml", valid_record())
    result = run_checker(ROOT, path)
    assert result.returncode == 0, result.stdout + result.stderr


def test_approval_identity_checker_rejects_mutation_enabled_true(tmp_path: Path) -> None:
    record = valid_record()
    record["mutation_enabled"] = True
    path = write_yaml(tmp_path / "identity.yaml", record)
    result = run_checker(ROOT, path)
    assert result.returncode == 1
    assert "mutation_enabled" in result.stdout


def test_approval_identity_checker_rejects_agent_mismatch(tmp_path: Path) -> None:
    record = valid_record()
    record["agent"] = "otheragent"
    path = write_yaml(tmp_path / "identity.yaml", record)
    result = run_checker(ROOT, path)
    assert result.returncode == 1
    assert "agent" in result.stdout


def test_approval_identity_checker_rejects_id_mismatch(tmp_path: Path) -> None:
    record = valid_record()
    record["identity_evidence_id"] = f"{CHANGE_ID}_other_identity"
    path = write_yaml(tmp_path / "identity.yaml", record)
    result = run_checker(ROOT, path)
    assert result.returncode == 1
    assert "identity_evidence_id" in result.stdout


def test_approval_identity_checker_rejects_method_provider_mismatch(tmp_path: Path) -> None:
    record = valid_record()
    record["external_identity"]["provider"] = "external_attestation"
    path = write_yaml(tmp_path / "identity.yaml", record)
    result = run_checker(ROOT, path)
    assert result.returncode == 1
    assert "external_identity.provider" in result.stdout


def test_approval_identity_checker_rejects_subject_mismatch(tmp_path: Path) -> None:
    record = valid_record()
    record["external_identity"]["subject"] = "other"
    path = write_yaml(tmp_path / "identity.yaml", record)
    result = run_checker(ROOT, path)
    assert result.returncode == 1
    assert "subject" in result.stdout


def test_approval_identity_checker_rejects_live_authentication_claim(tmp_path: Path) -> None:
    record = valid_record()
    record["assertions"]["live_authentication_not_performed"] = False
    path = write_yaml(tmp_path / "identity.yaml", record)
    result = run_checker(ROOT, path)
    assert result.returncode == 1
    assert "live_authentication_not_performed" in result.stdout


def test_approval_identity_checker_rejects_grant_approval_authority_claim(tmp_path: Path) -> None:
    record = valid_record()
    record["assertions"]["identity_evidence_does_not_grant_approval_authority"] = False
    path = write_yaml(tmp_path / "identity.yaml", record)
    result = run_checker(ROOT, path)
    assert result.returncode == 1
    assert "identity_evidence_does_not_grant_approval_authority" in result.stdout


def test_approval_identity_checker_requires_approval_file(tmp_path: Path) -> None:
    evidence_root = prepare_root(tmp_path)
    path = write_yaml(tmp_path / "identity.yaml", valid_record())
    result = run_checker(evidence_root, path, "--require-approval-file")
    assert result.returncode == 1
    assert "required approvals directory is missing" in result.stdout


def test_approval_identity_checker_binds_matching_approval_record(tmp_path: Path) -> None:
    evidence_root = prepare_root(tmp_path)
    approval_path = evidence_root / "changes" / CHANGE_ID / "approvals" / "approval.yaml"
    approval = approval_record()
    write_yaml(approval_path, approval)

    record = valid_record()
    record["approval_record_sha256"] = hashlib.sha256(approval_path.read_bytes()).hexdigest()
    identity_path = write_yaml(tmp_path / "identity.yaml", record)

    result = run_checker(evidence_root, identity_path, "--require-approval-file")
    assert result.returncode == 0, result.stdout + result.stderr

    approval["diff_sha256"] = "c" * 64
    write_yaml(approval_path, approval)
    record["approval_record_sha256"] = hashlib.sha256(approval_path.read_bytes()).hexdigest()
    write_yaml(identity_path, record)
    result = run_checker(evidence_root, identity_path, "--require-approval-file")
    assert result.returncode == 1
    assert "diff_sha256 mismatch" in result.stdout
