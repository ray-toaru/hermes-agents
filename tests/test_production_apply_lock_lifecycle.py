from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import jsonschema
import yaml

from agentops_test_utils import run_script

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts" / "check-production-apply-lock-lifecycle"
EXAMPLE = ROOT / "docs" / "examples" / "production-apply-lock-lifecycle.yaml"


def load_example() -> dict[str, Any]:
    return yaml.safe_load(EXAMPLE.read_text(encoding="utf-8"))


def write_yaml(path: Path, data: dict[str, Any]) -> Path:
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return path


def validate_schema(record: dict[str, Any]) -> None:
    schema = json.loads((ROOT / "schemas" / "production-apply-lock-lifecycle.schema.json").read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)
    validator = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())
    errors = list(validator.iter_errors(record))
    assert not errors, [error.message for error in errors]


def add_transition(record: dict[str, Any], start: str, end: str) -> None:
    record["allowed_transitions"].append({"from": start, "to": end, "requires": ["malicious extra transition"]})


def test_production_lock_lifecycle_example_is_valid() -> None:
    record = load_example()
    validate_schema(record)

    result = run_script(CHECKER, str(EXAMPLE), "--root", str(ROOT))
    assert result.returncode == 0, result.stdout + result.stderr
    assert record["design_only"] is True
    assert record["mutation_enabled"] is False
    assert record["apply_authorized"] is False
    assert record["lock_release_implemented"] is False


def test_rejects_release_implementation(tmp_path: Path) -> None:
    record = load_example()
    record["lock_release_implemented"] = True
    path = write_yaml(tmp_path / "contract.yaml", record)

    result = run_script(CHECKER, str(path), "--root", str(ROOT))
    assert result.returncode == 1
    assert "lock_release_implemented" in result.stdout


def test_rejects_unknown_state_auto_release(tmp_path: Path) -> None:
    record = load_example()
    record["release_rules"]["automatic_release_on_unknown_state"] = True
    path = write_yaml(tmp_path / "contract.yaml", record)

    result = run_script(CHECKER, str(path), "--root", str(ROOT))
    assert result.returncode == 1
    assert "automatic_release_on_unknown_state" in result.stdout


def test_rejects_release_from_wrong_state(tmp_path: Path) -> None:
    record = load_example()
    record["release_rules"]["release_allowed_only_from"] = ["audit_completed"]
    path = write_yaml(tmp_path / "contract.yaml", record)

    result = run_script(CHECKER, str(path), "--root", str(ROOT))
    assert result.returncode == 1
    assert "release_allowed_only_from" in result.stdout


def test_rejects_recovery_state_allowing_release(tmp_path: Path) -> None:
    record = load_example()
    for item in record["lifecycle_states"]:
        if item["state"] == "recovery_required":
            item["allows_release"] = True
    path = write_yaml(tmp_path / "contract.yaml", record)

    result = run_script(CHECKER, str(path), "--root", str(ROOT))
    assert result.returncode == 1
    assert "recovery_required" in result.stdout


def test_rejects_extra_transition_from_acquired_to_released(tmp_path: Path) -> None:
    record = load_example()
    add_transition(record, "acquired", "released")
    path = write_yaml(tmp_path / "contract.yaml", record)

    result = run_script(CHECKER, str(path), "--root", str(ROOT))
    assert result.returncode == 1
    assert "forbidden transition into released" in result.stdout
    assert "acquired" in result.stdout


def test_rejects_extra_transition_from_recovery_required_to_released(tmp_path: Path) -> None:
    record = load_example()
    add_transition(record, "recovery_required", "released")
    path = write_yaml(tmp_path / "contract.yaml", record)

    result = run_script(CHECKER, str(path), "--root", str(ROOT))
    assert result.returncode == 1
    assert "forbidden transition into released" in result.stdout
    assert "recovery_required" in result.stdout


def test_rejects_extra_transition_from_preserved_for_review_to_released(tmp_path: Path) -> None:
    record = load_example()
    add_transition(record, "preserved_for_review", "released")
    path = write_yaml(tmp_path / "contract.yaml", record)

    result = run_script(CHECKER, str(path), "--root", str(ROOT))
    assert result.returncode == 1
    assert "forbidden transition into released" in result.stdout
    assert "preserved_for_review" in result.stdout


def test_rejects_extra_transition_out_of_preserved_for_review(tmp_path: Path) -> None:
    record = load_example()
    add_transition(record, "preserved_for_review", "acquired")
    path = write_yaml(tmp_path / "contract.yaml", record)

    result = run_script(CHECKER, str(path), "--root", str(ROOT))
    assert result.returncode == 1
    assert "preserved_for_review is terminal" in result.stdout


def test_rejects_missing_evidence_binding(tmp_path: Path) -> None:
    record = load_example()
    record["required_evidence_bindings"].remove("production completion audit evidence")
    path = write_yaml(tmp_path / "contract.yaml", record)

    result = run_script(CHECKER, str(path), "--root", str(ROOT))
    assert result.returncode == 1
    assert "missing required evidence bindings" in result.stdout


def test_rejects_missing_design_doc_phrase(tmp_path: Path) -> None:
    doc_path = tmp_path / "doc.md"
    doc_path.write_text("# Stub\nStatus: **design/prototype-only**\n", encoding="utf-8")
    record = load_example()
    record["design_documents"]["lock_lifecycle_design"]["path"] = str(doc_path)
    path = write_yaml(tmp_path / "contract.yaml", record)

    result = run_script(CHECKER, str(path), "--root", str(ROOT))
    assert result.returncode == 1
    assert "unsafe" in result.stdout or "missing required phrase" in result.stdout


def test_apply_remains_disabled() -> None:
    result = run_script(ROOT / "scripts" / "hermes-agentops", "apply", "probe")
    assert result.returncode != 0
    assert "not implemented" in (result.stdout + result.stderr)
