# 2-minute demo script (screen recording)

1. **Terminal** — show project folder and run:
   ```bash
   source .venv/bin/activate
   python main.py --session demo
   ```
2. **Wait** — agent prints plan steps (✓ marks) and summary.
3. **Finder / VS Code** — open `output/demo/`:
   - `plan.json` — planned steps
   - `hist_*.png`, `correlation_heatmap.png`, `revenue_by_region.png` (if present)
   - `report.md` — final summary
   - `session_memory.json` — memory of completed steps
4. **Optional** — run again with a custom goal:
   ```bash
   python main.py --session demo2 --goal "Which product sells the most units?"
   ```
5. **Closing** — mention offline mode works without API key; with `OPENAI_API_KEY`, planner uses GPT.

Total time: ~90–120 seconds.
