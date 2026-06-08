from __future__ import annotations

import hashlib
import shutil
import subprocess
from pathlib import Path
from typing import Any

import yaml
from agentops_test_utils import run_script

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts" / "check-apply-readiness"
CHANGE_ID = "20260530T000000Z_agentops_aaaaaaaaaa"


def run_checker(root: Path, record: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return run_script(CHECKER, "--root", str(root), str(record), *args)


def write_yaml(path: Path, data: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return path


def prepare_root(root: Path) -> Path:
    schemas = root / "schemas"
    schemas.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / "schemas" / "apply-readiness-report.schema.json", schemas / "apply-readiness-report.schema.json")
    return root


def gate(name: str, *, status: str = "present", blocking: bool = False, required: bool = True, phase: str = "pre_apply", evidence_sha256: str | None = "a" * 64) -> dict[str, Any]:
    return {
        "name": name,
        "phase": phase,
        "required_before_apply": required,
        "status": status,
        "blocking": blocking,
        "evidence_path": f"changes/{CHANGE_ID}/{name}.yaml",
        "evidence_sha256": evidence_sha256,
        "note": "Evidence only.",
    }


def valid_report() -> dict[str, Any]:
    gates = [
        gate("change_verify"),
        gate("approval_identity"),
        gate("pre_apply_plan"),
        gate("apply_lock_analysis"),
        gate("apply_lock_record", phase="future_apply", required=False, status="future_only", evidence_sha256=None),
        gate("rollback_point", phase="future_apply", required=False, status="future_only", evidence_sha256=None),
        gate("audit_record", phase="future_apply", required=False, status="future_only", evidence_sha256=None),
        gate("post_apply_validation", phase="post_apply", required=False, status="future_only", evidence_sha256=None),
    ]
    return {
        "schema_version": 1,
        "readiness_report_id": f"{CHANGE_ID}_readiness",
        "change_id": CHANGE_ID,
        "agent": "agentops",
        "generated_at": "2026-05-30T00:00:00Z",
        "generated_by": "check-apply-readiness",
        "mutation_enabled": False,
        "apply_authorized": False,
        "status": "evidence_complete_not_authorized",
        "gate_count": len(gates),
        "blocking_count": 0,
        "gates": gates,
        "boundaries": {
            "report_is_read_only": True,
            "does_not_authorize_apply": True,
            "does_not_acquire_or_release_locks": True,
            "does_not_mutate_profiles_or_runtime": True,
            "does_not_read_secret_values": True,
            "does_not_execute_rollback": True,
            "does_not_orchestrate_business_tasks": True,
        },
        "summary": {
            "human_review_required": True,
            "note": "Evidence only; apply remains disabled.",
        },
    }


def test_apply_readiness_checker_accepts_valid_record(tmp_path: Path) -> None:
    path = write_yaml(tmp_path / "readiness.yaml", valid_report())
    result = run_checker(ROOT, path)
    assert result.returncode == 0, result.stdout + result.stderr


def test_apply_readiness_checker_accepts_blocked_required_gate_in_blocked_report(tmp_path: Path) -> None:
    record = valid_report()
    record["status"] = "blocked"
    record["gates"][3]["status"] = "blocked"
    record["gates"][3]["blocking"] = True
    record["blocking_count"] = 1
    path = write_yaml(tmp_path / "readiness.yaml", record)
    result = run_checker(ROOT, path)
    assert result.returncode == 0, result.stdout + result.stderr


def test_apply_readiness_checker_rejects_mutation_enabled_true(tmp_path: Path) -> None:
    record = valid_report()
    record["mutation_enabled"] = True
    path = write_yaml(tmp_path / "readiness.yaml", record)
    result = run_checker(ROOT, path)
    assert result.returncode == 1
    assert "mutation_enabled" in result.stdout


def test_apply_readiness_checker_rejects_apply_authorized_true(tmp_path: Path) -> None:
    record = valid_report()
    record["apply_authorized"] = True
    path = write_yaml(tmp_path / "readiness.yaml", record)
    result = run_checker(ROOT, path)
    assert result.returncode == 1
    assert "apply_authorized" in result.stdout


def test_apply_readiness_checker_rejects_agent_mismatch(tmp_path: Path) -> None:
    record = valid_report()
    record["agent"] = "otheragent"
    path = write_yaml(tmp_path / "readiness.yaml", record)
    result = run_checker(ROOT, path)
    assert result.returncode == 1
    assert "agent" in result.stdout


def test_apply_readiness_checker_rejects_id_mismatch(tmp_path: Path) -> None:
    record = valid_report()
    record["readiness_report_id"] = f"{CHANGE_ID}_wrong"
    path = write_yaml(tmp_path / "readiness.yaml", record)
    result = run_checker(ROOT, path)
    assert result.returncode == 1
    assert "readiness_report_id" in result.stdout


def test_apply_readiness_checker_rejects_gate_count_mismatch(tmp_path: Path) -> None:
    record = valid_report()
    record["gate_count"] = 999
    path = write_yaml(tmp_path / "readiness.yaml", record)
    result = run_checker(ROOT, path)
    assert result.returncode == 1
    assert "gate_count" in result.stdout


def test_apply_readiness_checker_rejects_complete_status_with_blocking_gate(tmp_path: Path) -> None:
    record = valid_report()
    record["gates"][0]["status"] = "blocked"
    record["gates"][0]["blocking"] = True
    record["blocking_count"] = 1
    path = write_yaml(tmp_path / "readiness.yaml", record)
    result = run_checker(ROOT, path)
    assert result.returncode == 1
    assert "complete evidence status" in result.stdout


def test_apply_readiness_checker_rejects_required_missing_gate_not_blocking(tmp_path: Path) -> None:
    record = valid_report()
    record["status"] = "blocked"
    record["gates"][0]["status"] = "missing"
    path = write_yaml(tmp_path / "readiness.yaml", record)
    result = run_checker(ROOT, path)
    assert result.returncode == 1
    assert "must be blocking" in result.stdout


def test_apply_readiness_checker_rejects_post_apply_required_before_apply(tmp_path: Path) -> None:
    record = valid_report()
    post_gate = record["gates"][-1]
    post_gate["required_before_apply"] = True
    post_gate["phase"] = "post_apply"
    path = write_yaml(tmp_path / "readiness.yaml", record)
    result = run_checker(ROOT, path)
    assert result.returncode == 1
    assert "post_apply_validation cannot be required" in result.stdout


def test_apply_readiness_checker_rejects_required_gate_marked_future_only(tmp_path: Path) -> None:
    record = valid_report()
    record["gates"][0]["phase"] = "future_apply"
    record["gates"][0]["required_before_apply"] = False
    record["gates"][0]["status"] = "future_only"
    record["gates"][0]["evidence_sha256"] = None
    path = write_yaml(tmp_path / "readiness.yaml", record)
    result = run_checker(ROOT, path)
    assert result.returncode == 1
    assert "required gate" in result.stdout
    assert "pre_apply" in result.stdout


def test_apply_readiness_checker_rejects_required_gate_without_hash(tmp_path: Path) -> None:
    record = valid_report()
    record["gates"][0]["evidence_sha256"] = None
    path = write_yaml(tmp_path / "readiness.yaml", record)
    result = run_checker(ROOT, path)
    assert result.returncode == 1
    assert "concrete evidence_sha256" in result.stdout


def test_apply_readiness_checker_rejects_duplicate_gate_names(tmp_path: Path) -> None:
    record = valid_report()
    record["gates"].append(gate("change_verify"))
    record["gate_count"] = len(record["gates"])
    path = write_yaml(tmp_path / "readiness.yaml", record)
    result = run_checker(ROOT, path)
    assert result.returncode == 1
    assert "duplicate gate names" in result.stdout


def test_apply_readiness_checker_rejects_unsafe_evidence_paths(tmp_path: Path) -> None:
    for bad_path in ("/tmp/evidence.yaml", "../evidence.yaml", "changes\\agentops\\evidence.yaml"):
        record = valid_report()
        record["gates"][0]["evidence_path"] = bad_path
        path = write_yaml(tmp_path / f"readiness-{len(bad_path)}.yaml", record)
        result = run_checker(ROOT, path)
        assert result.returncode == 1
        assert "safe relative path" in result.stdout


def test_apply_readiness_checker_binds_required_evidence_files(tmp_path: Path) -> None:
    root = prepare_root(tmp_path)
    record = valid_report()
    for gate_record in record["gates"]:
        if gate_record["required_before_apply"]:
            evidence_path = root / gate_record["evidence_path"]
            evidence_path.parent.mkdir(parents=True, exist_ok=True)
            evidence_path.write_text(gate_record["name"], encoding="utf-8")
            gate_record["evidence_sha256"] = hashlib.sha256(evidence_path.read_bytes()).hexdigest()
    path = write_yaml(tmp_path / "readiness.yaml", record)
    result = run_checker(root, path, "--require-evidence-files")
    assert result.returncode == 0, result.stdout + result.stderr

    record["gates"][0]["evidence_sha256"] = "0" * 64
    write_yaml(path, record)
    result = run_checker(root, path, "--require-evidence-files")
    assert result.returncode == 1
    assert "evidence_sha256 does not match" in result.stdout
