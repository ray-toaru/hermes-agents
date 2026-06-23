from __future__ import annotations

from pathlib import Path
from typing import Any

import jsonschema
import yaml

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "docs" / "examples" / "stage-readiness-v4.yaml"
SCHEMA = ROOT / "schemas" / "stage-readiness-v4.schema.json"


def load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def validate(data: dict[str, Any]) -> list[str]:
    schema = load_yaml(SCHEMA)
    validator = jsonschema.Draft202012Validator(schema)
    return [error.message for error in validator.iter_errors(data)]


def test_stage_readiness_v4_example_is_valid() -> None:
    assert validate(load_yaml(EXAMPLE)) == []


def test_stage_readiness_v4_lists_p7_evidence() -> None:
    data = load_yaml(EXAMPLE)
    names = {item["name"] for item in data["p7_evidence"]}
    assert names == {
        "github_approval_network_source",
        "production_lock_path_dry_run",
        "production_audit_closeout_dry_run",
        "command_dry_run_validation",
        "runtime_adjacent_policy",
    }
    assert data["decision"] == "deferred"
    assert data["next_stage_allowed"] is False
    assert data["apply_authorized"] is False
    assert data["real_apply_implementation_allowed"] is False


def test_rejects_next_stage_allowed() -> None:
    data = load_yaml(EXAMPLE)
    data["next_stage_allowed"] = True
    assert validate(data) != []


def test_rejects_apply_authorized() -> None:
    data = load_yaml(EXAMPLE)
    data["apply_authorized"] = True
    assert validate(data) != []


def test_rejects_real_apply_implementation_allowed() -> None:
    data = load_yaml(EXAMPLE)
    data["real_apply_implementation_allowed"] = True
    assert validate(data) != []
