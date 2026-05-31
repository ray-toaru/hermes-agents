from __future__ import annotations

from pathlib import Path

import yaml

from test_change_workflow import prepare_root, run_verify, write_change


def test_verify_rejects_non_integer_policy_threshold(tmp_path: Path) -> None:
    root = prepare_root(tmp_path)
    policy = root / "policies" / "global-permissions.yaml"
    data = yaml.safe_load(policy.read_text(encoding="utf-8"))
    data["risk_defaults"]["low_required_approvals"] = "not-an-integer"
    policy.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    change_id = write_change(root)

    result = run_verify(root, change_id)

    assert result.returncode == 2
    assert "policy.risk_defaults.low_required_approvals" in result.stdout
    assert "must be an integer" in result.stdout
