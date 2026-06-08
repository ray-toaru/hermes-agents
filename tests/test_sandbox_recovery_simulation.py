from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import jsonschema
import yaml

from agentops_test_utils import run_script
from test_change_workflow import write_change
from test_integrated_sandbox_mutation import CHANGE_ID, hash_tree, make_diff, prepare_repo
from test_sandbox_mutation_audit import generate_audit, run_integrated, write_integrated_report

ROOT = Path(__file__).resolve().parents[1]
SIMULATOR = ROOT / "scripts" / "simulate-sandbox-recovery"
CHECKER = ROOT / "scripts" / "check-sandbox-recovery-simulation"


def write_yaml(path: Path, data: dict[str, Any]) -> Path:
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return path


def validate_simulation(root: Path, simulation: dict[str, Any]) -> None:
    schema = json.loads((root / "schemas" / "sandbox-recovery-simulation.schema.json").read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)
    validator = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())
    errors = list(validator.iter_errors(simulation))
    assert not errors, [error.message for error in errors]


def build_audit_for_success(root: Path) -> tuple[Path, Path, dict[str, Any]]:
    soul = root / "profiles" / "agentops" / "SOUL.md"
    diff_text = make_diff(root, "profiles/agentops/SOUL.md", soul.read_text(encoding="utf-8") + "\nRecovery success note.\n")
    write_change(root, change_id=CHANGE_ID, diff_text=diff_text)
    report = run_integrated(root)
    assert report["status"] == "success"
    report_path = write_integrated_report(root, report)
    generated = generate_audit(root, report_path)
    assert generated.returncode == 0, generated.stdout + generated.stderr
    audit = yaml.safe_load(generated.stdout)
    audit_path = write_yaml(root / "sandbox-mutation-audit.yaml", audit)
    return report_path, audit_path, audit


def build_audit_for_validation_failure(root: Path) -> tuple[Path, Path, dict[str, Any]]:
    manifest = root / "profiles" / "agentops" / "manifest.yaml"
    diff_text = make_diff(root, "profiles/agentops/manifest.yaml", "")
    write_change(root, change_id=CHANGE_ID, diff_text=diff_text)
    report = run_integrated(root)
    assert report["status"] == "failed_closed"
    assert report["failure_stage"] == "post_apply_validation"
    report_path = write_integrated_report(root, report)
    generated = generate_audit(root, report_path)
    assert generated.returncode == 0, generated.stdout + generated.stderr
    audit = yaml.safe_load(generated.stdout)
    audit_path = write_yaml(root / "sandbox-mutation-audit.yaml", audit)
    return report_path, audit_path, audit


def run_simulation(root: Path, report_path: Path, audit_path: Path, *args: str):
    return run_script(
        SIMULATOR,
        str(audit_path),
        "--root",
        str(root),
        "--integrated-run",
        str(report_path),
        "--generated-at",
        "2026-05-30T00:04:00Z",
        *args,
    )


def test_simulate_sandbox_recovery_for_success_records_no_recovery(tmp_path: Path) -> None:
    root = prepare_repo(tmp_path)
    before = hash_tree(root / "profiles")
    report_path, audit_path, audit = build_audit_for_success(root)

    result = run_simulation(root, report_path, audit_path)
    assert result.returncode == 0, result.stdout + result.stderr
    simulation = yaml.safe_load(result.stdout)
    validate_simulation(root, simulation)

    assert simulation["status"] == "no_recovery_required_recorded"
    assert simulation["scenario"] == "no_recovery_required"
    assert simulation["hypothetical"] is False
    assert simulation["sandbox_only"] is True
    assert simulation["production_recovery"] is False
    assert simulation["mutation_enabled"] is False
    assert simulation["apply_authorized"] is False
    assert simulation["simulation_result"]["recovery_required"] is False
    assert simulation["simulation_result"]["manual_review_required"] is True
    assert simulation["simulation_result"]["rollback_executed"] is False
    assert simulation["simulation_result"]["lock_release_allowed"] is False
    assert simulation["evidence_hashes"]["sandbox_audit_record_sha256"]
    assert simulation["sandbox_audit_record_id"] == audit["sandbox_audit_record_id"]
    assert hash_tree(root / "profiles") == before

    sim_path = write_yaml(root / "sandbox-recovery-simulation.yaml", simulation)
    checked = run_script(CHECKER, str(sim_path), "--root", str(root), "--audit-record", str(audit_path), "--integrated-run", str(report_path))
    assert checked.returncode == 0, checked.stdout + checked.stderr


