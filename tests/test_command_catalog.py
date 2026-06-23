from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import jsonschema
import yaml

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "command-catalog.schema.json"
EXAMPLE = ROOT / "docs" / "examples" / "command-catalog.yaml"


def load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def errors(data: dict[str, Any]) -> list[str]:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)
    found = [error.message for error in validator.iter_errors(data)]
    for entry in data.get("entries", []):
        if entry.get("run_allowed") is not False:
            found.append("run_allowed must be false")
        if entry.get("dispatch_allowed") is not False:
            found.append("dispatch_allowed must be false")
    return found


def test_example_is_valid() -> None:
    assert errors(load_yaml(EXAMPLE)) == []


def test_rejects_run_allowed() -> None:
    data = load_yaml(EXAMPLE)
    data["entries"][0]["run_allowed"] = True
    assert any("run_allowed" in error for error in errors(data))


def test_rejects_dispatch_allowed() -> None:
    data = load_yaml(EXAMPLE)
    data["entries"][0]["dispatch_allowed"] = True
    assert any("dispatch_allowed" in error for error in errors(data))
