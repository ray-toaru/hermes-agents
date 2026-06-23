from __future__ import annotations

from pathlib import Path

import jsonschema
import yaml

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "guard-write-path-decision.schema.json"
EXAMPLE = ROOT / "docs" / "examples" / "guard-write-path-decision.yaml"


def validate(data: dict) -> list[str]:
    schema = yaml.safe_load(SCHEMA.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)
    return [error.message for error in validator.iter_errors(data)]


def test_example_is_valid() -> None:
    assert validate(yaml.safe_load(EXAMPLE.read_text(encoding="utf-8"))) == []


def test_guard_write_remains_disabled() -> None:
    data = yaml.safe_load(EXAMPLE.read_text(encoding="utf-8"))
    data["guard_write_enabled"] = True
    assert validate(data)


def test_release_remains_disabled() -> None:
    data = yaml.safe_load(EXAMPLE.read_text(encoding="utf-8"))
    data["release_enabled"] = True
    assert validate(data)
