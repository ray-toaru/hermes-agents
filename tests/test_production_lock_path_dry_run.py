from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

import yaml

from agentops_test_utils import run_script

ROOT = Path(__file__).resolve().parents[1]
COLLECTOR = ROOT / "scripts" / "collect-production-lock-readiness-source"
VERIFIER = ROOT / "scripts" / "verify-production-lock-readiness-source"
CHANGE_ID = "20260530T000000Z_agentops_aaaaaaaaaa"
HEAD_SHA = "a" * 40
REPOSITORY = "ray-toaru/hermes-agents"


def lock_id() -> str:
    return hashlib.sha256(f"{REPOSITORY}\n{CHANGE_ID}\n{HEAD_SHA}".encode("utf-8")).hexdigest()[:32]


def run_collector(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return run_script(
        COLLECTOR,
        CHANGE_ID,
        "--root",
        str(root),
        "--commit-sha",
        HEAD_SHA,
        "--lock-root",
        "locks",
        "--captured-at",
        "2026-05-30T00:03:00Z",
        *args,
    )


def verify_source(source_root: Path, source_text: str) -> dict[str, object]:
    path = source_root / "lock-source.yaml"
    path.write_text(source_text, encoding="utf-8")
    result = run_script(
        VERIFIER,
        CHANGE_ID,
        "--root",
        str(ROOT),
        "--source",
        str(path),
        "--verified-at",
        "2026-05-30T00:04:00Z",
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return yaml.safe_load(result.stdout)


def test_missing_lock_record_emits_conservative_source(tmp_path: Path) -> None:
    collected = run_collector(tmp_path)
    assert collected.returncode == 0, collected.stdout + collected.stderr
    source = yaml.safe_load(collected.stdout)
    assert source["lock_id"] == lock_id()
    assert source["current_state"] == "not_acquired"

    report = verify_source(tmp_path, collected.stdout)
    assert report["acquire_allowed"] is False
    assert report["release_allowed"] is False
    assert report["preserve_guard"] is True


def test_existing_bound_record_is_read_without_writes(tmp_path: Path) -> None:
    lock_root = tmp_path / "locks"
    lock_root.mkdir()
    lock_path = lock_root / f"{lock_id()}.yaml"
    lock_path.write_text(
        yaml.safe_dump(
            {
                "lock_id": lock_id(),
                "lock_owner": "agentops:operator",
                "lock_commit_sha": HEAD_SHA,
                "current_state": "acquired",
                "completion_audit_present": True,
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    before = lock_path.read_text(encoding="utf-8")
    collected = run_collector(tmp_path)
    after = lock_path.read_text(encoding="utf-8")
    assert collected.returncode == 0, collected.stdout + collected.stderr
    assert after == before

    report = verify_source(tmp_path, collected.stdout)
    assert report["current_state"] == "acquired"
    assert report["acquire_allowed"] is False
    assert report["release_allowed"] is False


def test_mismatched_record_commit_fails_closed(tmp_path: Path) -> None:
    lock_root = tmp_path / "locks"
    lock_root.mkdir()
    (lock_root / f"{lock_id()}.yaml").write_text(
        yaml.safe_dump(
            {
                "lock_id": lock_id(),
                "lock_owner": "agentops:operator",
                "lock_commit_sha": "b" * 40,
                "current_state": "acquired",
                "completion_audit_present": True,
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    collected = run_collector(tmp_path)
    assert collected.returncode == 2
    assert "commit mismatch" in collected.stderr
    assert collected.stdout == ""


def test_unsafe_lock_root_fails_closed(tmp_path: Path) -> None:
    result = run_collector(tmp_path, "--lock-root", "../locks")
    assert result.returncode == 2
    assert "repository-relative" in result.stderr
