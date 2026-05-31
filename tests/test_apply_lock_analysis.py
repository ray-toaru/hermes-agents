from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
ANALYZER = ROOT / "scripts" / "analyze-apply-locks"
NOW = "2026-05-30T00:00:00Z"


def run_analyzer(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python", str(ANALYZER), "--root", str(root), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def write_yaml(path: Path, data: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return path


def prepare_root(root: Path) -> Path:
    schemas = root / "schemas"
    schemas.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / "schemas" / "apply-lock.schema.json", schemas / "apply-lock.schema.json")
    shutil.copyfile(ROOT / "schemas" / "apply-lock-analysis.schema.json", schemas / "apply-lock-analysis.schema.json")
    return root


def lock_record(change_id: str, status: str, expires_at: str = "2026-05-30T01:00:00Z") -> dict[str, Any]:
    agent = change_id.split("_")[1]
    return {
        "schema_version": 1,
        "lock_id": f"{change_id}_lock",
        "change_id": change_id,
        "agent": agent,
        "scope": "repository",
        "mode": "exclusive",
        "status": status,
        "created_at": "2026-05-29T23:00:00Z",
        "created_by": "operator",
        "expires_at": expires_at,
        "base_commit": "0" * 40,
        "pre_apply_plan_sha256": "a" * 64,
        "mutation_enabled": False,
        "recovery": {
            "manual_review_required": True,
            "stale_lock_action": "inspect_before_release",
            "note": "Manual review required.",
        },
    }


def write_lock(root: Path, change_id: str, data: dict[str, Any]) -> Path:
    return write_yaml(root / "changes" / change_id / "apply-lock.yaml", data)


def parse_report(result: subprocess.CompletedProcess[str]) -> dict[str, Any]:
    assert result.returncode == 0, result.stdout + result.stderr
    return yaml.safe_load(result.stdout)


def test_apply_lock_analysis_accepts_example() -> None:
    result = run_analyzer(ROOT, "--validate-report")
    assert result.returncode == 0, result.stdout + result.stderr


def test_apply_lock_analysis_reports_no_locks(tmp_path: Path) -> None:
    root = prepare_root(tmp_path)
    report = parse_report(run_analyzer(root, "--now", NOW))
    assert report["lock_count"] == 0
    assert report["blocking_count"] == 0
    assert report["summary"]["has_blocking_locks"] is False


def test_apply_lock_analysis_rejects_output_argument(tmp_path: Path) -> None:
    root = prepare_root(tmp_path)
    output_path = tmp_path / "profiles" / "agentops" / "report.yaml"
    result = run_analyzer(root, "--now", NOW, "--output", str(output_path))
    assert result.returncode == 2
    assert not output_path.exists()


def test_apply_lock_analysis_classifies_active_and_released(tmp_path: Path) -> None:
    root = prepare_root(tmp_path)
    active_id = "20260530T000000Z_agentops_aaaaaaaaaa"
    released_id = "20260530T010000Z_agentops_bbbbbbbbbb"
    write_lock(root, active_id, lock_record(active_id, "active"))
    write_lock(root, released_id, lock_record(released_id, "released"))
    report = parse_report(run_analyzer(root, "--now", NOW))
    by_status = {item["effective_status"]: item for item in report["locks"]}
    assert report["lock_count"] == 2
    assert report["blocking_count"] == 1
    assert by_status["active"]["blocking"] is True
    assert by_status["released"]["blocking"] is False


def test_apply_lock_analysis_classifies_expired_active_as_blocking(tmp_path: Path) -> None:
    root = prepare_root(tmp_path)
    change_id = "20260530T000000Z_agentops_aaaaaaaaaa"
    write_lock(root, change_id, lock_record(change_id, "active", expires_at="2026-05-29T23:30:00Z"))
    report = parse_report(run_analyzer(root, "--now", NOW))
    assert report["locks"][0]["effective_status"] == "expired_active"
    assert report["locks"][0]["blocking"] is True


def test_apply_lock_analysis_classifies_stale_and_recovery_required_as_blocking(tmp_path: Path) -> None:
    root = prepare_root(tmp_path)
    stale_id = "20260530T000000Z_agentops_aaaaaaaaaa"
    recovery_id = "20260530T010000Z_agentops_bbbbbbbbbb"
    write_lock(root, stale_id, lock_record(stale_id, "stale"))
    write_lock(root, recovery_id, lock_record(recovery_id, "recovery_required"))
    report = parse_report(run_analyzer(root, "--now", NOW))
    assert report["blocking_count"] == 2
    assert {item["effective_status"] for item in report["locks"]} == {"stale", "recovery_required"}


def test_apply_lock_analysis_classifies_invalid_lock_as_blocking(tmp_path: Path) -> None:
    root = prepare_root(tmp_path)
    change_id = "20260530T000000Z_agentops_aaaaaaaaaa"
    record = lock_record(change_id, "released")
    record["mutation_enabled"] = True
    write_lock(root, change_id, record)
    report = parse_report(run_analyzer(root, "--now", NOW))
    assert report["locks"][0]["effective_status"] == "invalid"
    assert report["locks"][0]["blocking"] is True


def test_apply_lock_analysis_classifies_agent_mismatch_as_invalid_blocking(tmp_path: Path) -> None:
    root = prepare_root(tmp_path)
    change_id = "20260530T000000Z_agentops_aaaaaaaaaa"
    record = lock_record(change_id, "released")
    record["agent"] = "otheragent"
    write_lock(root, change_id, record)
    report = parse_report(run_analyzer(root, "--now", NOW))
    assert report["locks"][0]["effective_status"] == "invalid"
    assert report["locks"][0]["blocking"] is True


def test_apply_lock_analysis_report_validation_rejects_count_mismatch(tmp_path: Path) -> None:
    root = prepare_root(tmp_path)
    report = {
        "schema_version": 1,
        "generated_at": NOW,
        "generated_by": "analyze-apply-locks",
        "mutation_enabled": False,
        "lock_count": 999,
        "blocking_count": 0,
        "locks": [],
        "summary": {
            "has_blocking_locks": False,
            "manual_review_required": True,
            "note": "Read-only.",
        },
    }
    report_path = write_yaml(tmp_path / "report.yaml", report)
    result = run_analyzer(root, "--validate-report", str(report_path))
    assert result.returncode == 1
    assert "lock_count" in result.stdout
