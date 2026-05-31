from __future__ import annotations

import subprocess
from pathlib import Path

import yaml

from test_change_workflow import init_git_profile, prepare_root, run_agentops, write_change

ROOT = Path(__file__).resolve().parents[1]
DRY_RUN = ROOT / "scripts" / "sandbox-apply-dry-run"
CHANGE_ID = "20260530T000000Z_agentops_aaaaaaaaaa"


def run_dry_run(root: Path, change_id: str = CHANGE_ID) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python", str(DRY_RUN), change_id, "--root", str(root)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def test_sandbox_apply_dry_run_applies_patch_only_in_sandbox(tmp_path: Path) -> None:
    root = prepare_root(tmp_path)
    init_git_profile(root)
    before = (root / "profiles" / "agentops" / "SOUL.md").read_text(encoding="utf-8")
    write_change(root)

    result = run_dry_run(root)
    assert result.returncode == 0, result.stdout + result.stderr
    report = yaml.safe_load(result.stdout)

    assert report["status"] == "sandbox_applied"
    assert report["mutation_enabled"] is False
    assert report["apply_authorized"] is False
    assert report["sandbox_only"] is True
    assert report["source_profile_unchanged"] is True
    assert report["checks"]["strict_change_verify"] is True
    assert report["checks"]["sandbox_patch_check"] is True
    assert report["checks"]["sandbox_patch_applied"] is True
    assert report["boundaries"]["does_not_mutate_source_profiles"] is True
    assert report["boundaries"]["does_not_acquire_or_release_locks"] is True
    assert (root / "profiles" / "agentops" / "SOUL.md").read_text(encoding="utf-8") == before

    apply_attempt = run_agentops(root, "apply", CHANGE_ID)
    assert apply_attempt.returncode == 1
    assert "intentionally not implemented" in apply_attempt.stdout


def test_sandbox_apply_dry_run_fails_closed_when_strict_verify_fails(tmp_path: Path) -> None:
    root = prepare_root(tmp_path)
    init_git_profile(root, text="unexpected\n")
    before = (root / "profiles" / "agentops" / "SOUL.md").read_text(encoding="utf-8")
    write_change(root)

    result = run_dry_run(root)
    assert result.returncode == 2
    report = yaml.safe_load(result.stdout)

    assert report["status"] == "failed_closed"
    assert report["checks"]["strict_change_verify"] is False
    assert report["checks"]["sandbox_patch_applied"] is False
    assert "git.apply_check" in report["error"]
    assert report["source_profile_unchanged"] is True
    assert (root / "profiles" / "agentops" / "SOUL.md").read_text(encoding="utf-8") == before
