# CS767 Assignment 2 — 评分标准对照说明

**项目：** Data Analysis Agent（数据分析智能体）  
**课程：** COMPSCI 767 Intelligent Software Agents  
**对照来源：** `week7/Reasoning1.pdf` 中 Assignment 2 Rubrics  

本文档按官方七项评分标准，说明本仓库**已实现的内容**、**采用的方法/技术**，以及**提交材料中的对应位置**。

---

## 总览：Agent 循环与课程概念对应

本系统实现经典的 **Perceive → Decide → Act → Reflect** 循环（非单次 ChatGPT 问答）：

| 阶段 | 模块 | 课程概念 |
|------|------|----------|
| Perceive | `tools.profile_dataset()` | 感知环境（CSV 数据集） |
| Decide | `planner.plan_analysis_steps()` | 规划 / 推理（LLM 或启发式） |
| Act | `executor.execute_step()` + `tools` | 工具使用、代码执行 |
| Reflect | `memory.AgentMemory` + `summarize_results()` | 记忆、总结 |

**技术栈：** Python 3、pandas、matplotlib、seaborn、OpenAI API（可选）、python-dotenv、argparse CLI。

---

## 1. Problem definition and motivation（10%）

### 要解决什么问题

用户给定 **自然语言分析目标**（`--goal`）和 **CSV 数据文件**（`--csv`），需要自动完成：理解数据结构 → 选择分析步骤 → 执行统计/可视化 → 输出可读的结论与图表。

手工流程通常需要反复在 Excel/Python 之间切换、自行决定画什么图；本 Agent 将这一过程**自动化并面向目标定制**。

### 为什么适合 Agent 方式（而非静态脚本）

| 对比 | 固定脚本 | 本 Agent |
|------|----------|----------|
| 分析步骤 | 写死 pipeline | 根据 **dataset profile + goal** 动态生成 4–7 步计划 |
| 用户输入 | 固定参数 | **自然语言 goal**（如「按 region 看 revenue」） |
| 执行方式 | 单一流程 | **多步顺序执行**，每步选用不同 builtin tool 或定制 code |
| 状态 | 无 | **Session memory** 记录已完成步骤与产物路径 |
| 安全 | 无约束 | 对 LLM 生成代码做 **AST/正则沙箱** 校验 |

这与课件示例 *「Data Analysis Agent: Takes a CSV file, chooses analysis steps, creates plots, and summarizes findings」* 一致。

### 对应材料

- 说明：`README.md` 开头、本文件  
- 2 页 Report 第 1 节：`report/REPORT.md` — *System design*  

---

## 2. Agentic behavior（25%）— 权重最高

### 已实现的行为（逐项对应 Rubric）

| Rubric 要求 | 本项目的实现 |
|-------------|--------------|
| **Goal-directed action** | `main.py --goal` 驱动全流程；启发式规划器在 goal 含 `revenue`/`sales` 时插入 `custom_revenue` 代码步 |
| **Multi-step reasoning / planning** | `planner.py` 输出 JSON 计划（4–7 步）；有 LLM planner（`OPENAI_API_KEY`）与 **heuristic fallback** 双模式 |
| **Decision-making** | 根据 `numeric_columns` / `categorical_columns` 数量决定画热力图、直方图、分组聚合等 |
| **Tool use** | 6 个 builtin tools：`summary_statistics`, `missing_report`, `plot_histogram`, `plot_bar_categorical`, `plot_correlation_heatmap`, `groupby_aggregate` |
| **Code execution** | `type: "code"` 步骤在受限 `exec()` 中运行 pandas/matplotlib 片段 |
| **Memory** | `AgentMemory` 保存 profile、每步结果、artifact 路径；`context_for_planner()` 可供后续扩展多轮 |
| **Interaction with environment** | 「环境」= CSV 文件 + `output/` 目录；每步读写日志、PNG、`plan.json` |

### 核心方法与代码位置

```
用户 goal + CSV
    → profile_dataset()          # 感知
    → plan_analysis_steps()      # 决策（LLM 或 heuristic）
    → for step in plan:
          execute_step()         # 行动（builtin / sandboxed code）
          memory.add_step()      # 记忆更新
    → summarize_results()        # 生成 report.md
```

- **LLM 规划：** OpenAI Chat Completions（`gpt-4o-mini` 可配置），system prompt 约束输出 JSON 数组、禁止危险操作  
- **启发式规划：** 无 API 时按列类型规则生成步骤（保证可离线复现）  
- **ReAct 思想（部分体现）：** 先 profile 再 plan 再 act，而非单轮问答  

### 对应材料

- 实现：`src/agent.py`, `src/planner.py`, `src/executor.py`, `src/memory.py`  
- 运行证据：`output/demo_test/`, `output/demo_test2/` 下的 `plan.json`, `session_memory.json`  

