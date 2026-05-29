"""Built-in analysis tools (no arbitrary code)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


def load_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path)


def profile_dataset(df: pd.DataFrame) -> dict[str, Any]:
    numeric = df.select_dtypes(include="number").columns.tolist()
    categorical = df.select_dtypes(exclude="number").columns.tolist()
    missing = df.isnull().sum().to_dict()
    return {
        "rows": int(len(df)),
        "columns": list(df.columns),
        "numeric_columns": numeric,
        "categorical_columns": categorical,
        "missing_counts": missing,
        "dtypes": {c: str(t) for c, t in df.dtypes.items()},
    }


def summary_statistics(df: pd.DataFrame) -> str:
    desc = df.describe(include="all").to_string()
    return f"Summary statistics:\n{desc}"


def missing_report(df: pd.DataFrame) -> str:
    missing = df.isnull().sum()
    pct = (missing / len(df) * 100).round(2)
    report = pd.DataFrame({"missing": missing, "percent": pct})
    return f"Missing values:\n{report.to_string()}"


def plot_histogram(df: pd.DataFrame, column: str, output_dir: Path) -> str:
    if column not in df.columns:
        raise ValueError(f"Column not found: {column}")
    if not pd.api.types.is_numeric_dtype(df[column]):
        raise ValueError(f"Column {column} is not numeric")
    fig, ax = plt.subplots(figsize=(8, 5))
    df[column].dropna().hist(ax=ax, bins=20, edgecolor="black")
    ax.set_title(f"Histogram: {column}")
    ax.set_xlabel(column)
    ax.set_ylabel("count")
    out = output_dir / f"hist_{column}.png"
    fig.tight_layout()
    fig.savefig(out, dpi=120)
    plt.close(fig)
    return str(out)


def plot_bar_categorical(
    df: pd.DataFrame,
    column: str,
    output_dir: Path,
    value_col: str | None = None,
) -> str:
    if column not in df.columns:
        raise ValueError(f"Column not found: {column}")
    if value_col:
        if value_col not in df.columns:
            raise ValueError(f"Column not found: {value_col}")
        if not pd.api.types.is_numeric_dtype(df[value_col]):
            raise ValueError(f"Column {value_col} is not numeric")
        counts = (
            df.groupby(column, dropna=False)[value_col]
            .sum()
            .sort_values(ascending=False)
            .head(10)
        )
    else:
        counts = df[column].value_counts().head(10)
    fig, ax = plt.subplots(figsize=(8, 5))
    counts.plot(kind="bar", ax=ax, color="steelblue")
    ax.set_title(f"Top categories: {column}")
    ax.set_ylabel("count")
    plt.xticks(rotation=45, ha="right")
    out = output_dir / f"bar_{column}.png"
    fig.tight_layout()
    fig.savefig(out, dpi=120)
    plt.close(fig)
    return str(out)


def plot_correlation_heatmap(df: pd.DataFrame, output_dir: Path) -> str:
    numeric = df.select_dtypes(include="number")
    if numeric.shape[1] < 2:
        return "Skipped correlation heatmap: fewer than 2 numeric columns."
    corr = numeric.corr()
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", ax=ax)
    ax.set_title("Correlation heatmap")
    out = output_dir / "correlation_heatmap.png"
    fig.tight_layout()
    fig.savefig(out, dpi=120)
    plt.close(fig)
    return str(out)


def groupby_aggregate(df: pd.DataFrame, group_col: str, value_col: str, agg: str) -> str:
    if group_col not in df.columns or value_col not in df.columns:
        raise ValueError(f"Columns not found: {group_col}, {value_col}")
    grouped = df.groupby(group_col)[value_col].agg(agg)
    return f"Group by {group_col}, {agg} of {value_col}:\n{grouped.to_string()}"


BUILTIN_TOOLS = {
    "summary_statistics": summary_statistics,
    "missing_report": missing_report,
    "plot_histogram": plot_histogram,
    "plot_bar_categorical": plot_bar_categorical,
    "plot_correlation_heatmap": plot_correlation_heatmap,
    "groupby_aggregate": groupby_aggregate,
}


def run_builtin_tool(
    tool_name: str,
    df: pd.DataFrame,
    output_dir: Path,
    params: dict[str, Any],
) -> str:
    if tool_name not in BUILTIN_TOOLS:
        raise ValueError(f"Unknown tool: {tool_name}")

    fn = BUILTIN_TOOLS[tool_name]
    if tool_name == "summary_statistics":
        return fn(df)
    if tool_name == "missing_report":
        return fn(df)
    if tool_name == "plot_histogram":
        column = params.get("column") or params.get("x")
        if not column:
            raise ValueError("plot_histogram requires 'column'")
        return fn(df, column, output_dir)
    if tool_name == "plot_bar_categorical":
        column = params.get("column") or params.get("x")
        if not column:
            raise ValueError("plot_bar_categorical requires 'column' or 'x'")
        value_col = params.get("value_col") or params.get("y")
        return fn(df, column, output_dir, value_col=value_col)
    if tool_name == "plot_correlation_heatmap":
        return fn(df, output_dir)
    if tool_name == "groupby_aggregate":
        group_col = params.get("group_col")
        if not group_col and params.get("groupby_columns"):
            group_col = params["groupby_columns"][0]
        value_col = params.get("value_col")
        if not value_col and params.get("aggregate_columns"):
            value_col = params["aggregate_columns"][0]
        if not group_col or not value_col:
            raise ValueError(
                "groupby_aggregate requires group/value columns (group_col/value_col)"
            )
        return fn(df, group_col, value_col, params.get("agg", params.get("aggfunc", "sum")))
    raise ValueError(f"Unhandled tool: {tool_name}")
