from __future__ import annotations

import subprocess
from pathlib import Path

import yaml

from test_change_workflow import init_git_profile, prepare_root, run_agentops, write_change
from agentops_test_utils import run_script

ROOT = Path(__file__).resolve().parents[1]
VERIFIER = ROOT / "scripts" / "verify-authenticated-approval"
CHECKER = ROOT / "scripts" / "check-authenticated-approval"
CHANGE_ID = "20260530T000000Z_agentops_aaaaaaaaaa"


def run_verifier(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return run_script(VERIFIER, CHANGE_ID, "--root", str(root), "--verified-at", "2026-05-30T00:02:00Z", *args)


def run_checker(root: Path, evidence_path: Path) -> subprocess.CompletedProcess[str]:
    return run_script(CHECKER, "--root", str(root), str(evidence_path))


def test_fixture_verifier_emits_contract_valid_evidence(tmp_path: Path) -> None:
    root = prepare_root(tmp_path)
    init_git_profile(root)
    write_change(root)

    result = run_verifier(root)
    assert result.returncode == 0, result.stdout + result.stderr
    evidence = yaml.safe_load(result.stdout)
    assert evidence["verifier_mode"] == "fixture_contract_only"
    assert evidence["mutation_enabled"] is False
    assert evidence["apply_authorized"] is False
    assert evidence["status"] == "verified_not_authorized"
    assert evidence["required_approvals"] == 1
    assert len(evidence["verified_approvals"]) == 1

    evidence_path = tmp_path / "authenticated-approval.yaml"
    evidence_path.write_text(result.stdout, encoding="utf-8")
    check = run_checker(root, evidence_path)
    assert check.returncode == 0, check.stdout + check.stderr

    apply_attempt = run_agentops(root, "apply", CHANGE_ID)
    assert apply_attempt.returncode == 1
    assert "intentionally not implemented" in apply_attempt.stdout


def test_fixture_verifier_fails_closed_for_live_github_mode(tmp_path: Path) -> None:
    root = prepare_root(tmp_path)
    init_git_profile(root)
    write_change(root)

    result = run_verifier(root, "--mode", "live_github")
    assert result.returncode == 2
    assert "not implemented" in result.stderr
    assert result.stdout == ""


def test_fixture_verifier_fails_closed_on_rejection(tmp_path: Path) -> None:
    root = prepare_root(tmp_path)
    init_git_profile(root)
    write_change(root)
    reject = run_agentops(root, "changes", "approve", CHANGE_ID, "--approver", "rejecter", "--decision", "reject")
    assert reject.returncode == 0, reject.stdout + reject.stderr

    result = run_verifier(root)
    assert result.returncode == 2
    assert "rejections are present" in result.stderr
    assert result.stdout == ""


def test_fixture_verifier_fails_closed_on_threshold_failure(tmp_path: Path) -> None:
    root = prepare_root(tmp_path)
    init_git_profile(root)
    write_change(root, required_approvals=2)

    result = run_verifier(root)
    assert result.returncode == 2
    assert "approval threshold unmet" in result.stderr
    assert result.stdout == ""


def test_fixture_verifier_fails_closed_on_diff_mismatch(tmp_path: Path) -> None:
    root = prepare_root(tmp_path)
    init_git_profile(root)
    write_change(root)
    diff_path = root / "changes" / CHANGE_ID / "diff.patch"
    diff_path.write_text(diff_path.read_text(encoding="utf-8") + "\n# tamper\n", encoding="utf-8")

    result = run_verifier(root)
    assert result.returncode == 2
    assert "proposal diff_sha256 mismatch" in result.stderr
    assert result.stdout == ""


def test_fixture_verifier_fails_closed_on_duplicate_approver(tmp_path: Path) -> None:
    root = prepare_root(tmp_path)
    init_git_profile(root)
    write_change(root)
    duplicate = run_agentops(root, "changes", "approve", CHANGE_ID, "--approver", "reviewer-1")
    assert duplicate.returncode == 0, duplicate.stdout + duplicate.stderr

    result = run_verifier(root)
    assert result.returncode == 2
    assert "duplicate approval approver" in result.stderr
    assert result.stdout == ""


def canonical_json_bytes(value: object) -> bytes:
    import json

    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def write_signed_attestation(root: Path, *, decision: str = "approve", tamper: bool = False, permission: str = "write") -> Path:
    import base64

    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives import serialization

    proposal = yaml.safe_load((root / "changes" / CHANGE_ID / "proposal.yaml").read_text(encoding="utf-8"))
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    key_id = "reviewer-1-ed25519"
    (root / "policies" / "trusted-approval-signers.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": 1,
                "trusted_signers": [
                    {
                        "key_id": key_id,
                        "approver": "reviewer-1",
                        "identity_provider": "signed_attestation",
                        "identity_subject": "reviewer-1@example.test",
                        "permission": permission,
                        "public_key": {
                            "algorithm": "ed25519",
                            "encoding": "raw_base64",
                            "value": base64.b64encode(public_key).decode("ascii"),
                        },
                    }
                ],
                "boundaries": {
                    "public_keys_only": True,
                    "does_not_authorize_apply": True,
                    "does_not_mutate_profiles_or_runtime": True,
                    "does_not_read_secret_values": True,
                    "business_orchestration_not_authorized": True,
                },
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    payload = {
        "attestation_id": f"{CHANGE_ID}_reviewer-1_{decision}_attestation",
        "repository": {
            "provider": "github",
            "full_name": "ray-toaru/hermes-agents",
            "default_branch": "main",
        },
        "change_id": CHANGE_ID,
        "agent": "agentops",
        "diff_sha256": proposal["diff_sha256"],
        "approver": "reviewer-1",
        "identity_provider": "signed_attestation",
        "identity_subject": "reviewer-1@example.test",
        "decision": decision,
        "signed_at": "2026-05-30T00:01:00Z",
        "signer_key_id": key_id,
        "evidence_ref": "signed-attestation://test/reviewer-1",
    }
    signature = private_key.sign(canonical_json_bytes(payload))
    if tamper:
        payload["diff_sha256"] = "b" * 64
    attestation = {
        "schema_version": 1,
        "payload": payload,
        "signature": {
            "algorithm": "ed25519",
            "encoding": "base64",
            "value": base64.b64encode(signature).decode("ascii"),
        },
    }
    path = root / "changes" / CHANGE_ID / "signed-attestation.yaml"
    path.write_text(yaml.safe_dump(attestation, sort_keys=False), encoding="utf-8")
    return path


def test_signed_attestation_verifier_emits_contract_valid_evidence(tmp_path: Path) -> None:
    root = prepare_root(tmp_path)
    init_git_profile(root)
    write_change(root)
    attestation_path = write_signed_attestation(root)

    result = run_verifier(root, "--mode", "signed_attestation", "--attestation", str(attestation_path))
    assert result.returncode == 0, result.stdout + result.stderr
    evidence = yaml.safe_load(result.stdout)
    assert evidence["verifier_mode"] == "signed_attestation"
    assert evidence["repository"]["provider"] == "signed_attestation"
    assert evidence["mutation_enabled"] is False
    assert evidence["apply_authorized"] is False
    assert evidence["status"] == "verified_not_authorized"
    assert evidence["verified_approvals"][0]["identity_provider"] == "signed_attestation"
    assert evidence["verified_approvals"][0]["permission"] == "write"

    evidence_path = tmp_path / "authenticated-approval-signed.yaml"
    evidence_path.write_text(result.stdout, encoding="utf-8")
    check = run_checker(root, evidence_path)
    assert check.returncode == 0, check.stdout + check.stderr

    apply_attempt = run_agentops(root, "apply", CHANGE_ID)
    assert apply_attempt.returncode == 1
    assert "intentionally not implemented" in apply_attempt.stdout


def test_signed_attestation_verifier_fails_closed_on_tampered_payload(tmp_path: Path) -> None:
    root = prepare_root(tmp_path)
    init_git_profile(root)
    write_change(root)
    attestation_path = write_signed_attestation(root, tamper=True)

    result = run_verifier(root, "--mode", "signed_attestation", "--attestation", str(attestation_path))
    assert result.returncode == 2
    assert "diff_sha256 mismatch" in result.stderr
    assert result.stdout == ""


def test_signed_attestation_verifier_fails_closed_on_rejection(tmp_path: Path) -> None:
    root = prepare_root(tmp_path)
    init_git_profile(root)
    write_change(root)
    attestation_path = write_signed_attestation(root, decision="reject")

    result = run_verifier(root, "--mode", "signed_attestation", "--attestation", str(attestation_path))
    assert result.returncode == 2
    assert "signed rejection attestation is present" in result.stderr
    assert result.stdout == ""


def test_signed_attestation_verifier_fails_closed_on_insufficient_permission(tmp_path: Path) -> None:
    root = prepare_root(tmp_path)
    init_git_profile(root)
    write_change(root)
    attestation_path = write_signed_attestation(root, permission="write")

    result = run_verifier(
        root,
        "--mode",
        "signed_attestation",
        "--attestation",
        str(attestation_path),
        "--minimum-permission",
        "maintain",
    )
    assert result.returncode == 2
    assert "below required" in result.stderr
    assert result.stdout == ""


def test_signed_attestation_verifier_fails_closed_without_attestation(tmp_path: Path) -> None:
    root = prepare_root(tmp_path)
    init_git_profile(root)
    write_change(root)

    result = run_verifier(root, "--mode", "signed_attestation")
    assert result.returncode == 2
    assert "--attestation is required" in result.stderr
    assert result.stdout == ""
