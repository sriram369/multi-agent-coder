"""File management utilities for writing generated code to disk."""

from __future__ import annotations

import os
import shutil
from pathlib import Path

from rich.console import Console

console = Console()


def write_files(files: dict[str, str], base_dir: str) -> list[str]:
    """Write all generated files to disk, creating directories as needed.

    Args:
        files: Mapping of relative file paths to their contents.
        base_dir: Base directory to write files into.

    Returns:
        List of absolute paths of written files.
    """
    written: list[str] = []
    base = Path(base_dir)

    for filepath, content in files.items():
        full_path = base / filepath
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding="utf-8")
        written.append(str(full_path))
        console.print(f"  [dim]Wrote {filepath}[/dim]")

    return written


def read_file(filepath: str) -> str:
    """Read a file and return its contents.

    Args:
        filepath: Absolute or relative path to the file.

    Returns:
        The file contents as a string.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    return Path(filepath).read_text(encoding="utf-8")


def clean_output_dir(base_dir: str) -> None:
    """Remove and recreate the output directory.

    Args:
        base_dir: Path to the output directory to clean.
    """
    path = Path(base_dir)
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)
