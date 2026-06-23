from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

from apply_blocked_helpers import load_apply_blocked_report

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / ("run-" + "apply" + "-entrypoint-blocked")
PREFLIGHT = ROOT / "docs" / "examples" / "governance-preflight-report.yaml"


def run_entrypoint(*args: str) -> dict[str, Any]:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    return load_apply_blocked_report(result)


def test_entrypoint_reports_blocked_with_preflight() -> None:
    report = run_entrypoint("demo", "--preflight-report", str(PREFLIGHT))
    assert report["decision"] == "blocked"
    assert report["change_id"] == "demo"
    assert report["preflight_report"]["present"] is True
    assert report["preflight_report"]["decision"] == "blocked"
    assert all(value is False for value in report["boundaries"].values())
    assert "real_apply_deferred" in report["blockers"]


def test_entrypoint_reports_missing_preflight() -> None:
    report = run_entrypoint("demo")
    assert report["preflight_report"]["present"] is False
    assert "preflight_report_not_provided" in report["blockers"]


def test_entrypoint_reports_unblocked_preflight_as_blocked(tmp_path: Path) -> None:
    path = tmp_path / "preflight.yaml"
    path.write_text(yaml.safe_dump({"decision": "ready"}), encoding="utf-8")
    report = run_entrypoint("demo", "--preflight-report", str(path))
    assert report["preflight_report"]["decision"] == "ready"
    assert "preflight_not_blocked" in report["blockers"]
    assert all(value is False for value in report["boundaries"].values())
