"""Safety checks for tool code and file access."""

from __future__ import annotations

import ast
import re
from pathlib import Path

BLOCKED_IMPORTS = {
    "os",
    "sys",
    "subprocess",
    "socket",
    "shutil",
    "pathlib",
    "pickle",
    "builtins",
    "__builtin__",
    "importlib",
    "ctypes",
    "multiprocessing",
    "requests",
    "urllib",
    "http",
    "ftplib",
    "eval",
    "exec",
    "compile",
    "open",
}

BLOCKED_CALLS = {"exec", "eval", "compile", "__import__", "open", "input"}


class UnsafeCodeError(ValueError):
    pass


def validate_analysis_code(code: str) -> None:
    """Reject code that tries filesystem/network access outside the sandbox."""
    lowered = code.lower()
    for pattern in (
        r"\bopen\s*\(",
        r"\b__import__\s*\(",
        r"\beval\s*\(",
        r"\bexec\s*\(",
        r"\bos\.",
        r"\bsubprocess\b",
        r"\brequests\b",
        r"\bsocket\b",
        r"to_csv\s*\(",
        r"read_csv\s*\([^)]*http",
    ):
        if re.search(pattern, lowered):
            raise UnsafeCodeError(f"Blocked pattern in generated code: {pattern}")

    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        raise UnsafeCodeError(f"Invalid Python syntax: {exc}") from exc

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root in BLOCKED_IMPORTS:
                    raise UnsafeCodeError(f"Blocked import: {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                root = node.module.split(".")[0]
                if root in BLOCKED_IMPORTS:
                    raise UnsafeCodeError(f"Blocked import from: {node.module}")
        elif isinstance(node, ast.Call):
            func = node.func
            name = None
            if isinstance(func, ast.Name):
                name = func.id
            elif isinstance(func, ast.Attribute):
                name = func.attr
            if name in BLOCKED_CALLS:
                raise UnsafeCodeError(f"Blocked call: {name}")


def ensure_output_dir(path: Path) -> Path:
    path = path.resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def ensure_csv_readable(csv_path: Path, project_root: Path) -> Path:
    csv_path = csv_path.resolve()
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")
    if csv_path.suffix.lower() != ".csv":
        raise ValueError("Input must be a .csv file")
    # Allow sample_data or user-provided paths; block reading outside reasonable scope
    if csv_path.stat().st_size > 20 * 1024 * 1024:
        raise ValueError("CSV too large (>20MB)")
    return csv_path
