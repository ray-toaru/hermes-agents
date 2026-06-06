from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from agentops_common import TIMEOUT_EXIT_CODE, run_command, run_internal_python_command, run_python_script_main


def test_run_command_returns_timeout_failure() -> None:
    result = run_command(
        [sys.executable, "-c", "import time; time.sleep(2)"],
        ROOT,
        timeout=1,
    )

    assert result.returncode == TIMEOUT_EXIT_CODE
    assert "timed out" in result.stderr


def test_run_python_script_main_captures_main_output_and_restores_cwd(tmp_path: Path) -> None:
    script = tmp_path / "tool.py"
    script.write_text(
        "from pathlib import Path\n"
        "def main(argv):\n"
        "    print('cwd=' + Path.cwd().name)\n"
        "    print('argv=' + ','.join(argv))\n"
        "    return 7\n",
        encoding="utf-8",
    )
    before = Path.cwd()

    result = run_python_script_main(script, ["alpha", "beta"], cwd=tmp_path)

    assert result.returncode == 7
    assert f"cwd={tmp_path.name}" in result.stdout
    assert "argv=alpha,beta" in result.stdout
    assert result.stderr == ""
    assert Path.cwd() == before


def test_run_internal_python_command_dispatches_existing_script_in_process(tmp_path: Path) -> None:
    script = tmp_path / "tool.py"
    script.write_text(
        "def main(argv):\n"
        "    print('internal:' + ':'.join(argv))\n"
        "    return 0\n",
        encoding="utf-8",
    )

    result = run_internal_python_command([sys.executable, str(script), "one", "two"], tmp_path)

    assert result.returncode == 0
    assert result.stdout.strip() == "internal:one:two"
    assert result.stderr == ""
