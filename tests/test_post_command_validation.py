from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import jsonschema
import yaml

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "post-command-validation.schema.json"
EXAMPLE = ROOT / "docs" / "examples" / "post-command-validation.yaml"


def load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def errors(data: dict[str, Any]) -> list[str]:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)
    found = [error.message for error in validator.iter_errors(data)]
    if data.get("state_changed") is not False:
        found.append("state_changed must be false")
    if data.get("guard_released") is not False:
        found.append("guard_released must be false")
    if data.get("followup_required") is not True:
        found.append("followup_required must be true")
    return found


def test_example_is_valid() -> None:
    assert errors(load_yaml(EXAMPLE)) == []


def test_rejects_state_changed() -> None:
    data = load_yaml(EXAMPLE)
    data["state_changed"] = True
    assert any("state_changed" in error for error in errors(data))


def test_rejects_guard_release() -> None:
    data = load_yaml(EXAMPLE)
    data["guard_released"] = True
    assert any("guard_released" in error for error in errors(data))


def test_requires_followup() -> None:
    data = load_yaml(EXAMPLE)
    data["followup_required"] = False
    assert any("followup_required" in error for error in errors(data))
