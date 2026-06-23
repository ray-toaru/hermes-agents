from __future__ import annotations

from pathlib import Path
from typing import Any

import jsonschema
import yaml

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "docs" / "examples" / "stage-readiness-v5.yaml"
SCHEMA = ROOT / "schemas" / "stage-readiness-v5.schema.json"


def load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_stage_readiness_v5_validates() -> None:
    schema = load_yaml(SCHEMA)
    data = load_yaml(EXAMPLE)
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.Draft202012Validator(schema).validate(data)


def test_stage_readiness_v5_remains_deferred() -> None:
    data = load_yaml(EXAMPLE)
    assert data["decision"] == "deferred"
    assert data["next_stage_allowed"] is False
    assert data["apply_authorized"] is False
    assert data["real_apply_implementation_allowed"] is False
