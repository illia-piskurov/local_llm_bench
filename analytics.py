"""Analytics and data calculations layer for local LLM benchmark MCP server.
Provides domain queries, comparisons (intelligence, code, hardware), and report formatting.
Decoupled from MCP protocol and FastMCP server interface.
"""

import ast
import json
import re
import sqlite3
from pathlib import Path

from benchmarks import REGISTRY

ROOT = Path(__file__).parent
DB_PATH = ROOT / "bench.db"


SCHEMA_TEXT = """\
# Database schema bench.db

## hosts — hardware configurations
| Column     | Type    | Description |
|------------|---------|-------------|
| id         | TEXT PK | Unique ID |
| label      | TEXT    | Hardware description (e.g. "Ryzen 7 250 | 32 GB | 780m Radeon iGPU") |
| created_at | TEXT    | Creation timestamp |
| is_active  | INTEGER | 1 = active configuration |

## runs — execution sessions / benchmark runs
| Column            | Type | Description |
|-------------------|------|-------------|
| id                | TEXT | Run identifier (PK) |
| host_id           | TEXT | FK → hosts.id |
| model_key         | TEXT | Model identifier |
| model_name        | TEXT | Model display name |
| quantization      | TEXT | Quantization format (e.g. Q4_K_M, Q8_0, QAT, FP16) |
| backend           | TEXT | Backend runner (e.g. LM Studio, Ollama, vLLM, llama.cpp) |
| generation_params | TEXT | JSON object with temperature, top_p, seed, max_tokens |
| suite_version     | TEXT | Git commit / benchmark suite version |
| started_at        | TEXT | Run start timestamp |
| completed_at      | TEXT | Run completion timestamp |
| status            | TEXT | Run status ('completed', 'interrupted', 'in_progress', 'failed') |

## results — benchmark quality test results
| Column       | Type    | Description |
|--------------|---------|-------------|
| run_id       | TEXT    | FK → runs.id |
| model        | TEXT    | Model identifier |
| benchmark    | TEXT    | Benchmark ID (vm, sql, kv, scheduler, priority_scheduler, c_framing, js_async, lua_game_ai) |
| level        | TEXT    | Level (level1, level2, level3) |
| tested_at    | TEXT    | Test timestamp |
| passed       | INTEGER | Passed tests (automated evaluation) |
| total        | INTEGER | Total tests |
| failures     | TEXT    | JSON array of failure descriptions |
| manual_score | INTEGER | Manual score 1-10 (for manual levels) |
| comment      | TEXT    | Comment for manual score |

**PK:** (run_id, benchmark, level)

## speed_results — generation speed samples
| Column                      | Type | Description |
|-----------------------------|------|-------------|
| run_id                      | TEXT | FK → runs.id |
| host_id                     | TEXT | FK → hosts.id |
| model                       | TEXT | Model identifier |
| benchmark                   | TEXT | Benchmark ID |
| level                       | TEXT | Level |
| tested_at                   | TEXT | Sample timestamp |
| input_tokens                | INT  | Prompt tokens |
| total_output_tokens         | INT  | Generated tokens |
| reasoning_output_tokens     | INT  | Reasoning/thinking tokens |
| tokens_per_second           | REAL | Generation speed |
| time_to_first_token_seconds | REAL | Time to first token |
| model_load_time_seconds     | REAL | Model load time |

**PK:** (run_id, benchmark, level)
"""


def _conn() -> sqlite3.Connection:
    if not DB_PATH.exists():
        try:
            from database import Database
            from sync import import_all

            db = Database(DB_PATH)
            import_all(db)
        except Exception:
            pass
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def _safe(key: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]", "_", key)


def _pct(row) -> float:
    if row["manual_score"] is not None:
        return row["manual_score"] * 10.0
    if row["total"] and row["total"] > 0:
        return row["passed"] * 100.0 / row["total"]
    return 0.0


def _score_text(row) -> str:
    if row["manual_score"] is not None:
        return f"{row['manual_score']}/10"
    return f"{row['passed']}/{row['total']}"


def _find_model(conn: sqlite3.Connection, query_name: str) -> str | None:
    """Finds model by exact match or fuzzy search."""
    q = query_name.strip()
    exact = conn.execute("SELECT DISTINCT model FROM results WHERE model = ?", (q,)).fetchone()
    if exact:
        return exact["model"]
    fuzzy = conn.execute(
        "SELECT DISTINCT model FROM results WHERE model LIKE ? ORDER BY LENGTH(model)", (f"%{q}%",)
    ).fetchall()
    if len(fuzzy) == 1:
        return fuzzy[0]["model"]
    if len(fuzzy) > 1:
        # Prefix or suffix matches
        prefix_matches = [r["model"] for r in fuzzy if r["model"].endswith(q) or q in r["model"].split("/")[-1]]
        if len(prefix_matches) == 1:
            return prefix_matches[0]
        return fuzzy[0]["model"]
    return None


def _find_code_file(model: str, benchmark: str, level: str) -> tuple[Path | None, str | None]:
    """Finds model solution file and determines language."""
    key = _safe(model)
    prefix = f"{key}_{benchmark}_{level}"

    for search_dir, extensions in [
        (ROOT / "models_answers", ["py", "c", "js", "lua", "html", "sql", "txt"]),
        (ROOT / "html_answers", ["html"]),
    ]:
        if not search_dir.exists():
            continue
        for ext in extensions:
            path = search_dir / f"{prefix}.{ext}"
            if path.exists():
                return path, ext

    raw_path = ROOT / "raw_answers" / f"{prefix}.txt"
    if raw_path.exists():
        return raw_path, "txt"

    return None, None


