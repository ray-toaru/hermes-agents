from __future__ import annotations

import contextlib
import hashlib
import importlib.machinery
import importlib.util
import io
import os
import signal
import sys
import subprocess
import threading
from pathlib import Path
from types import ModuleType
from typing import Any

_MODULE_CACHE: dict[Path, ModuleType] = {}
TEST_SCRIPT_TIMEOUT_SECONDS = int(os.environ.get("AGENTOPS_TEST_SCRIPT_TIMEOUT_SECONDS", os.environ.get("AGENTOPS_TEST_COMMAND_TIMEOUT_SECONDS", "60")))


def load_script_module(script: Path) -> ModuleType:
    """Load a repository script once so tests do not cold-start Python repeatedly.

    Most AgentOps validators expose ``main(argv)`` and are intentionally
    side-effect-light. Running them in-process keeps CLI behavior observable via
    captured stdout/stderr while avoiding repeated jsonschema imports in child
    interpreters.
    """

    resolved = script.resolve()
    cached = _MODULE_CACHE.get(resolved)
    if cached is not None:
        return cached

    script_dir = resolved.parent
    if str(script_dir) not in sys.path:
        sys.path.insert(0, str(script_dir))

    name = f"agentops_test_{resolved.stem.replace('-', '_')}_{hashlib.sha256(str(resolved).encode('utf-8')).hexdigest()[:12]}"
    loader = importlib.machinery.SourceFileLoader(name, str(resolved))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    if spec is None:
        raise RuntimeError(f"cannot load script spec for {resolved}")
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    _MODULE_CACHE[resolved] = module
    return module


def run_script(script: Path, *args: Any) -> subprocess.CompletedProcess[str]:
    """Run a script's main(argv) in-process and return a CompletedProcess shape."""

    module = load_script_module(script)
    if not hasattr(module, "main"):
        raise RuntimeError(f"{script} does not expose main(argv)")
    argv = [str(arg) for arg in args]
    stdout = io.StringIO()
    stderr = io.StringIO()
    code: Any = 0

    class _ScriptTimeout(Exception):
        pass

    def _timeout_handler(_signum: int, _frame: Any) -> None:
        raise _ScriptTimeout(f"test script timed out after {TEST_SCRIPT_TIMEOUT_SECONDS}s: {script} {' '.join(argv)}")

    old_handler: Any = None
    old_timer: tuple[float, float] | None = None
    try:
        if threading.current_thread() is threading.main_thread() and TEST_SCRIPT_TIMEOUT_SECONDS > 0:
            old_handler = signal.getsignal(signal.SIGALRM)
            old_timer = signal.setitimer(signal.ITIMER_REAL, TEST_SCRIPT_TIMEOUT_SECONDS)
            signal.signal(signal.SIGALRM, _timeout_handler)
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            try:
                code = module.main(argv)
            except SystemExit as exc:
                code = exc.code
    except _ScriptTimeout as exc:
        print(f"error: {exc}", file=stderr)
        code = 124
    finally:
        if old_timer is not None:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, old_handler)
            remaining, interval = old_timer
            if remaining > 0:
                signal.setitimer(signal.ITIMER_REAL, remaining, interval)
    if code is None:
        returncode = 0
    elif isinstance(code, int):
        returncode = code
    else:
        returncode = 1
    return subprocess.CompletedProcess([str(script), *argv], returncode, stdout.getvalue(), stderr.getvalue())