---

## 3. System design and architecture（20%）

### 架构组件（对应 Rubric 中的 major components）

| 组件 | 文件 | 职责 |
|------|------|------|
| **Agent controller** | `src/agent.py` — `DataAnalysisAgent` | 编排 perceive → decide → act → summarize |
| **Planner** | `src/planner.py` | 生成分析计划；LLM / heuristic |
| **Executor** | `src/executor.py` | 调度 builtin 或 code 步骤 |
| **Tools** | `src/tools.py` | 内置分析工具集 |
| **Memory** | `src/memory.py` | 会话状态持久化 |
| **Safety** | `src/safety.py` | 代码与文件访问校验 |
| **User interface** | `main.py` | CLI：`--csv`, `--goal`, `--output`, `--session` |

### 架构图

见 `README.md` 中 ASCII 图，以及 `report/REPORT.md` Page 1。

### 设计决策（Design choices）

1. **Builtin tools 为主、code 为辅** — 保证多数步骤稳定可复现；仅在 goal 需要时（如 revenue = units × unit_price）插入 code 步。  
2. **双模式 Planner** — 评分人可无 API key 运行；有 key 时展示 LLM agent 能力。  
3. **失败步不中断** — `agent.py` 对每步记录 `success: true/false`，继续执行后续步骤（健壮 act loop）。  
4. **输出可追溯** — 每步 `log_<step_id>.txt`，外加 `dataset_profile.json`, `plan.json`。  

### 对应材料

- `README.md` — System design 表  
- `report/REPORT.md` — Page 1 Architecture  

---

## 4. Implementation quality（20%）

### 功能完整性

- ✅ 可一键运行：`python main.py`（默认 `sample_data/sales.csv`）  
- ✅ 自定义数据与目标：`python main.py --csv path --goal "..."`  
- ✅ 生成多种产物：统计文本、PNG 图、`report.md`、`session_memory.json`  
- ✅ **超越简单 prompt/静态聊天**：有明确模块划分、工具注册表、计划 JSON、执行器、沙箱  

### 技术与实现要点

| 技术 | 用途 |
|------|------|
| **pandas** | 读 CSV、describe、groupby、缺失值分析 |
| **matplotlib + seaborn** | 直方图、柱状图、相关热力图（Agg 后端，无 GUI） |
| **OpenAI API** | 可选：步骤规划 + 最终报告润色 |
| **python-dotenv** | `.env` 加载 `OPENAI_API_KEY` |
| **ast + regex** | `safety.validate_analysis_code()` 拦截危险 import/call |
| **受限 exec** | 仅暴露 `df, pd, plt, sns, output_dir` 与白名单 builtins |

### 项目结构

```
data-analysis-agent/
├── main.py              # CLI 入口
├── src/
│   ├── agent.py         # 主循环
│   ├── planner.py       # LLM + heuristic
│   ├── executor.py      # 步骤执行
│   ├── tools.py         # 内置工具
│   ├── memory.py        # 会话记忆
│   └── safety.py        # 沙箱校验
├── sample_data/sales.csv
├── output/              # 运行产物（demo_test 等）
├── DEMO_SCRIPT.md       # 2 分钟 demo 脚本
└── report/REPORT.md     # 2 页 PDF 报告模板
```

### 对应材料

- 复现：`README.md` — Quick start  
- 运行结果：`output/demo_test2/`（7 步计划含 `custom_revenue` 代码步）  

---

## 5. Evaluation and testing（10%）

### 已进行的测试

| 测试场景 | 命令 / 方式 | 结果 |
|----------|-------------|------|
| **默认销售数据** | `python main.py --session demo_test` | 6 步全部成功；生成 correlation、hist、bar 等图 |
| **收入相关 goal** | `python main.py --session demo_test2 --goal "Analyze sales performance by region..."` | 7 步；含 `custom_revenue` 代码步与 `revenue_by_region.png` |
| **启发式模式** | 不设置 `OPENAI_API_KEY` | `planner_mode: heuristic`，可完全离线运行 |
| **LLM 模式** | 设置 `OPENAI_API_KEY` | `planner_mode: llm`（需网络与 API） |

### 成功 / 失败案例说明

- **成功：** `session_memory.json` 中每步 `"success": true`；例如 `demo_test2` 检测到 `units` 列 1 个缺失值并写入 missing report。  
- **失败处理：** `executor.py` 捕获异常返回 `(False, error_message, [])`；Agent 继续执行后续步骤（见 `agent.py` 循环）。  
- **安全拒绝：** 若 code 含 `os.`、`open(`、`subprocess` 等，`UnsafeCodeError` 阻止执行。  

### 性能与规模

