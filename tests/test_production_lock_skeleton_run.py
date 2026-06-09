from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "run-production-lock-lifecycle-skeleton"
CHECKER = ROOT / "scripts" / "check-production-lock-skeleton-run"
EXAMPLE = ROOT / "docs" / "examples" / "production-lock-skeleton-run.yaml"
CHANGE_ID = "20260608T000000Z_agentops-manager_0123456789"


def run_script(script: Path, *args: Any):
    import subprocess
    import sys

    return subprocess.run([sys.executable, str(script), *map(str, args)], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)


def load_example() -> dict[str, Any]:
    return yaml.safe_load(EXAMPLE.read_text(encoding="utf-8"))


def write_yaml(path: Path, data: dict[str, Any]) -> Path:
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return path


def run_skeleton(*args: str):
    return run_script(RUNNER, CHANGE_ID, "--root", str(ROOT), "--operator", "tester", *args)


def test_example_skeleton_run_is_valid() -> None:
    record = load_example()
    result = run_script(CHECKER, str(EXAMPLE), "--root", str(ROOT))
    assert result.returncode == 0, result.stdout + result.stderr
    assert record["design_only"] is True
    assert record["lock_acquired"] is False
    assert record["lock_released"] is False
    assert record["production_lock_written"] is False
    assert record["apply_authorized"] is False


def test_acquire_skeleton_emits_non_executed_evidence() -> None:
    result = run_skeleton("--action", "acquire", "--current-state", "not_acquired")
    assert result.returncode == 0, result.stdout + result.stderr
    record = yaml.safe_load(result.stdout)
    assert record["status"] == "would_acquire_not_executed"
    assert record["requested_transition"]["from"] == "not_acquired"
    assert record["requested_transition"]["to"] == "acquired"
    assert record["requested_transition"]["executed"] is False
    assert record["lock_acquired"] is False
    assert record["production_lock_written"] is False


def test_preserve_skeleton_emits_non_release_evidence() -> None:
    result = run_skeleton("--action", "preserve", "--current-state", "recovery_required")
    assert result.returncode == 0, result.stdout + result.stderr
    record = yaml.safe_load(result.stdout)
    assert record["status"] == "would_preserve_not_released"
    assert record["requested_transition"]["from"] == "recovery_required"
    assert record["requested_transition"]["to"] == "preserved_for_review"
    assert record["decision"]["would_preserve_lock"] is True
    assert record["decision"]["manual_review_required"] is True
    assert record["lock_released"] is False


def test_invalid_preserve_state_fails_closed() -> None:
    result = run_skeleton("--action", "preserve", "--current-state", "acquired")
    assert result.returncode == 2
    record = yaml.safe_load(result.stdout)
    assert record["status"] == "failed_closed"
    assert record["lock_released"] is False
    assert record["decision"]["next_allowed_step"] == "fix_contract_or_inputs"


def test_runner_rejects_release_action() -> None:
    result = run_skeleton("--action", "release", "--current-state", "release_eligible")
    assert result.returncode != 0
    assert "invalid choice" in result.stderr


def test_runner_rejects_absolute_contract_path(tmp_path: Path) -> None:
    result = run_skeleton("--action", "acquire", "--current-state", "not_acquired", "--contract", str(tmp_path / "secret.yaml"))
    assert result.returncode == 2
    assert "safe repository-relative path" in result.stderr


def test_checker_rejects_lock_acquired_true(tmp_path: Path) -> None:
    record = load_example()
    record["lock_acquired"] = True
    path = write_yaml(tmp_path / "record.yaml", record)
    result = run_script(CHECKER, str(path), "--root", str(ROOT))
    assert result.returncode == 1
    assert "lock_acquired" in result.stdout


def test_checker_rejects_lock_released_true(tmp_path: Path) -> None:
    record = load_example()
    record["lock_released"] = True
    path = write_yaml(tmp_path / "record.yaml", record)
    result = run_script(CHECKER, str(path), "--root", str(ROOT))
    assert result.returncode == 1
    assert "lock_released" in result.stdout


def test_checker_rejects_absolute_contract_path(tmp_path: Path) -> None:
    record = load_example()
    record["contract"]["path"] = str(tmp_path / "secret.yaml")
    path = write_yaml(tmp_path / "record.yaml", record)
    result = run_script(CHECKER, str(path), "--root", str(ROOT))
    assert result.returncode == 1
    assert "contract.path" in result.stdout


def test_checker_rejects_contract_hash_mismatch(tmp_path: Path) -> None:
    record = load_example()
    record["contract"]["sha256"] = "1" * 64
    path = write_yaml(tmp_path / "record.yaml", record)
    result = run_script(CHECKER, str(path), "--root", str(ROOT))
    assert result.returncode == 1
    assert "contract.sha256" in result.stdout


def test_apply_remains_disabled() -> None:
    result = run_script(ROOT / "scripts" / "hermes-agentops", "apply", "probe")
    assert result.returncode != 0
    assert "not implemented" in (result.stdout + result.stderr)