def list_models(conn: sqlite3.Connection | None = None) -> str:
    """List all tested models with average quality and breakdown on complex L3 tests."""
    close_on_exit = False
    if conn is None:
        conn = _conn()
        close_on_exit = True
    try:
        rows = conn.execute("""
            SELECT model,
                   COUNT(*) AS tests,
                   AVG(CASE
                       WHEN manual_score IS NOT NULL THEN manual_score * 10.0
                       WHEN total > 0 THEN passed * 100.0 / total
                       ELSE 0
                   END) AS avg_quality,
                   AVG(CASE
                       WHEN level = 'level3' AND total > 0 THEN passed * 100.0 / total
                       ELSE NULL
                   END) AS l3_quality,
                   COUNT(CASE WHEN level = 'level3' THEN 1 ELSE NULL END) AS l3_count
            FROM results
            GROUP BY model
            ORDER BY avg_quality DESC
        """).fetchall()
        if not rows:
            return "No models found in database."
        lines = [
            "| # | Model | Tests | Average Quality | Complex Tests (L3) |",
            "|---|-------|-------|-----------------|--------------------|",
        ]
        for i, r in enumerate(rows, 1):
            l3_str = f"{r['l3_quality']:.1f}% ({r['l3_count']} tests)" if r["l3_quality"] is not None else "—"
            lines.append(f"| {i} | `{r['model']}` | {r['tests']} | {r['avg_quality']:.1f}% | {l3_str} |")
        lines.append(f"\nTotal models: {len(rows)}")
        return "\n".join(lines)
    finally:
        if close_on_exit:
            conn.close()


def list_hosts(conn: sqlite3.Connection | None = None) -> str:
    """List hardware (host) configurations with speed sample counts."""
    close_on_exit = False
    if conn is None:
        conn = _conn()
        close_on_exit = True
    try:
        rows = conn.execute("""
            SELECT h.id, h.label, h.is_active,
                   COUNT(sr.host_id) AS samples
            FROM hosts h
            LEFT JOIN speed_results sr ON h.id = sr.host_id
            GROUP BY h.id
            ORDER BY h.created_at
        """).fetchall()
        if not rows:
            return "No hardware configurations found."
        lines = []
        for r in rows:
            active = " **(active)**" if r["is_active"] else ""
            lines.append(f"- `{r['id']}` — **{r['label']}**, {r['samples']} samples{active}")
        return "\n".join(lines)
    finally:
        if close_on_exit:
            conn.close()


def list_benchmarks(conn: sqlite3.Connection | None = None) -> str:
    """List all available benchmarks, their levels, programming languages, and statistics."""
    close_on_exit = False
    if conn is None:
        conn = _conn()
        close_on_exit = True
    try:
        stats: dict[tuple[str, str], tuple[int, float]] = {}
        for r in conn.execute("""
            SELECT benchmark, level, COUNT(DISTINCT model) AS models,
                   AVG(CASE
                       WHEN manual_score IS NOT NULL THEN manual_score * 10.0
                       WHEN total > 0 THEN passed * 100.0 / total
                       ELSE 0
                   END) AS avg_score
            FROM results
            GROUP BY benchmark, level
        """).fetchall():
            stats[(r["benchmark"], r["level"])] = (r["models"], r["avg_score"])

        lines = [
            "| ID | Benchmark | Language | Level | Tested Models | Average Score |",
            "|----|-----------|----------|-------|---------------|---------------|",
        ]
        for b in REGISTRY:
            for lvl in b.levels:
                key = (b.id, lvl.id)
                if key in stats:
                    models, avg_sc = stats[key]
                    sc_str = f"{avg_sc:.1f}%"
                    tested_str = f"{models} models"
                else:
                    sc_str = "—"
                    tested_str = "0 models (ready to run)"
                lines.append(f"| `{b.id}` | {b.short} | {b.code_lang} | {lvl.name} | {tested_str} | {sc_str} |")
        return "\n".join(lines)
    finally:
        if close_on_exit:
            conn.close()


def get_leaderboard(conn: sqlite3.Connection | None = None) -> str:
    """Full ranking of models by quality — all benchmarks, averages, rankings."""
    close_on_exit = False
    if conn is None:
        conn = _conn()
        close_on_exit = True
    try:
        results = conn.execute("""
            SELECT model, benchmark, level,
                   passed, total, manual_score
            FROM results
            ORDER BY model, benchmark, level
        """).fetchall()
        if not results:
            return "No results found."

        columns: list[tuple[str, str]] = []
        seen: set[tuple[str, str]] = set()
        for r in results:
            key = (r["benchmark"], r["level"])
            if key not in seen:
                columns.append(key)
                seen.add(key)
        columns.sort()

        by_model: dict[str, dict[tuple[str, str], tuple[float, str]]] = {}
        for r in results:
            p = _pct(r)
            s = _score_text(r)
            by_model.setdefault(r["model"], {})[(r["benchmark"], r["level"])] = (p, s)

        rows = []
        for model, entries in by_model.items():
            percents = [v[0] for v in entries.values()]
            avg = sum(percents) / len(percents) if percents else 0
            rows.append((model, entries, avg, len(percents)))
        rows.sort(key=lambda x: x[2], reverse=True)

        col_hdr = [f"{benchmark} L{level[-1]}" for benchmark, level in columns]
        lines = [
            "| # | Model | " + " | ".join(col_hdr) + " | Average | Tests |",
            "|---|-------|" + "|".join(["---"] * len(columns)) + "|---------|-------|",
        ]
        for i, (model, entries, avg, cnt) in enumerate(rows, 1):
            scores = [entries.get(c, (None, "—"))[1] for c in columns]
            lines.append(f"| {i} | {model} | " + " | ".join(scores) + f" | {avg:.0f}% | {cnt} |")

        return "\n".join(lines)
    finally:
        if close_on_exit:
            conn.close()


