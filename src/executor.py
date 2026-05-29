"""Execute analysis steps via built-in tools or sandboxed pandas code."""

from __future__ import annotations

import traceback
from io import StringIO
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from .safety import UnsafeCodeError, validate_analysis_code
from .tools import run_builtin_tool


def execute_step(
    step: dict[str, Any],
    df: pd.DataFrame,
    output_dir: Path,
) -> tuple[bool, str, list[str]]:
    """
    Run one planned step. Returns (success, message, artifact_paths).
    """
    artifacts: list[str] = []
    step_type = step.get("type", "builtin")
    try:
        if step_type == "builtin":
            result = run_builtin_tool(
                step["tool"],
                df,
                output_dir,
                step.get("params", {}),
            )
            if result.endswith(".png") and Path(result).exists():
                artifacts.append(result)
            return True, result, artifacts

        if step_type == "code":
            code = step.get("code", "")
            validate_analysis_code(code)
            existing_pngs = {str(p.resolve()) for p in output_dir.glob("*.png")}
            local_vars: dict[str, Any] = {
                "df": df.copy(),
                "pd": pd,
                "plt": plt,
                "sns": sns,
                "output_dir": str(output_dir),
            }
            stdout = StringIO()
            # Restricted namespace — no builtins open/exec
            safe_builtins = {
                "len": len,
                "range": range,
                "min": min,
                "max": max,
                "sum": sum,
                "float": float,
                "int": int,
                "str": str,
                "list": list,
                "dict": dict,
                "print": lambda *a, **k: print(*a, file=stdout, **k),
            }
            exec(  # noqa: S102 — validated snippet only
                code,
                {"__builtins__": safe_builtins},
                local_vars,
            )
            plt.close("all")
            msg = stdout.getvalue().strip() or "Code executed successfully."
            current_pngs = {str(p.resolve()) for p in output_dir.glob("*.png")}
            artifacts.extend(sorted(current_pngs - existing_pngs))
            return True, msg, artifacts

        return False, f"Unknown step type: {step_type}", []

    except (UnsafeCodeError, Exception) as exc:
        return False, f"{type(exc).__name__}: {exc}\n{traceback.format_exc()[-500:]}", []
