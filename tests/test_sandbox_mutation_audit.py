from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import jsonschema
import yaml

from agentops_test_utils import run_script
from test_change_workflow import write_change
from test_integrated_sandbox_mutation import CHANGE_ID, RUNNER, hash_tree, make_diff, prepare_repo

ROOT = Path(__file__).resolve().parents[1]
AUDIT_GENERATOR = ROOT / "scripts" / "generate-sandbox-mutation-audit"
AUDIT_CHECKER = ROOT / "scripts" / "check-sandbox-mutation-audit"


def run_integrated(root: Path, *args: str) -> dict[str, Any]:
    result = run_script(
        RUNNER,
        CHANGE_ID,
        "--root",
        str(root),
        "--operator",
        "sandboxer",
        "--verified-at",
        "2026-05-30T00:02:00Z",
        *args,
    )
    assert result.stdout, result.stderr
    return yaml.safe_load(result.stdout)


def write_integrated_report(root: Path, report: dict[str, Any]) -> Path:
    path = root / "integrated-sandbox-run.yaml"
    path.write_text(yaml.safe_dump(report, sort_keys=False), encoding="utf-8")
    return path


def generate_audit(root: Path, report_path: Path):
    return run_script(
        AUDIT_GENERATOR,
        str(report_path),
        "--root",
        str(root),
        "--repository",
        "ray-toaru/hermes-agents",
        "--default-branch",
        "main",
        "--generated-at",
        "2026-05-30T00:03:00Z",
    )


def validate_audit(root: Path, audit: dict[str, Any]) -> None:
    schema = json.loads((root / "schemas" / "sandbox-mutation-audit-record.schema.json").read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)
    validator = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())
    errors = list(validator.iter_errors(audit))
    assert not errors, [error.message for error in errors]


def test_generate_sandbox_mutation_audit_for_successful_integrated_run(tmp_path: Path) -> None:
    root = prepare_repo(tmp_path)
    soul = root / "profiles" / "agentops" / "SOUL.md"
    diff_text = make_diff(root, "profiles/agentops/SOUL.md", soul.read_text(encoding="utf-8") + "\nAudit success note.\n")
    write_change(root, change_id=CHANGE_ID, diff_text=diff_text)
    before = hash_tree(root / "profiles")
    report = run_integrated(root)
    assert report["status"] == "success"
    report_path = write_integrated_report(root, report)

    generated = generate_audit(root, report_path)
    assert generated.returncode == 0, generated.stdout + generated.stderr
    audit = yaml.safe_load(generated.stdout)
    validate_audit(root, audit)

    assert audit["status"] == "success_recorded"
    assert audit["audited_status"] == "success"
    assert audit["audited_failure_stage"] is None
    assert audit["sandbox_only"] is True
    assert audit["production_audit"] is False
    assert audit["mutation_enabled"] is False
    assert audit["apply_authorized"] is False
    assert audit["recovery_required"] is False
    assert audit["manual_review_required"] is True
    assert audit["source_profiles_hash_before"] == before
    assert audit["source_profiles_hash_after"] == before
    assert audit["evidence_hashes"]["authenticated_approval_sha256"] == report["artifacts"]["authenticated_approval"]["sha256"]
    assert audit["evidence_hashes"]["apply_readiness_sha256"] == report["artifacts"]["apply_readiness"]["sha256"]
    assert audit["evidence_hashes"]["real_apply_lock_sha256"] == report["artifacts"]["real_apply_lock"]["sha256"]
    assert audit["evidence_hashes"]["rollback_point_sha256"] == report["artifacts"]["rollback_point"]["sha256"]
    assert audit["evidence_hashes"]["post_apply_validation_sha256"] == report["artifacts"]["post_apply_validation"]["sha256"]
    assert {step["name"] for step in audit["step_summary"]} >= {"change_verify", "sandbox_lock", "post_apply_validation"}
    assert hash_tree(root / "profiles") == before
    assert not (root / "changes" / CHANGE_ID / "sandbox-mutation-audit.yaml").exists()

    audit_path = root / "sandbox-mutation-audit.yaml"
    audit_path.write_text(generated.stdout, encoding="utf-8")
    checked = run_script(AUDIT_CHECKER, str(audit_path), "--root", str(root), "--integrated-run", str(report_path))
    assert checked.returncode == 0, checked.stdout + checked.stderr