def compare_intelligence(model_a: str, model_b: str, host_id: str = "", conn: sqlite3.Connection | None = None) -> str:
    """Deep intelligence comparison between two models:
    - Head-to-head wins/losses on shared tests
    - Breakdown by difficulty levels (L1 basic vs L2 logic vs L3 algorithms/architecture)
    - Retention rate (does the model degrade on L3 or maintain quality)
    - Category breakdown (VM/systems, databases/SQL, schedulers, data structures)
    - Analysis of critical failures and errors
    - Reasoning statistics (reasoning tokens) and intelligence/speed ratio.

    Args:
        model_a: First model name (or substring).
        model_b: Second model name (or substring).
        host_id: (optional) Host ID to compare generation speed."""
    close_on_exit = False
    if conn is None:
        conn = _conn()
        close_on_exit = True
    try:
        resolved_a = _find_model(conn, model_a)
        resolved_b = _find_model(conn, model_b)

        if not resolved_a:
            return f"Model '{model_a}' not found in database."
        if not resolved_b:
            return f"Model '{model_b}' not found in database."
        if resolved_a == resolved_b:
            return f"Both arguments refer to the same model: '{resolved_a}'."

        results_a = {
            (r["benchmark"], r["level"]): r
            for r in conn.execute("SELECT * FROM results WHERE model = ?", (resolved_a,)).fetchall()
        }
        results_b = {
            (r["benchmark"], r["level"]): r
            for r in conn.execute("SELECT * FROM results WHERE model = ?", (resolved_b,)).fetchall()
        }

        common_keys = sorted(set(results_a.keys()) & set(results_b.keys()))
        if not common_keys:
            return (
                f"Models `{resolved_a}` and `{resolved_b}` have no shared tests!\n"
                f"- `{resolved_a}` passed {len(results_a)} tests\n"
                f"- `{resolved_b}` passed {len(results_b)} tests"
            )

        # Score tallying
        wins_a = 0
        wins_b = 0
        ties = 0

        level_scores_a: dict[str, list[float]] = {"level1": [], "level2": [], "level3": []}
        level_scores_b: dict[str, list[float]] = {"level1": [], "level2": [], "level3": []}

        category_map = {
            "vm": "Systems/Interpreters",
            "sql": "Databases/SQL Engines",
            "kv": "Data Structures/Transactions",
            "scheduler": "Task Scheduling",
            "priority_scheduler": "Priority Queues",
            "c_framing": "C99/Networking/WASM",
            "js_async": "JS/Async/Concurrency",
            "lua_game_ai": "Lua/Game AI/Coroutines",
        }
        cat_scores_a: dict[str, list[float]] = {}
        cat_scores_b: dict[str, list[float]] = {}

        decisive_a: list[str] = []
        decisive_b: list[str] = []

        failures_a_count = 0
        failures_b_count = 0
        zero_a = 0
        zero_b = 0

        detail_rows = []

        for key in common_keys:
            bench, lvl = key
            ra = results_a[key]
            rb = results_b[key]

            pa = _pct(ra)
            pb = _pct(rb)

            level_scores_a.setdefault(lvl, []).append(pa)
            level_scores_b.setdefault(lvl, []).append(pb)

            cat = category_map.get(bench, "Other")
            cat_scores_a.setdefault(cat, []).append(pa)
            cat_scores_b.setdefault(cat, []).append(pb)

            sa = _score_text(ra)
            sb = _score_text(rb)

            if pa > pb:
                wins_a += 1
                winner = f"**{resolved_a.split('/')[-1]}**"
            elif pb > pa:
                wins_b += 1
                winner = f"**{resolved_b.split('/')[-1]}**"
            else:
                ties += 1
                winner = "tie"

            if pa - pb >= 30:
                decisive_a.append(f"{bench}/{lvl} ({sa} vs {sb})")
            elif pb - pa >= 30:
                decisive_b.append(f"{bench}/{lvl} ({sb} vs {sa})")

            if pa == 0:
                zero_a += 1
            if pb == 0:
                zero_b += 1

            if ra["failures"]:
                failures_a_count += len(json.loads(ra["failures"]))
            if rb["failures"]:
                failures_b_count += len(json.loads(rb["failures"]))

            detail_rows.append((bench, lvl, sa, sb, pa, pb, winner))

        # Aggregates
        total_a = sum(sum(v) for v in level_scores_a.values())
        total_b = sum(sum(v) for v in level_scores_b.values())
        avg_a = total_a / len(common_keys)
        avg_b = total_b / len(common_keys)

        lines = [
            f"# 🧠 Intelligence Analysis: {resolved_a} vs {resolved_b}\n",
            f"Comparison based on **{len(common_keys)} shared tests**.\n",
            "## 🏆 Overall Score (Head-to-Head)\n",
            f"- **{resolved_a}**: **{wins_a}** wins (average score: **{avg_a:.1f}%**)",
            f"- **{resolved_b}**: **{wins_b}** wins (average score: **{avg_b:.1f}%**)",
            f"- Ties: **{ties}**\n",
        ]

        # Verdict
        diff = avg_a - avg_b
        if abs(diff) < 2.0 and wins_a == wins_b:
            verdict = "🤝 **Models are roughly equal in intelligence** (minimal difference)."
        elif diff > 0:
            verdict = (
                f"⭐ **{resolved_a} is smarter** by **+{diff:.1f}%** (won {wins_a} out of {len(common_keys)} tests)."
            )
        else:
            verdict = f"⭐ **{resolved_b} is smarter** by **+{abs(diff):.1f}%** (won {wins_b} out of {len(common_keys)} tests)."
        lines.append(f"> {verdict}\n")

        # Level retention breakdown (L1 vs L2 vs L3)
        lines.append("## 📊 Difficulty Retention Analysis (Level Retention)\n")
        lines.append("| Difficulty Level | Description | " + f"`{resolved_a}` | `{resolved_b}` | Difference |")
        lines.append(
            "|------------------|-------------|------------------------|------------------------|------------|"
        )

        level_descriptions = {
            "level1": "Basic requirements / syntax",
            "level2": "Edge cases / branching / state",
            "level3": "Complex architecture / algorithms",
        }

        for lvl in ["level1", "level2", "level3"]:
            va = level_scores_a.get(lvl, [])
            vb = level_scores_b.get(lvl, [])
            if va and vb:
                al = sum(va) / len(va)
                bl = sum(vb) / len(vb)
                dl = al - bl
                sign = "+" if dl > 0 else ""
                diff_str = (
                    f"**{sign}{dl:.1f}%** ({resolved_a.split('/')[-1] if dl > 0 else resolved_b.split('/')[-1]})"
                    if abs(dl) >= 0.5
                    else "equal"
                )
                lines.append(
                    f"| **{lvl.upper()}** ({len(va)} tests) | {level_descriptions.get(lvl, '')} | "
                    f"**{al:.1f}%** | **{bl:.1f}%** | {diff_str} |"
                )

        # L1 -> L3 degradation calculation
        l1_a = sum(level_scores_a["level1"]) / len(level_scores_a["level1"]) if level_scores_a["level1"] else 0
        l3_a = sum(level_scores_a["level3"]) / len(level_scores_a["level3"]) if level_scores_a["level3"] else None
        l1_b = sum(level_scores_b["level1"]) / len(level_scores_b["level1"]) if level_scores_b["level1"] else 0
        l3_b = sum(level_scores_b["level3"]) / len(level_scores_b["level3"]) if level_scores_b["level3"] else None

        if l3_a is not None and l3_b is not None:
            drop_a = l1_a - l3_a
            drop_b = l1_b - l3_b
            lines.append("\n**True Intelligence Test (drop in quality on complex L3 tasks):**")
            lines.append(f"- `{resolved_a}`: drop from L1 ({l1_a:.0f}%) to L3 ({l3_a:.0f}%) by **-{drop_a:.1f}%**")
            lines.append(f"- `{resolved_b}`: drop from L1 ({l1_b:.0f}%) to L3 ({l3_b:.0f}%) by **-{drop_b:.1f}%**")
            if drop_a < drop_b - 5:
                lines.append(
                    f"💡 `{resolved_a}` retains complex logic and algorithms much better (less degradation on L3)."
                )
            elif drop_b < drop_a - 5:
                lines.append(
                    f"💡 `{resolved_b}` retains complex logic and algorithms much better (less degradation on L3)."
                )

        # Domain breakdown
        lines.append("\n## 🎯 Domain Strengths by Category\n")
        lines.append(f"| Category | Tests | `{resolved_a}` | `{resolved_b}` | Leader |")
        lines.append("|----------|-------|------------------------|------------------------|--------|")
        for cat in sorted(cat_scores_a.keys()):
            va = cat_scores_a[cat]
            vb = cat_scores_b[cat]
            ca = sum(va) / len(va)
            cb = sum(vb) / len(vb)
            dc = ca - cb
            if abs(dc) < 1.0:
                ldr = "parity"
            elif dc > 0:
                ldr = f"**{resolved_a.split('/')[-1]}** (+{dc:.0f}%)"
            else:
                ldr = f"**{resolved_b.split('/')[-1]}** (+{abs(dc):.0f}%)"
            lines.append(f"| {cat} | {len(va)} | {ca:.1f}% | {cb:.1f}% | {ldr} |")

        # Decisive tests
        if decisive_a or decisive_b:
            lines.append("\n## 💥 Decisive Tests (gap > 30%)\n")
            if decisive_a:
                lines.append(f"**Where `{resolved_a}` scored a decisive win:**")
                for d in decisive_a:
                    lines.append(f"- {d}")
            if decisive_b:
                lines.append(f"**Where `{resolved_b}` scored a decisive win:**")
                for d in decisive_b:
                    lines.append(f"- {d}")

        # Critical failures
        lines.append("\n## ⚠️ Errors and Reliability\n")
        lines.append(
            f"- `{resolved_a}`: individual test case failures: **{failures_a_count}**, total zero scores (0%): **{zero_a}**"
        )
        lines.append(
            f"- `{resolved_b}`: individual test case failures: **{failures_b_count}**, total zero scores (0%): **{zero_b}**"
        )

        # Speed and reasoning tokens
        speed_q = """
            SELECT model,
                   AVG(tokens_per_second) AS avg_tps,
                   AVG(time_to_first_token_seconds) AS avg_ttft,
                   AVG(reasoning_output_tokens) AS avg_reasoning,
                   AVG(total_output_tokens) AS avg_output
            FROM speed_results
            WHERE model IN (?, ?)
        """
        params = [resolved_a, resolved_b]
        if host_id:
            speed_q += " AND host_id = ?"
            params.append(host_id)
        speed_q += " GROUP BY model"

        speed_stats = {r["model"]: r for r in conn.execute(speed_q, params).fetchall()}
        if speed_stats:
            lines.append("\n## ⚡ Speed and Reasoning (Thinking / Reasoning)\n")
            lines.append("| Model | Speed (tok/s) | TTFT | Reasoning Tokens | Output Tokens |")
            lines.append("|-------|---------------|------|------------------|---------------|")
            for m in [resolved_a, resolved_b]:
                sp = speed_stats.get(m)
                if sp and sp["avg_tps"]:
                    rsn = f"{sp['avg_reasoning']:.0f}" if sp["avg_reasoning"] else "0"
                    lines.append(
                        f"| `{m}` | **{sp['avg_tps']:.1f}** | {sp['avg_ttft']:.3f}s | {rsn} | {sp['avg_output']:.0f} |"
                    )
                else:
                    lines.append(f"| `{m}` | — | — | — | — |")

        # Table of all common tests
        lines.append("\n<details><summary><b>📋 Expand detailed table of all shared tests</b></summary>\n")
        lines.append("| Benchmark | Level | " + f"`{resolved_a}` | `{resolved_b}` | Winner |")
        lines.append("|-----------|-------|------------------------|------------------------|--------|")
        for bench, lvl, sa, sb, pa, pb, winner in detail_rows:
            lines.append(f"| {bench} | {lvl} | {sa} ({pa:.0f}%) | {sb} ({pb:.0f}%) | {winner} |")
        lines.append("\n</details>")

        return "\n".join(lines)
    finally:
        if close_on_exit:
            conn.close()


