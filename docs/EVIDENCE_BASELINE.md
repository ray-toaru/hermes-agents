# Evidence Baseline

## Purpose

This document records the upstream Hermes evidence that shaped the AgentOps Manager design. It preserves the source-to-constraint chain from the initial v0.1 design baseline so future agents do not have to reconstruct it from conversation history.

## Hermes Architecture

Evidence source:

- `https://hermes-agent.nousresearch.com/docs/developer-guide/architecture`

Derived constraints:

- Hermes entry points such as CLI, Gateway, ACP, Batch Runner, API Server, and Python Library enter the official `AIAgent` loop.
- AgentOps must not replace `AIAgent`, prompt building, provider resolution, tool dispatch, compression/caching, session storage, or tool backends.
- AgentOps belongs around the runtime as a governance/control plane for profile assets and change evidence.

## Profile Isolation

Evidence source:

- `https://hermes-agent.nousresearch.com/docs/developer-guide/architecture`

Derived constraints:

- Hermes supports profile isolation through per-profile `HERMES_HOME`, config, memory, sessions, gateway PID, and concurrent profiles.
- AgentOps uses a Hermes profile as the minimum managed unit.
- Repository-managed assets live under `profiles/<agent>/`.
- Runtime homes, sessions, logs, and workspaces stay outside the repository.

## Tools Runtime and Registry

Evidence source:

- `https://hermes-agent.nousresearch.com/docs/developer-guide/tools-runtime`

Derived constraints:

- Hermes tools are registered through the official registry and dispatched through the official runtime path.
- AgentOps must not bypass Hermes tool registration or dispatch.
- Tool permission and profile governance may be declared and reviewed, but AgentOps must not become a parallel tool runtime.

## Provider Runtime Resolution

Evidence source:

- `https://hermes-agent.nousresearch.com/docs/developer-guide/provider-runtime`

Derived constraints:

- Provider runtime resolution is shared by CLI, gateway, cron jobs, ACP, and auxiliary model calls.
- AgentOps may govern declared provider references and config changes.
- AgentOps must not hard-code or bypass provider/base URL/API key resolution.
- Real secret values remain outside repository governance files.

## Session Storage

Evidence source:

- `https://hermes-agent.nousresearch.com/docs/developer-guide/session-storage`

Derived constraints:

- Hermes session state is runtime data and may include message history, model configuration, token/cost/tool-call metadata, and other execution details.
- Session databases and logs must not be committed.
- Current AgentOps scripts must not read runtime state as authority for governance mutation.
- Future health reporting may use minimal metadata only after explicit design and redaction rules.

## Gateway Internals

Evidence source:

- `https://hermes-agent.nousresearch.com/docs/developer-guide/gateway-internals`

Derived constraints:

- Gateway is a long-running runtime entry point that maps platform events into Hermes sessions and agent responses.
- AgentOps may later use gateway-adjacent notifications or approval surfaces only through explicit design.
- AgentOps must not turn gateway into a business workflow orchestrator or bypass the official agent loop.

## Terminal Dangerous-Command Approval Flow

Evidence source:

- `https://hermes-agent.nousresearch.com/docs/developer-guide/tools-runtime`

Derived constraints:

- Hermes already has runtime-level approval behavior for dangerous terminal commands.
- AgentOps still needs repository-level policy, diff-first review, and apply-readiness gates above that runtime approval layer.
- Runtime approval does not make repository mutation safe by itself.

## Initial Design Baseline

The initial AgentOps Manager v0.1 design converged on these durable decisions:

- AgentOps is a management/control plane, not a business orchestrator.
- It manages agents, not business tasks delegated to agents.
- Profile is the minimum managed unit.
- Git stores declared profile/governance assets; local runtime stores state; secret manager stores real secret values.
- Critical changes are diff-first.
- Low-risk documentation/governance fixes may be automated only when explicitly allowed.
- Secret values are reference-only in the repository.
- Health/deployment/repair management is a long-term AgentOps direction, but current scripts must not mutate runtime state or bypass Hermes runtime mechanisms.
