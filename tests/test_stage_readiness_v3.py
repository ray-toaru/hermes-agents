from __future__ import annotations

from pathlib import Path
from typing import Any

import jsonschema
import yaml

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "stage-readiness-v3.schema.json"
EXAMPLE = ROOT / "docs" / "examples" / "stage-readiness-v3.yaml"


def load_example() -> dict[str, Any]:
    return yaml.safe_load(EXAMPLE.read_text(encoding="utf-8"))


def validate(data: dict[str, Any]) -> list[str]:
    schema = yaml.safe_load(SCHEMA.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)
    return [error.message for error in validator.iter_errors(data)]


def test_stage_readiness_v3_example_is_valid() -> None:
    assert validate(load_example()) == []


def test_decision_remains_deferred() -> None:
    data = load_example()
    data["decision"] = "approved"
    assert validate(data)


def test_next_stage_remains_closed() -> None:
    data = load_example()
    data["next_stage_allowed"] = True
    assert validate(data)


def test_missing_prerequisites_are_required() -> None:
    data = load_example()
    data["missing_prerequisites"] = []
    assert validate(data)
