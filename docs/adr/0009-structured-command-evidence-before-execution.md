# ADR 0009: Execution-Adjacent Evidence Must Use Structured Commands

## Status

Accepted for future apply design.

## Context

Current audit records contain command strings as redacted evidence. P1 hardening requires those entries to declare `command_evidence_type: recorded_only` and `command_is_not_execution_authority: true`.

A future mutation pipeline will need to run validation and audit commands. Reusing free-form shell strings as execution input would create command injection, ambiguity, environment drift, and privilege boundary risks.

## Decision

Future execution-adjacent records must use structured command evidence before any command can be run by AgentOps.

A future structured command record must include at least:

- command identifier from an allowlisted registry;
- argv array, not shell text;
- working directory policy;
- allowed environment keys;
- forbidden environment keys;
- expected read/write paths;
- timeout;
- redaction policy;
- expected exit-code semantics;
- output hash capture rules;
- whether the command is validation-only, mutation, rollback, or audit capture.

Commands must be dispatched through reviewed AgentOps/Hermes-compatible registries, not through arbitrary shell execution.

Current command strings in audit records remain evidence only and must not be executed by future code.

## Consequences

- A future apply implementation must introduce a structured command schema before execution.
- Shell metacharacter filtering is not sufficient for mutation safety.
- Existing audit command strings are not execution plans.
- Future audit capture should store both structured command metadata and redacted outputs.
- This ADR does not implement command execution.
