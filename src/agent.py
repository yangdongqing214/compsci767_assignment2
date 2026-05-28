"""Data Analysis Agent — perceive, plan, act, summarize."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .executor import execute_step
from .memory import AgentMemory
from .planner import plan_analysis_steps, summarize_results
from .safety import ensure_csv_readable, ensure_output_dir
from .tools import load_csv, profile_dataset


@dataclass
class AgentRunResult:
    goal: str
    csv_path: str
    output_dir: str
    planner_mode: str
    plan: list[dict[str, Any]]
    step_results: list[dict[str, Any]]
    summary: str
    memory_path: str


class DataAnalysisAgent:
    """
    Intelligent software agent loop:
    1. Perceive — load CSV and build dataset profile
    2. Decide — plan analysis steps (LLM or heuristic)
    3. Act — execute tools / sandboxed code
    4. Reflect — store memory and produce summary
    """

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root.resolve()

    def run(
        self,
        csv_path: Path,
        goal: str,
        output_dir: Path | None = None,
        session_id: str | None = None,
    ) -> AgentRunResult:
        csv_path = ensure_csv_readable(csv_path, self.project_root)
        goal = goal.strip() or "Explore this dataset and summarize key insights."

        ts = session_id or datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        out = ensure_output_dir(
            output_dir or (self.project_root / "output" / ts)
        )

        memory = AgentMemory(goal=goal, csv_path=str(csv_path))
        memory_path = out / "session_memory.json"

        # --- Perceive ---
        df = load_csv(csv_path)
        profile = profile_dataset(df)
        memory.dataset_profile = profile
        (out / "dataset_profile.json").write_text(
            json.dumps(profile, indent=2, default=str),
            encoding="utf-8",
        )

        # --- Decide ---
        plan, planner_mode = plan_analysis_steps(
            goal, profile, memory.context_for_planner()
        )
        (out / "plan.json").write_text(
            json.dumps(plan, indent=2),
            encoding="utf-8",
        )

        # --- Act ---
        step_results: list[dict[str, Any]] = []
        for step in plan:
            success, result, artifacts = execute_step(step, df, out)
            memory.add_step(
                step.get("step_id", "unknown"),
                step.get("description", ""),
                result,
                success,
            )
            for art in artifacts:
                memory.add_artifact(art)
            step_results.append(
                {
                    "step_id": step.get("step_id"),
                    "description": step.get("description"),
                    "success": success,
                    "result": result,
                    "artifacts": artifacts,
                }
            )
            (out / f"log_{step.get('step_id', 'step')}.txt").write_text(
                result, encoding="utf-8"
            )

        memory.save(memory_path)

        # --- Summarize ---
        summary = summarize_results(goal, profile, step_results)
        (out / "report.md").write_text(summary, encoding="utf-8")

        return AgentRunResult(
            goal=goal,
            csv_path=str(csv_path),
            output_dir=str(out),
            planner_mode=planner_mode,
            plan=plan,
            step_results=step_results,
            summary=summary,
            memory_path=str(memory_path),
        )
