# Live GitHub Approval Verifier Design

Status: read-only captured-source implementation.

`verify-live-github-approval-source` consumes a local YAML capture of GitHub repository, pull request, review, permission, and diff-binding facts. It does not contact GitHub, read tokens, write repository state, authorize apply, or mutate managed state.

The verifier fails closed when repository binding, change binding, diff binding, review head binding, approval threshold, rejection markers, or minimum permission checks do not hold. Successful output uses the existing authenticated approval evidence schema with `verifier_mode: live_github`, `mutation_enabled: false`, and `apply_authorized: false`.

This closes the first implementation gap without introducing a live network adapter. A future network adapter must produce the same source contract before its output can be trusted by this verifier.