def compare_code(model_a: str, model_b: str, benchmark: str, level: str, conn: sqlite3.Connection | None = None) -> str:
    """Compare code generated by two models for the same benchmark task.
    Shows solutions of both models, test results, failures, code metrics
    (lines, AST syntax validity, functions) and architecture analysis guidelines.

    Args:
        model_a: First model name.
        model_b: Second model name.
        benchmark: Benchmark ID (e.g. 'vm', 'sql', 'kv', 'scheduler', 'priority_scheduler', 'c_framing', 'js_async', 'lua_game_ai').
        level: Difficulty level ('level1', 'level2', 'level3')."""
    close_on_exit = False
    if conn is None:
        conn = _conn()
        close_on_exit = True
    try:
        resolved_a = _find_model(conn, model_a)
        resolved_b = _find_model(conn, model_b)

        if not resolved_a:
            return f"Model '{model_a}' not found."
        if not resolved_b:
            return f"Model '{model_b}' not found."

        # Test results
        res_a = conn.execute(
            "SELECT * FROM results WHERE model = ? AND benchmark = ? AND level = ?",
            (resolved_a, benchmark, level),
        ).fetchone()
        res_b = conn.execute(
            "SELECT * FROM results WHERE model = ? AND benchmark = ? AND level = ?",
            (resolved_b, benchmark, level),
        ).fetchone()

        path_a, ext_a = _find_code_file(resolved_a, benchmark, level)
        path_b, ext_b = _find_code_file(resolved_b, benchmark, level)

        code_a = path_a.read_text(encoding="utf-8") if path_a and path_a.exists() else None
        code_b = path_b.read_text(encoding="utf-8") if path_b and path_b.exists() else None

        if not code_a and not code_b:
            return f"Solution files not found for either model ({benchmark}/{level})."

        lines = [
            f"# 💻 Code Comparison: {benchmark} / {level}\n",
            f"**Model A:** `{resolved_a}`  \n**Model B:** `{resolved_b}`\n",
            "## 📊 Test Results Summary\n",
            "| Metric | " + f"`{resolved_a}` | `{resolved_b}` |",
            "|---------|------------------------|------------------------|",
        ]

        # Scores
        score_a_str = _score_text(res_a) if res_a else "not tested"
        score_b_str = _score_text(res_b) if res_b else "not tested"
        pct_a = f"{_pct(res_a):.0f}%" if res_a else "—"
        pct_b = f"{_pct(res_b):.0f}%" if res_b else "—"
        lines.append(f"| Test Result | **{score_a_str}** ({pct_a}) | **{score_b_str}** ({pct_b}) |")

        # Code metrics A and B
        lines_a = len(code_a.splitlines()) if code_a else 0
        lines_b = len(code_b.splitlines()) if code_b else 0

        def _check_syntax(code: str | None, ext: str | None) -> tuple[str, list[str]]:
            if not code:
                return "No file", []
            if ext == "py":
                try:
                    tree = ast.parse(code)
                    defs = [n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.ClassDef))]
                    return "Syntax valid (Python AST)", defs
                except SyntaxError as e:
                    return f"Syntax error: {e.msg}", []
            elif ext == "js":
                try:
                    import quickjs

                    ctx = quickjs.Context()
                    ctx.set_time_limit(1)
                    ctx.eval(code)
                    return "Syntax valid (JS)", []
                except Exception as e:
                    return f"JS error: {e}", []
            elif ext == "lua":
                try:
                    import lupa

                    rt = lupa.LuaRuntime(register_builtins=False)
                    rt.execute(code)
                    return "Syntax valid (Lua)", []
                except Exception as e:
                    return f"Lua error: {e}", []
            elif ext == "c":
                return "C99 source", []
            return "Plain text", []

        ast_ok_a, defs_a = _check_syntax(code_a, ext_a)
        ast_ok_b, defs_b = _check_syntax(code_b, ext_b)

        lines.append(f"| Lines of code | {lines_a} | {lines_b} |")
        lines.append(f"| Syntax | {ast_ok_a} | {ast_ok_b} |")
        if defs_a or defs_b:
            lines.append(f"| Functions/Classes | {len(defs_a)} | {len(defs_b)} |")

        # Test failures
        fails_a = json.loads(res_a["failures"]) if res_a and res_a["failures"] else []
        fails_b = json.loads(res_b["failures"]) if res_b and res_b["failures"] else []

        if fails_a or fails_b:
            lines.append("\n## ❌ Failed Tests\n")
            if fails_a:
                lines.append(f"**Failures for `{resolved_a}` ({len(fails_a)}):**")
                for f in fails_a:
                    lines.append(f"- `{f}`")
            else:
                lines.append(f"**`{resolved_a}`**: all tests passed successfully! ✅")

            if fails_b:
                lines.append(f"\n**Failures for `{resolved_b}` ({len(fails_b)}):**")
                for f in fails_b:
                    lines.append(f"- `{f}`")
            else:
                lines.append(f"**`{resolved_b}`**: all tests passed successfully! ✅")

        # Model A code
        lines.append(f"\n## 📄 Model Code: `{resolved_a}`\n")
        if code_a:
            lines.append(f"```{ext_a or 'python'}\n{code_a.strip()}\n```\n")
        else:
            lines.append("*Solution file missing.*\n")

        # Model B code
        lines.append(f"## 📄 Model Code: `{resolved_b}`\n")
        if code_b:
            lines.append(f"```{ext_b or 'python'}\n{code_b.strip()}\n```\n")
        else:
            lines.append("*Solution file missing.*\n")

        lines.append("## 🔍 AI Code Analysis Guidelines:")
        lines.append(
            "1. Compare architecture: which model produced more modular and extensible code.\n"
            "2. Find the root cause of test failures in the weaker model (logic bug, edge case, race condition, overflow).\n"
            "3. Assess code quality: readability, error handling, idiomatic conventions and style."
        )

        return "\n".join(lines)
    finally:
        if close_on_exit:
            conn.close()


