# P5 Real Apply Readiness Review v2

## Decision

The project is **ready to design** a real apply pipeline, but it is **not ready to implement or enable** real apply.

The only acceptable next step is a design-only PR for real apply architecture, threat model, recovery runbook, and a disabled skeleton if needed. `hermes-agentops apply` must remain disabled.

Structured review evidence is recorded in:

- `docs/examples/p5-real-apply-readiness-review-v2.yaml`

That record is validated by:

- `schemas/real-apply-readiness-review.schema.json`
- `scripts/check-real-apply-readiness-review`

## Evidence Reviewed

The review covers the v2.1-v2.6 prerequisite chain:

| Slice | Evidence | Review conclusion |
| --- | --- | --- |
| v2.1 maintainability and timeouts | `scripts/agentops_common.py`, `docs/v2.1-maintainability-and-timeouts.md` | Useful hardening; does not affect mutation authority. |
| v2.2 test harness and internal dispatch | `tests/agentops_test_utils.py`, `docs/v2.2-test-harness-and-internal-dispatch.md` | Reduces repeated subprocess cold starts; internal dispatch remains repository-internal and non-shell. |
| v2.3 signed approval verifier | `scripts/verify-authenticated-approval`, signed attestation schemas | Provides read-only authenticated approval evidence; `live_github` remains fail-closed. |
| v2.4 integrated sandbox mutation pipeline | `scripts/run-integrated-sandbox-mutation` | Composes the evidence chain in a temporary workspace only. |
| v2.5 sandbox audit capture | `scripts/generate-sandbox-mutation-audit` | Records sandbox success/failure evidence; not production audit. |
| v2.6 sandbox recovery simulation | `scripts/simulate-sandbox-recovery` | Records fail-closed recovery decisions; does not release locks or execute rollback. |

The existing P5 baseline remains correct that real mutation is blocked until production lifecycle controls exist. This v2 review refines the conclusion: the sandbox and read-only evidence is now sufficient to start **designing** real apply, not implementing it.

## Readiness Matrix

| Gate | Current state | Blocks design? | Blocks implementation? | Reason |
| --- | --- | --- | --- | --- |
| Authenticated approval | Read-only signed attestation implemented | No | No for signed-attestation path | It can authenticate reviewed offline approval evidence, but does not authorize apply. |
| Live GitHub approval | Not implemented | No | No if signed attestations are accepted; yes if direct GitHub reviews are required by policy | Keep fail-closed until separately designed. |
| Structured command evidence | Read-only / validation-only implemented | No | No for design | Mutation dispatch remains absent by design. |
| Integrated sandbox pipeline | Sandbox-only implemented | No | No for design | Proves sequencing and source immutability, not production safety. |
| Sandbox audit capture | Sandbox-only implemented | No | No for design | Captures sandbox facts only. |
| Sandbox recovery simulation | Sandbox-only implemented | No | No for design | Exercises fail-closed decisions only. |
| Real lock lifecycle | Prototype-only | No | Yes | No production apply owner for acquisition, release, stale handling, or recovery-required transitions. |
| Rollback execution | Not implemented | No | Yes | Rollback point creation exists, but rollback execution and validation are absent. |
| Production post-apply validation | Sandbox-only | No | Yes | It is not integrated after real mutation or before real lock release. |
| Production audit capture | Not implemented | No | Yes | Production success/failure audit records are not generated. |
| Production recovery | Not implemented | No | Yes | Unknown-state and retry rules are simulated only. |
| Test stability | Split-run coverage passes; single-process full pytest still times out in the current interactive tool environment | No | Yes until measured/stabilized | Implementation should not proceed without explicit CI/test-runner stability evidence. |

## Required Scope of the Next Design PR

A real apply design PR may include:

- `docs/REAL_APPLY_PIPELINE_DESIGN.md`;
- `docs/REAL_APPLY_THREAT_MODEL.md`;
- `docs/REAL_APPLY_RECOVERY_RUNBOOK.md`;
- optional disabled command skeleton that still returns non-zero and does not mutate anything;
- updates to `docs/IMPLEMENTATION_MATRIX.md`, `docs/ROADMAP.md`, and ADRs if the design changes boundaries.

It must not include:

- source profile mutation;
- runtime state mutation;
- real secret reading;
- real lock release after mutation;
- rollback execution;
- production audit creation;
- business orchestration;
- any feature flag that can enable real apply.

## Blocking Gaps Before Implementation

Before implementation of real apply, the design must be followed by reviewed implementation slices for:

1. production lock lifecycle integration;
2. rollback execution and post-rollback validation;
3. production mutation audit capture;
4. production recovery and retry state machine;
5. post-apply validation after real mutation and before lock release;
6. green grouped CI/test-runner evidence for the full suite and preserved fail-closed timeout behavior.

## Attack Review

### Attack: Treat design readiness as implementation permission

Rejected. The structured review record requires `ready_to_implement_real_apply: false`, `ready_to_enable_real_apply: false`, and `apply_must_remain_disabled: true`. Design readiness only permits a design-only PR.

### Attack: Reuse sandbox evidence as production evidence

Rejected. Sandbox pipeline, sandbox audit, and sandbox recovery records all carry non-production, non-authorizing flags. They prove sequencing and failure semantics, not live mutation safety.

### Attack: Treat temporary lock and rollback prototypes as production controls

Rejected. The prototypes are useful for behavior modeling, but production apply needs integrated lifecycle ownership, stale handling, recovery-required preservation, rollback execution, and audit binding.

### Attack: Treat signed approval as universal live reviewer proof

Rejected. Signed attestation is a valid authenticated evidence path when trust roots are reviewed. Direct GitHub review provenance remains a separate optional verifier and must remain fail-closed until implemented.

### Attack: Ignore the full-pytest timeout because split tests pass

Rejected. Split-run coverage is sufficient for this evidence review, and v2.7 adds explicit grouped CI commands with fail-closed timeouts. Real implementation must still require green grouped CI and must not remove timeout behavior.


## v2.8 Design Package Follow-Up

The design-only next step identified by this review has been materialized in v2.8 through:

- `docs/REAL_APPLY_PIPELINE_DESIGN.md`;
- `docs/REAL_APPLY_THREAT_MODEL.md`;
- `docs/REAL_APPLY_RECOVERY_RUNBOOK.md`;
- `docs/examples/real-apply-design-contract.yaml`;
- `schemas/real-apply-design-contract.schema.json`;
- `scripts/check-real-apply-design-contract`;
- `tests/test_real_apply_design_contract.py`.

This follow-up does not change the implementation decision: real apply is still not ready to implement or enable. The next safe work is prerequisite production slices with `apply` still disabled, beginning with production lock lifecycle integration.

## Final Conclusion

`ready_to_design_real_apply: true`

`ready_to_implement_real_apply: false`

`ready_to_enable_real_apply: false`

`apply_must_remain_disabled: true`

The v2.8 design-only package satisfies the design PR step. Real mutation remains blocked; the next safe step is prerequisite production-slice design/implementation with `apply` still disabled.
