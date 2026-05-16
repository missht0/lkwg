"""Bootstrap the packaged MaaLK Python agent.

The release package runs on the user's machine, not in the development venv.
This wrapper installs Python dependencies into agent/.deps on first launch,
adds that directory to sys.path, and then executes main.py with the original
MFA identifier argument.
"""

from __future__ import annotations

import importlib.util
import runpy
import subprocess
import sys
from pathlib import Path


AGENT_DIR = Path(__file__).resolve().parent
DEPS_DIR = AGENT_DIR / ".deps"
REQUIREMENTS = AGENT_DIR / "requirements.txt"
MAIN = AGENT_DIR / "main.py"

REQUIRED_MODULES = ("maa", "numpy")


def _prepend_deps_path() -> None:
    if DEPS_DIR.exists():
        sys.path.insert(0, str(DEPS_DIR))


def _deps_ready() -> bool:
    _prepend_deps_path()
    return all(importlib.util.find_spec(module) is not None for module in REQUIRED_MODULES)


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
    if not _deps_ready():
        _install_deps()
        if not _deps_ready():
            missing = [m for m in REQUIRED_MODULES if importlib.util.find_spec(m) is None]
            raise RuntimeError(f"Agent dependencies are still missing: {missing}")

    sys.argv = [str(MAIN), *sys.argv[1:]]
    runpy.run_path(str(MAIN), run_name="__main__")


if __name__ == "__main__":
    main()
