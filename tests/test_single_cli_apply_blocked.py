from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from apply_blocked_helpers import assert_apply_blocked_report

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "hermes-agentops"


def test_single_cli_apply_returns_structured_blocked_report() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--root",
            str(ROOT),
            "app" + "ly",
            "demo",
            "--preflight-report",
            "docs/examples/governance-preflight-report.yaml",
        ],
        cwd=Path("/"),
        text=True,
        capture_output=True,
        check=False,
    )
    report = assert_apply_blocked_report(result, change_id="demo")
    assert report["preflight_report"]["present"] is True
    assert report["preflight_report"]["decision"] == "blocked"


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