def compare_models(models: str, host_id: str = "", conn: sqlite3.Connection | None = None) -> str:
    """Compare multiple models by quality (and speed if host_id is provided).

    Args:
        models: Comma-separated model names (e.g. "qwen3-1.7b, gemma-4-e2b").
                Fuzzy search is supported.
        host_id: (optional) PC configuration ID to compare speed."""
    raw_list = [m.strip() for m in models.split(",") if m.strip()]
    if len(raw_list) < 2:
        return "Specify at least 2 models separated by comma."

    close_on_exit = False
    if conn is None:
        conn = _conn()
        close_on_exit = True
    try:
        model_list = []
        for raw in raw_list:
            found = _find_model(conn, raw)
            if found:
                model_list.append(found)
            else:
                return f"Model '{raw}' not found."

        ph = ",".join("?" * len(model_list))
        results = conn.execute(
            f"""
            SELECT model, benchmark, level, passed, total, manual_score
            FROM results WHERE model IN ({ph})
            ORDER BY benchmark, level, model
        """,
            model_list,
        ).fetchall()

        if not results:
            return f"No results for: {', '.join(model_list)}"

        by_model: dict[str, dict[tuple[str, str], tuple[float, str]]] = {}
        all_tests: set[tuple[str, str]] = set()
        for r in results:
            key = (r["benchmark"], r["level"])
            by_model.setdefault(r["model"], {})[key] = (_pct(r), _score_text(r))
            all_tests.add(key)

        active = [m for m in model_list if m in by_model]
        if len(active) < 2:
            return f"Results found only for: {', '.join(by_model.keys())}. Need at least 2."

        tests = sorted(all_tests)

        lines = [f"# Comparison: {' vs '.join(active)}\n", "## Quality\n"]
        lines.append("| Benchmark | Level | " + " | ".join(active) + " | Best |")
        lines.append("|-----------|-------|" + "|".join(["---"] * len(active)) + "|------|")

        wins = {m: 0 for m in active}
        totals: dict[str, list[float]] = {m: [] for m in active}

        for bench, level in tests:
            scores = []
            pcts: list[tuple[str, float]] = []
            for m in active:
                entry = by_model.get(m, {}).get((bench, level))
                if entry:
                    scores.append(entry[1])
                    pcts.append((m, entry[0]))
                    totals[m].append(entry[0])
                else:
                    scores.append("—")

            valid = [(m, p) for m, p in pcts if p >= 0]
            if valid:
                best_p = max(v[1] for v in valid)
                winners = [m for m, p in valid if p == best_p]
                if len(winners) > 1:
                    winner = "tie"
                else:
                    winner = winners[0].split("/")[-1][:20]
                    wins[winners[0]] += 1
            else:
                winner = "—"

            lines.append(f"| {bench} | {level} | " + " | ".join(scores) + f" | {winner} |")

        lines.append("\n## Summary\n")
        avgs = {}
        for m in active:
            vals = totals[m]
            avg = sum(vals) / len(vals) if vals else 0
            avgs[m] = avg
            lines.append(f"- **{m}**: average {avg:.1f}%, wins {wins[m]}/{len(tests)}")

        best = max(avgs, key=lambda k: avgs[k])
        second = max((v for k, v in avgs.items() if k != best), default=0)
        diff = avgs[best] - second
        lines.append(f"\n**Best quality: {best}** (+{diff:.1f}%)")

        if host_id:
            speed_rows = conn.execute(
                f"""
                SELECT model,
                       AVG(tokens_per_second) AS avg_tps,
                       AVG(time_to_first_token_seconds) AS avg_ttft,
                       COUNT(*) AS samples
                FROM speed_results
                WHERE model IN ({ph}) AND host_id = ?
                GROUP BY model
                ORDER BY avg_tps DESC
            """,
                model_list + [host_id],
            ).fetchall()

            if speed_rows:
                host_row = conn.execute("SELECT label FROM hosts WHERE id = ?", (host_id,)).fetchone()
                hl = host_row["label"] if host_row else host_id
                lines.append(f"\n## Speed ({hl})\n")
                lines.append("| Model | tok/s | TTFT | Samples |")
                lines.append("|-------|-------|------|---------|")
                for sr in speed_rows:
                    ttft = f"{sr['avg_ttft']:.3f}s" if sr["avg_ttft"] else "—"
                    lines.append(f"| {sr['model']} | {sr['avg_tps']:.1f} | {ttft} | {sr['samples']} |")
                if len(speed_rows) >= 2 and speed_rows[1]["avg_tps"]:
                    ratio = speed_rows[0]["avg_tps"] / speed_rows[1]["avg_tps"]
                    lines.append(f"\n**Faster: {speed_rows[0]['model']}** (x{ratio:.1f})")

        return "\n".join(lines)
    finally:
        if close_on_exit:
            conn.close()


