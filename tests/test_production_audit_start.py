from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import jsonschema
import yaml

from agentops_test_utils import run_script

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts" / "check-production-audit-start"
EXAMPLE = ROOT / "docs" / "examples" / "production-audit-start.yaml"


def load_example() -> dict[str, Any]:
    return yaml.safe_load(EXAMPLE.read_text(encoding="utf-8"))


def write_yaml(path: Path, data: dict[str, Any]) -> Path:
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return path


def check_modified(tmp_path: Path, record: dict[str, Any]):
    path = write_yaml(tmp_path / "contract.yaml", record)
    return run_script(CHECKER, str(path), "--root", str(ROOT))


def test_production_audit_start_example_is_valid() -> None:
    record = load_example()
    schema = json.loads((ROOT / "schemas" / "production-audit-start.schema.json").read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)
    errors = list(jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker()).iter_errors(record))
    assert not errors, [error.message for error in errors]
    result = run_script(CHECKER, str(EXAMPLE), "--root", str(ROOT))
    assert result.returncode == 0, result.stdout + result.stderr
    assert record["design_only"] is True
    assert record["production_audit_written"] is False
    assert record["audit_sequence"]["mutation_command_dispatched"] is False


def test_rejects_written_audit_record_claim(tmp_path: Path) -> None:
    record = load_example()
    record["production_audit_written"] = True
    record["audit_start_record_created"] = True
    result = check_modified(tmp_path, record)
    assert result.returncode == 1
    assert "production_audit_written" in result.stdout
    assert "audit_start_record_created" in result.stdout


def test_rejects_mutation_dispatched_claim(tmp_path: Path) -> None:
    record = load_example()
    record["audit_sequence"]["mutation_command_dispatched"] = True
    result = check_modified(tmp_path, record)
    assert result.returncode == 1
    assert "mutation_command_dispatched" in result.stdout


def test_rejects_audit_start_failure_not_preserving_lock(tmp_path: Path) -> None:
    record = load_example()
    record["failure_policy"]["audit_start_write_failure_preserves_lock"] = False
    result = check_modified(tmp_path, record)
    assert result.returncode == 1
    assert "audit_start_write_failure_preserves_lock" in result.stdout


def test_rejects_missing_required_evidence_binding(tmp_path: Path) -> None:
    record = load_example()
    del record["evidence_bindings"]["structured_mutation_command_sha256"]
    result = check_modified(tmp_path, record)
    assert result.returncode == 1
    assert "missing evidence bindings" in result.stdout


def test_rejects_bad_evidence_hash(tmp_path: Path) -> None:
    record = load_example()
    record["evidence_bindings"]["readiness_report_sha256"] = "NOT-A-SHA"
    result = check_modified(tmp_path, record)
    assert result.returncode == 1
    assert "readiness_report_sha256" in result.stdout


def test_rejects_missing_production_audit_blocker(tmp_path: Path) -> None:
    record = load_example()
    record["production_blockers"] = [item for item in record["production_blockers"] if item != "production audit writing is not implemented"]
    result = check_modified(tmp_path, record)
    assert result.returncode == 1
    assert "missing production blockers" in result.stdout


def test_rejects_unsafe_design_doc_path(tmp_path: Path) -> None:
    record = load_example()
    record["design_documents"]["audit_capture_design"]["path"] = "../outside.md"
    result = check_modified(tmp_path, record)
    assert result.returncode == 1
    assert "audit_capture_design" in result.stdout or "unsafe" in result.stdout


def test_apply_remains_disabled() -> None:
    result = run_script(ROOT / "scripts" / "hermes-agentops", "apply", "probe")
    assert result.returncode != 0
    assert "not implemented" in (result.stdout + result.stderr)
