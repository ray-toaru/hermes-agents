# Lock Write Path ADR

Status: deferred.

This ADR records prerequisites for any future production lock write path. Current implementation remains read-only: no acquire, release, overwrite, or production lock store mutation is allowed.

Required before reconsideration:

- live approval source bound to the target change
- governance preflight blocked report available
- audit start and closeout candidate binding
- unknown state preserves the guard
- manual review before any write-capable implementation
