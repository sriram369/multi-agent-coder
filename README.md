# Multi-Agent Coder

> Give it a task. Four AI agents — Architect, Coder, Reviewer, Tester — collaborate to plan, write, review, and test production code. Like a mini AI dev team in your terminal.

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/LangGraph-Orchestration-FF6B35?style=for-the-badge" alt="LangGraph"/>
  <img src="https://img.shields.io/badge/Claude_Sonnet_4-LLM-D4A574?style=for-the-badge" alt="Claude"/>
  <img src="https://img.shields.io/badge/FastAPI-REST_API-009688?style=for-the-badge&logo=fastapi" alt="FastAPI"/>
  <img src="https://img.shields.io/badge/License-MIT-blue?style=for-the-badge" alt="MIT"/>
</p>

---

## Demo

```
$ python main.py "Build a REST API for a todo app with FastAPI and SQLite"

╭──────────────────────────────────────────────────╮
│  🏛  Architect Agent                              │
│  Planning implementation...                       │
│                                                   │
│  Files: main.py, models.py, database.py,         │
│         schemas.py, requirements.txt              │
│  Stack: FastAPI + SQLAlchemy + SQLite             │
╰──────────────────────────────────────────────────╯

╭──────────────────────────────────────────────────╮
│  💻  Coder Agent                                  │
│  Writing 5 files...          ████████████ 100%   │
╰──────────────────────────────────────────────────╯

╭──────────────────────────────────────────────────╮
│  🔍  Reviewer Agent                               │
│  Issues found: 2 (severity: minor)                │
│  → Missing HTTP 404 handler in DELETE endpoint    │
│  → No index on todos.created_at column            │
│  Sending back to Coder (cycle 1/2)...             │
╰──────────────────────────────────────────────────╯

╭──────────────────────────────────────────────────╮
│  🔍  Reviewer Agent (re-review)                   │
│  ✓ No issues found. Code approved.               │
╰──────────────────────────────────────────────────╯

╭──────────────────────────────────────────────────╮
│  🧪  Tester Agent                                 │
│  Generated: tests/test_main.py (12 test cases)   │
│  ............ 12 passed in 1.34s                 │
╰──────────────────────────────────────────────────╯

Output: output/todo_api_20260217_143022/
Tokens: 18,432 input · 9,211 output · Est. cost: $0.19
```

---

## How It Works

Four specialized agents run as nodes in a **LangGraph state machine**. Each has a focused role and a distinct system prompt — no single agent tries to do everything.

```
User Task
    │
    ▼
Architect ── creates plan, file structure, tech choices
    │
    ▼
Coder ────── writes all files from the plan
    │
    ▼
Reviewer ─── inspects every file for bugs, security, quality
    │
    ├─ issues found + cycles < 2 ──► Coder (fix loop)
    │
    └─ approved ──────────────────────────────────────┐
                                                      ▼
                                                   Tester
                                                      │
                                                      ▼
                                               output/ directory
```

The Reviewer can send code back to the Coder up to **2 times** (configurable). This mirrors real-world PR review cycles and consistently catches issues a single-agent pipeline would miss.

---

## Agents

| Agent | Role | Output |
|-------|------|--------|
| **Architect** | Analyzes task, creates implementation plan, picks stack | Structured plan with file list and specs |
| **Coder** | Writes production code file by file from the plan | Complete, runnable code files |
| **Reviewer** | Reviews every file for bugs, security, best practices | Severity-rated issue list or approval |
| **Tester** | Writes pytest tests for the final approved code | Test files + executed results |

---

## Technical Highlights

**Why LangGraph instead of a simple loop:**
Each agent transition is a conditional edge in a state machine. The Reviewer's decision — approve or re-review — is encoded as a graph condition, not an if/else in application code. This makes the workflow inspectable, serializable, and easy to extend (adding a Security Agent between Reviewer and Tester is one new edge).

**Shared state via Pydantic:**
All agents read from and write to a single `PipelineState` Pydantic model. No hidden globals, no inter-agent message passing — the state is the source of truth at every step. Trivially debuggable: print the state after any node.

**Robust XML file parsing:**
LLMs produce inconsistent output formats. The Coder wraps each file in XML-style tags (`<file name="main.py">...</file>`). A custom parser handles malformed tags, missing attributes, and partial outputs gracefully — no crashes on imperfect LLM output.

**Sandboxed test execution:**
Generated tests run inside a `subprocess` with a configurable timeout. The main process is never exposed to arbitrary code execution from the generated files.

**Token tracking and cost estimation:**
Every LLM call logs input and output tokens. The final summary shows total cost at current Claude Sonnet pricing — useful for understanding the economics of multi-agent pipelines at scale.

---

## Stack

- **Python 3.11+**
- **LangGraph** — agent orchestration and conditional state machine
- **Anthropic SDK** — Claude Sonnet 4 for all agents
- **Pydantic v2** — structured shared state and schemas
- **Rich** — color-coded terminal UI with panels, progress bars, syntax highlighting
- **FastAPI + Uvicorn** — REST API for programmatic access
- **pytest** — generated test execution

---

## Quickstart

```bash
git clone https://github.com/sriram369/multi-agent-coder.git
cd multi-agent-coder
pip install -r requirements.txt
cp .env.example .env   # add your ANTHROPIC_API_KEY
```

**CLI:**
```bash
python main.py "Build a REST API for a todo app with FastAPI"
```

**API:**
```bash
uvicorn api.server:app --reload

curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"task": "Build a FastAPI todo app with SQLite"}'
```

---

## API Reference

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/generate` | Run the full agent pipeline |

**POST /generate response:**
```json
{
  "status": "success",
  "files": {"app/main.py": "...", "app/models.py": "..."},
  "test_files": {"tests/test_main.py": "..."},
  "test_results": "12 passed in 1.34s",
  "review_cycles": 1,
  "total_input_tokens": 18432,
  "total_output_tokens": 9211,
  "errors": []
}
```

---

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | — | Required |
| `MODEL_NAME` | `claude-sonnet-4-20250514` | LLM model |
| `MAX_TOKENS` | `8096` | Max tokens per LLM call |
| `MAX_REVIEW_CYCLES` | `2` | Max Reviewer → Coder iterations |
| `OUTPUT_DIR` | `output` | Where generated files are written |

---

## Cost Estimates

Using Claude Sonnet 4 ($3/M input, $15/M output):

| Task | Approx Tokens | Approx Cost |
|------|--------------|-------------|
| Simple (todo API) | 15K in · 8K out | ~$0.17 |
| Medium (auth + CRUD) | 25K in · 15K out | ~$0.30 |
| Complex (multi-service) | 40K in · 25K out | ~$0.50 |

---

## Project Structure

```
multi-agent-coder/
├── agents/
│   ├── base.py          # Base agent: LLM calls, retry logic, logging
│   ├── architect.py     # Planning agent
│   ├── coder.py         # Code generation + XML file parser
│   ├── reviewer.py      # Code review + severity rating
│   └── tester.py        # Test generation + sandboxed execution
├── orchestrator/
│   ├── graph.py         # LangGraph state machine + conditional edges
│   └── state.py         # Pydantic shared pipeline state
├── tools/
│   ├── file_manager.py  # Disk I/O for generated files
│   └── code_runner.py   # Sandboxed subprocess test runner
├── prompts/
│   └── system_prompts.py
├── api/
│   └── server.py        # FastAPI REST API
├── main.py              # CLI entry point
└── requirements.txt
```

---

## License

MIT