def compare_hosts(host_ids: str, conn: sqlite3.Connection | None = None) -> str:
    """Compare host configurations by generation speed on shared models.

    Args:
        host_ids: Comma-separated configuration IDs (e.g. "56a307df6486, e9d2b834bf61")."""
    id_list = [h.strip() for h in host_ids.split(",") if h.strip()]
    if len(id_list) < 2:
        return "Specify at least 2 configuration IDs separated by comma."

    close_on_exit = False
    if conn is None:
        conn = _conn()
        close_on_exit = True
    try:
        ph = ",".join("?" * len(id_list))
        hosts = {}
        for row in conn.execute(f"SELECT id, label FROM hosts WHERE id IN ({ph})", id_list):
            hosts[row["id"]] = row["label"]

        missing = [h for h in id_list if h not in hosts]
        if missing:
            return f"Unknown IDs: {', '.join(missing)}"

        rows = conn.execute(
            f"""
            SELECT host_id, model, benchmark, level, tokens_per_second, time_to_first_token_seconds
            FROM speed_results
            WHERE host_id IN ({ph}) AND tokens_per_second IS NOT NULL
        """,
            id_list,
        ).fetchall()

        by_host: dict[str, dict[tuple[str, str, str], dict]] = {}
        for r in rows:
            by_host.setdefault(r["host_id"], {})[(r["model"], r["benchmark"], r["level"])] = dict(r)

        common = None
        for hid in id_list:
            keys = set(by_host.get(hid, {}).keys())
            common = keys if common is None else common & keys

        if not common:
            return "No common models/benchmarks across all selected configurations."

        by_model: dict[str, list[tuple[str, str, str]]] = {}
        for key in common:
            by_model.setdefault(key[0], []).append(key)

        labels = [hosts[h] for h in id_list]
        lines = [f"# Hardware Comparison: {' vs '.join(labels)}\n", "## Generation Speed (tok/s)\n"]
        lines.append("| Model | Tests | " + " | ".join(labels) + " | Faster |")
        lines.append("|-------|-------|" + "|".join(["---"] * len(id_list)) + "|--------|")

        wins = {h: 0 for h in id_list}
        all_speeds: dict[str, list[float]] = {h: [] for h in id_list}

        for model, keys in sorted(by_model.items()):
            speeds = {}
            for hid in id_list:
                hd = by_host.get(hid, {})
                ss = [hd[k]["tokens_per_second"] for k in keys if k in hd and hd[k]["tokens_per_second"]]
                avg = sum(ss) / len(ss) if ss else 0
                speeds[hid] = avg
                all_speeds[hid].append(avg)

            mx = max(speeds.values())
            wid = [h for h, s in speeds.items() if s == mx][0]
            wins[wid] += 1

            cells = []
            for hid in id_list:
                s = speeds[hid]
                cells.append(f"**{s:.1f}**" if hid == wid else f"{s:.1f}")
            wl = hosts[wid].split("|")[0].strip()
            lines.append(f"| {model} | {len(keys)} | " + " | ".join(cells) + f" | {wl} |")

        lines.append("\n## Summary\n")
        avgs = {}
        for hid in id_list:
            vals = all_speeds[hid]
            avg = sum(vals) / len(vals) if vals else 0
            avgs[hid] = avg
            lines.append(f"- **{hosts[hid]}**: average {avg:.1f} tok/s, faster in {wins[hid]}/{len(by_model)} models")

        best = max(avgs, key=lambda k: avgs[k])
        lines.append(f"\n**Speed winner: {hosts[best]}**")
        return "\n".join(lines)
    finally:
        if close_on_exit:
            conn.close()


