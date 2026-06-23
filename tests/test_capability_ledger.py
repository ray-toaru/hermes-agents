from __future__ import annotations

from pathlib import Path
from typing import Any

import jsonschema
import yaml

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "docs" / "examples" / "capability-ledger.yaml"
SCHEMA = ROOT / "schemas" / "capability-ledger.schema.json"


def load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_ledger_schema_validates() -> None:
    schema = load_yaml(SCHEMA)
    data = load_yaml(LEDGER)
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.Draft202012Validator(schema).validate(data)


def test_present_ledger_paths_exist() -> None:
    data = load_yaml(LEDGER)
    missing = []
    for item in data["items"]:
        if item["status"] != "present":
            continue
        for rel in item["paths"]:
            if not (ROOT / rel).exists():
                missing.append(rel)
    assert missing == []


def test_recent_passive_targets_are_marked_present() -> None:
    data = load_yaml(LEDGER)
    statuses = {item["name"]: item["status"] for item in data["items"]}
    assert statuses["completion_index"] == "present"
    assert statuses["guard_review_notes"] == "present"
    assert statuses["final_handoff"] == "present"
    assert statuses["command_catalog"] == "present"
    assert statuses["post_command_validation"] == "present"
    assert statuses["governance_stage_gate"] == "present"
    assert statuses["github_approval_network_source"] == "present"


def test_non_present_items_have_notes() -> None:
    data = load_yaml(LEDGER)
    missing_notes = [item["name"] for item in data["items"] if item["status"] != "present" and not item.get("note")]
    assert missing_notes == []


def test_status_values_are_reviewable() -> None:
    data = load_yaml(LEDGER)
    assert {item["status"] for item in data["items"]} <= {"present", "planned", "blocked", "deferred"}
