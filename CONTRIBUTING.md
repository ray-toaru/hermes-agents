# Contributing

This repository is managed as a controlled AgentOps codebase.

## Workflow

1. Open or claim an Issue.
2. Create a branch using one of:
   - `bootstrap/*`
   - `feature/*`
   - `fix/*`
   - `docs/*`
   - `schema/*`
   - `policy/*`
   - `ci/*`
3. Make the smallest coherent change.
4. Open a pull request.
5. Ensure CI passes.
6. Wait for review before merge.

## Pull Request Requirements

Every PR must describe:

- goal
- non-goal
- evidence
- risk
- files changed
- tests
- rollback
- review/attack notes

## Security Rules

Do not commit:

- `.env`
- real API keys or tokens
- private keys
- `state.db`
- logs
- sessions
- workspaces
- runtime cache

## AgentOps Boundary

AgentOps manages Hermes agent profiles and governance. It must not become a business task scheduler or multi-agent workflow orchestrator.
