"""Sandboxed code execution via subprocess with timeouts."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

# Find the Python executable — prefer the current interpreter
PYTHON = sys.executable or shutil.which("python3") or shutil.which("python") or "python3"


def run_code(
    filepath: str, timeout: int = 30
) -> tuple[str, str, int]:
    """Run a Python file in a subprocess with a timeout.

    Args:
        filepath: Path to the Python file to execute.
        timeout: Maximum execution time in seconds.

    Returns:
        Tuple of (stdout, stderr, return_code).
    """
    try:
        result = subprocess.run(
            [PYTHON, filepath],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(Path(filepath).parent),
        )
        return result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        return "", f"Execution timed out after {timeout}s", 1
    except FileNotFoundError:
        return "", f"File not found: {filepath}", 1
    except Exception as e:
        return "", f"Execution error: {e}", 1


def run_tests(
    test_dir: str, timeout: int = 60
) -> tuple[str, str, int]:
    """Run pytest on a directory and return results.

    Args:
        test_dir: Path to the directory containing test files.
        timeout: Maximum execution time in seconds.

    Returns:
        Tuple of (stdout, stderr, return_code).
    """
    try:
        result = subprocess.run(
            [PYTHON, "-m", "pytest", test_dir, "-v", "--tb=short"],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(Path(test_dir).parent) if Path(test_dir).is_dir() else str(Path(test_dir).parent.parent),
        )
        return result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        return "", f"Tests timed out after {timeout}s", 1
    except Exception as e:
        return "", f"Test execution error: {e}", 1
