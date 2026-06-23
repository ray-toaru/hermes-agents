# v15 Capability Ledger

Status: tracking-only.

This ledger records which project slices are present in the repository and keeps future work grouped into reviewable units. It does not change runtime behavior.

The ledger is intentionally small: each item has a name, status, and path list. Tests validate that every listed path exists and that status values remain from the allowed set.

## Maintenance

When a planned item lands, the same follow-up slice must mark it `present` and point at the merged repository path. Non-present items must keep a note explaining the gap.
