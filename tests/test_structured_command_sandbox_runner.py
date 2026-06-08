from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

import jsonschema
import yaml

from test_change_workflow import run_agentops
from test_structured_command_validator import valid_record, write_yaml
from agentops_test_utils import run_script

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "run-structured-command-sandbox"
CHANGE_ID = "20260530T000000Z_agentops_aaaaaaaaaa"


def prepare_runtime_root(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    for name in ("schemas", "policies", "profiles", "scripts", "inventory"):
        shutil.copytree(ROOT / name, root / name)
    return root


def run_runner(root: Path, record: Path) -> subprocess.CompletedProcess[str]:
    return run_script(RUNNER, "--root", str(root), str(record))


def hash_tree(path: Path) -> str:
    digest = __import__("hashlib").sha256()
    for file_path in sorted(item for item in path.rglob("*") if item.is_file()):
        digest.update(file_path.relative_to(path).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(file_path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def validate_run_report(root: Path, report: dict[str, Any]) -> None:
    schema = json.loads((root / "schemas" / "structured-command-run.schema.json").read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)
    validator = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())
    errors = list(validator.iter_errors(report))
    assert not errors, [error.message for error in errors]


def test_validation_only_runner_executes_allowlisted_command_in_sandbox(tmp_path: Path) -> None:
    root = prepare_runtime_root(tmp_path)
    record = valid_record()
    record_path = write_yaml(tmp_path / "structured-command.yaml", record)
    before = hash_tree(root / "profiles")

    result = run_runner(root, record_path)
    assert result.returncode == 0, result.stdout + result.stderr
    report = yaml.safe_load(result.stdout)
    validate_run_report(root, report)
    assert report["status"] == "success"
    assert report["sandbox_only"] is True
    assert report["execution_scope"] == "validation_only"
    assert report["command_id"] == "agentops.validate-profiles"
    assert report["input_argv_ignored_for_dispatch"] is True
    assert report["source_profiles_unchanged"] is True
    assert report["source_profile_hash_before"] == before
    assert report["source_profile_hash_after"] == before
    assert hash_tree(root / "profiles") == before

    apply_attempt = run_agentops(root, "apply", CHANGE_ID)
    assert apply_attempt.returncode == 1
    assert "intentionally not implemented" in apply_attempt.stdout


def test_runner_fails_closed_for_non_allowlisted_command(tmp_path: Path) -> None:
    root = prepare_runtime_root(tmp_path)
    record = valid_record()
    record["command"]["command_id"] = "agentops.unknown"
    record_path = write_yaml(tmp_path / "structured-command.yaml", record)

    result = run_runner(root, record_path)
    assert result.returncode == 2
    assert "not allowlisted" in result.stderr
    assert result.stdout == ""


def test_runner_fails_closed_for_mutation_class(tmp_path: Path) -> None:
    root = prepare_runtime_root(tmp_path)
    record = valid_record()
    record["command"]["command_class"] = "mutation"
    record_path = write_yaml(tmp_path / "structured-command.yaml", record)

    result = run_runner(root, record_path)
    assert result.returncode == 2
    assert "validation_only" in result.stderr or "validation_only" in result.stdout
    assert result.stdout == ""


def test_runner_fails_closed_for_write_paths(tmp_path: Path) -> None:
    root = prepare_runtime_root(tmp_path)
    record = valid_record()
    record["paths"]["write"] = ["profiles/agentops/SOUL.md"]
    record_path = write_yaml(tmp_path / "structured-command.yaml", record)

    result = run_runner(root, record_path)
    assert result.returncode == 2
    assert "write paths must remain empty" in result.stderr
    assert result.stdout == ""


def test_runner_ignores_record_argv_and_uses_registry(tmp_path: Path) -> None:
    root = prepare_runtime_root(tmp_path)
    record = valid_record()
    record["command"]["argv"] = ["python", "not-the-command"]
    record_path = write_yaml(tmp_path / "structured-command.yaml", record)

    result = run_runner(root, record_path)
    assert result.returncode == 0, result.stdout + result.stderr
    report = yaml.safe_load(result.stdout)
    assert report["status"] == "success"
    assert report["input_argv_ignored_for_dispatch"] is True
    assert report["command_id"] == "agentops.validate-profiles"
