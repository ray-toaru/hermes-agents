from __future__ import annotations

from pathlib import Path

import yaml

from agentops_test_utils import run_script

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "scripts" / "build-production-audit-closeout-dry-run"
CHANGE_ID = "20260530T000000Z_agentops_aaaaaaaaaa"


def run_builder(*args: str):
    return run_script(BUILDER, CHANGE_ID, "--root", str(ROOT), *args)


def test_success_closeout_candidate_is_conservative() -> None:
    result = run_builder("--outcome", "success", "--start-ref", "audit-start:1", "--completion-ref", "audit-success:1")
    assert result.returncode == 0, result.stdout + result.stderr
    document = yaml.safe_load(result.stdout)
    assert document["outcome"] == "success"
    assert document["completion_ref"] == "audit-success:1"
    assert document["failure_ref"] is None
    assert document["release_allowed"] is False
    assert document["apply_authorized"] is False
    assert document["production_record_written"] is False


def test_failure_closeout_candidate_is_conservative() -> None:
    result = run_builder("--outcome", "failure", "--start-ref", "audit-start:1", "--failure-ref", "audit-failure:1")
    assert result.returncode == 0, result.stdout + result.stderr
    document = yaml.safe_load(result.stdout)
    assert document["outcome"] == "failure"
    assert document["completion_ref"] is None
    assert document["failure_ref"] == "audit-failure:1"
    assert document["lock_guard_preserved"] is True
    assert document["release_allowed"] is False


def test_success_requires_completion_ref() -> None:
    result = run_builder("--outcome", "success", "--start-ref", "audit-start:1")
    assert result.returncode == 2
    assert "completion-ref" in result.stderr
    assert result.stdout == ""


def test_failure_rejects_completion_ref() -> None:
    result = run_builder(
        "--outcome",
        "failure",
        "--start-ref",
        "audit-start:1",
        "--completion-ref",
        "audit-success:1",
        "--failure-ref",
        "audit-failure:1",
    )
    assert result.returncode == 2
    assert "must not include" in result.stderr
    assert result.stdout == ""
