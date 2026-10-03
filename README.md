# Local LLM Benchmark (`local-models-bench`)

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A deterministic, sandboxed benchmark suite for evaluating local Large Language Models (LLMs) across multi-turn code generation, progressive algorithmic reasoning, and real-world inference speed.

Built for seamless local execution with **LM Studio**, **Ollama**, and OpenAI-compatible endpoints, featuring zero-overhead sandboxing, conflict-free multi-device Git synchronization, and interactive HTML dashboards.

---

## 🚀 Key Features

- **Multi-Language Polyglot Benchmarks**: Rigorous multi-level coding tasks covering systems, algorithmic, and concurrent programming across **Python**, **C99**, **JavaScript**, and **Lua**.
- **Isolated Execution Sandboxes**:
  - **Python**: Sandboxed inside **MicroPython WASI** with instruction-level fuel metering and an automatic **CPython standard library compatibility layer** (`sandboxes/mpy_compat.py`).
  - **C99**: Compiled on the fly via `ziglang` to `wasm32-wasi` and executed inside `wasmtime` with zero disk/network access.
  - **JavaScript**: Executed in `quickjs` using a virtualized zero-latency timer queue and polyfilled `AbortController` / `AbortSignal`.
  - **Lua**: Sandboxed in `lupa` with OS, IO, package, and debug primitives completely revoked.
- **Progressive Multi-Turn Reasoning**:
  - Multi-level challenges where level $N$ builds upon code from level $N-1$.
  - Structured chat-role context preservation.
  - First-class support for reasoning models (DeepSeek-R1, QwQ, etc.) with automatic `<think>` tag stripping and draft shielding (preventing draft code from executing).
- **Comprehensive Performance & Speed Profiling**:
  - Generation speed (`tok/s`), Time-to-First-Token (`TTFT`), total tokens, and reasoning tokens.
  - Hardware-aware auto-profiling (CPU model, RAM, OS, hostname).
- **Conflict-Free Multi-Device Git Synchronization**:
  - Fast bidirectional sync between local SQLite cache (`bench.db`) and atomic JSON records (`records/`).
  - Records are partitioned by `{host_id}__{run_id}` to prevent merge conflicts across laptops, desktops, and branches.
  - Content-hash checking (`_write_if_changed`) prevents unnecessary Git churn.
- **Standalone Dashboard & MCP Server**:
  - Zero-dependency, single-file interactive dark-mode HTML report (`report.html`).
  - Model Context Protocol (MCP) server (`mcp_server.py`) exposing leaderboards, model comparisons, and speed analytics to AI tools.

---

## 📊 Benchmark Suite

| Benchmark ID | Language | Runtime | Topics & Mechanics |
|---|---|---|---|
| `kv` | Python | MicroPython WASI | In-memory key-value store with nested transactions (`BEGIN`, `COMMIT`, `ROLLBACK`) |
| `sql` | Python | MicroPython WASI | In-memory SQL AST compiler and engine (`SELECT`, `WHERE`, `JOIN`, `GROUP BY`, `HAVING`) |
| `vm` | Python | MicroPython WASI | Bytecode stack virtual machine with call stack, frames, and local/global scoping |
| `scheduler` | Python | MicroPython WASI | Dependency graph topological sorting, critical path analysis, and cycle detection |
| `priority_scheduler` | Python | MicroPython WASI | Priority task scheduler with resource constraints and preemption |
| `c_framing` | C99 | Zig WASM / Wasmtime | Ring buffer, streaming packet decoder, and CRC validation |
| `js_async` | JavaScript | QuickJS | Concurrency pool, task retries with exponential backoff, and `AbortSignal` cancellation |
| `lua_game_ai` | Lua | Lupa (Sandboxed) | Behavior Trees, Blackboard change watchers, and coroutine execution |

---

## 🔒 Python MicroPython WASI & Compatibility Layer

To guarantee complete host safety, Python code runs inside a WebAssembly sandbox via **MicroPython WASI**.

Modern LLMs write idiomatic CPython 3.10+ code that frequently relies on standard library utilities (`typing`, `collections.deque`, `defaultdict`, `Counter`, `itertools`, `heapq`, `functools`, `bisect`, `copy`, `abc`). Rather than penalizing models for using standard Python or compromising sandbox security, `local_llm_bench` includes an AST-driven compatibility layer (`sandboxes/mpy_compat.py`):
1. Guest code AST is inspected prior to execution.
2. Lightweight, pure-Python shims matching the exact imported modules are injected at the script header.
3. Instruction-level fuel counting ensures deterministic timeout protection.

All compatibility shims are verified for behavioral parity against native CPython in `tests/test_mpy_shims.py`.

---

## 🛠️ Quick Start

