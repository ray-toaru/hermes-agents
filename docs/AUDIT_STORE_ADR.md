# Audit Store ADR

Status: deferred.

This ADR records prerequisites for any future production audit store path. Current implementation remains read-only: no append, overwrite, external sink, or production audit store write is allowed.

Required before reconsideration:

- append-only storage model
- hash binding to change, approval, lock guard, and closeout records
- failure closeout path preserving the guard
- retention and tamper-evidence policy
- manual review before any write-capable implementation
