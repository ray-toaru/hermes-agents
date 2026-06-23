from __future__ import annotations

from pathlib import Path
from typing import Any

import jsonschema
import yaml

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "docs" / "examples" / "runtime-adjacent-policy.yaml"
SCHEMA = ROOT / "schemas" / "runtime-adjacent-policy.schema.json"


def load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def validate(data: dict[str, Any]) -> list[str]:
    schema = load_yaml(SCHEMA)
    validator = jsonschema.Draft202012Validator(schema)
    return [error.message for error in validator.iter_errors(data)]


def test_runtime_adjacent_policy_example_is_valid() -> None:
    assert validate(load_yaml(EXAMPLE)) == []


def test_all_runtime_adjacent_domains_are_currently_denied() -> None:
    data = load_yaml(EXAMPLE)
    names = {domain["name"] for domain in data["domains"]}
    assert names == {"runtime_logs", "sessions", "gateway", "containers", "cron", "protected_values"}
    for domain in data["domains"]:
        assert domain["current_access_allowed"] is False
        assert domain["mutation_allowed"] is False
        assert domain["protected_value_read_allowed"] is False
        assert domain["requires_separate_adr"] is True


def test_rejects_current_access_enabled() -> None:
    data = load_yaml(EXAMPLE)
    data["domains"][0]["current_access_allowed"] = True
    assert validate(data) != []


def test_rejects_mutation_enabled() -> None:
    data = load_yaml(EXAMPLE)
    data["domains"][1]["mutation_allowed"] = True
    assert validate(data) != []


def test_rejects_protected_value_read_enabled() -> None:
    data = load_yaml(EXAMPLE)
    data["domains"][5]["protected_value_read_allowed"] = True
    assert validate(data) != []