### 1. Prerequisites
- Python 3.12 or higher.
- [uv](https://github.com/astral-sh/uv) (recommended) or standard `pip`.
- LM Studio, Ollama, or an OpenAI-compatible inference server running locally.

### 2. Installation
Clone the repository and install dependencies:
```bash
git clone https://github.com/your-username/local_llm_bench.git
cd local_llm_bench
uv sync
```

### 3. Running Benchmarks
Launch the interactive terminal runner:
```bash
uv run python main.py
```
From the interactive menu, you can:
- Run all benchmarks or select specific models and tasks.
- Profile inference speed and token generation rates.
- Re-run failed or missing test levels.
- View real-time terminal leaderboards.

### 4. Generating the HTML Dashboard
Generate a standalone, zero-dependency HTML report:
```bash
uv run python main.py report
```
This opens `report.html` in your default browser, featuring:
- Overall intelligence leaderboards.
- Tokens per second (`tok/s`) and TTFT comparisons across hardware backends.
- Detailed pass/fail breakdowns per level and benchmark.
- Inspector for model-generated source code and reasoning thought chains.

### 5. Multi-Device Git Synchronization
Synchronize your local SQLite cache with versioned Git records:
```bash
uv run python main.py sync
```

### 6. Model Context Protocol (MCP) Server
Integrate your benchmark database with Claude Desktop, Cursor, Windsurf, or Antigravity:
```bash
uv run python mcp_server.py
```

---

## 📁 Repository Structure

```text
local_llm_bench/
├── benchmarks/               # Self-contained benchmark definitions (prompts + test suites)
│   ├── c_framing.py          # C99: Ring buffer & packet decoder (WASM)
│   ├── js_async.py           # JS: Concurrency pool & AbortSignal (QuickJS)
│   ├── kv.py                 # Python: KV store with nested transactions
│   ├── lua_game_ai.py        # Lua: Behavior Trees & Blackboard (Lupa)
│   ├── priority_scheduler.py # Python: Priority task scheduler
│   ├── scheduler.py          # Python: Dependency graph topological sort
│   ├── sql.py                # Python: SQL AST query engine
│   └── vm.py                 # Python: Bytecode stack virtual machine
├── sandboxes/                # Zero-overhead guest isolation engines
│   ├── c_wasm.py             # Zig CC (wasm32-wasi) compiler & Wasmtime runtime
│   ├── js_quickjs.py         # QuickJS engine with virtual clock & AbortSignal
│   ├── lua_runtime.py        # Sandboxed Lupa Lua runtime
│   ├── mpy_compat.py         # CPython stdlib shims for MicroPython WASI
│   ├── process.py            # AST validation & safe execution helpers
│   └── python_wasm.py        # MicroPython WASI with fuel-metering
├── records/                  # Conflict-free JSON records (committed to Git)
│   ├── hosts/                # Hardware profiles (<host_id>.json)
│   ├── runs/                 # Run metadata (<host_id>__<run_id>.json)
│   ├── results/              # Evaluation results (<host_id>__<run_id>__<model>_<bench>_<level>.json)
│   └── speeds/               # Speed benchmark samples (<host_id>__<run_id>__<model>_<bench>_<level>.json)
├── tests/                    # Pytest test suite (175+ tests)
│   ├── test_benchmark_contracts.py
│   ├── test_golden_solutions.py
│   ├── test_harness.py
│   ├── test_host_matching.py
│   ├── test_mpy_shims.py
│   ├── test_records_and_runner.py
│   ├── test_runs.py
│   └── test_sandbox_and_db_fixes.py
├── analytics.py              # Pure data aggregation & analytics query layer
├── database.py               # SQLite schema & connection management (bench.db)
├── host_configs.py           # Hardware auto-detection & machine profile management
├── html_report.py            # Standalone HTML dashboard generator
├── lmstudio.py               # HTTP client for LM Studio, Ollama, and OpenAI endpoints
├── main.py                   # Interactive CLI entry point
├── mcp_server.py             # Model Context Protocol (MCP) server
├── report_data.py            # Report payload assembly & rendering context
├── runner.py                 # Benchmark execution engine & speed profiling
├── storage.py                # Atomic filesystem persistence
└── sync.py                   # Bidirectional sync between SQLite and records/
```

---

## 🧪 Development & Testing

Run the complete test suite:
```bash
uv run pytest
```

Run style and linting checks with [Ruff](https://github.com/astral-sh/ruff):
```bash
uv run ruff check .
uv run ruff format --check .
```

---

## 📜 Documentation & Guidelines

- **[`AGENT.md`](./AGENT.md)**: Comprehensive architectural guide and development invariants.
- **[`AGENTS.md`](./AGENTS.md)**: Dedicated instructions for autonomous AI coding agents regarding MicroPython WASI and compatibility shims.
- **[`CLAUDE.md`](./CLAUDE.md)**: Operational protocols and coding standards.

> **CRITICAL RULE**: All documentation files (`*.md`), code comments, docstrings, and git commit messages in this repository **MUST be written strictly and exclusively in English**.

---

## 📄 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
