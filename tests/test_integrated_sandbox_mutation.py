from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

import jsonschema
import yaml

from agentops_test_utils import run_script
from test_authenticated_approval_verifier import write_signed_attestation
from test_change_workflow import run_agentops, write_change

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "run-integrated-sandbox-mutation"
CHANGE_ID = "20260530T000000Z_agentops_aaaaaaaaaa"


def prepare_repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    for name in ("schemas", "policies", "profiles", "scripts", "inventory"):
        shutil.copytree(ROOT / name, root / name)
    subprocess.run(["git", "init"], cwd=root, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    subprocess.run(["git", "config", "user.email", "pytest@example.local"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "pytest"], cwd=root, check=True)
    subprocess.run(["git", "add", "profiles"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-m", "profiles baseline"], cwd=root, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return root


def hash_tree(path: Path) -> str:
    digest = hashlib.sha256()
    for file_path in sorted(item for item in path.rglob("*") if item.is_file()):
        digest.update(file_path.relative_to(path).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(file_path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def make_diff(root: Path, relative_path: str, new_text: str) -> str:
    path = root / relative_path
    original = path.read_text(encoding="utf-8")
    path.write_text(new_text, encoding="utf-8")
    diff = subprocess.run(["git", "diff", "--", relative_path], cwd=root, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True).stdout
    path.write_text(original, encoding="utf-8")
    return diff


def run_runner(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return run_script(RUNNER, CHANGE_ID, "--root", str(root), "--operator", "sandboxer", "--verified-at", "2026-05-30T00:02:00Z", *args)


def validate_report(root: Path, report: dict[str, Any]) -> None:
    schema = json.loads((root / "schemas" / "integrated-sandbox-mutation-run.schema.json").read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)
    validator = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())
    errors = list(validator.iter_errors(report))
    assert not errors, [error.message for error in errors]


def test_integrated_sandbox_pipeline_succeeds_without_source_mutation(tmp_path: Path) -> None:
    root = prepare_repo(tmp_path)
    soul = root / "profiles" / "agentops" / "SOUL.md"
    diff_text = make_diff(root, "profiles/agentops/SOUL.md", soul.read_text(encoding="utf-8") + "\nIntegrated sandbox note.\n")
    write_change(root, change_id=CHANGE_ID, diff_text=diff_text)
    before = hash_tree(root / "profiles")

    result = run_runner(root)
    assert result.returncode == 0, result.stdout + result.stderr
    report = yaml.safe_load(result.stdout)
    validate_report(root, report)

    assert report["status"] == "success"
    assert report["failure_stage"] is None
    assert report["sandbox_only"] is True
    assert report["mutation_enabled"] is False
    assert report["apply_authorized"] is False
    assert report["source_profiles_unchanged"] is True
    assert report["source_profiles_hash_before"] == before
    assert report["source_profiles_hash_after"] == before
    assert {step["name"] for step in report["steps"]} >= {
        "change_verify",
        "authenticated_approval",
        "pre_apply_plan",
        "apply_lock_analysis",
        "apply_readiness",
        "pre_apply_commit",
        "sandbox_lock",
        "rollback_point",
        "post_apply_validation",
    }
    assert report["assertions"] == {
        "authenticated_approval_verified": True,
        "readiness_complete_not_authorized": True,
        "sandbox_lock_acquired": True,
        "rollback_point_created": True,
        "post_apply_validation_success": True,
        "post_apply_validation_same_sandbox": True,
        "source_profiles_unchanged": True,
        "does_not_authorize_apply": True,
    }
    assert report["artifacts"]["real_apply_lock"]["status"] == "present"
    assert report["artifacts"]["rollback_point"]["status"] == "present"
    assert report["artifacts"]["post_apply_validation"]["status"] == "present"
    assert report["assertions"]["post_apply_validation_same_sandbox"] is True
    assert hash_tree(root / "profiles") == before
    assert not (root / ".hermes-agentops").exists()
    assert not (root / "changes" / CHANGE_ID / "integrated-sandbox-evidence").exists()

    apply_attempt = run_agentops(root, "apply", CHANGE_ID)
    assert apply_attempt.returncode == 1
    assert "intentionally not implemented" in apply_attempt.stdout


def test_integrated_sandbox_pipeline_fails_closed_on_signed_rejection(tmp_path: Path) -> None:
    root = prepare_repo(tmp_path)
    soul = root / "profiles" / "agentops" / "SOUL.md"
    diff_text = make_diff(root, "profiles/agentops/SOUL.md", soul.read_text(encoding="utf-8") + "\nRejected signed attestation.\n")
    write_change(root, change_id=CHANGE_ID, diff_text=diff_text)
    before = hash_tree(root / "profiles")
    attestation_path = write_signed_attestation(root, decision="reject")

    result = run_runner(root, "--approval-mode", "signed_attestation", "--attestation", str(attestation_path))
    assert result.returncode == 2
    report = yaml.safe_load(result.stdout)
    validate_report(root, report)
    assert report["status"] == "failed_closed"
    assert report["failure_stage"] == "authenticated_approval"
    assert report["assertions"]["authenticated_approval_verified"] is False
    assert report["source_profiles_unchanged"] is True
    assert hash_tree(root / "profiles") == before


def test_integrated_sandbox_pipeline_fails_closed_on_blocking_governance_lock(tmp_path: Path) -> None:
    root = prepare_repo(tmp_path)
    soul = root / "profiles" / "agentops" / "SOUL.md"
    diff_text = make_diff(root, "profiles/agentops/SOUL.md", soul.read_text(encoding="utf-8") + "\nBlocking lock.\n")
    write_change(root, change_id=CHANGE_ID, diff_text=diff_text)
    before = hash_tree(root / "profiles")
    (root / "changes" / CHANGE_ID / "apply-lock.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": 1,
                "lock_id": f"{CHANGE_ID}_lock",
                "change_id": CHANGE_ID,
                "agent": "agentops",
                "scope": "repository",
                "mode": "exclusive",
                "status": "active",
                "created_at": "2026-05-30T00:01:00Z",
                "created_by": "pytest",
                "expires_at": "2099-01-01T00:00:00Z",
                "base_commit": "a" * 40,
                "pre_apply_plan_sha256": "b" * 64,
                "mutation_enabled": False,
                "recovery": {
                    "manual_review_required": True,
                    "stale_lock_action": "inspect_before_release",
                    "note": "Blocking lock for test.",
                },
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    result = run_runner(root)
    assert result.returncode == 2
    report = yaml.safe_load(result.stdout)
    validate_report(root, report)
    assert report["status"] == "failed_closed"
    assert report["failure_stage"] == "apply_lock_analysis"
    assert report["artifacts"]["apply_lock_analysis"]["status"] == "present"
    assert report["source_profiles_unchanged"] is True
    assert hash_tree(root / "profiles") == before


def test_integrated_sandbox_pipeline_fails_closed_on_post_apply_validation_failure(tmp_path: Path) -> None:
    root = prepare_repo(tmp_path)
    manifest = root / "profiles" / "agentops" / "manifest.yaml"
    diff_text = make_diff(root, "profiles/agentops/manifest.yaml", "")
    write_change(root, change_id=CHANGE_ID, diff_text=diff_text)
    before = hash_tree(root / "profiles")

    result = run_runner(root)
    assert result.returncode == 2
    report = yaml.safe_load(result.stdout)
    validate_report(root, report)
    assert report["status"] == "failed_closed"
    assert report["failure_stage"] == "post_apply_validation"
    assert report["assertions"]["sandbox_lock_acquired"] is True
    assert report["assertions"]["rollback_point_created"] is True
    assert report["assertions"]["post_apply_validation_success"] is False
    assert report["source_profiles_unchanged"] is True
    assert hash_tree(root / "profiles") == before
    assert manifest.read_text(encoding="utf-8") != ""