def get_model_details(model: str, conn: sqlite3.Connection | None = None) -> str:
    """Detailed results for a specific model — all tests, failures, speed.

    Args:
        model: Model name (or substring for fuzzy search)."""
    close_on_exit = False
    if conn is None:
        conn = _conn()
        close_on_exit = True
    try:
        model_key = _find_model(conn, model)
        if not model_key:
            return f"Model '{model}' not found."

        results = conn.execute(
            """
            SELECT benchmark, level, tested_at, passed, total, failures, manual_score, comment
            FROM results WHERE model = ?
            ORDER BY benchmark, level
        """,
            (model_key,),
        ).fetchall()

        lines = [f"# {model_key}\n", "## Test Results\n"]
        lines.append("| Benchmark | Level | Result | Date |")
        lines.append("|-----------|-------|--------|------|")

        percents = []
        all_failures: list[tuple[str, str, str]] = []
        for r in results:
            p = _pct(r)
            s = _score_text(r)
            percents.append(p)
            lines.append(f"| {r['benchmark']} | {r['level']} | {s} ({p:.0f}%) | {r['tested_at']} |")
            if r["failures"]:
                for f in json.loads(r["failures"]):
                    all_failures.append((r["benchmark"], r["level"], f))

        avg = sum(percents) / len(percents) if percents else 0
        lines.append(f"\n**Average: {avg:.1f}%** across {len(percents)} tests")

        if all_failures:
            lines.append(f"\n## Failed Tests ({len(all_failures)})\n")
            for bench, level, fail in all_failures:
                lines.append(f"- **{bench}/{level}**: {fail}")

        speed_rows = conn.execute(
            """
            SELECT sr.host_id, h.label AS host_label,
                   sr.benchmark, sr.level,
                   sr.tokens_per_second, sr.time_to_first_token_seconds,
                   sr.input_tokens, sr.total_output_tokens
            FROM speed_results sr
            LEFT JOIN hosts h ON sr.host_id = h.id
            WHERE sr.model = ?
            ORDER BY h.label, sr.benchmark, sr.level
        """,
            (model_key,),
        ).fetchall()

        if speed_rows:
            lines.append("\n## Speed\n")
            lines.append("| Configuration | Benchmark | Level | tok/s | TTFT | Tokens In/Out |")
            lines.append("|---------------|-----------|-------|-------|------|---------------|")
            for sr in speed_rows:
                ttft = f"{sr['time_to_first_token_seconds']:.3f}s" if sr["time_to_first_token_seconds"] else "—"
                tps = f"{sr['tokens_per_second']:.1f}" if sr["tokens_per_second"] else "—"
                tok = f"{sr['input_tokens'] or '?'}/{sr['total_output_tokens'] or '?'}"
                lines.append(
                    f"| {sr['host_label'] or sr['host_id']} | {sr['benchmark']} | "
                    f"{sr['level']} | {tps} | {ttft} | {tok} |"
                )

        return "\n".join(lines)
    finally:
        if close_on_exit:
            conn.close()


def list_runs(model: str = "", host_id: str = "", limit: int = 50, conn: sqlite3.Connection | None = None) -> str:
    """List historical benchmark runs with metadata: host, model, quantization, backend, and score.

    Args:
        model: (optional) Filter by model name/substring.
        host_id: (optional) Filter by host configuration ID.
        limit: Max number of runs to return (default: 50)."""
    close_on_exit = False
    if conn is None:
        conn = _conn()
        close_on_exit = True
    try:
        query_sql = """
            SELECT r.id, r.started_at, r.model_key, r.quantization, r.backend,
                   r.host_id, h.label AS host_label, r.status,
                   COUNT(res.benchmark) as tests_completed,
                   AVG(CASE WHEN res.total > 0 THEN (res.passed * 100.0 / res.total) ELSE 0 END) as avg_score,
                   AVG(s.tokens_per_second) as avg_speed
            FROM runs r
            LEFT JOIN hosts h ON r.host_id = h.id
            LEFT JOIN results res ON r.id = res.run_id
            LEFT JOIN speed_results s ON r.id = s.run_id AND res.benchmark = s.benchmark AND res.level = s.level
        """
        conditions = []
        params: list = []
        if model:
            resolved = _find_model(conn, model) or model
            conditions.append("(r.model_key LIKE ? OR r.model_key = ?)")
            params.extend([f"%{resolved}%", resolved])
        if host_id:
            conditions.append("r.host_id = ?")
            params.append(host_id)
        if conditions:
            query_sql += " WHERE " + " AND ".join(conditions)
        query_sql += " GROUP BY r.id ORDER BY r.started_at DESC LIMIT ?"
        params.append(limit)

        rows = conn.execute(query_sql, params).fetchall()
        if not rows:
            return "No runs found matching the criteria."

        lines = [
            f"# Benchmark Runs ({len(rows)})\n",
            "| Run ID | Date | Model | Quant | Host | Score | Speed | Status |",
            "|--------|------|-------|-------|------|-------|-------|--------|",
        ]
        for r in rows:
            speed_str = f"{r['avg_speed']:.1f} tok/s" if r["avg_speed"] else "—"
            score_str = f"{r['avg_score']:.1f}%" if r["avg_score"] is not None else "—"
            host_short = (r["host_label"] or r["host_id"]).split("|")[0].strip()
            lines.append(
                f"| `{r['id']}` | {r['started_at'][:16]} | {r['model_key']} | "
                f"{r['quantization'] or '—'} | {host_short} | {score_str} | {speed_str} | {r['status']} |"
            )
        return "\n".join(lines)
    finally:
        if close_on_exit:
            conn.close()


