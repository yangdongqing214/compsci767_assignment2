"""Plan analysis steps — LLM when API key present, else heuristic fallback."""

from __future__ import annotations

import json
import os
import re
from typing import Any

PLANNER_SYSTEM = """You are a data analysis planner for an intelligent agent.
Given a user goal and dataset profile, output a JSON array of 4-6 steps.
Each step is an object with:
- step_id: short snake_case id
- description: what this step does
- type: "builtin" or "code"
- tool: (if builtin) one of: summary_statistics, missing_report, plot_histogram,
  plot_bar_categorical, plot_correlation_heatmap, groupby_aggregate
- params: (if builtin) dict of parameters, e.g. {"column": "units"}
- code: (if code) short pandas/matplotlib snippet using only df, pd, plt, sns.
  Save plots to output_dir with plt.savefig(f"{output_dir}/custom_plot.png")
Rules: no file reads, no network, no os/subprocess. Prefer builtin tools.
Output ONLY valid JSON array, no markdown."""


def _heuristic_plan(profile: dict[str, Any], goal: str) -> list[dict[str, Any]]:
    numeric = profile.get("numeric_columns", [])
    categorical = profile.get("categorical_columns", [])
    steps: list[dict[str, Any]] = [
        {
            "step_id": "overview",
            "description": "Compute summary statistics",
            "type": "builtin",
            "tool": "summary_statistics",
            "params": {},
        },
        {
            "step_id": "missing",
            "description": "Report missing values",
            "type": "builtin",
            "tool": "missing_report",
            "params": {},
        },
    ]
    if len(numeric) >= 2:
        steps.append(
            {
                "step_id": "correlation",
                "description": "Plot correlation heatmap for numeric columns",
                "type": "builtin",
                "tool": "plot_correlation_heatmap",
                "params": {},
            }
        )
    if numeric:
        col = numeric[0]
        steps.append(
            {
                "step_id": f"hist_{col}",
                "description": f"Histogram of {col}",
                "type": "builtin",
                "tool": "plot_histogram",
                "params": {"column": col},
            }
        )
    if categorical:
        cols = profile.get("columns", [])
        col = "region" if "region" in cols else categorical[0]
        steps.append(
            {
                "step_id": f"bar_{col}",
                "description": f"Bar chart of {col}",
                "type": "builtin",
                "tool": "plot_bar_categorical",
                "params": {"column": col},
            }
        )
    if len(categorical) >= 1 and len(numeric) >= 1:
        steps.append(
            {
                "step_id": "group_agg",
                "description": f"Aggregate {numeric[0]} by {categorical[0]}",
                "type": "builtin",
                "tool": "groupby_aggregate",
                "params": {
                    "group_col": categorical[0],
                    "value_col": numeric[0],
                    "agg": "sum",
                },
            }
        )
    goal_lower = goal.lower()
    if ("revenue" in goal_lower or "sales" in goal_lower) and len(numeric) >= 2:
        if "units" in df_cols_if_present(profile) and "unit_price" in df_cols_if_present(profile):
            steps.insert(
                min(3, len(steps)),
                {
                    "step_id": "custom_revenue",
                    "description": "Compute revenue by region (units × unit_price)",
                    "type": "code",
                    "code": (
                        "df['revenue'] = df['units'] * df['unit_price']\n"
                        "print('Total revenue:', df['revenue'].sum())\n"
                        "df.groupby('region')['revenue'].sum().plot(kind='bar')\n"
                        "plt.title('Revenue by region')\n"
                        "plt.tight_layout()\n"
                        "plt.savefig(f'{output_dir}/revenue_by_region.png')\n"
                    ),
                },
            )
    return steps[:7]


def df_cols_if_present(profile: dict[str, Any]) -> list[str]:
    return profile.get("columns", [])


def _parse_llm_json(text: str) -> list[dict[str, Any]]:
    text = text.strip()
    match = re.search(r"\[[\s\S]*\]", text)
    if not match:
        raise ValueError("No JSON array in LLM response")
    return json.loads(match.group())


def plan_analysis_steps(
    goal: str,
    profile: dict[str, Any],
    memory_context: str,
) -> tuple[list[dict[str, Any]], str]:
    """
    Returns (steps, planner_mode).
    planner_mode is 'llm' or 'heuristic'.
    """
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return _heuristic_plan(profile, goal), "heuristic"

    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        user_msg = (
            f"User goal: {goal}\n\n"
            f"Dataset profile:\n{json.dumps(profile, indent=2, default=str)}\n\n"
            f"Session context:\n{memory_context}"
        )
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": PLANNER_SYSTEM},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.2,
        )
        content = resp.choices[0].message.content or "[]"
        steps = _parse_llm_json(content)
        return steps, "llm"
    except Exception:
        return _heuristic_plan(profile, goal), "heuristic"


def summarize_results(
    goal: str,
    profile: dict[str, Any],
    step_results: list[dict[str, Any]],
) -> str:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        lines = [f"# Analysis summary\n\n**Goal:** {goal}\n"]
        for s in step_results:
            status = "OK" if s["success"] else "FAILED"
            lines.append(f"- [{status}] {s['step_id']}: {s['description']}")
            if s["success"]:
                lines.append(f"  - {s['result'][:300]}...")
        arts = [a for s in step_results for a in s.get("artifacts", [])]
        if arts:
            lines.append(f"\n**Artifacts:** {', '.join(arts)}")
        return "\n".join(lines)

    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        payload = json.dumps(
            {"goal": goal, "profile": profile, "steps": step_results},
            default=str,
            indent=2,
        )[:8000]
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Write a concise data analysis report (markdown, ~250 words) "
                        "for a course assignment. Include key findings, limitations, "
                        "and suggested next steps."
                    ),
                },
                {"role": "user", "content": payload},
            ],
            temperature=0.3,
        )
        return resp.choices[0].message.content or "Summary unavailable."
    except Exception as exc:
        return f"Summary failed ({exc}). See step logs in output/."
