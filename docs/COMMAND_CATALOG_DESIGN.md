# Command Catalog Design

Status: catalog-only.

This design records the shape of a future reviewed command catalog. Entries are metadata only. They are not runnable, not dispatchable, and not authority for apply.

## Required properties

Each entry must have a name, purpose, owner, risk, and disabled guard fields. The catalog must keep `run_allowed: false` and `dispatch_allowed: false` for every entry until a separate reviewed implementation exists.

## Boundary

This document does not change profiles, locks, audit records, runtime state, secrets, or business systems.
