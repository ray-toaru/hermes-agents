from __future__ import annotations

import contextlib
import hashlib
import importlib.machinery
import importlib.util
import io
import shutil
import subprocess
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "hermes-agentops"

loader = importlib.machinery.SourceFileLoader("hermes_agentops_reject_status", str(CLI))
spec = importlib.util.spec_from_loader(loader.name, loader)
assert spec is not None
AGENTOPS = importlib.util.module_from_spec(spec)
loader.exec_module(AGENTOPS)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def prepare_root(tmp_path: Path) -> Path:
    shutil.copytree(ROOT / "schemas", tmp_path / "schemas")
    shutil.copytree(ROOT / "policies", tmp_path / "policies")
    return tmp_path


def run_agentops(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    argv = ["--root", str(root), *args]
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        code = AGENTOPS.main(argv)
    return subprocess.CompletedProcess([str(CLI), *argv], code, stdout.getvalue(), stderr.getvalue())


def write_rejected_change(root: Path) -> str:
    change_id = "20260530T010000Z_agentops_rejected"
    diff_text = """diff --git a/profiles/agentops/SOUL.md b/profiles/agentops/SOUL.md
--- a/profiles/agentops/SOUL.md
+++ b/profiles/agentops/SOUL.md
@@ -1 +1 @@
-old
+new
"""
    digest = sha256_text(diff_text)
    cdir = root / "changes" / change_id
    (cdir / "approvals").mkdir(parents=True)
    (cdir / "diff.patch").write_text(diff_text, encoding="utf-8")
    proposal = {
        "schema_version": 1,
        "change_id": change_id,
        "agent": "agentops",
        "title": "Rejected test change",
        "summary": "Test summary",
        "reason": "Test reason",
        "risk_level": "low",
        "created_at": "2026-05-30T01:00:00Z",
        "created_by": "pytest",
        "diff_sha256": digest,
        "required_approvals": 1,
        "status": "proposed",
        "rollback": {"strategy": "git_first", "note": "Revert the test change."},
        "validation": {"required_before_apply": ["changes verify"], "note": "Test validation."},
    }
    rejection = {
        "schema_version": 1,
        "change_id": change_id,
        "decision": "reject",
        "approver": "reviewer-1",
        "created_at": "2026-05-30T01:01:00Z",
        "comment": "Rejected in test.",
        "diff_sha256": digest,
        "acknowledgements": {
            "reviewed_diff": True,
            "understands_apply_not_automatic": True,
            "secret_values_not_reviewed": True,
            "business_orchestration_not_authorized": True,
        },
    }
    (cdir / "proposal.yaml").write_text(yaml.safe_dump(proposal, sort_keys=False), encoding="utf-8")
    (cdir / "approvals" / "01_reviewer-1_reject.yaml").write_text(
        yaml.safe_dump(rejection, sort_keys=False),
        encoding="utf-8",
    )
    return change_id


def test_valid_rejection_verifies_failed_but_displays_rejected(tmp_path: Path) -> None:
    root = prepare_root(tmp_path)
    change_id = write_rejected_change(root)

    verify = run_agentops(root, "changes", "verify", change_id)
    assert verify.returncode == 2
    assert "approval.status" in verify.stdout

    show = run_agentops(root, "changes", "show", change_id)
    assert show.returncode == 0
    assert "status: rejected" in show.stdout
    assert "status: invalid" not in show.stdout

    listed = run_agentops(root, "changes", "list")
    assert listed.returncode == 0
    assert "\trejected\t" in listed.stdout
    assert "\tinvalid\t" not in listed.stdout
