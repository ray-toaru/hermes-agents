# Governance Stage Gate ADR

Status: proposed and deferred.

This ADR defines the gate for any future transition from governance-only records to a guarded change stage. The current decision is to keep the project in governance-only mode.

## Required gates before reconsideration

Before this decision can change, the repository must have a live approval verifier, integrated lock lifecycle evidence, completion audit evidence, a reviewed command catalog, and post-command validation evidence. Each prerequisite must have tests and CI coverage.

## Current decision

The next stage remains deferred. This ADR adds a measurable gate only; it does not change managed state.
