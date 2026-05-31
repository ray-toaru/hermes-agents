from __future__ import annotations

import subprocess
from pathlib import Path

import yaml

from test_change_workflow import init_git_profile, prepare_root, run_agentops, write_change

ROOT = Path(__file__).resolve().parents[1]
VERIFIER = ROOT / "scripts" / "verify-authenticated-approval"
CHECKER = ROOT / "scripts" / "check-authenticated-approval"
CHANGE_ID = "20260530T000000Z_agentops_aaaaaaaaaa"


def run_verifier(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python", str(VERIFIER), CHANGE_ID, "--root", str(root), "--verified-at", "2026-05-30T00:02:00Z", *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def run_checker(root: Path, evidence_path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python", str(CHECKER), "--root", str(root), str(evidence_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def test_fixture_verifier_emits_contract_valid_evidence(tmp_path: Path) -> None:
    root = prepare_root(tmp_path)
    init_git_profile(root)
    write_change(root)

    result = run_verifier(root)
    assert result.returncode == 0, result.stdout + result.stderr
    evidence = yaml.safe_load(result.stdout)
    assert evidence["verifier_mode"] == "fixture_contract_only"
    assert evidence["mutation_enabled"] is False
    assert evidence["apply_authorized"] is False
    assert evidence["status"] == "verified_not_authorized"
    assert evidence["required_approvals"] == 1
    assert len(evidence["verified_approvals"]) == 1

    evidence_path = tmp_path / "authenticated-approval.yaml"
    evidence_path.write_text(result.stdout, encoding="utf-8")
    check = run_checker(root, evidence_path)
    assert check.returncode == 0, check.stdout + check.stderr

    apply_attempt = run_agentops(root, "apply", CHANGE_ID)
    assert apply_attempt.returncode == 1
    assert "intentionally not implemented" in apply_attempt.stdout


def test_fixture_verifier_fails_closed_for_live_modes(tmp_path: Path) -> None:
    root = prepare_root(tmp_path)
    init_git_profile(root)
    write_change(root)

    for mode in ("live_github", "signed_attestation"):
        result = run_verifier(root, "--mode", mode)
        assert result.returncode == 2
        assert "not implemented" in result.stderr
        assert result.stdout == ""


def test_fixture_verifier_fails_closed_on_rejection(tmp_path: Path) -> None:
    root = prepare_root(tmp_path)
    init_git_profile(root)
    write_change(root)
    reject = run_agentops(root, "changes", "approve", CHANGE_ID, "--approver", "rejecter", "--decision", "reject")
    assert reject.returncode == 0, reject.stdout + reject.stderr

    result = run_verifier(root)
    assert result.returncode == 2
    assert "rejections are present" in result.stderr
    assert result.stdout == ""


def test_fixture_verifier_fails_closed_on_threshold_failure(tmp_path: Path) -> None:
    root = prepare_root(tmp_path)
    init_git_profile(root)
    write_change(root, required_approvals=2)

    result = run_verifier(root)
    assert result.returncode == 2
    assert "approval threshold unmet" in result.stderr
    assert result.stdout == ""


def test_fixture_verifier_fails_closed_on_diff_mismatch(tmp_path: Path) -> None:
    root = prepare_root(tmp_path)
    init_git_profile(root)
    write_change(root)
    diff_path = root / "changes" / CHANGE_ID / "diff.patch"
    diff_path.write_text(diff_path.read_text(encoding="utf-8") + "\n# tamper\n", encoding="utf-8")

    result = run_verifier(root)
    assert result.returncode == 2
    assert "proposal diff_sha256 mismatch" in result.stderr
    assert result.stdout == ""


def test_fixture_verifier_fails_closed_on_duplicate_approver(tmp_path: Path) -> None:
    root = prepare_root(tmp_path)
    init_git_profile(root)
    write_change(root)
    duplicate = run_agentops(root, "changes", "approve", CHANGE_ID, "--approver", "reviewer-1")
    assert duplicate.returncode == 0, duplicate.stdout + duplicate.stderr

    result = run_verifier(root)
    assert result.returncode == 2
    assert "duplicate approval approver" in result.stderr
    assert result.stdout == ""
