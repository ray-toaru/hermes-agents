from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any

import jsonschema
import yaml

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run-governance-preflight"
SCHEMA = ROOT / "schemas" / "governance-preflight-report.schema.json"


def write_yaml(path: Path, data: dict[str, Any]) -> None:
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def base_inputs(tmp_path: Path) -> dict[str, Path]:
    paths = {
        "approval": tmp_path / "approval.yaml",
        "lock": tmp_path / "lock.yaml",
        "audit": tmp_path / "audit.yaml",
        "command": tmp_path / "command.yaml",
        "runtime": tmp_path / "runtime.yaml",
        "stage": tmp_path / "stage.yaml",
    }
    write_yaml(paths["approval"], {"approval_reviews": [{"reviewer": "alice"}], "no_rejections_present": True})
    write_yaml(paths["lock"], {"current_state": "not_acquired"})
    write_yaml(paths["audit"], {"production_record_written": False, "release_allowed": False, "apply_authorized": False})
    write_yaml(paths["command"], {"state_changed": False, "guard_released": False})
    write_yaml(paths["runtime"], {"domains": [{"name": "runtime_logs", "current_access_allowed": False, "mutation_allowed": False, "protected_value_read_allowed": False}]})
    write_yaml(paths["stage"], {"decision": "deferred", "next_stage_allowed": False, "apply_authorized": False, "real_apply_implementation_allowed": False})
    return paths


def run_preflight(paths: dict[str, Path]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--approval-source",
            str(paths["approval"]),
            "--lock-source",
            str(paths["lock"]),
            "--audit-closeout",
            str(paths["audit"]),
            "--command-validation",
            str(paths["command"]),
            "--runtime-policy",
            str(paths["runtime"]),
            "--stage-readiness",
            str(paths["stage"]),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_preflight_report_is_blocked_and_schema_valid(tmp_path: Path) -> None:
    result = run_preflight(base_inputs(tmp_path))
    assert result.returncode == 0, result.stderr
    report = yaml.safe_load(result.stdout)
    schema = yaml.safe_load(SCHEMA.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(schema).validate(report)
    assert report["decision"] == "blocked"
    assert report["boundaries"] == {
        "apply_authorized": False,
        "mutation_allowed": False,
        "lock_acquire_allowed": False,
        "audit_write_allowed": False,
        "command_execution_allowed": False,
    }
    assert "real_apply_deferred" in report["blockers"]


def test_preflight_flags_runtime_access_request(tmp_path: Path) -> None:
    paths = base_inputs(tmp_path)
    write_yaml(paths["runtime"], {"domains": [{"name": "runtime_logs", "current_access_allowed": True, "mutation_allowed": False, "protected_value_read_allowed": False}]})
    result = run_preflight(paths)
    assert result.returncode == 0, result.stderr
    report = yaml.safe_load(result.stdout)
    assert "runtime_access_requested" in report["blockers"]


def test_preflight_rejects_missing_input(tmp_path: Path) -> None:
    paths = base_inputs(tmp_path)
    paths["lock"].unlink()
    result = run_preflight(paths)
    assert result.returncode != 0
    assert "preflight input error" in result.stderr
