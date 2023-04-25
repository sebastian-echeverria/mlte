"""
Unit tests for command line interface.
"""

import os
import sys
import subprocess
from pathlib import Path


def python() -> Path:
    """Return the path to the current interpreter."""
    return Path(sys.executable)


def script() -> Path:
    """Return the path to the CLI script."""
    path = Path(os.path.dirname(__file__))
    path = path.parent.parent / "src" / "mlte" / "cli" / "cli.py"
    return path.resolve()


def execute_cli() -> int:
    """Execute the CLI script."""
    command = [str(python()), str(script())]
    p = subprocess.run(command)
    return p.returncode


def test_cli():
    assert execute_cli() == 0
