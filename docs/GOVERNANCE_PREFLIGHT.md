# Governance Preflight

`run-governance-preflight` is a read-only aggregator for already captured governance evidence.

It consumes local source files for approval, lock readiness, audit closeout, command validation, runtime-adjacent policy, and stage readiness. The checked example is aligned to `stage-readiness-v5.yaml` and still emits a unified preflight report with a blocked decision.

Boundary:

- does not run `hermes-agentops apply`
- does not mutate profiles or runtime state
- does not acquire or release locks
- does not write production audit records
- does not execute commands
- does not read protected values

The report is an operator review aid, not execution authority.
