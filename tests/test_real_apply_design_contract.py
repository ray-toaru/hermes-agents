from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import jsonschema
import yaml

from agentops_test_utils import run_script

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts" / "check-real-apply-design-contract"
EXAMPLE = ROOT / "docs" / "examples" / "real-apply-design-contract.yaml"


def load_example() -> dict[str, Any]:
    return yaml.safe_load(EXAMPLE.read_text(encoding="utf-8"))


def write_yaml(path: Path, data: dict[str, Any]) -> Path:
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return path


def validate_schema(record: dict[str, Any]) -> None:
    schema = json.loads((ROOT / "schemas" / "real-apply-design-contract.schema.json").read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)
    validator = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())
    errors = list(validator.iter_errors(record))
    assert not errors, [error.message for error in errors]


def test_real_apply_design_contract_example_is_valid() -> None:
    record = load_example()
    validate_schema(record)

    result = run_script(CHECKER, str(EXAMPLE), "--root", str(ROOT))
    assert result.returncode == 0, result.stdout + result.stderr
    assert record["design_status"]["design_only"] is True
    assert record["design_status"]["ready_to_implement_real_apply"] is False
    assert record["design_status"]["ready_to_enable_real_apply"] is False
    assert record["design_status"]["apply_must_remain_disabled"] is True


def test_real_apply_design_contract_rejects_implementation_permission(tmp_path: Path) -> None:
    record = load_example()
    record["design_status"]["ready_to_implement_real_apply"] = True
    path = write_yaml(tmp_path / "contract.yaml", record)

    result = run_script(CHECKER, str(path), "--root", str(ROOT))
    assert result.returncode == 1
    assert "ready_to_implement_real_apply" in result.stdout


def test_real_apply_design_contract_rejects_feature_flag_enablement(tmp_path: Path) -> None:
    record = load_example()
    record["design_status"]["feature_flag_allowed"] = True
    path = write_yaml(tmp_path / "contract.yaml", record)

    result = run_script(CHECKER, str(path), "--root", str(ROOT))
    assert result.returncode == 1
    assert "feature_flag_allowed" in result.stdout


def test_real_apply_design_contract_rejects_missing_required_doc_phrase(tmp_path: Path) -> None:
    doc_path = tmp_path / "doc.md"
    doc_path.write_text("# Stub\nStatus: **design-only**\n", encoding="utf-8")
    record = load_example()
    record["design_documents"]["pipeline_design"]["path"] = str(doc_path.relative_to(ROOT)) if doc_path.is_relative_to(ROOT) else str(doc_path)
    path = write_yaml(tmp_path / "contract.yaml", record)

    result = run_script(CHECKER, str(path), "--root", str(ROOT))
    assert result.returncode == 1
    assert "unsafe" in result.stdout or "missing required phrase" in result.stdout


def test_real_apply_design_contract_rejects_missing_pipeline_stage(tmp_path: Path) -> None:
    record = load_example()
    record["pipeline_stages"] = [item for item in record["pipeline_stages"] if item["stage"] != "post_apply_validation"]
    path = write_yaml(tmp_path / "contract.yaml", record)

    result = run_script(CHECKER, str(path), "--root", str(ROOT))
    assert result.returncode == 1
    assert "missing required pipeline stages" in result.stdout


def test_real_apply_design_contract_rejects_out_of_order_stage(tmp_path: Path) -> None:
    record = load_example()
    for item in record["pipeline_stages"]:
        if item["stage"] == "mutation_command_dispatch":
            item["order"] = 6
    path = write_yaml(tmp_path / "contract.yaml", record)

    result = run_script(CHECKER, str(path), "--root", str(ROOT))
    assert result.returncode == 1
    assert "mutation_command_dispatch" in result.stdout


def test_real_apply_design_contract_rejects_missing_production_blocker(tmp_path: Path) -> None:
    record = load_example()
    record["production_blockers"] = [
        item for item in record["production_blockers"] if item["blocker"] != "production recovery state machine is not implemented"
    ]
    path = write_yaml(tmp_path / "contract.yaml", record)

    result = run_script(CHECKER, str(path), "--root", str(ROOT))
    assert result.returncode == 1
    assert "missing production blockers" in result.stdout


def test_real_apply_design_contract_checks_apply_remains_disabled() -> None:
    result = run_script(ROOT / "scripts" / "hermes-agentops", "apply", "probe")
    assert result.returncode != 0
    assert "not implemented" in (result.stdout + result.stderr)
