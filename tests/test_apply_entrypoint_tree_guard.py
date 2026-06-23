from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / ("run-" + "apply" + "-entrypoint-blocked")


def snapshot(root: Path) -> dict[str, str]:
    return {
        str(path.relative_to(root)): path.read_text(encoding="utf-8")
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def test_blocked_entrypoint_keeps_worktree_unchanged(tmp_path: Path) -> None:
    preflight = tmp_path / "preflight.yaml"
    preflight.write_text(yaml.safe_dump({"decision": "blocked"}), encoding="utf-8")
    for dirname in ["a/demo", "b", "c", "d", "e"]:
        directory = tmp_path / dirname
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "sentinel.txt").write_text("unchanged", encoding="utf-8")
    before = snapshot(tmp_path)

    result = subprocess.run(
        [sys.executable, str(SCRIPT), "demo", "--preflight-report", str(preflight)],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    report = json.loads(result.stdout)
    assert report["decision"] == "blocked"
    assert all(value is False for value in report["boundaries"].values())
    assert snapshot(tmp_path) == before
