from __future__ import annotations

import subprocess
from pathlib import Path

import yaml

from agentops_test_utils import run_script
from test_change_workflow import init_git_profile, prepare_root, run_agentops, write_change

ROOT = Path(__file__).resolve().parents[1]
VERIFIER = ROOT / "scripts" / "verify-live-github-approval-source"
CHECKER = ROOT / "scripts" / "check-authenticated-approval"
CHANGE_ID = "20260530T000000Z_agentops_aaaaaaaaaa"
HEAD_SHA = "a" * 40


def run_verifier(root: Path, source_path: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return run_script(
        VERIFIER,
        CHANGE_ID,
        "--root",
        str(root),
        "--source",
        str(source_path),
        "--verified-at",
        "2026-05-30T00:03:00Z",
        *args,
    )


def write_source(root: Path, *, permission: str = "write", rejected: bool = False, diff_sha256: str | None = None, commit_sha: str = HEAD_SHA) -> Path:
    proposal = yaml.safe_load((root / "changes" / CHANGE_ID / "proposal.yaml").read_text(encoding="utf-8"))
    document = {
        "schema_version": 1,
        "source_id": f"{CHANGE_ID}_github_source",
        "repository": {"provider": "github", "full_name": "ray-toaru/hermes-agents", "default_branch": "main"},
        "change_id": CHANGE_ID,
        "agent": "agentops",
        "diff_sha256": diff_sha256 or proposal["diff_sha256"],
        "pull_request": {"number": 123, "head_sha": HEAD_SHA, "base_branch": "main"},
        "approval_reviews": [
            {
                "review_id": 456,
                "reviewer": "reviewer-1",
                "state": "APPROVED",
                "submitted_at": "2026-05-30T00:02:00Z",
                "commit_sha": commit_sha,
                "permission": permission,
                "identity_subject": "reviewer-1",
            }
        ],
        "no_rejections_present": not rejected,
        "retrieved_at": "2026-05-30T00:02:30Z",
    }
    path = root / "changes" / CHANGE_ID / "github-source.yaml"
    path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
    return path


def test_captured_live_github_source_emits_valid_evidence(tmp_path: Path) -> None:
    root = prepare_root(tmp_path)
    init_git_profile(root)
    write_change(root)
    source_path = write_source(root)

    result = run_verifier(root, source_path)
    assert result.returncode == 0, result.stdout + result.stderr
    evidence = yaml.safe_load(result.stdout)
    assert evidence["verifier_mode"] == "live_github"
    assert evidence["verified_by"] == "captured-live-github-source-verifier"
    assert evidence["mutation_enabled"] is False
    assert evidence["apply_authorized"] is False
    assert evidence["status"] == "verified_not_authorized"
    assert evidence["verified_approvals"][0]["evidence_ref"] == "github://ray-toaru/hermes-agents/pull/123#review-456"

    evidence_path = tmp_path / "authenticated-approval-live.yaml"
    evidence_path.write_text(result.stdout, encoding="utf-8")
    check = run_script(CHECKER, "--root", str(root), str(evidence_path))
    assert check.returncode == 0, check.stdout + check.stderr

    apply_attempt = run_agentops(root, "apply", CHANGE_ID)
    assert apply_attempt.returncode == 1
    assert "intentionally not implemented" in apply_attempt.stdout


def test_captured_live_github_source_fails_closed_on_rejection_marker(tmp_path: Path) -> None:
    root = prepare_root(tmp_path)
    init_git_profile(root)
    write_change(root)
    source_path = write_source(root, rejected=True)

    result = run_verifier(root, source_path)
    assert result.returncode == 2
    assert "no_rejections_present" in result.stderr or "rejection" in result.stderr
    assert result.stdout == ""


def test_captured_live_github_source_fails_closed_on_diff_mismatch(tmp_path: Path) -> None:
    root = prepare_root(tmp_path)
    init_git_profile(root)
    write_change(root)
    source_path = write_source(root, diff_sha256="b" * 64)

    result = run_verifier(root, source_path)
    assert result.returncode == 2
    assert "diff_sha256 mismatch" in result.stderr
    assert result.stdout == ""


def test_captured_live_github_source_fails_closed_on_insufficient_permission(tmp_path: Path) -> None:
    root = prepare_root(tmp_path)
    init_git_profile(root)
    write_change(root)
    source_path = write_source(root, permission="write")

    result = run_verifier(root, source_path, "--minimum-permission", "maintain")
    assert result.returncode == 2
    assert "below required" in result.stderr
    assert result.stdout == ""


def test_captured_live_github_source_fails_closed_on_review_head_mismatch(tmp_path: Path) -> None:
    root = prepare_root(tmp_path)
    init_git_profile(root)
    write_change(root)
    source_path = write_source(root, commit_sha="b" * 40)

    result = run_verifier(root, source_path)
    assert result.returncode == 2
    assert "not bound to pull request head" in result.stderr
    assert result.stdout == ""
