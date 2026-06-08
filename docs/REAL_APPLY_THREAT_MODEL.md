# Real Apply Threat Model

Status: **design-only**. This document does not implement, enable, or authorize real apply.

## Assets

Protected assets:

- managed profile declarations under `profiles/<agent>/`;
- change proposals and approval evidence under `changes/<change_id>/`;
- policy and schema files;
- production lock records;
- rollback evidence;
- production audit records;
- CI and review history;
- future canary apply targets.

Out of scope for this repository unless a separate runtime-adjacent design is approved:

- real secret values;
- Hermes runtime sessions, logs, state databases, gateway, cron, containers, or systemd units;
- business task execution.

## Attacker Model

Assume an attacker may attempt to:

1. submit a malicious diff that escapes `profiles/<agent>/`;
2. reuse or replay old approval evidence;
3. tamper with diff hashes after approval;
4. forge YAML approval records;
5. introduce a rejection after approvals are collected;
6. bypass readiness by fabricating a report;
7. create or hide stale locks;
8. induce a dirty worktree before rollback evidence is recorded;
9. cause mutation timeout or partial write;
10. cause post-apply validation to fail after mutation;
11. suppress audit evidence;
12. trick recovery into releasing locks after unknown state;
13. smuggle secret reads or runtime mutation into validation commands;
14. treat sandbox evidence as production evidence;
15. treat design readiness as apply authorization.

## Required Mitigations

| Threat | Required mitigation |
| --- | --- |
| Path escape | Normalize and restrict all changed paths to `profiles/<agent>/`; reject absolute paths, path traversal, backslashes, and ambiguous quoted paths. |
| Approval replay | Bind approval evidence to repository, branch, change ID, agent, diff hash, approver identity, decision, and time. |
| Diff tampering | Recompute and compare diff hash immediately before mutation. |
| YAML approval forgery | Require authenticated approval evidence; YAML approvals alone remain governance records. |
| Late rejection | Treat any rejection or changes-requested evidence as blocking until explicitly superseded by reviewed policy. |
| Fabricated readiness | Validate readiness schema, gate uniqueness, required gates, evidence paths, hashes, and blocking statuses. |
| Lock bypass | Require production lock before rollback or mutation; active, stale, or recovery-required locks block. |
| Dirty worktree | Require clean worktree before rollback point and before applying the reviewed diff. |
| Partial mutation | Use timeout-bound commands, capture pre/post hashes, and preserve lock on uncertainty. |
| Validation failure | Run post-apply validation before lock release; failure enters recovery-required. |
| Audit suppression | Write audit-start before mutation and audit-completion after outcome; audit write failure preserves lock. |
| Unsafe recovery | Unknown state fails closed; no automatic lock release or retry without manual review. |
| Secret/runtime command smuggling | Use reviewed argv-only allowlists; reject commands that access secret or runtime paths. |
| Sandbox/production confusion | Production records must have production-specific schemas and flags; sandbox records cannot satisfy production gates. |
| Design/authorization confusion | Design records must say implementation and enablement are false; `apply` remains disabled. |

## Fail-Closed Requirements

The future real apply implementation must fail closed when:

- required evidence is missing or malformed;
- evidence hashes do not match;
- approval verifier mode is unsupported;
- any rejection exists;
- lock state is active, stale, recovery-required, or unknown;
- rollback point cannot be created or verified;
- audit-start cannot be written before mutation;
- mutation exits non-zero or times out;
- post-apply validation fails or times out;
- audit-completion cannot be written;
- recovery cannot prove the resulting state.

Fail-closed means: preserve evidence, preserve or mark the production lock, require manual review, and do not retry automatically.

## Attacks Rejected by This Design

### Attack: Enable real apply by adding a feature flag

Rejected. A feature flag that enables mutation before production lock, rollback, audit, validation, and recovery slices converge would bypass the staged safety model.

### Attack: Reuse integrated sandbox evidence as production proof

Rejected. Sandbox evidence proves sequencing and immutability of source profiles during tests. It does not acquire a production lock, execute production mutation, or write production audit.

### Attack: Release lock after failed validation to unblock operators

Rejected. Failed validation after mutation creates uncertainty. The lock must be preserved or marked recovery-required until manual review.

### Attack: Let rollback execute automatically for every failure

Rejected. Rollback execution requires known preconditions. Unknown state must not trigger blind rollback or lock release.

### Attack: Treat signed approval as universal live GitHub proof

Rejected. Signed attestation is a valid reviewed evidence path. Live GitHub review provenance remains a separate verifier and must fail closed until implemented.
