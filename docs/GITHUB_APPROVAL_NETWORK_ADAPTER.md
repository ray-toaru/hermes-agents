# GitHub Approval Network Adapter

Status: read-only adapter.

`collect-github-approval-source` collects pull request review facts from the GitHub REST API and emits the existing captured approval source contract. The emitted document must still be consumed by `verify-live-github-approval-source` before it can become authenticated approval evidence.

The adapter fails closed when the token environment variable is missing, when the pull request base branch is unexpected, when a changes-requested review is present, when an approval is not bound to the pull request head, or when the reviewer permission is below the configured threshold.

Boundary: this adapter does not authorize apply, does not modify GitHub, does not read repository secret files, does not write production state, and does not mutate profiles or runtime state.
