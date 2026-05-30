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

loader = importlib.machinery.SourceFileLoader("hermes_agentops", str(CLI))
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


def run_agentops(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    argv = ["--root", str(root), *args]
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        code = AGENTOPS.main(argv)
    return subprocess.CompletedProcess([str(CLI), *argv], code, stdout.getvalue(), stderr.getvalue())


def run_verify(root: Path, change_id: str, *flags: str) -> subprocess.CompletedProcess[str]:
    return run_agentops(root, "changes", "verify", change_id, *flags)


def init_git_profile(root: Path, text: str = "old\n") -> None:
    profile = root / "profiles" / "agentops"
    profile.mkdir(parents=True)
    (profile / "SOUL.md").write_text(text, encoding="utf-8")
    subprocess.run(["git", "init"], cwd=root, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    subprocess.run(["git", "config", "user.email", "pytest@example.local"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "pytest"], cwd=root, check=True)
    subprocess.run(["git", "add", "profiles/agentops/SOUL.md"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-m", "baseline"], cwd=root, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


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
    change_id = write_change(root, approvals=[("reviewer-1", "approve"), ("reviewer-1", "approve")])
    result = run_verify(root, change_id)
    assert result.returncode == 2
    assert "duplicate_approver" in result.stdout


def test_bad_created_at_format_is_rejected(tmp_path: Path) -> None:
    root = prepare_root(tmp_path)
    change_id = write_change(root, created_at="not-a-date-time")
    result = run_verify(root, change_id)
    assert result.returncode == 2
    assert "created_at" in result.stdout


def test_rejection_record_is_rejected(tmp_path: Path) -> None:
    root = prepare_root(tmp_path)
    change_id = write_change(root, approvals=[("reviewer-1", "reject")])
    result = run_verify(root, change_id)
    assert result.returncode == 2
    assert "approval.status" in result.stdout


def test_diff_hash_mismatch_is_rejected(tmp_path: Path) -> None:
    root = prepare_root(tmp_path)
    change_id = write_change(root)
    (root / "changes" / change_id / "diff.patch").write_text("tampered\n", encoding="utf-8")
    result = run_verify(root, change_id)
    assert result.returncode == 2
    assert "diff_sha256" in result.stdout


def test_malformed_approval_record_is_rejected(tmp_path: Path) -> None:
    root = prepare_root(tmp_path)
    change_id = write_change(root)
    approval = root / "changes" / change_id / "approvals" / "01_reviewer-1_approve.yaml"
    data = yaml.safe_load(approval.read_text(encoding="utf-8"))
    data.pop("acknowledgements")
    approval.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    result = run_verify(root, change_id)
    assert result.returncode == 2
    assert "schema.approval-record" in result.stdout


def test_delete_diff_inside_profile_passes(tmp_path: Path) -> None:
    root = prepare_root(tmp_path)
    diff_text = """diff --git a/profiles/agentops/old.md b/profiles/agentops/old.md
deleted file mode 100644
--- a/profiles/agentops/old.md
+++ /dev/null
@@ -1 +0,0 @@
-old
"""
    change_id = write_change(root, diff_text=diff_text)
    result = run_verify(root, change_id)
    assert result.returncode == 0, result.stdout


def test_rename_diff_outside_profile_is_rejected(tmp_path: Path) -> None:
    root = prepare_root(tmp_path)
    diff_text = """diff --git a/profiles/agentops/SOUL.md b/profiles/other/SOUL.md
similarity index 100%
rename from profiles/agentops/SOUL.md
rename to profiles/other/SOUL.md
"""
    change_id = write_change(root, diff_text=diff_text)
    result = run_verify(root, change_id)
    assert result.returncode == 2
    assert "change.path_scope" in result.stdout


def test_apply_remains_disabled(tmp_path: Path) -> None:
    root = prepare_root(tmp_path)
    result = run_agentops(root, "apply", "20260530T000000Z_agentops_aaaaaaaaaa")
    assert result.returncode == 1
    assert "intentionally not implemented" in result.stdout


def test_policy_effective_reports_thresholds(tmp_path: Path) -> None:
    root = prepare_root(tmp_path)
    result = run_agentops(root, "policy", "effective", "--json")
    assert result.returncode == 0, result.stdout + result.stderr
    data = yaml.safe_load(result.stdout)
    assert data["apply_enabled"] is False
    assert data["risk_approvals"]["high"] == 2
    assert "read_secret_values" in data["global_forbidden"]


def test_policy_check_rejects_missing_forbidden_default(tmp_path: Path) -> None:
    root = prepare_root(tmp_path)
    policy = root / "policies" / "global-permissions.yaml"
    data = yaml.safe_load(policy.read_text(encoding="utf-8"))
    data["global_forbidden"].remove("read_secret_values")
    policy.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    result = run_agentops(root, "policy", "check")
    assert result.returncode == 2
    assert "policy.global_forbidden" in result.stdout


def test_policy_explain_marks_critical_path(tmp_path: Path) -> None:
    root = prepare_root(tmp_path)
    result = run_agentops(root, "policy", "explain", "profiles/agentops/SOUL.md")
    assert result.returncode == 0
    assert "critical: true" in result.stdout


def test_git_clean_gate_rejects_dirty_profile(tmp_path: Path) -> None:
    root = prepare_root(tmp_path)
    init_git_profile(root)
    change_id = write_change(root)
    (root / "profiles" / "agentops" / "SOUL.md").write_text("dirty\n", encoding="utf-8")
    result = run_verify(root, change_id, "--check-git-clean")
    assert result.returncode == 2
    assert "git.clean" in result.stdout


def test_patch_applicability_gate_accepts_applicable_patch(tmp_path: Path) -> None:
    root = prepare_root(tmp_path)
    init_git_profile(root)
    change_id = write_change(root)
    result = run_verify(root, change_id, "--check-patch-applicable")
    assert result.returncode == 0, result.stdout + result.stderr


def test_patch_applicability_gate_rejects_non_applicable_patch(tmp_path: Path) -> None:
    root = prepare_root(tmp_path)
    init_git_profile(root, text="unexpected\n")
    change_id = write_change(root)
    result = run_verify(root, change_id, "--check-patch-applicable")
    assert result.returncode == 2
    assert "git.apply_check" in result.stdout
