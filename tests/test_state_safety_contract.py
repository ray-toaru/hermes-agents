from __future__ import annotations

from pathlib import Path
from typing import Any

import jsonschema
import yaml

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "docs" / "examples" / "state-safety-contract.yaml"
SCHEMA = ROOT / "schemas" / "state-safety-contract.schema.json"


def load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def validate(data: dict[str, Any]) -> list[str]:
    schema = yaml.safe_load(SCHEMA.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)
    errors = [error.message for error in validator.iter_errors(data)]
    for field in ["change_enabled", "change_done", "release_ok"]:
        if data.get(field) is not False:
            errors.append(f"{field} must be false")
    return errors


def test_example_is_valid() -> None:
    assert validate(load_yaml(EXAMPLE)) == []


def test_rejects_change_done() -> None:
    data = load_yaml(EXAMPLE)
    data["change_done"] = True
    assert any("change_done" in error for error in validate(data))


def test_rejects_release_ok() -> None:
    data = load_yaml(EXAMPLE)
    data["release_ok"] = True
    assert any("release_ok" in error for error in validate(data))
