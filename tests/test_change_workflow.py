from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "hermes-agentops"


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def prepare_root(tmp_path: Path) -> Path:
    shutil.copytree(ROOT / "schemas", tmp_path / "schemas")
    shutil.copytree(ROOT / "policies", tmp_path / "policies")
    return tmp_path


def write_change(
    root: Path,
    *,
    change_id: str = "20260530T000000Z_agentops_aaaaaaaaaa",
    agent: str = "agentops",
    risk_level: str = "low",
    diff_text: str | None = None,
    approvals: list[tuple[str, str]] | None = None,
    required_approvals: int | None = None,
    created_at: str = "2026-05-30T00:00:00Z",
) -> str:
    if diff_text is None:
        diff_text = """diff --git a/profiles/agentops/SOUL.md b/profiles/agentops/SOUL.md
--- a/profiles/agentops/SOUL.md
+++ b/profiles/agentops/SOUL.md
@@ -1 +1 @@
-old
+new
"""
    digest = sha256_text(diff_text)
    if approvals is None:
        approvals = [("reviewer-1", "approve")]
    if required_approvals is None:
        required_approvals = 1 if risk_level in {"low", "medium"} else 2

    cdir = root / "changes" / change_id
    (cdir / "approvals").mkdir(parents=True)
    (cdir / "diff.patch").write_text(diff_text, encoding="utf-8")
    proposal = {
        "schema_version": 1,
        "change_id": change_id,
        "agent": agent,
        "title": "Test change",
        "summary": "Test summary",
        "reason": "Test reason",
        "risk_level": risk_level,
        "created_at": created_at,
        "created_by": "pytest",
        "diff_sha256": digest,
        "required_approvals": required_approvals,
        "status": "proposed",
        "rollback": {"strategy": "git_first", "note": "Revert the test change."},
        "validation": {"required_before_apply": ["changes verify"], "note": "Test validation."},
    }
    (cdir / "proposal.yaml").write_text(yaml.safe_dump(proposal, sort_keys=False), encoding="utf-8")

    for index, (approver, decision) in enumerate(approvals, start=1):
        record = {
            "schema_version": 1,
            "change_id": change_id,
            "decision": decision,
            "approver": approver,
            "created_at": "2026-05-30T00:01:00Z",
            "comment": "Reviewed in test.",
            "diff_sha256": digest,
            "acknowledgements": {
                "reviewed_diff": True,
                "understands_apply_not_automatic": True,
                "secret_values_not_reviewed": True,
                "business_orchestration_not_authorized": True,
            },
        }
        (cdir / "approvals" / f"{index:02d}_{approver}_{decision}.yaml").write_text(
            yaml.safe_dump(record, sort_keys=False),
            encoding="utf-8",
        )
    return change_id


def run_verify(root: Path, change_id: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run(
        [sys.executable, str(CLI), "--root", str(root), "changes", "verify", change_id],
        cwd=ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def test_valid_change_passes(tmp_path: Path) -> None:
    root = prepare_root(tmp_path)
    change_id = write_change(root)
    result = run_verify(root, change_id)
    assert result.returncode == 0, result.stdout + result.stderr


def test_high_risk_threshold_is_loaded_from_policy(tmp_path: Path) -> None:
    root = prepare_root(tmp_path)
    change_id = write_change(root, risk_level="high", approvals=[("reviewer-1", "approve")])
    result = run_verify(root, change_id)
    assert result.returncode == 2
    assert "approval.threshold" in result.stdout


def test_path_traversal_is_rejected(tmp_path: Path) -> None:
    root = prepare_root(tmp_path)
    diff_text = """diff --git a/profiles/agentops/../../evil b/profiles/agentops/../../evil
--- a/profiles/agentops/../../evil
+++ b/profiles/agentops/../../evil
@@ -1 +1 @@
-old
+new
"""
    change_id = write_change(root, diff_text=diff_text)
    result = run_verify(root, change_id)
    assert result.returncode == 2
    assert "traversal" in result.stdout


def test_malformed_diff_header_is_rejected(tmp_path: Path) -> None:
    root = prepare_root(tmp_path)
    diff_text = """diff --git profiles/agentops/SOUL.md profiles/agentops/SOUL.md
--- profiles/agentops/SOUL.md
+++ profiles/agentops/SOUL.md
@@ -1 +1 @@
-old
+new
"""
    change_id = write_change(root, diff_text=diff_text)
    result = run_verify(root, change_id)
    assert result.returncode == 2
    assert "diff.header" in result.stdout


def test_duplicate_approver_is_rejected(tmp_path: Path) -> None:
    root = prepare_root(tmp_path)
    change_id = write_change(
        root,
        approvals=[("reviewer-1", "approve"), ("reviewer-1", "approve")],
    )
    result = run_verify(root, change_id)
    assert result.returncode == 2
    assert "duplicate_approver" in result.stdout


def test_bad_created_at_format_is_rejected(tmp_path: Path) -> None:
    root = prepare_root(tmp_path)
    change_id = write_change(root, created_at="not-a-date-time")
    result = run_verify(root, change_id)
    assert result.returncode == 2
    assert "created_at" in result.stdout
