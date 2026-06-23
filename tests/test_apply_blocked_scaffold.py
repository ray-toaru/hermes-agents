from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import jsonschema
import yaml

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / ("run-" + "apply" + "-blocked-scaffold")
SCHEMA = ROOT / "schemas" / ("apply" + "-blocked-report.schema.json")
EXAMPLE = ROOT / "docs" / "examples" / ("apply" + "-blocked-report.yaml")
PREFLIGHT = ROOT / "docs" / "examples" / "governance-preflight-report.yaml"


def validate_report(report: dict) -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(schema).validate(report)


def test_example_report_is_valid() -> None:
    validate_report(yaml.safe_load(EXAMPLE.read_text(encoding="utf-8")))


def test_helper_outputs_blocked_report() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--change-id", "demo", "--preflight-report", str(PREFLIGHT)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 1
    report = json.loads(result.stdout)
    validate_report(report)
    assert report["decision"] == "blocked"
    assert report["preflight_report"]["decision"] == "blocked"
    assert all(value is False for value in report["boundaries"].values())


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
