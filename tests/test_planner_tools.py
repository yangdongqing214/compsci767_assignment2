from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.planner import normalize_plan_steps
from src.tools import run_builtin_tool


class PlannerToolsCompatibilityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.df = pd.DataFrame(
            {
                "region": ["North", "South", "North"],
                "product": ["A", "B", "A"],
                "units": [10, 20, 5],
                "unit_price": [100.0, 80.0, 120.0],
            }
        )
        self.profile = {
            "columns": list(self.df.columns),
            "numeric_columns": ["units", "unit_price"],
            "categorical_columns": ["region", "product"],
        }

    def test_normalize_groupby_aliases(self) -> None:
        steps = [
            {
                "step_id": "g",
                "type": "builtin",
                "tool": "groupby_aggregate",
                "params": {
                    "groupby_columns": ["region", "product"],
                    "aggregate_columns": ["units"],
                    "aggfunc": "sum",
                },
            }
        ]
        normalized = normalize_plan_steps(steps, self.profile)
        params = normalized[0]["params"]
        self.assertEqual(params["group_col"], "region")
        self.assertEqual(params["value_col"], "units")
        self.assertEqual(params["agg"], "sum")

    def test_plot_bar_accepts_xy_params(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = run_builtin_tool(
                "plot_bar_categorical",
                self.df,
                Path(tmp),
                {"x": "region", "y": "units"},
            )
            self.assertTrue(out.endswith(".png"))
            self.assertTrue(Path(out).exists())

    def test_groupby_accepts_list_aliases(self) -> None:
        result = run_builtin_tool(
            "groupby_aggregate",
            self.df,
            Path("."),
            {
                "groupby_columns": ["region"],
                "aggregate_columns": ["units"],
                "aggfunc": "sum",
            },
        )
        self.assertIn("Group by region", result)


if __name__ == "__main__":
    unittest.main()
