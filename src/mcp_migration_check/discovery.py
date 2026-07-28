"""Walks a folder for Python files, skipping code that isn't the user's own.

See docs/high-level-design/001-scan-pipeline.md, stage 2 (File discovery).
"""

from __future__ import annotations

import os
from pathlib import Path

_SKIP_DIR_NAMES = {
    "__pycache__",
    "node_modules",
    "site-packages",
    "dist",
    "build",
}


def _is_hidden(dir_name: str) -> bool:
    return dir_name.startswith(".")


def _looks_like_venv(dir_path: Path) -> bool:
    return (dir_path / "pyvenv.cfg").is_file()


def _should_skip_dir(dir_name: str, dir_path: Path) -> bool:
    if _is_hidden(dir_name):
        return True
    if dir_name in _SKIP_DIR_NAMES:
        return True
    if dir_name.endswith(".egg-info"):
        return True
    if _looks_like_venv(dir_path):
        return True
    return False


def discover_python_files(root: Path) -> list[Path]:
    """Return every .py file under root, skipping virtualenvs/caches/hidden dirs.

    A bare file path (not a directory) is returned as a single-item list when
    it is itself a .py file, so the CLI can also point at one file directly.
    """
    if root.is_file():
        return [root] if root.suffix == ".py" else []

    found: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        current = Path(dirpath)
        dirnames[:] = [d for d in dirnames if not _should_skip_dir(d, current / d)]
        for name in filenames:
            if name.endswith(".py"):
                found.append(current / name)
    return found
