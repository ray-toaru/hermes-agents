# Repository Governance Baseline

## Purpose

This baseline adds repository-level review ownership and CI guardrails for long-term AgentOps evolution. It does not enable `apply`, does not mutate managed profiles, does not read secrets, and does not orchestrate business work.

## Evidence from GitHub documentation

- Protected branches are available for public repositories on GitHub Free. Branch protection can require pull request reviews, required status checks, conversation resolution, signed commits, linear history, and related controls.
- CODEOWNERS can be created in `.github/`, repository root, or `docs/`; GitHub checks `.github/` first when multiple files exist.
- Code owners must have explicit write access. CODEOWNERS paths are case-sensitive. Invalid lines are skipped. CODEOWNERS must remain under 3 MB.
- GitHub recommends owning the CODEOWNERS file itself, preferably by placing it under `.github/` and assigning an owner for `.github/` or `.github/CODEOWNERS`.
- Repository rulesets are another official mechanism and are available for public repositories on GitHub Free, but this repository-level baseline keeps the documented configuration compatible with branch protection first because branch protection is already sufficient for the immediate requirements.

References:

- https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches
- https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners
- https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets

## Implemented in repository

- `.github/CODEOWNERS` assigns `@ray-toaru` as owner for the repository and explicitly for high-risk paths.
- `scripts/check-codeowners` validates the CODEOWNERS baseline in CI.
- `.github/workflows/ci.yml` runs the CODEOWNERS baseline check alongside existing validation.

## Required manual GitHub settings

The repository files above are not a substitute for GitHub enforcement. Configure `main` with branch protection or an equivalent ruleset:

1. Require a pull request before merging.
2. For a single-owner repository, do not require author self-approval. GitHub rejects self-approval, so use zero required approvals or a deliberate bypass model while retaining PR and status-check enforcement.
3. Require status checks before merging, including the real `validate` job from the `ci` workflow.
4. Require conversation resolution before merging.
5. Do not allow force pushes.
6. Do not allow deletions.
7. Require linear history and allow only squash or rebase merges when linear history is enabled.
8. Prefer strict required status checks when multiple collaborators are active.

## Current ruleset evidence

The default-branch ruleset was exported and reviewed as `protect-default-branch`. It targets `~DEFAULT_BRANCH`, has `enforcement: active`, includes deletion and non-fast-forward protection, requires PR flow, requires status check `validate`, and uses linear history. Earlier configuration with `lint`, `test`, and `build` status checks was rejected because those checks did not exist in this repository; the real check is the `validate` job from the `ci` workflow.

The ruleset smoke test PR verified that the corrected status check runs successfully and that the single-owner mode can merge through the PR path after the self-approval deadlock was removed. Keep future exported ruleset JSON or screenshots/settings evidence alongside this document whenever the ruleset changes.

## Attack / defense convergence

### Design point: CODEOWNERS location

Attack 1: A root-level CODEOWNERS could be shadowed by a later `.github/CODEOWNERS` file.
Defense 1: Use `.github/CODEOWNERS`, which GitHub searches before root and docs locations.
Result: unchanged.

Attack 2: If `.github/CODEOWNERS` is not itself owned, an attacker can weaken owner mappings.
Defense 2: Add both `/.github/ @ray-toaru` and `/.github/CODEOWNERS @ray-toaru`.
Result: unchanged.

Attack 3: A future contributor might add a second CODEOWNERS elsewhere and think it applies.
Defense 3: Documentation states `.github/` is the authoritative location and the CI guard checks only `.github/CODEOWNERS`.
Result: unchanged.

Converged decision: use `.github/CODEOWNERS` and explicitly own `.github/` and `.github/CODEOWNERS`.

### Design point: owner scope

Attack 1: A single global `*` owner is broad but easy to miss high-risk intent.
Defense 1: Keep `* @ray-toaru` and repeat explicit high-risk path entries for readability and CI validation.
Result: unchanged.

Attack 2: Repeated entries could drift.
Defense 2: `scripts/check-codeowners` requires the exact high-risk entries.
Result: unchanged.

Attack 3: A stricter future model may need different owners per subsystem.
Defense 3: The baseline is intentionally owner-minimal now; future teams can replace exact required owners in one script and one CODEOWNERS file.
Result: unchanged.

Converged decision: global owner plus explicit high-risk owner entries.

### Design point: CI guard vs GitHub enforcement

Attack 1: A CI guard cannot force a human to require code-owner review.
Defense 1: Documentation separates repository guardrails from required manual GitHub branch protection/ruleset settings.
Result: unchanged.

Attack 2: A user with admin access could bypass CI or merge anyway.
Defense 2: Recommend branch protection/ruleset configuration with required checks, required reviews, and no bypass where feasible.
Result: unchanged.

Attack 3: CI scripts can be changed in the same PR.
Defense 3: CODEOWNERS owns `.github/`, scripts, and docs; once branch protection requires Code Owner approval and status checks, changes to the guard require review.
Result: unchanged.

Converged decision: CI guard is a detection layer; GitHub branch protection or rulesets are the enforcement layer.

## Deep review checklist

Use this checklist for every governance PR:

- Safety boundary: `apply` remains disabled; no profile mutation, secret read, runtime state mutation, or business orchestration is introduced.
- Official mechanism alignment: repository files complement GitHub branch protection/rulesets rather than pretending to replace them.
- CODEOWNERS correctness: authoritative file is `.github/CODEOWNERS`; owner has write access; file is under 3 MB; required paths are covered; syntax avoids unsupported negation and bracket ranges.
- CI correctness: guard is deterministic, local-only, and fails closed on missing or changed required entries.
- Review workflow: PR remains required; status checks pass; conversations are resolved; code-owner review is required once branch protection/rulesets are configured.
- Maintainability: paths and owners are explicit; future changes are centralized in CODEOWNERS plus the guard script.
- Rollback: revert the PR to remove the baseline without changing AgentOps runtime behavior.
