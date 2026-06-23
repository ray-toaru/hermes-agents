from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

import jsonschema
import yaml

from test_change_workflow import run_agentops, write_change
from agentops_test_utils import run_script
from apply_blocked_helpers import assert_apply_blocked_report

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "run-post-apply-validation-sandbox"
CHANGE_ID = "20260530T000000Z_agentops_aaaaaaaaaa"


def prepare_repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    for name in ("schemas", "policies", "profiles", "scripts", "inventory"):
        shutil.copytree(ROOT / name, root / name)
    subprocess.run(["git", "init"], cwd=root, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    subprocess.run(["git", "config", "user.email", "pytest@example.local"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "pytest"], cwd=root, check=True)
    subprocess.run(["git", "add", "profiles"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-m", "profiles baseline"], cwd=root, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return root


def hash_tree(path: Path) -> str:
    digest = hashlib.sha256()
    for file_path in sorted(item for item in path.rglob("*") if item.is_file()):
        digest.update(file_path.relative_to(path).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(file_path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def make_diff(root: Path, relative_path: str, new_text: str) -> str:
    path = root / relative_path
    original = path.read_text(encoding="utf-8")
    path.write_text(new_text, encoding="utf-8")
    diff = subprocess.run(["git", "diff", "--", relative_path], cwd=root, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True).stdout
    path.write_text(original, encoding="utf-8")
    return diff


def write_change_with_diff(root: Path, diff_text: str) -> str:
    return write_change(root, change_id=CHANGE_ID, diff_text=diff_text)


def run_runner(root: Path, change_id: str = CHANGE_ID) -> subprocess.CompletedProcess[str]:
    return run_script(RUNNER, change_id, "--root", str(root))


def validate_report(root: Path, report: dict[str, Any]) -> None:
    schema = json.loads((root / "schemas" / "post-apply-validation-run.schema.json").read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)
    validator = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())
    errors = list(validator.iter_errors(report))
    assert not errors, [error.message for error in errors]


def test_runs_post_apply_validation_in_sandbox_without_source_mutation(tmp_path: Path) -> None:
    root = prepare_repo(tmp_path)
    soul = root / "profiles" / "agentops" / "SOUL.md"
    diff_text = make_diff(root, "profiles/agentops/SOUL.md", soul.read_text(encoding="utf-8") + "\nSandbox validation note.\n")
    write_change_with_diff(root, diff_text)
    before = hash_tree(root / "profiles")

    result = run_runner(root)
    assert result.returncode == 0, result.stdout + result.stderr
    report = yaml.safe_load(result.stdout)
    validate_report(root, report)
    assert report["status"] == "success"
    assert report["sandbox_only"] is True
    assert report["mutation_enabled"] is False
    assert report["apply_authorized"] is False
    assert report["sandbox_patch_applied"] is True
    assert report["source_profiles_unchanged"] is True
    assert report["source_profile_hash_before"] == before
    assert report["source_profile_hash_after"] == before
    assert {command["command_id"] for command in report["validation_commands"]} == {
        "agentops.validate-schemas",
        "agentops.validate-profiles",
        "git.diff-check",
    }
    assert all(command["status"] == "success" for command in report["validation_commands"])
    assert hash_tree(root / "profiles") == before

    apply_attempt = run_agentops(root, "apply", CHANGE_ID)
    assert apply_attempt.returncode == 1
    assert_apply_blocked_report(apply_attempt, change_id=CHANGE_ID)


def test_fails_closed_when_patch_cannot_apply(tmp_path: Path) -> None:
    root = prepare_repo(tmp_path)
    diff_text = """diff --git a/profiles/agentops/SOUL.md b/profiles/agentops/SOUL.md
--- a/profiles/agentops/SOUL.md
+++ b/profiles/agentops/SOUL.md
@@ -1 +1 @@
-this line is not present
+new line
"""
    write_change_with_diff(root, diff_text)

    result = run_runner(root)
    assert result.returncode == 2
    assert "git.apply_check" in result.stderr or "patch" in result.stderr or "change.diff_sha256" in result.stderr
    assert result.stdout == ""


def test_fails_closed_when_post_apply_validation_fails(tmp_path: Path) -> None:
    root = prepare_repo(tmp_path)
    manifest = root / "profiles" / "agentops" / "manifest.yaml"
    diff_text = make_diff(root, "profiles/agentops/manifest.yaml", "")
    write_change_with_diff(root, diff_text)
    before = hash_tree(root / "profiles")

    result = run_runner(root)
    assert result.returncode == 2
    assert result.stdout
    report = yaml.safe_load(result.stdout)
    validate_report(root, report)
    assert report["status"] == "failed_closed"
    assert report["sandbox_patch_applied"] is True
    assert any(command["status"] == "failed" for command in report["validation_commands"])
    assert hash_tree(root / "profiles") == before
    assert manifest.read_text(encoding="utf-8") != ""


def test_fails_closed_when_secret_file_would_be_copied(tmp_path: Path) -> None:
    root = prepare_repo(tmp_path)
    soul = root / "profiles" / "agentops" / "SOUL.md"
    diff_text = make_diff(root, "profiles/agentops/SOUL.md", soul.read_text(encoding="utf-8") + "\nSecret guard test.\n")
    write_change_with_diff(root, diff_text)
    (root / "scripts" / ".env").write_text("SECRET=value\n", encoding="utf-8")

    result = run_runner(root)
    assert result.returncode == 2
    assert "refusing to copy secret/runtime file" in result.stderr
    assert result.stdout == ""


def test_fails_closed_when_source_profile_changes_before_run(tmp_path: Path) -> None:
    root = prepare_repo(tmp_path)
    soul = root / "profiles" / "agentops" / "SOUL.md"
    diff_text = make_diff(root, "profiles/agentops/SOUL.md", soul.read_text(encoding="utf-8") + "\nSandbox validation note.\n")
    write_change_with_diff(root, diff_text)
    soul.write_text(soul.read_text(encoding="utf-8") + "\nsource dirty\n", encoding="utf-8")

    result = run_runner(root)
    assert result.returncode == 2
    assert "git.clean" in result.stderr or "unmanaged changes" in result.stderr
    assert result.stdout == ""
