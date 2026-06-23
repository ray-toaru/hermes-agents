from __future__ import annotations

from pathlib import Path

import jsonschema
import yaml

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "stage-readiness-v6.schema.json"
EXAMPLE = ROOT / "docs" / "examples" / "stage-readiness-v6.yaml"


def validate(data: dict) -> list[str]:
    schema = yaml.safe_load(SCHEMA.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)
    return [error.message for error in validator.iter_errors(data)]


def test_example_is_valid() -> None:
    assert validate(yaml.safe_load(EXAMPLE.read_text(encoding="utf-8"))) == []


def test_next_stage_remains_disallowed() -> None:
    data = yaml.safe_load(EXAMPLE.read_text(encoding="utf-8"))
    data["next_stage_allowed"] = True
    assert validate(data)


def test_apply_remains_unauthorized() -> None:
    data = yaml.safe_load(EXAMPLE.read_text(encoding="utf-8"))
    data["apply_authorized"] = True
    assert validate(data)
