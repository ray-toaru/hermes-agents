from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import jsonschema
import yaml

ROOT = Path(__file__).resolve().parents[1]
TAXONOMY = ROOT / "docs" / "examples" / "governance-blockers.yaml"
SCHEMA = ROOT / "schemas" / "governance-blockers.schema.json"
PREFLIGHT = ROOT / "scripts" / "run-governance-preflight"


def load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_governance_blocker_taxonomy_validates() -> None:
    schema = load_yaml(SCHEMA)
    data = load_yaml(TAXONOMY)
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.Draft202012Validator(schema).validate(data)


def test_blocker_codes_are_unique() -> None:
    data = load_yaml(TAXONOMY)
    codes = [item["code"] for item in data["blockers"]]
    assert sorted(codes) == sorted(set(codes))


def test_preflight_emitted_blockers_are_taxonomized() -> None:
    data = load_yaml(TAXONOMY)
    known = {item["code"] for item in data["blockers"]}
    script = PREFLIGHT.read_text(encoding="utf-8")
    emitted = set(re.findall(r'blockers\.append\("([a-z0-9_]+)"\)', script))
    emitted.add("real_apply_deferred")
    assert emitted <= known