def test_generate_sandbox_mutation_audit_for_failed_integrated_run_requires_recovery(tmp_path: Path) -> None:
    root = prepare_repo(tmp_path)
    manifest = root / "profiles" / "agentops" / "manifest.yaml"
    diff_text = make_diff(root, "profiles/agentops/manifest.yaml", "")
    write_change(root, change_id=CHANGE_ID, diff_text=diff_text)
    before = hash_tree(root / "profiles")
    report = run_integrated(root)
    assert report["status"] == "failed_closed"
    assert report["failure_stage"] == "post_apply_validation"
    report_path = write_integrated_report(root, report)

    generated = generate_audit(root, report_path)
    assert generated.returncode == 0, generated.stdout + generated.stderr
    audit = yaml.safe_load(generated.stdout)
    validate_audit(root, audit)

    assert audit["status"] == "failure_recorded"
    assert audit["audited_status"] == "failed_closed"
    assert audit["audited_failure_stage"] == "post_apply_validation"
    assert audit["recovery_required"] is True
    assert audit["manual_review_required"] is True
    assert audit["evidence_hashes"]["real_apply_lock_sha256"] == report["artifacts"]["real_apply_lock"]["sha256"]
    assert audit["evidence_hashes"]["rollback_point_sha256"] == report["artifacts"]["rollback_point"]["sha256"]
    assert audit["evidence_hashes"]["post_apply_validation_sha256"] == report["artifacts"]["post_apply_validation"]["sha256"]
    assert hash_tree(root / "profiles") == before
    assert manifest.read_text(encoding="utf-8") != ""


def test_check_sandbox_mutation_audit_rejects_tampered_integrated_hash(tmp_path: Path) -> None:
    root = prepare_repo(tmp_path)
    soul = root / "profiles" / "agentops" / "SOUL.md"
    diff_text = make_diff(root, "profiles/agentops/SOUL.md", soul.read_text(encoding="utf-8") + "\nAudit tamper note.\n")
    write_change(root, change_id=CHANGE_ID, diff_text=diff_text)
    report = run_integrated(root)
    report_path = write_integrated_report(root, report)
    generated = generate_audit(root, report_path)
    assert generated.returncode == 0, generated.stdout + generated.stderr
    audit_path = root / "sandbox-mutation-audit.yaml"
    audit_path.write_text(generated.stdout, encoding="utf-8")

    report["operator"] = "different"
    report_path.write_text(yaml.safe_dump(report, sort_keys=False), encoding="utf-8")
    checked = run_script(AUDIT_CHECKER, str(audit_path), "--root", str(root), "--integrated-run", str(report_path))
    assert checked.returncode == 1
    assert "integrated_sandbox_run_sha256 does not match" in checked.stdout
    assert "operator does not match" in checked.stdout


def test_check_sandbox_mutation_audit_rejects_authorization_flags(tmp_path: Path) -> None:
    root = prepare_repo(tmp_path)
    soul = root / "profiles" / "agentops" / "SOUL.md"
    diff_text = make_diff(root, "profiles/agentops/SOUL.md", soul.read_text(encoding="utf-8") + "\nAudit auth flag note.\n")
    write_change(root, change_id=CHANGE_ID, diff_text=diff_text)
    report = run_integrated(root)
    report_path = write_integrated_report(root, report)
    generated = generate_audit(root, report_path)
    assert generated.returncode == 0, generated.stdout + generated.stderr
    audit = yaml.safe_load(generated.stdout)
    audit["apply_authorized"] = True
    audit_path = root / "sandbox-mutation-audit.yaml"
    audit_path.write_text(yaml.safe_dump(audit, sort_keys=False), encoding="utf-8")

    checked = run_script(AUDIT_CHECKER, str(audit_path), "--root", str(root), "--integrated-run", str(report_path))
    assert checked.returncode == 1
    assert "True was expected to be false" in checked.stdout or "must not enable mutation" in checked.stdout
