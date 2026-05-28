#!/usr/bin/env python3
"""CLI for the CS767 Data Analysis Agent."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

from src.agent import DataAnalysisAgent


def main() -> int:
    load_dotenv()
    root = Path(__file__).resolve().parent

    parser = argparse.ArgumentParser(
        description="Data Analysis Agent — plan, execute, and summarize CSV analysis."
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=root / "sample_data" / "sales.csv",
        help="Path to input CSV",
    )
    parser.add_argument(
        "--goal",
        type=str,
        default="Analyze sales performance by region and product; highlight trends and data quality issues.",
        help="Analysis goal in natural language",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output directory (default: output/<timestamp>)",
    )
    parser.add_argument(
        "--session",
        type=str,
        default=None,
        help="Optional session id for output folder name",
    )
    args = parser.parse_args()

    agent = DataAnalysisAgent(root)
    print("=" * 60)
    print("Data Analysis Agent (CS767 A2)")
    print("=" * 60)
    print(f"CSV:  {args.csv}")
    print(f"Goal: {args.goal}\n")

    result = agent.run(
        csv_path=args.csv,
        goal=args.goal,
        output_dir=args.output,
        session_id=args.session,
    )

    print(f"Planner: {result.planner_mode}")
    print(f"Steps:   {len(result.plan)}")
    print(f"Output:  {result.output_dir}\n")
    for s in result.step_results:
        mark = "✓" if s["success"] else "✗"
        print(f"  {mark} {s['step_id']}: {s['description']}")
        for art in s.get("artifacts", []):
            print(f"      → {art}")

    print("\n" + "-" * 60)
    print("SUMMARY")
    print("-" * 60)
    print(result.summary[:2000])
    if len(result.summary) > 2000:
        print("... (see output/report.md for full text)")
    print(f"\nFull report: {result.output_dir}/report.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
