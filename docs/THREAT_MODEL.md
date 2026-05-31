# Threat Model

## Scope

This threat model covers repository-backed AgentOps governance and any future path toward applying managed profile changes.

It does not cover Hermes runtime internals, business task execution, model behavior, or external secret manager implementation except where AgentOps must avoid touching them.

## Assets

- integrity of `main`;
- integrity of managed profile declarations;
- integrity of policies and schemas;
- integrity of change proposals, diffs, approvals, pre-apply plans, and lock records;
- confidentiality of real secret values;
- separation between AgentOps governance and Hermes runtime/business execution;
- auditability of future mutation attempts.

## Trust Boundaries

| Boundary | Trusted Inputs | Untrusted Inputs |
| --- | --- | --- |
| GitHub ruleset | configured repository enforcement | local comments, stale PRs, bypass claims |
| CI | checked-out repository at PR SHA | claims that tests passed without evidence |
| Policy/schema | repository-reviewed files | proposal-local overrides |
| Change records | schema-valid, hash-bound files | user claims, stale records, mismatched hashes |
| Approvals | structurally valid review records | identity claims without future authentication |
| Runtime | external Hermes runtime | repository scripts pretending to be runtime authority |
| Secrets | external secret manager | committed secret values, `.env`, logs |

## Threats and Mitigations

### Malicious or stale PR

Threat: A PR reintroduces older CLI, weaker policy, or bypasses current guards.

Mitigations:

- ruleset/PR flow;
- CODEOWNERS;
- CI;
- expected-head merge discipline;
- close stale PRs without rebasing when they would regress main.

### CI bypass or guard weakening

Threat: CI scripts are weakened in the same PR that changes protected files.

Mitigations:

- CODEOWNERS over `.github/` and scripts;
- ruleset status checks;
- review checklist treats CI as detection and ruleset as enforcement.

### Policy drift

Threat: Code constants and policy thresholds diverge.

Mitigations:

- load thresholds from policy;
- validate policy before proposal and verification;
- keep constants as fallbacks only where documented.

### Approval forgery or misuse

Threat: Approval records are treated as authenticated identity or execution authority.

Mitigations:

- schema and hash binding;
- duplicate approver rejection;
- rejection blocks verification;
- documentation states approval records are not identity proofs;
- future authenticated approval design remains required.

### Diff tampering

Threat: `diff.patch` changes after proposal or approval.

Mitigations:

- proposal and approvals bind to `diff_sha256`;
- verifier recalculates hash;
- pre-apply plan binds to verified evidence.

### Path escape

Threat: Diff paths escape `profiles/<agent>/` or use ambiguous encoding.

Mitigations:

- reject absolute, traversal, backslash, empty segment, quoted, whitespace, non-normal, and malformed paths;
- require path scope validation;
- re-run patch applicability immediately before future mutation.

### Dirty worktree or stale patch

Threat: A plan is generated or applied against unexpected repository state.

Mitigations:

- base verification is non-mutating;
- plan generation requires `changes verify --check-git-clean --check-patch-applicable`;
- future apply must re-run both immediately before mutation;
- pre-apply plan records base commit.

### Plan reuse

Threat: A pre-apply plan is reused for another change or repository state.

Mitigations:

- plan binds to change ID, agent, base commit, diff evidence, and canonical audit path;
- validator checks cross-field consistency.

### Lock reuse or stale lock abuse

Threat: A lock is reused for a different plan, or stale lock release erases evidence.

Mitigations:

- lock binds to change ID, plan hash, and base commit;
- repository-scoped exclusive lock contract;
- stale locks require manual inspection before release;
- current checker is read-only.

### Secret leakage

Threat: Secret values enter Git, diffs, plans, approvals, logs, or audit output.

Mitigations:

- `.gitignore` and CI secret/runtime guards;
- policy forbids reading secret values;
- docs and approval acknowledgements explicitly state secret values were not reviewed.

### Runtime-adjacent management creep

Threat: Health, deployment, repair, gateway, cron, container, systemd, or session-related work is added implicitly through validators, plans, locks, or apply code without a separate design and approval model.

Mitigations:

- current scripts must not mutate runtime state;
- future runtime-adjacent management requires explicit design/ADR;
- start read-only where possible;
- require approval for service-affecting operations;
- do not treat runtime state as governance authority;
- do not bypass Hermes provider resolution, tool dispatch, or session handling.

### Business orchestration creep

Threat: AgentOps becomes a workflow scheduler or business decision system.

Mitigations:

- role boundary: control plane only;
- policy forbidden `execute_business_actions`;
- PR checklist rejects business orchestration.

## Residual Risks

- Current approval records are not authenticated identity proofs.
- Current lock checker does not acquire or release locks.
- Current rollback and audit records are not implemented.
- Ruleset configuration is external to Git; repository docs must be updated when it changes.
- Future runtime-adjacent management requires separate design before implementation.
- A future apply implementation will need sandboxing and recovery tests beyond current read-only validators.
