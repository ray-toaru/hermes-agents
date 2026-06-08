from __future__ import annotations

import os
import signal
import subprocess
from collections.abc import Iterator
from typing import Any

import pytest

TEST_SUBPROCESS_TIMEOUT_SECONDS = int(os.environ.get("AGENTOPS_TEST_COMMAND_TIMEOUT_SECONDS", "60"))


@pytest.fixture(autouse=True)
def subprocess_timeout(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Fail closed instead of letting test subprocesses hang indefinitely."""

    original_run = subprocess.run

    def run_with_timeout(*popenargs: Any, **kwargs: Any) -> subprocess.CompletedProcess[Any]:
        kwargs.setdefault("timeout", TEST_SUBPROCESS_TIMEOUT_SECONDS)
        return original_run(*popenargs, **kwargs)

    monkeypatch.setattr(subprocess, "run", run_with_timeout)
    yield
    # Test helpers and repository-internal dispatch use SIGALRM for fail-closed
    # in-process script timeouts. Ensure no alarm leaks across tests or into
    # Python interpreter shutdown, where it can make single-process pytest runs
    # nondeterministic in sandbox-heavy suites.
    signal.setitimer(signal.ITIMER_REAL, 0)
    signal.signal(signal.SIGALRM, signal.SIG_DFL)
