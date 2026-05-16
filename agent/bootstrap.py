"""Bootstrap the packaged MaaLK Python agent.

The release package runs on the user's machine, not in the development venv.
This wrapper installs Python dependencies into agent/.deps on first launch,
adds that directory to sys.path, and then executes main.py with the original
MFA identifier argument.
"""

from __future__ import annotations

import importlib.util
import os
import runpy
import subprocess
import sys
import traceback
from datetime import datetime
from pathlib import Path


AGENT_DIR = Path(__file__).resolve().parent
DEPS_DIR = AGENT_DIR / ".deps"
REQUIREMENTS = AGENT_DIR / "requirements.txt"
MAIN = AGENT_DIR / "main.py"

REQUIRED_MODULES = ("maa", "numpy")


class _Tee:
    def __init__(self, log_file, original):
        self._log_file = log_file
        self._original = original

    def write(self, text):
        self._log_file.write(text)
        self._log_file.flush()
        if self._original:
            self._original.write(text)
            self._original.flush()

    def flush(self):
        self._log_file.flush()
        if self._original:
            self._original.flush()


def _setup_logging():
    log_dir = AGENT_DIR / "logs"
    log_dir.mkdir(exist_ok=True)
    log_path = log_dir / f"bootstrap_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    log_file = open(log_path, "a", encoding="utf-8")
    sys.stdout = _Tee(log_file, sys.stdout)
    sys.stderr = _Tee(log_file, sys.stderr)
    print(f"=== Bootstrap started at {datetime.now().isoformat()} ===")
    print(f"PID: {os.getpid()}")
    print(f"CWD: {os.getcwd()}")
    print(f"argv: {sys.argv}")
    print(f"Python: {sys.executable} {sys.version}")
    print(f"Agent dir: {AGENT_DIR}")
    print(f"Deps dir: {DEPS_DIR}")
    return log_file


def _prepend_runtime_paths() -> None:
    agent_path = str(AGENT_DIR)
    if agent_path not in sys.path:
        sys.path.insert(0, agent_path)

    if DEPS_DIR.exists():
        deps_path = str(DEPS_DIR)
        if deps_path not in sys.path:
            sys.path.insert(0, deps_path)


def _deps_ready() -> bool:
    _prepend_runtime_paths()
    missing = [module for module in REQUIRED_MODULES if importlib.util.find_spec(module) is None]
    if missing:
        print(f"[Bootstrap] Missing modules: {missing}")
        return False
    print("[Bootstrap] Dependencies are ready.")
    return True


def _install_deps() -> None:
    if not REQUIREMENTS.exists():
        raise FileNotFoundError(f"Missing requirements file: {REQUIREMENTS}")

    DEPS_DIR.mkdir(parents=True, exist_ok=True)
    command = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--upgrade",
        "--target",
        str(DEPS_DIR),
        "-r",
        str(REQUIREMENTS),
    ]
    print("[Bootstrap] Installing agent dependencies...")
    print("[Bootstrap] " + " ".join(command))
    subprocess.check_call(command)


def main() -> None:
    log_file = _setup_logging()
    try:
        _prepend_runtime_paths()
        if not _deps_ready():
            _install_deps()
            if not _deps_ready():
                missing = [m for m in REQUIRED_MODULES if importlib.util.find_spec(m) is None]
                raise RuntimeError(f"Agent dependencies are still missing: {missing}")

        sys.argv = [str(MAIN), *sys.argv[1:]]
        print(f"[Bootstrap] Running main: {sys.argv}")
        runpy.run_path(str(MAIN), run_name="__main__")
    except Exception:
        print("[Bootstrap] FATAL ERROR")
        print(traceback.format_exc())
        raise
    finally:
        log_file.close()


if __name__ == "__main__":
    main()
