from __future__ import annotations

from pathlib import Path
from typing import Any

import jsonschema
import yaml

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "recovery-stage-adr.schema.json"
EXAMPLE = ROOT / "docs" / "examples" / "recovery-stage-adr.yaml"


def load_example() -> dict[str, Any]:
    return yaml.safe_load(EXAMPLE.read_text(encoding="utf-8"))


def validate(data: dict[str, Any]) -> list[str]:
    schema = yaml.safe_load(SCHEMA.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)
    return [error.message for error in validator.iter_errors(data)]


def test_stage_adr_example_is_valid() -> None:
    assert validate(load_example()) == []


def test_stage_remains_deferred() -> None:
    data = load_example()
    data["status"] = "open"
    assert validate(data)


def test_runner_remains_disabled() -> None:
    data = load_example()
    data["runner_enabled"] = True
    assert validate(data)


def test_prerequisites_are_required() -> None:
    data = load_example()
    data["live_approval_required"] = False
    assert validate(data)
