# P10 Stage Readiness v7

P10 has a blocked entrypoint adapter and tree guard coverage.

Decision: deferred.

The adapter proves the blocked report shape and non-writing behavior, but the monolithic `hermes-agentops apply` command has not yet been safely patched to call it directly.

The project must continue to keep apply non-zero and non-mutating until a safe single-entrypoint patch is reviewed and tested.
