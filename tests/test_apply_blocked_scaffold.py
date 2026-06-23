from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import jsonschema
import yaml

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / ("run-" + "apply" + "-blocked-scaffold")
PREFLIGHT_SCRIPT = ROOT / "scripts" / "run-governance-preflight"
SCHEMA = ROOT / "schemas" / ("apply" + "-blocked-report.schema.json")
EXAMPLE = ROOT / "docs" / "examples" / ("apply" + "-blocked-report.yaml")
PREFLIGHT = ROOT / "docs" / "examples" / "governance-preflight-report.yaml"


def validate_report(report: dict) -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(schema).validate(report)


def write_yaml(path: Path, data: dict) -> None:
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def test_example_report_is_valid() -> None:
    validate_report(yaml.safe_load(EXAMPLE.read_text(encoding="utf-8")))


def run_helper(path: Path) -> dict:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--change-id", "demo", "--preflight-report", str(path)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 1
    report = json.loads(result.stdout)
    validate_report(report)
    return report


def test_helper_outputs_blocked_report() -> None:
    report = run_helper(PREFLIGHT)
    assert report["decision"] == "blocked"
    assert report["preflight_report"]["decision"] == "blocked"
    assert all(value is False for value in report["boundaries"].values())


def test_generated_preflight_can_feed_helper(tmp_path: Path) -> None:
    approval = tmp_path / "approval.yaml"
    lock = tmp_path / "lock.yaml"
    audit = tmp_path / "audit.yaml"
    command = tmp_path / "command.yaml"
    runtime = tmp_path / "runtime.yaml"
    stage = tmp_path / "stage.yaml"
    preflight_path = tmp_path / "preflight.yaml"

    write_yaml(approval, {"approval_reviews": [{"reviewer": "alice"}], "no_rejections_present": True})
    write_yaml(lock, {"current_state": "not_acquired"})
    write_yaml(audit, {"production_record_written": False, "release_allowed": False, "apply_authorized": False})
    write_yaml(command, {"state_changed": False, "guard_released": False})
    write_yaml(runtime, {"domains": [{"name": "runtime_logs", "current_access_allowed": False, "mutation_allowed": False, "protected_value_read_allowed": False}]})
    write_yaml(stage, {"decision": "deferred", "next_stage_allowed": False, "apply_authorized": False, "real_apply_implementation_allowed": False})

    result = subprocess.run(
        [
            sys.executable,
            str(PREFLIGHT_SCRIPT),
            "--approval-source",
            str(approval),
            "--lock-source",
            str(lock),
            "--audit-closeout",
            str(audit),
            "--command-validation",
            str(command),
            "--runtime-policy",
            str(runtime),
            "--stage-readiness",
            str(stage),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    preflight_path.write_text(result.stdout, encoding="utf-8")
    report = run_helper(preflight_path)
    assert report["preflight_report"]["present"] is True
    assert "real_apply_deferred" in report["blockers"]


def test_helper_flags_missing_preflight_report() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--preflight-report", str(ROOT / "missing.yaml")],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 1
    report = json.loads(result.stdout)
    validate_report(report)
    assert "preflight_report_missing" in report["blockers"]
