# Data Analysis Agent (CS767 Assignment 2)

An intelligent software agent that **perceives** a CSV dataset, **plans** analysis steps toward a user goal, **acts** via tools and sandboxed code execution, and **summarizes** findings with session memory.

## Demo video

Record a ~2-minute screen capture running the commands in [DEMO_SCRIPT.md](DEMO_SCRIPT.md), upload to YouTube/Drive, and add the link here:

`YOUR_DEMO_VIDEO_URL`

## Quick start

```bash
cd data-analysis-agent
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Outputs appear under `output/<timestamp>/` (plots, `plan.json`, `report.md`, `session_memory.json`).

### Optional LLM planning (recommended for demo)

```bash
cp .env.example .env
# Edit .env and set OPENAI_API_KEY=sk-...
python main.py --goal "Find which region has the highest revenue and any missing data"
```

Without an API key, the agent uses a **heuristic planner** (fully offline, reproducible).

### Custom CSV and goal

```bash
python main.py --csv path/to/data.csv --goal "Your analysis question here"
python main.py --session demo_run --output output/demo_run
```

## System design

```
┌─────────────┐     profile      ┌──────────────┐     plan (JSON)
│  Perceive   │ ───────────────► │    Decide    │ ───────────────►
│  load CSV   │                  │ LLM/heuristic│
└─────────────┘                  └──────────────┘
       │                                │
       │                                ▼
       │                         ┌──────────────┐
       │                         │     Act      │
       └────────────────────────►│ tools + safe │
                                 │    code      │
                                 └──────────────┘
                                        │
                    memory ◄────────────┴────────► summary (report.md)
```

| Component | Role |
|-----------|------|
| **Perceive** | `profile_dataset()` — schema, dtypes, missing values |
| **Decide** | `planner.py` — 4–6 steps (builtin tools or short pandas code) |
| **Act** | `executor.py` + `tools.py` — histograms, heatmaps, groupbys |
| **Memory** | `memory.py` — steps and artifacts per session |
| **Safety** | `safety.py` — blocks dangerous imports/calls in generated code |

## Project layout

```
data-analysis-agent/
├── main.py                 # CLI entry
├── src/
│   ├── agent.py            # orchestration loop
│   ├── planner.py          # LLM + heuristic planning
│   ├── executor.py         # step execution
│   ├── tools.py            # builtin analysis tools
│   ├── memory.py           # session memory
│   └── safety.py           # code sandbox checks
├── sample_data/sales.csv
├── output/                 # generated (gitignored)
├── DEMO_SCRIPT.md          # 2-minute video script
└── report/REPORT.md        # template for 2-page PDF submission
```

## Suggested commit checkpoints (for GitHub)

1. `feat: scaffold agent loop and sample CSV`
2. `feat: builtin analysis tools and plotting`
3. `feat: heuristic planner and session memory`
4. `feat: optional OpenAI planner + summarizer`
5. `feat: safety validation for code steps`
6. `docs: README, demo script, report template`

## Author

COMPSCI 767 — Intelligent Software Agents, University of Auckland.
