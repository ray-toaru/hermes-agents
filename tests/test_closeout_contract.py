from __future__ import annotations

from pathlib import Path
from typing import Any

import jsonschema
import yaml

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "production-audit-closeout.schema.json"
OK = ROOT / "docs" / "examples" / "production-audit-closeout-success.yaml"
ERR = ROOT / "docs" / "examples" / "production-audit-closeout-failure.yaml"


def load(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def errors(data: dict[str, Any]) -> list[str]:
    schema = yaml.safe_load(SCHEMA.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)
    return [item.message for item in validator.iter_errors(data)]


def test_examples_are_valid() -> None:
    assert errors(load(OK)) == []
    assert errors(load(ERR)) == []


def test_allow_flag_stays_false() -> None:
    data = load(OK)
    data["release_allowed"] = True
    assert errors(data)


def test_outcome_refs_are_required() -> None:
    data = load(ERR)
    data["failure_ref"] = None
    assert errors(data)
    data = load(OK)
    data["completion_ref"] = None
    assert errors(data)
