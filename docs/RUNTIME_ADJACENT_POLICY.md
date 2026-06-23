# Runtime Adjacent Policy

Status: policy-only.

This policy records that runtime logs, live sessions, gateway operations, container/process control, schedulers, and protected values remain outside the current AgentOps scope.

The policy allows no current access, no mutation, and no protected value reads. Any future runtime-adjacent work requires a separate ADR, dedicated tests, and a new readiness review before implementation.
