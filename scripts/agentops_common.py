"""Shared helpers for Hermes AgentOps governance scripts.

The helpers in this module are intentionally small and side-effect-light. They
centralize file parsing, hashing, UTC timestamp formatting, and subprocess
execution so safety behavior is consistent across standalone scripts.
"""

from __future__ import annotations

import contextlib
import hashlib
import importlib.machinery
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

DEFAULT_COMMAND_TIMEOUT_SECONDS = int(os.environ.get("AGENTOPS_COMMAND_TIMEOUT_SECONDS", "30"))
TIMEOUT_EXIT_CODE = 124


def load_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def write_yaml(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(data, handle, allow_unicode=True, sort_keys=False)


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def utc_now_compact() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def iso_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_date_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def agent_from_change_id(change_id: str) -> str | None:
    parts = change_id.split("_")
    return parts[1] if len(parts) == 3 else None


def run_command(
    command: list[str],
    cwd: Path | None = None,
    *,
    input_text: str | None = None,
    timeout: int | None = None,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run an argv-only subprocess with captured output and a hard timeout.

    The project intentionally avoids shell commands for governance scripts. A
    timeout returns a CompletedProcess with exit code 124 so existing fail-closed
    call sites can report the failure without hanging indefinitely.
    """

    actual_timeout = DEFAULT_COMMAND_TIMEOUT_SECONDS if timeout is None else timeout
    try:
        return subprocess.run(
            command,
            cwd=cwd,
            input=input_text,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=actual_timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else ""
        stderr = exc.stderr if isinstance(exc.stderr, str) else ""
        timeout_message = f"command timed out after {actual_timeout}s: {' '.join(command)}"
        stderr = (stderr + "\n" + timeout_message).strip()
        return subprocess.CompletedProcess(command, TIMEOUT_EXIT_CODE, stdout, stderr)



def run_python_script_main(
    script: Path,
    argv: list[str],
    cwd: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run a Python script's main(argv) in-process with captured output.

    This is used only for reviewed repository-internal Python entry points where
    spawning a child interpreter adds no security boundary. It preserves the
    CompletedProcess interface used by subprocess call sites while avoiding
    repeated cold imports in tests and sandbox-only validation paths.
    """

    resolved = script.resolve()
    command = [sys.executable, str(resolved), *argv]
    script_dir = resolved.parent
    old_cwd = Path.cwd()
    old_sys_path = list(sys.path)
    saved_common = sys.modules.get("agentops_common")
    common_was_present = "agentops_common" in sys.modules
    stdout = io.StringIO()
    stderr = io.StringIO()
    code: Any = 0
    try:
        if cwd is not None:
            os.chdir(cwd)
        if str(script_dir) not in sys.path:
            sys.path.insert(0, str(script_dir))
        if (script_dir / "agentops_common.py").exists():
            sys.modules.pop("agentops_common", None)
        module_name = f"agentops_internal_{resolved.stem.replace('-', '_')}_{sha256_text(str(resolved))[:12]}"
        loader = importlib.machinery.SourceFileLoader(module_name, str(resolved))
        spec = importlib.util.spec_from_loader(loader.name, loader)
        if spec is None:
            raise RuntimeError(f"cannot load script spec for {resolved}")
        module = importlib.util.module_from_spec(spec)
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            loader.exec_module(module)
            if not hasattr(module, "main"):
                raise RuntimeError(f"{resolved} does not expose main(argv)")
            try:
                code = module.main(list(argv))
            except SystemExit as exc:
                code = exc.code
    except Exception as exc:
        print(f"error: {exc}", file=stderr)
        code = 1
    finally:
        if common_was_present:
            sys.modules["agentops_common"] = saved_common  # type: ignore[assignment]
        else:
            sys.modules.pop("agentops_common", None)
        sys.path[:] = old_sys_path
        os.chdir(old_cwd)
    returncode = code if isinstance(code, int) else 1
    return subprocess.CompletedProcess(command, returncode, stdout.getvalue(), stderr.getvalue())


def run_internal_python_command(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    if len(command) >= 2 and Path(command[0]).resolve() == Path(sys.executable).resolve():
        script = Path(command[1])
        script_path = script if script.is_absolute() else cwd / script
        if script_path.exists():
            return run_python_script_main(script_path, command[2:], cwd=cwd)
    return run_command(command, cwd)

def require_success(process: subprocess.CompletedProcess[str], label: str) -> None:
    if process.returncode != 0:
        details = (process.stdout + process.stderr).strip()
        raise RuntimeError(f"{label} failed: {details}")


def is_safe_relative_path(value: Any) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    if "\\" in value:
        return False
    candidate = Path(value)
    return not candidate.is_absolute() and ".." not in candidate.parts



def validate_copy_source(
    path: Path,
    *,
    forbidden_path_parts: set[str],
    forbidden_filenames: set[str],
) -> None:
    for item in path.rglob("*"):
        rel_parts = item.relative_to(path).parts
        if item.is_symlink():
            raise RuntimeError(f"refusing to copy symlink: {item}")
        if any(part in forbidden_path_parts for part in rel_parts):
            raise RuntimeError(f"refusing to copy runtime path: {item}")
        if item.name in forbidden_filenames:
            raise RuntimeError(f"refusing to copy secret/runtime file: {item}")


def copy_workspace_dirs(
    root: Path,
    sandbox: Path,
    *,
    copy_dirs: tuple[str, ...],
    forbidden_path_parts: set[str],
    forbidden_filenames: set[str],
) -> None:
    for dirname in copy_dirs:
        source = root / dirname
        if not source.exists():
            continue
        validate_copy_source(
            source,
            forbidden_path_parts=forbidden_path_parts,
            forbidden_filenames=forbidden_filenames,
        )
        shutil.copytree(source, sandbox / dirname, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))

def schema_error_messages(instance: Any, validator: Any, path: Path) -> list[str]:
    errors: list[str] = []
    for error in sorted(validator.iter_errors(instance), key=lambda item: list(item.path)):
        location = ".".join(str(part) for part in error.path) or "<root>"
        errors.append(f"{path}: {location}: {error.message}")
    return errors
