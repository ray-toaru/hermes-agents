from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import jsonschema
import yaml

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "production-audit-capture-v2.schema.json"
SUCCESS = ROOT / "docs" / "examples" / "production-audit-capture-v2-success.yaml"
FAILURE = ROOT / "docs" / "examples" / "production-audit-capture-v2-failure.yaml"


def load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def errors(record: dict[str, Any]) -> list[str]:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)
    found = [error.message for error in validator.iter_errors(record)]
    if record.get("capture_enabled") is not False:
        found.append("capture_enabled must be false")
    if record.get("record_written") is not False:
        found.append("record_written must be false")
    return found


def test_success_and_failure_examples_are_valid() -> None:
    success = load_yaml(SUCCESS)
    failure = load_yaml(FAILURE)
    assert errors(success) == []
    assert errors(failure) == []
    assert success["path_kind"] == "success"
    assert failure["path_kind"] == "failure"


def test_rejects_enabled_capture() -> None:
    record = load_yaml(SUCCESS)
    record["capture_enabled"] = True
    assert any("capture_enabled" in error for error in errors(record))


def test_rejects_written_record_claim() -> None:
    record = load_yaml(FAILURE)
    record["record_written"] = True
    assert any("record_written" in error for error in errors(record))
