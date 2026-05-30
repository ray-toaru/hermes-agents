# Ruleset Smoke Test

This file is a controlled, low-risk change used to verify repository ruleset behavior for the default branch.

Expected protections:

- required status check: `validate`
- required pull request review
- required Code Owner review
- required review thread resolution
- non-fast-forward updates blocked
- deletion blocked
- linear history preserved

This file can remain as an audit artifact after the ruleset verification is complete.
