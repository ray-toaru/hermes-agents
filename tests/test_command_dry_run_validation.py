from __future__ import annotations

from pathlib import Path

import yaml

from agentops_test_utils import run_script

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "scripts" / "build-command-dry-run-validation"


def write_catalog(path: Path, *, run_allowed: bool = False, dispatch_allowed: bool = False) -> Path:
    document = {
        "schema_version": 1,
        "catalog_id": "command_catalog/v1",
        "status": "catalog_only",
        "entries": [
            {
                "name": "safe-plan-review",
                "purpose": "review a planned command without running it",
                "owner": "agentops",
                "risk": "medium",
                "run_allowed": run_allowed,
                "dispatch_allowed": dispatch_allowed,
            }
        ],
    }
    path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
    return path


def run_builder(catalog: Path, *args: str):
    return run_script(
        BUILDER,
        "--root",
        str(ROOT),
        "--catalog",
        str(catalog),
        "--entry",
        "safe-plan-review",
        "--review-request-id",
        "review-1",
        *args,
    )


def test_command_dry_run_validation_is_blocked(tmp_path: Path) -> None:
    catalog = write_catalog(tmp_path / "catalog.yaml")
    result = run_builder(catalog)
    assert result.returncode == 0, result.stdout + result.stderr
    document = yaml.safe_load(result.stdout)
    assert document["catalog_entry"] == "safe-plan-review"
    assert document["result_status"] == "blocked"
    assert document["state_changed"] is False
    assert document["guard_released"] is False
    assert document["followup_required"] is True


def test_command_dry_run_rejects_missing_entry(tmp_path: Path) -> None:
    catalog = write_catalog(tmp_path / "catalog.yaml")
    result = run_script(
        BUILDER,
        "--root",
        str(ROOT),
        "--catalog",
        str(catalog),
        "--entry",
        "missing-entry",
        "--review-request-id",
        "review-1",
    )
    assert result.returncode == 2
    assert "not found" in result.stderr
    assert result.stdout == ""


def test_command_dry_run_rejects_non_passive_catalog(tmp_path: Path) -> None:
    catalog = write_catalog(tmp_path / "catalog.yaml", run_allowed=True)
    result = run_builder(catalog)
    assert result.returncode == 2
    assert "False was expected" in result.stderr or "not passive" in result.stderr
    assert result.stdout == ""
