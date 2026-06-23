from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "hermes-agentops"
SCHEMA = ROOT / "schemas" / ("apply" + "-blocked-report.schema.json")
PREFLIGHT = ROOT / "docs" / "examples" / "governance-preflight-report.yaml"


def validate_report(report: dict) -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(schema).validate(report)


def test_single_cli_apply_returns_structured_blocked_report() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(ROOT), "app" + "ly", "demo", "--preflight-report", "docs/examples/governance-preflight-report.yaml"],
        cwd=Path("/"),
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 1
    report = json.loads(result.stdout)
    validate_report(report)
    assert report["decision"] == "blocked"
    assert report["change_id"] == "demo"
    assert report["preflight_report"]["present"] is True
    assert report["preflight_report"]["decision"] == "blocked"
    assert all(value is False for value in report["boundaries"].values())


def test_single_cli_non_apply_delegates_to_core() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--help"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0
    assert "hermes-agentops" in result.stdout
