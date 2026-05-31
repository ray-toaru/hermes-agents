# ADR 0001: AgentOps is a Control Plane, Not a Business Orchestrator

## Status

Accepted.

## Context

Hermes AgentOps Manager manages repository-backed lifecycle assets for Hermes agent profiles. Some managed agents may eventually have business-specific permissions or workflows.

If AgentOps inherited those permissions or dispatched business work, the repository governance layer would become a runtime orchestration system and collapse the safety boundary.

The initial AgentOps design also included long-term health, deployment, repair, gateway, cron, and container management. Those capabilities are compatible with AgentOps only when they remain lifecycle management, are explicitly designed, and do not become business task routing or Hermes runtime replacement.

## Decision

AgentOps is a control plane for profile lifecycle governance and explicitly designed lifecycle management.

It may validate, document, propose, approve, plan, audit, and later design health/deployment/repair management for profile lifecycle operations. It must not schedule agents to perform business tasks, execute trading/research/business actions, or replace Hermes runtime dispatch.

## Consequences

- Business workflow orchestration is out of scope.
- Managed agent permissions do not become AgentOps permissions.
- `execute_business_actions` remains globally forbidden.
- PRs that add business routing must be rejected or moved to a separate system design.
- Runtime-adjacent lifecycle management requires its own design/ADR, read-only-first validation where possible, and approval gates before service-affecting operations.
