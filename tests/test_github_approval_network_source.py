from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import yaml

from agentops_test_utils import run_script
from test_change_workflow import init_git_profile, prepare_root, run_agentops, write_change

ROOT = Path(__file__).resolve().parents[1]
COLLECTOR = ROOT / "scripts" / "collect-github-approval-source"
VERIFIER = ROOT / "scripts" / "verify-live-github-approval-source"
CHECKER = ROOT / "scripts" / "check-authenticated-approval"
CHANGE_ID = "20260530T000000Z_agentops_aaaaaaaaaa"
HEAD_SHA = "a" * 40


class FakeResponse:
    def __init__(self, payload: bytes) -> None:
        self.payload = payload

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return self.payload


def change_diff_text(root: Path) -> str:
    return (root / "changes" / CHANGE_ID / "diff.patch").read_text(encoding="utf-8")


def fake_urlopen_factory(
    diff_text: str,
    *,
    state: str = "APPROVED",
    permission: str = "write",
    review_sha: str = HEAD_SHA,
):
    def fake_urlopen(request: Any, timeout: int = 20) -> FakeResponse:
        url = request.full_url
        accept = request.get_header("Accept") or ""
        if accept == "application/vnd.github.v3.diff":
            return FakeResponse(diff_text.encode("utf-8"))
        if url.endswith("/repos/ray-toaru/hermes-agents"):
            return FakeResponse(b'{"default_branch":"main"}')
        if url.endswith("/pulls/123"):
            return FakeResponse((
                '{"number":123,"head":{"sha":"' + HEAD_SHA + '"},"base":{"ref":"main"}}'
            ).encode("utf-8"))
        if url.endswith("/pulls/123/reviews"):
            body = (
                '[{"id":456,"state":"' + state + '","submitted_at":"2026-05-30T00:02:00Z",'
                '"commit_id":"' + review_sha + '","user":{"login":"reviewer-1","id":1001}}]'
            )
            return FakeResponse(body.encode("utf-8"))
        if url.endswith("/collaborators/reviewer-1/permission"):
            return FakeResponse(("{\"permission\":\"" + permission + "\"}").encode("utf-8"))
        raise AssertionError(f"unexpected URL: {url}")

    return fake_urlopen


def run_collector(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return run_script(
        COLLECTOR,
        CHANGE_ID,
        "--root",
        str(root),
        "--agent",
        "agentops",
        "--pull-request",
        "123",
        "--retrieved-at",
        "2026-05-30T00:03:00Z",
        *args,
    )


def test_network_collector_outputs_source_accepted_by_verifier(tmp_path: Path, monkeypatch: Any) -> None:
    root = prepare_root(tmp_path)
    init_git_profile(root)
    write_change(root)
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen_factory(change_diff_text(root)))

    collected = run_collector(root)
    assert collected.returncode == 0, collected.stdout + collected.stderr
    source = yaml.safe_load(collected.stdout)
    assert source["repository"]["full_name"] == "ray-toaru/hermes-agents"
    assert source["pull_request"]["head_sha"] == HEAD_SHA
    assert source["approval_reviews"][0]["permission"] == "write"

    source_path = tmp_path / "github-source.yaml"
    source_path.write_text(collected.stdout, encoding="utf-8")
    verified = run_script(
        VERIFIER,
        CHANGE_ID,
        "--root",
        str(root),
        "--source",
        str(source_path),
        "--verified-at",
        "2026-05-30T00:04:00Z",
    )
    assert verified.returncode == 0, verified.stdout + verified.stderr
    evidence = yaml.safe_load(verified.stdout)
    assert evidence["apply_authorized"] is False
    assert evidence["mutation_enabled"] is False

    evidence_path = tmp_path / "approval.yaml"
    evidence_path.write_text(verified.stdout, encoding="utf-8")
    checked = run_script(CHECKER, "--root", str(root), str(evidence_path))
    assert checked.returncode == 0, checked.stdout + checked.stderr

    apply_attempt = run_agentops(root, "apply", CHANGE_ID)
    assert apply_attempt.returncode == 1
    assert "intentionally not implemented" in apply_attempt.stdout


def test_network_collector_fails_closed_without_token(tmp_path: Path, monkeypatch: Any) -> None:
    root = prepare_root(tmp_path)
    init_git_profile(root)
    write_change(root)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)

    result = run_collector(root)
    assert result.returncode == 2
    assert "GITHUB_TOKEN" in result.stderr
    assert result.stdout == ""


def test_network_collector_fails_closed_on_changes_requested(tmp_path: Path, monkeypatch: Any) -> None:
    root = prepare_root(tmp_path)
    init_git_profile(root)
    write_change(root)
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen_factory(change_diff_text(root), state="CHANGES_REQUESTED"))

    result = run_collector(root)
    assert result.returncode == 2
    assert "changes-requested" in result.stderr
    assert result.stdout == ""


def test_network_collector_fails_closed_on_low_permission(tmp_path: Path, monkeypatch: Any) -> None:
    root = prepare_root(tmp_path)
    init_git_profile(root)
    write_change(root)
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen_factory(change_diff_text(root), permission="write"))

    result = run_collector(root, "--minimum-permission", "maintain")
    assert result.returncode == 2
    assert "permission below" in result.stderr
    assert result.stdout == ""


def test_network_collector_fails_closed_on_review_head_mismatch(tmp_path: Path, monkeypatch: Any) -> None:
    root = prepare_root(tmp_path)
    init_git_profile(root)
    write_change(root)
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen_factory(change_diff_text(root), review_sha="b" * 40))

    result = run_collector(root)
    assert result.returncode == 2
    assert "not bound" in result.stderr
    assert result.stdout == ""
