from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "apply-blocked-report.schema.json"

EXPECTED_BOUNDARY_FLAGS = {
    "apply_authorized",
    "mutation_allowed",
    "profile_write_allowed",
    "runtime_write_allowed",
    "lock_acquire_allowed",
    "audit_write_allowed",
    "command_execution_allowed",
}


def load_apply_blocked_report(result: subprocess.CompletedProcess[str]) -> dict[str, Any]:
    """Parse and schema-validate a disabled-apply result.

    Tests should assert the structured blocked report rather than duplicating
    JSON parsing and schema validation at each apply-disabled call site. The
    apply-disabled boundary remains governed by stdout JSON, not legacy prose.
    """

    assert result.returncode == 1
    try:
        report = json.loads(result.stdout)
    except json.JSONDecodeError as exc:  # pragma: no cover - pytest displays output
        raise AssertionError(
            f"apply stdout must be a JSON blocked report: {result.stdout!r}"
        ) from exc

    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(schema).validate(report)
    return report


def assert_apply_blocked_report(
    result: subprocess.CompletedProcess[str],
    *,
    change_id: str | None = None,
) -> dict[str, Any]:
    report = load_apply_blocked_report(result)
    assert report["report_id"] == "apply_blocked_report/v1"
    assert report["decision"] == "blocked"
    if change_id is not None:
        assert report["change_id"] == change_id

    boundaries = report["boundaries"]
    assert set(boundaries) == EXPECTED_BOUNDARY_FLAGS
    assert all(value is False for value in boundaries.values())

    blockers = set(report["blockers"])
    assert "real_apply_deferred" in blockers
    assert "apply_disabled" in blockers
    return report
