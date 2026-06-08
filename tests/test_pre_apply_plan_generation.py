from __future__ import annotations

import subprocess
from pathlib import Path

import yaml

from test_change_workflow import init_git_profile, prepare_root, write_change
from agentops_test_utils import run_script

ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "scripts" / "generate-pre-apply-plan"
CHECKER = ROOT / "scripts" / "check-pre-apply-plan"


def run_generator(root: Path, change_id: str, *args: str) -> subprocess.CompletedProcess[str]:
    return run_script(GENERATOR, change_id, "--root", str(root), *args)


def test_generate_pre_apply_plan_for_verified_change(tmp_path: Path) -> None:
    root = prepare_root(tmp_path)
    init_git_profile(root)
    change_id = write_change(root)

    result = run_generator(root, change_id)
    assert result.returncode == 0, result.stdout + result.stderr

    plan_path = root / "changes" / change_id / "pre-apply-plan.yaml"
    assert plan_path.exists()
    plan = yaml.safe_load(plan_path.read_text(encoding="utf-8"))
    proposal = yaml.safe_load((root / "changes" / change_id / "proposal.yaml").read_text(encoding="utf-8"))

    assert plan["mutation_enabled"] is False
    assert plan["change_id"] == change_id
    assert plan["agent"] == "agentops"
    assert plan["proposal_diff_sha256"] == proposal["diff_sha256"]
    assert plan["audit"]["record_path"] == f"changes/{change_id}/pre-apply-plan.yaml"

    check = run_script(CHECKER, str(plan_path))
    assert check.returncode == 0, check.stdout + check.stderr


def test_generate_pre_apply_plan_requires_verified_change(tmp_path: Path) -> None:
    root = prepare_root(tmp_path)
    init_git_profile(root)
    change_id = write_change(root, approvals=[])

    result = run_generator(root, change_id)
    assert result.returncode == 2
    assert "approval.threshold" in result.stdout
    assert not (root / "changes" / change_id / "pre-apply-plan.yaml").exists()


def test_generate_pre_apply_plan_refuses_overwrite_by_default(tmp_path: Path) -> None:
    root = prepare_root(tmp_path)
    init_git_profile(root)
    change_id = write_change(root)

    first = run_generator(root, change_id)
    assert first.returncode == 0, first.stdout + first.stderr
    second = run_generator(root, change_id)
    assert second.returncode == 2
    assert "already exists" in second.stdout

    third = run_generator(root, change_id, "--overwrite")
    assert third.returncode == 0, third.stdout + third.stderr


def test_generate_pre_apply_plan_rejects_output_under_profile(tmp_path: Path) -> None:
    root = prepare_root(tmp_path)
    init_git_profile(root)
    change_id = write_change(root)

    result = run_generator(root, change_id, "--output", "profiles/agentops/pre-apply-plan.yaml")
    assert result.returncode == 2
    assert "output must be exactly" in result.stdout
    assert not (root / "profiles" / "agentops" / "pre-apply-plan.yaml").exists()


def test_generate_pre_apply_plan_rejects_absolute_output_outside_repo(tmp_path: Path) -> None:
    root = prepare_root(tmp_path / "repo")
    init_git_profile(root)
    change_id = write_change(root)
    outside = tmp_path / "outside.yaml"

    result = run_generator(root, change_id, "--output", str(outside))
    assert result.returncode == 2
    assert "output must be exactly" in result.stdout
    assert not outside.exists()


def test_generate_pre_apply_plan_allows_explicit_canonical_output(tmp_path: Path) -> None:
    root = prepare_root(tmp_path)
    init_git_profile(root)
    change_id = write_change(root)

    result = run_generator(root, change_id, "--output", f"changes/{change_id}/pre-apply-plan.yaml")
    assert result.returncode == 0, result.stdout + result.stderr
    assert (root / "changes" / change_id / "pre-apply-plan.yaml").exists()
