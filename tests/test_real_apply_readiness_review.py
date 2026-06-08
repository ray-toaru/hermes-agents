from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import jsonschema
import yaml

from agentops_test_utils import run_script

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts" / "check-real-apply-readiness-review"
EXAMPLE = ROOT / "docs" / "examples" / "p5-real-apply-readiness-review-v2.yaml"


def load_example() -> dict[str, Any]:
    return yaml.safe_load(EXAMPLE.read_text(encoding="utf-8"))


def write_yaml(path: Path, data: dict[str, Any]) -> Path:
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return path


def validate_schema(record: dict[str, Any]) -> None:
    schema = json.loads((ROOT / "schemas" / "real-apply-readiness-review.schema.json").read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)
    validator = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())
    errors = list(validator.iter_errors(record))
    assert not errors, [error.message for error in errors]


def test_real_apply_readiness_review_example_is_valid() -> None:
    record = load_example()
    validate_schema(record)

    result = run_script(CHECKER, str(EXAMPLE), "--root", str(ROOT))
    assert result.returncode == 0, result.stdout + result.stderr
    assert record["decision"]["ready_to_design_real_apply"] is True
    assert record["decision"]["ready_to_implement_real_apply"] is False
    assert record["decision"]["ready_to_enable_real_apply"] is False
    assert record["decision"]["apply_must_remain_disabled"] is True


def test_real_apply_readiness_review_rejects_implementation_authorization(tmp_path: Path) -> None:
    record = load_example()
    record["decision"]["ready_to_implement_real_apply"] = True
    path = write_yaml(tmp_path / "review.yaml", record)

    result = run_script(CHECKER, str(path), "--root", str(ROOT))
    assert result.returncode == 1
    assert "ready_to_implement_real_apply" in result.stdout


def test_real_apply_readiness_review_rejects_apply_enablement(tmp_path: Path) -> None:
    record = load_example()
    record["decision"]["apply_must_remain_disabled"] = False
    path = write_yaml(tmp_path / "review.yaml", record)

    result = run_script(CHECKER, str(path), "--root", str(ROOT))
    assert result.returncode == 1
    assert "apply_must_remain_disabled" in result.stdout or "True was expected" in result.stdout


def test_real_apply_readiness_review_requires_unique_required_gates(tmp_path: Path) -> None:
    record = load_example()
    record["gate_reviews"] = [item for item in record["gate_reviews"] if item["gate"] != "production_recovery"]
    path = write_yaml(tmp_path / "review.yaml", record)

    result = run_script(CHECKER, str(path), "--root", str(ROOT))
    assert result.returncode == 1
    assert "missing required gate" in result.stdout


def test_real_apply_readiness_review_rejects_unsafe_or_missing_paths(tmp_path: Path) -> None:
    record = load_example()
    record["gate_reviews"][0]["evidence_paths"] = ["../outside"]
    path = write_yaml(tmp_path / "review.yaml", record)

    result = run_script(CHECKER, str(path), "--root", str(ROOT))
    assert result.returncode == 1
    assert "unsafe path" in result.stdout or "does not match" in result.stdout


def test_real_apply_readiness_review_requires_blockers_for_production_lifecycle(tmp_path: Path) -> None:
    record = load_example()
    for item in record["gate_reviews"]:
        if item["gate"] == "production_audit_capture":
            item["blocks_implementation"] = False
    path = write_yaml(tmp_path / "review.yaml", record)

    result = run_script(CHECKER, str(path), "--root", str(ROOT))
    assert result.returncode == 1
    assert "production_audit_capture must block" in result.stdout
