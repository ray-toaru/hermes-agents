# Post-Command Validation Contract

Status: validation-only.

This contract defines passive checks for reviewed command catalog entries after a future guarded operation reports a result. It records required evidence shape only; it does not grant authority, run commands, or change managed state.

## Required outcome fields

Each report must identify the catalog entry, the reviewed request id, the result status, and three guard fields. The guard fields must remain conservative unless a separate reviewed implementation changes this contract.
