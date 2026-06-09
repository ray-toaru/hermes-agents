from __future__ import annotations

import contextlib
import hashlib
import importlib.machinery
import importlib.util
import io
import sys
import subprocess
from pathlib import Path
from types import ModuleType
from typing import Any

_MODULE_CACHE: dict[Path, ModuleType] = {}


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
    """Run a script's main(argv) in-process and return a CompletedProcess shape.

    The test helper deliberately avoids SIGALRM around the entire script. Many
    AgentOps scripts launch git subprocesses; asynchronously interrupting the
    parent while it is inside subprocess.run can leave child processes defunct
    or make pytest hang after assertions pass. Child subprocesses still receive
    fail-closed timeouts via tests/conftest.py and agentops_common.run_command,
    and CI keeps grouped pytest commands under an outer `timeout`.
    """

    module = load_script_module(script)
    if not hasattr(module, "main"):
        raise RuntimeError(f"{script} does not expose main(argv)")
    argv = [str(arg) for arg in args]
    stdout = io.StringIO()
    stderr = io.StringIO()
    code: Any = 0

    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        try:
            code = module.main(argv)
        except SystemExit as exc:
            code = exc.code
    if code is None:
        returncode = 0
    elif isinstance(code, int):
        returncode = code
    else:
        returncode = 1
    return subprocess.CompletedProcess([str(script), *argv], returncode, stdout.getvalue(), stderr.getvalue())
