from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import jsonschema
import yaml

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "governance-stage-gate.schema.json"
EXAMPLE = ROOT / "docs" / "examples" / "governance-stage-gate.yaml"


def load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def errors(data: dict[str, Any]) -> list[str]:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)
    found = [error.message for error in validator.iter_errors(data)]
    if data.get("stage_change_allowed") is not False:
        found.append("stage_change_allowed must be false")
    if data.get("implementation_allowed") is not False:
        found.append("implementation_allowed must be false")
    if data.get("current_decision") != "defer":
        found.append("current_decision must be defer")
    return found


def test_example_is_valid() -> None:
    assert errors(load_yaml(EXAMPLE)) == []


def test_rejects_stage_change_allowed() -> None:
    data = load_yaml(EXAMPLE)
    data["stage_change_allowed"] = True
    assert any("stage_change_allowed" in error for error in errors(data))


def test_rejects_implementation_allowed() -> None:
    data = load_yaml(EXAMPLE)
    data["implementation_allowed"] = True
    assert any("implementation_allowed" in error for error in errors(data))


def test_rejects_non_deferred_decision() -> None:
    data = load_yaml(EXAMPLE)
    data["current_decision"] = "approve"
    assert any("current_decision" in error for error in errors(data))
