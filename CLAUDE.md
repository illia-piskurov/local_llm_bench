# CLAUDE.md - Project Directives & AI Agent Guide

> **MANDATORY POLICY**:
> All documentation files (`*.md`), code comments, docstrings, and git commit messages in this repository **MUST be written strictly and exclusively in English**. No other language is permitted inside codebase files or documentation.

---

## 1. Primary Reference: `AGENT.md`

For comprehensive technical documentation, subsystem architecture, benchmark contracts, and development protocols, always refer to:
👉 **[`AGENT.md`](./AGENT.md)**

`AGENT.md` is the canonical reference containing:
- Full repository tree and modular layout.
- Benchmark specifications (`benchmarks/`) across Python, C99, JavaScript, and Lua.
- Execution sandboxes (`sandboxes/`) using MicroPython WASI, Wasmtime Zig C99, QuickJS, and Lupa.
- Multi-device Git synchronization (`records/` vs `bench.db` SQLite cache).
- Hardware auto-profiling (`host_configs.py`) and LM Studio client handling (`lmstudio.py`).
- Model Context Protocol (MCP) server integration (`mcp_server.py`).

---

## 2. Quick Command Reference

```powershell
# Interactive CLI benchmark runner
python main.py

# Generate & open standalone HTML performance report
python main.py report

# Bidirectional sync between SQLite (bench.db) and Git records (records/)
python main.py sync

# Manage and delete model results, speeds, and runs
python main.py delete

# Run the complete test suite (unit tests, sandboxes, golden solutions)
uv run pytest

# Linting and style checks with Ruff
uv run ruff check

# Automatic code formatting with Ruff
uv run ruff format

# Launch MCP server (STDIO)
uv run python mcp_server.py
```

---

## 3. Core Architectural Invariants

When working on this repository, you must respect the following rules:

1. **Language Invariant**:
   - Write all code comments, docstrings, markdown files, and commit messages in **English**.
   - User chat can be in the user's preferred language, but project files must remain strictly English.

2. **Isolated Sandboxing**:
   - Never execute untrusted model-generated code directly in the host Python process.
   - Always route guest code through the appropriate engine in `sandboxes/` with strict fuel or timeout limits.

3. **Git Hygiene & Storage**:
   - Never commit `bench.db`, `*.db-wal`, `*.db-shm`, `.local_host`, `.local_server`, or `report.html`.
   - Results and speed measurements are persisted as atomic, conflict-free JSON files under `records/` and synced via `sync.py`.

4. **Reasoning Models Handling**:
   - When communicating with reasoning models (DeepSeek-R1, QwQ, etc.), extract and strip reasoning blocks (`<think>`, `<thought>`, `<reasoning>`) before extracting source code to avoid executing draft code.
   - Do not force a default `temperature` in LM Studio requests unless explicitly requested; allow the user's LM Studio presets to govern sampling.

5. **Code Style & Verification**:
   - Target Python 3.12+ features and strict typing annotations.
   - Line length limit is 120 characters (`pyproject.toml`).
   - Run `uv run ruff check` and `uv run pytest` before completing any changes.
