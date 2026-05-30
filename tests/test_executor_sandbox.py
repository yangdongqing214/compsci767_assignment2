from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.executor import execute_step, prepare_sandbox_code


class ExecutorSandboxTests(unittest.TestCase):
    def setUp(self) -> None:
        self.df = pd.DataFrame(
            {
                "region": ["East", "North", "South", "West"],
                "product": ["A", "B", "C", "D"],
                "units": [10, 20, 30, 40],
            }
        )

    def test_prepare_sandbox_code_strips_matplotlib_import(self) -> None:
        code = (
            "import matplotlib.pyplot as plt\n"
            "region_sales = df.groupby('region')['units'].sum().reset_index()\n"
            "plt.bar(region_sales['region'], region_sales['units'])\n"
            "plt.savefig(f'{output_dir}/sales_by_region.png')\n"
        )
        cleaned = prepare_sandbox_code(code)
        self.assertNotIn("import", cleaned)

    def test_code_step_with_import_runs(self) -> None:
        step = {
            "type": "code",
            "code": (
                "import matplotlib.pyplot as plt\n"
                "region_sales = df.groupby('region')['units'].sum().reset_index()\n"
                "plt.bar(region_sales['region'], region_sales['units'])\n"
                "plt.tight_layout()\n"
                "plt.savefig(f'{output_dir}/sales_by_region.png')\n"
            ),
        }
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            success, message, artifacts = execute_step(step, self.df, out)
            self.assertTrue(success, message)
            self.assertTrue(any(p.endswith("sales_by_region.png") for p in artifacts))


if __name__ == "__main__":
    unittest.main()
