# CS767 Assignment 2 — Data Analysis Agent

**Student:** _Your Name_  
**ID:** _291140653_  
**GitHub:** _https://github.com/YOUR_USER/data-analysis-agent_  
**Demo video:** _link in README_

---

## Page 1 — System design

### Repository

`https://github.com/YOUR_USER/data-analysis-agent`

### Architecture

The agent follows a **perceive → decide → act → reflect** loop:

1. **Perceive:** Load CSV; compute profile (columns, types, missing counts).
2. **Decide:** Planner produces a JSON list of steps (LLM if `OPENAI_API_KEY` set, else heuristic rules).
3. **Act:** Each step runs a **builtin tool** (statistics, plots, groupby) or **sandboxed pandas code** validated by `safety.py`.
4. **Reflect:** Results stored in `AgentMemory`; final markdown report written to `output/`.

```
User goal + CSV
      ↓
 [DataAnalysisAgent]
      ↓
 profile → plan → execute steps → memory + report.md + PNG artifacts
```

### Design choices

- **Tools vs. free-form code:** Most steps use reliable builtins; optional code step for goal-specific metrics (e.g. revenue = units × price).
- **Safety:** AST scan blocks `os`, `subprocess`, `open`, network imports before `exec`.
- **Reproducibility:** Heuristic mode requires no API; graders can run `python main.py` immediately.

---

## Page 2 — Screenshots and behaviour

### Screenshot 1 — CLI run

_Paste terminal showing: planner mode, step checkmarks, output path._

Caption: Agent completes 5–6 steps and prints a short summary.

### Screenshot 2 — Generated artifacts

_Paste Finder/IDE showing `output/demo/` with PNG plots and `report.md`._

Caption: Histogram, correlation heatmap, and bar charts produced automatically.

### Screenshot 3 — Plan and memory (optional)

_Paste `plan.json` or `session_memory.json` excerpt._

Caption: Structured plan and session memory support traceability (course concept: agent state).

### How it works (short)

The user supplies a **goal** and **CSV**. The agent does not hard-code one analysis pipeline—it **selects steps from the dataset profile** and user goal, executes them, and aggregates results. Failed steps are logged without stopping the whole run (robust act loop).

---

_Export this file to PDF (2 pages) for Canvas upload._