def get_run_details(run_id: str, conn: sqlite3.Connection | None = None) -> str:
    """Get full details of a specific benchmark run, including hyperparameters, all tests, scores, and speeds.

    Args:
        run_id: ID of the run (or substring to match)."""
    close_on_exit = False
    if conn is None:
        conn = _conn()
        close_on_exit = True
    try:
        run = conn.execute(
            """
            SELECT r.*, h.label AS host_label
            FROM runs r
            LEFT JOIN hosts h ON r.host_id = h.id
            WHERE r.id = ? OR r.id LIKE ?
            LIMIT 1
        """,
            (run_id, f"%{run_id}%"),
        ).fetchone()

        if not run:
            return f"Run '{run_id}' not found."

        full_id = run["id"]
        results = conn.execute(
            """
            SELECT res.benchmark, res.level, res.tested_at, res.passed, res.total, res.failures,
                   s.tokens_per_second, s.time_to_first_token_seconds, s.reasoning_output_tokens
            FROM results res
            LEFT JOIN speed_results s
              ON res.run_id = s.run_id AND res.benchmark = s.benchmark AND res.level = s.level
            WHERE res.run_id = ?
            ORDER BY res.benchmark, res.level
        """,
            (full_id,),
        ).fetchall()

        params = {}
        if run["generation_params"]:
            try:
                params = (
                    json.loads(run["generation_params"])
                    if isinstance(run["generation_params"], str)
                    else run["generation_params"]
                )
            except Exception:
                params = {}

        lines = [
            f"# Run: `{full_id}`\n",
            f"- **Model**: {run['model_key']}",
            f"- **Quantization**: {run['quantization'] or 'Unknown / Unspecified'}",
            f"- **Host**: {run['host_label'] or run['host_id']}",
            f"- **Backend**: {run['backend'] or 'Unknown'}",
            f"- **Suite Version**: {run['suite_version'] or '—'}",
            f"- **Started**: {run['started_at']} | **Completed**: {run['completed_at'] or 'In progress'}",
            f"- **Status**: `{run['status']}`",
        ]
        if params:
            hp_items = []
            for k in ["temperature", "seed", "top_p", "max_tokens", "timeout_seconds"]:
                if k in params:
                    hp_items.append(f"`{k}={params[k]}`")
            if hp_items:
                lines.append(f"- **Hyperparameters**: {', '.join(hp_items)}")
            art = params.get("artifact")
            if art and isinstance(art, dict):
                art_items = []
                if art.get("architecture"):
                    art_items.append(f"arch: `{art['architecture']}`")
                if art.get("size_bytes"):
                    art_items.append(f"size: `{art['size_bytes'] / (1024**3):.2f} GB`")
                if art.get("params_string"):
                    art_items.append(f"params: `{art['params_string']}`")
                if art.get("format"):
                    art_items.append(f"format: `{art['format']}`")
                if art_items:
                    lines.append(f"- **Model Artifact**: {', '.join(art_items)}")
            if params.get("suite_hash"):
                lines.append(f"- **Suite Hash**: `{params['suite_hash']}`")
        else:
            lines.append(f"- **Generation Params**: `{run['generation_params'] or '{}'}`")

        lines.extend(
            [
                "\n## Tests in this Run\n",
                "| Benchmark | Level | Result | Score | Speed | TTFT |",
                "|-----------|-------|--------|-------|-------|------|",
            ]
        )

        percents = []
        for r in results:
            p = (r["passed"] / r["total"] * 100) if r["total"] and r["total"] > 0 else 0.0
            percents.append(p)
            tps_str = f"{r['tokens_per_second']:.1f} tok/s" if r["tokens_per_second"] else "—"
            ttft_str = f"{r['time_to_first_token_seconds']:.2f}s" if r["time_to_first_token_seconds"] else "—"
            lines.append(
                f"| {r['benchmark']} | {r['level']} | {r['passed']}/{r['total']} | {p:.0f}% | {tps_str} | {ttft_str} |"
            )

        if percents:
            avg = sum(percents) / len(percents)
            lines.append(f"\n**Average Score: {avg:.1f}%** across {len(percents)} tests")

        return "\n".join(lines)
    finally:
        if close_on_exit:
            conn.close()


def read_answer(model: str, benchmark: str, level: str) -> str:
    """Read code/answer that the model generated for a benchmark.

    Args:
        model: Model name.
        benchmark: Benchmark ID (vm, sql, kv, c_framing, js_async, lua_game_ai, etc.).
        level: Level (level1, level2, level3)."""
    path, ext = _find_code_file(model, benchmark, level)
    if path and path.exists():
        content = path.read_text(encoding="utf-8")
        return f"## {model} — {benchmark}/{level}\n\nFile: `{path.name}`\n\n```{ext or 'text'}\n{content}\n```"

    return f"Answer file not found: {model} / {benchmark} / {level}"


def query(sql: str, conn: sqlite3.Connection | None = None) -> str:
    """Execute an arbitrary SELECT query against the benchmark database.
    See table schema in bench://schema resource.

    Args:
        sql: SQL query (SELECT only)."""
    if not sql.strip().upper().startswith("SELECT"):
        return "Error: only SELECT queries are allowed."

    close_on_exit = False
    if conn is None:
        conn = _conn()
        close_on_exit = True
    try:
        cursor = conn.execute(sql.strip())
        rows = cursor.fetchall()
        if not rows:
            return "Query returned 0 rows."

        columns = [desc[0] for desc in cursor.description]
        lines = ["| " + " | ".join(columns) + " |", "|" + "|".join(["---"] * len(columns)) + "|"]
        for row in rows[:200]:
            vals = [str(row[c]) if row[c] is not None else "—" for c in columns]
            lines.append("| " + " | ".join(vals) + " |")

        result = "\n".join(lines)
        if len(rows) > 200:
            result += f"\n\n... and {len(rows) - 200} more rows (truncated)"
        result += f"\n\n({len(rows)} rows)"
        return result
    except sqlite3.Error as e:
        return f"SQL error: {e}"
    finally:
        if close_on_exit:
            conn.close()
