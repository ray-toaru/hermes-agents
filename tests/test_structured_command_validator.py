from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any

import yaml
from agentops_test_utils import run_script

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts" / "check-structured-command"
EMPTY_SHA = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"


def run_checker(root: Path, record: Path) -> subprocess.CompletedProcess[str]:
    return run_script(CHECKER, "--root", str(root), str(record))


def write_yaml(path: Path, data: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return path


def prepare_root(root: Path) -> Path:
    schemas = root / "schemas"
    schemas.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / "schemas" / "structured-command.schema.json", schemas / "structured-command.schema.json")
    return root


def valid_record() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "structured_command_id": "agentops_validate_profiles_structured_command",
        "created_at": "2026-05-31T00:00:00Z",
        "created_by": "pytest",
        "execution_enabled": False,
        "apply_authorized": False,
        "command": {
            "command_id": "agentops.validate-profiles",
            "command_class": "validation_only",
            "argv": ["python", "scripts/hermes-agentops", "validate", "-v"],
            "shell_allowed": False,
        },
        "working_directory": {"base": "repository_root", "path": "."},
        "environment": {
            "allowed_keys": ["PYTHONPATH"],
            "forbidden_keys": ["AWS_SECRET_ACCESS_KEY", "GITHUB_TOKEN", "HERMES_SECRET", "OPENAI_API_KEY"],
            "inherit_parent_environment": False,
        },
        "paths": {
            "read": ["profiles", "policies", "schemas", "scripts/hermes-agentops"],
            "write": [],
        },
        "timeout_seconds": 120,
        "redaction": {"secret_values_must_be_redacted": True, "capture_stdout": True, "capture_stderr": True},
        "exit_codes": {"success": [0], "failure_is_terminal": True},
        "output_capture": {
            "stdout_sha256": EMPTY_SHA,
            "stderr_sha256": EMPTY_SHA,
            "combined_redacted_summary_required": True,
        },
        "boundaries": {
            "does_not_execute_commands": True,
            "does_not_authorize_apply": True,
            "does_not_read_secret_values": True,
            "does_not_mutate_profiles_or_runtime": True,
            "business_orchestration_not_authorized": True,
        },
    }


def test_structured_command_checker_accepts_valid_record(tmp_path: Path) -> None:
    path = write_yaml(tmp_path / "structured-command.yaml", valid_record())
    result = run_checker(ROOT, path)
    assert result.returncode == 0, result.stdout + result.stderr


def test_structured_command_checker_rejects_execution_enabled(tmp_path: Path) -> None:
    record = valid_record()
    record["execution_enabled"] = True
    path = write_yaml(tmp_path / "structured-command.yaml", record)
    result = run_checker(ROOT, path)
    assert result.returncode == 1
    assert "execution_enabled" in result.stdout


def test_structured_command_checker_rejects_apply_authorized(tmp_path: Path) -> None:
    record = valid_record()
    record["apply_authorized"] = True
    path = write_yaml(tmp_path / "structured-command.yaml", record)
    result = run_checker(ROOT, path)
    assert result.returncode == 1
    assert "apply_authorized" in result.stdout


def test_structured_command_checker_rejects_shell_text(tmp_path: Path) -> None:
    record = valid_record()
    record["command"]["argv"] = ["sh", "-c", "python scripts/hermes-agentops validate; rm -rf profiles"]
    path = write_yaml(tmp_path / "structured-command.yaml", record)
    result = run_checker(ROOT, path)
    assert result.returncode == 1
    assert "shell metacharacters" in result.stdout


def test_structured_command_checker_rejects_sensitive_allowed_env(tmp_path: Path) -> None:
    record = valid_record()
    record["environment"]["allowed_keys"] = ["GITHUB_TOKEN"]
    path = write_yaml(tmp_path / "structured-command.yaml", record)
    result = run_checker(ROOT, path)
    assert result.returncode == 1
    assert "sensitive environment" in result.stdout


def test_structured_command_checker_rejects_unsafe_paths(tmp_path: Path) -> None:
    record = valid_record()
    record["paths"]["read"] = ["../profiles", "/tmp/hermes", "logs/run.txt", "profiles/agentops/.env"]
    path = write_yaml(tmp_path / "structured-command.yaml", record)
    result = run_checker(ROOT, path)
    assert result.returncode == 1
    assert "traversal" in result.stdout
    assert "absolute" in result.stdout
    assert "secret/runtime" in result.stdout


def test_structured_command_checker_rejects_write_paths(tmp_path: Path) -> None:
    record = valid_record()
    record["paths"]["write"] = ["profiles/agentops/SOUL.md"]
    path = write_yaml(tmp_path / "structured-command.yaml", record)
    result = run_checker(ROOT, path)
    assert result.returncode == 1
    assert "write paths must remain empty" in result.stdout


def test_structured_command_checker_rejects_mutation_class(tmp_path: Path) -> None:
    record = valid_record()
    record["command"]["command_class"] = "mutation"
    path = write_yaml(tmp_path / "structured-command.yaml", record)
    result = run_checker(ROOT, path)
    assert result.returncode == 1
    assert "validation_only" in result.stdout


def test_structured_command_checker_rejects_missing_output_hash(tmp_path: Path) -> None:
    record = valid_record()
    del record["output_capture"]["stdout_sha256"]
    path = write_yaml(tmp_path / "structured-command.yaml", record)
    result = run_checker(ROOT, path)
    assert result.returncode == 1
    assert "stdout_sha256" in result.stdout


def test_structured_command_checker_can_run_against_copied_schema(tmp_path: Path) -> None:
    root = prepare_root(tmp_path / "repo")
    path = write_yaml(tmp_path / "structured-command.yaml", valid_record())
    result = run_checker(root, path)
    assert result.returncode == 0, result.stdout + result.stderr