- CSV 大小限制：>20MB 拒绝（`safety.ensure_csv_readable`）  
- 样本数据：20 行 × 6 列，单次运行数秒内完成  

### 对应材料

- 测试输出目录：`output/demo_test/`, `output/demo_test2/`  
- 计划样例：`output/demo_test2/plan.json`  
- 记忆样例：`output/demo_test2/session_memory.json`  

---

## 6. Critical reflection（10%）

### 局限性（Limitations）

1. **单轮规划** — 计划一次性生成，未根据中间结果动态重规划（未实现 full ReAct 循环）。  
2. **Memory 利用有限** — `context_for_planner()` 已写入 LLM prompt，但当前单次 `run()` 内 planner 在 act 之前只调用一次。  
3. **Code 沙箱** — 使用 `exec` + 白名单，非独立进程；复杂恶意代码模式理论上仍需加强。  
4. **LLM 依赖** — 有 API 时计划质量更高，但可能产生无效 tool 名或 JSON 格式错误（已用 try/except 回退 heuristic）。  
5. **数据类型** — `date` 列被当作 categorical，未做时间序列专项分析。  

### 设计权衡（Trade-offs）

| 选择 | 好处 | 代价 |
|------|------|------|
| Builtin 为主 | 稳定、可评分复现 | 灵活性低于纯 LLM 写代码 |
| Heuristic fallback | 无 API 可跑 | 对复杂 goal 不如 LLM 贴切 |
| 失败继续执行 | 鲁棒、demo 不易全挂 | 可能带着错误上下文写 summary |
| 2 页 Report 限制 | 符合课程要求 | 细节需放在 README / 本文件 |

### 可改进方向（Possible improvements）

- 增加 **observe → replan** 循环：某步失败或结果异常时自动调整计划  
- 支持 **多 CSV / SQL** 作为环境扩展  
- 用 **subprocess 隔离** 或 Jupyter kernel 替代 `exec`  
- 增加单元测试（pytest）覆盖 `safety.py` 与各 builtin tool  
- Web UI（Streamlit）降低 CLI 使用门槛  

### 对应材料

- LLM summary prompt 已要求写 limitations：`planner.py` — `summarize_results()`  
- 本文件本节；可摘录进 `report/REPORT.md` 或 2 页 PDF  

---

## 7. Demo quality（5%）

### 已准备内容

| 项目 | 状态 | 位置 |
|------|------|------|
| **Demo 脚本** | ✅ 已写 | `DEMO_SCRIPT.md`（约 90–120 秒流程） |
| **可演示运行** | ✅ 已跑通 | `output/demo_test/`, `demo_test2/` |
| **2 分钟视频链接** | ⏳ 待录制上传 | `README.md` 中 `YOUR_DEMO_VIDEO_URL` 占位 |
| **口头讲解要点** | ✅ 脚本含 | 展示 plan、图表、memory；说明 offline / LLM 双模式 |

### Demo 建议讲解顺序（对照 Rubric）

1. 说明 **问题与 goal**（10 秒）  
2. 运行 `python main.py --session demo`（30 秒）  
3. 打开 `output/demo/plan.json` + PNG + `report.md`（40 秒）  
4. 提及 **safety、memory、非聊天机器人**（20 秒）  

### 对应材料

- `DEMO_SCRIPT.md`  
- 录屏后链接写入 `README.md` 与 `report/REPORT.md`  

---

## 提交清单（Report + GitHub，非评分项但影响 Implementation / Demo）

| 要求 | 状态 | 说明 |
|------|------|------|
| 2 页 Report PDF | 模板已有 | 填写 `report/REPORT.md` 姓名/学号/GitHub/截图后导出 |
| GitHub 仓库 | 待确认 | 需含 README、commit checkpoints |
| README 复现说明 | ✅ | `README.md` |
| 2 分钟 demo 视频 | 待录制 | 按 `DEMO_SCRIPT.md` |
| Commit 历史 | 建议按 README 中 6 条 checkpoint 提交 | 体现逐步开发 |

---

## 文件索引（快速定位）

| 评分项 | 主要文件 |
|--------|----------|
| Problem & motivation | 本文 §1；`report/REPORT.md` |
| Agentic behavior | `src/agent.py`, `planner.py`, `executor.py`, `memory.py` |
| Architecture | `README.md`, `report/REPORT.md` |
| Implementation | 全 `src/`，`main.py`, `requirements.txt` |
| Evaluation | `output/demo_test*/` |
| Reflection | 本文 §6；LLM `summarize_results` 输出 |
| Demo | `DEMO_SCRIPT.md`, `README.md` |

---

*文档生成说明：对照 `week7/Reasoning1.pdf` Assignment 2 Rubrics，基于当前仓库代码与 `output/demo_test*` 运行结果整理。*
