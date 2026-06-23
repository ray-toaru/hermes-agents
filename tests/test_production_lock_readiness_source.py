from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import yaml

from agentops_test_utils import run_script

ROOT = Path(__file__).resolve().parents[1]
VERIFIER = ROOT / "scripts" / "verify-production-lock-readiness-source"
CHANGE_ID = "20260608T000000Z_agentops-manager_0123456789"
LOCK_SHA = "a" * 40


def write_source(path: Path, **overrides: Any) -> Path:
    document: dict[str, Any] = {
        "schema_version": 1,
        "source_id": f"{CHANGE_ID}_lock_source",
        "repository": {"full_name": "ray-toaru/hermes-agents", "default_branch": "main"},
        "change_id": CHANGE_ID,
        "lock_id": "lock/agentops-manager/main",
        "lock_owner": "agentops-manager:tester",
        "lock_commit_sha": LOCK_SHA,
        "current_state": "preserved_for_review",
        "completion_audit_present": False,
        "requested_decision": "readiness",
        "captured_at": "2026-06-08T00:01:00Z",
    }
    document.update(overrides)
    path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
    return path


def run_verifier(source: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return run_script(
        VERIFIER,
        CHANGE_ID,
        "--root",
        str(ROOT),
        "--source",
        str(source),
        "--verified-at",
        "2026-06-08T00:02:00Z",
        *args,
    )


def test_lock_readiness_source_emits_conservative_report(tmp_path: Path) -> None:
    source = write_source(tmp_path / "lock-source.yaml")
    result = run_verifier(source)
    assert result.returncode == 0, result.stdout + result.stderr
    report = yaml.safe_load(result.stdout)
    assert report["mutation_enabled"] is False
    assert report["acquire_allowed"] is False
    assert report["release_allowed"] is False
    assert report["preserve_guard"] is True
    assert report["manual_review_required"] is True
    assert report["assertions"]["does_not_release_lock"] is True


def test_lock_readiness_source_preserves_guard_without_completion_audit(tmp_path: Path) -> None:
    source = write_source(tmp_path / "lock-source.yaml", current_state="acquired", completion_audit_present=False)
    result = run_verifier(source)
    assert result.returncode == 0, result.stdout + result.stderr
    report = yaml.safe_load(result.stdout)
    assert report["preserve_guard"] is True
    assert report["release_allowed"] is False


def test_lock_readiness_source_rejects_repository_mismatch(tmp_path: Path) -> None:
    source = write_source(tmp_path / "lock-source.yaml", repository={"full_name": "other/repo", "default_branch": "main"})
    result = run_verifier(source)
    assert result.returncode == 2
    assert "repository full_name mismatch" in result.stderr
    assert result.stdout == ""


def test_lock_readiness_source_rejects_unbound_owner(tmp_path: Path) -> None:
    source = write_source(tmp_path / "lock-source.yaml", lock_owner="other-agent:tester")
    result = run_verifier(source)
    assert result.returncode == 2
    assert "lock_owner" in result.stderr
    assert result.stdout == ""


def test_lock_readiness_source_rejects_invalid_state(tmp_path: Path) -> None:
    source = write_source(tmp_path / "lock-source.yaml", current_state="released")
    result = run_verifier(source)
    assert result.returncode == 2
    assert "current_state" in result.stderr
    assert result.stdout == ""
