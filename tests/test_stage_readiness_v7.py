from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import yaml

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "stage-readiness-v7.schema.json"
EXAMPLE = ROOT / "docs" / "examples" / "stage-readiness-v7.yaml"


def validate(data: dict) -> list[str]:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)
    return [error.message for error in validator.iter_errors(data)]


def test_example_is_valid() -> None:
    data = yaml.safe_load(EXAMPLE.read_text(encoding="utf-8"))
    assert validate(data) == []


def test_rejects_single_entrypoint_claim() -> None:
    data = yaml.safe_load(EXAMPLE.read_text(encoding="utf-8"))
    data["single_cli_entrypoint_integrated"] = True
    assert any("False was expected" in error for error in validate(data))


def test_rejects_apply_authorization() -> None:
    data = yaml.safe_load(EXAMPLE.read_text(encoding="utf-8"))
    data["apply_authorized"] = True
    assert any("False was expected" in error for error in validate(data))