def test_simulate_sandbox_recovery_for_validation_failure_preserves_lock_semantics(tmp_path: Path) -> None:
    root = prepare_repo(tmp_path)
    before = hash_tree(root / "profiles")
    report_path, audit_path, _audit = build_audit_for_validation_failure(root)

    result = run_simulation(root, report_path, audit_path)
    assert result.returncode == 0, result.stdout + result.stderr
    simulation = yaml.safe_load(result.stdout)
    validate_simulation(root, simulation)

    assert simulation["status"] == "recovery_required_recorded"
    assert simulation["scenario"] == "validation_failed"
    assert simulation["observed_state"]["lock_evidence_present"] is True
    assert simulation["observed_state"]["rollback_point_evidence_present"] is True
    assert simulation["observed_state"]["post_apply_validation_evidence_present"] is True
    assert simulation["simulation_result"]["recovery_required"] is True
    assert simulation["simulation_result"]["rollback_candidate_available"] is True
    assert simulation["simulation_result"]["rollback_simulated"] is True
    assert simulation["simulation_result"]["rollback_executed"] is False
    assert simulation["simulation_result"]["lock_release_allowed"] is False
    assert simulation["simulation_result"]["next_action"] == "preserve_lock_and_request_manual_review"
    assert hash_tree(root / "profiles") == before


def test_simulate_sandbox_recovery_unknown_state_fails_closed(tmp_path: Path) -> None:
    root = prepare_repo(tmp_path)
    report_path, audit_path, _audit = build_audit_for_success(root)

    result = run_simulation(root, report_path, audit_path, "--scenario", "unknown_state")
    assert result.returncode == 0, result.stdout + result.stderr
    simulation = yaml.safe_load(result.stdout)
    validate_simulation(root, simulation)

    assert simulation["status"] == "failed_closed"
    assert simulation["scenario"] == "unknown_state"
    assert simulation["hypothetical"] is True
    assert simulation["observed_state"]["unknown_state"] is True
    assert simulation["simulation_result"]["recovery_required"] is True
    assert simulation["simulation_result"]["next_action"] == "manual_review_unknown_state"
    assert simulation["simulation_result"]["rollback_executed"] is False
    assert simulation["simulation_result"]["lock_release_allowed"] is False


def test_check_sandbox_recovery_simulation_rejects_tampered_lock_release(tmp_path: Path) -> None:
    root = prepare_repo(tmp_path)
    report_path, audit_path, _audit = build_audit_for_success(root)
    result = run_simulation(root, report_path, audit_path)
    assert result.returncode == 0, result.stdout + result.stderr
    simulation = yaml.safe_load(result.stdout)
    simulation["simulation_result"]["lock_release_allowed"] = True
    sim_path = write_yaml(root / "sandbox-recovery-simulation.yaml", simulation)

    checked = run_script(CHECKER, str(sim_path), "--root", str(root), "--audit-record", str(audit_path), "--integrated-run", str(report_path))
    assert checked.returncode == 1
    assert "True was expected to be false" in checked.stdout or "lock release must not be allowed" in checked.stdout


def test_simulate_sandbox_recovery_rejects_tampered_integrated_hash(tmp_path: Path) -> None:
    root = prepare_repo(tmp_path)
    report_path, audit_path, _audit = build_audit_for_success(root)
    report = yaml.safe_load(report_path.read_text(encoding="utf-8"))
    report["operator"] = "other"
    report_path.write_text(yaml.safe_dump(report, sort_keys=False), encoding="utf-8")

    result = run_simulation(root, report_path, audit_path)
    assert result.returncode == 2
    assert "integrated run hash does not match" in result.stderr
