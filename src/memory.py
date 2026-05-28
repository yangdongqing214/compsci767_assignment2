"""Session memory: dataset profile and completed analysis steps."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class AgentMemory:
    goal: str = ""
    csv_path: str = ""
    dataset_profile: dict[str, Any] = field(default_factory=dict)
    completed_steps: list[dict[str, Any]] = field(default_factory=list)
    artifacts: list[str] = field(default_factory=list)

    def add_step(self, step_id: str, description: str, result: str, success: bool) -> None:
        self.completed_steps.append(
            {
                "step_id": step_id,
                "description": description,
                "result": result[:2000],
                "success": success,
            }
        )

    def add_artifact(self, path: str) -> None:
        if path not in self.artifacts:
            self.artifacts.append(path)

    def context_for_planner(self) -> str:
        lines = [
            f"Goal: {self.goal}",
            f"Dataset: {self.csv_path}",
            f"Profile: {json.dumps(self.dataset_profile, default=str)[:1500]}",
            f"Completed steps: {[s['step_id'] for s in self.completed_steps]}",
            f"Artifacts: {self.artifacts}",
        ]
        return "\n".join(lines)

    def save(self, path: Path) -> None:
        path.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> "AgentMemory":
        if not path.exists():
            return cls()
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls(**data)
