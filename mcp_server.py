#!/usr/bin/env python3
"""MCP-сервер бенчмарка локальных LLM.

Предоставляет инструменты для анализа, сравнения моделей (по интеллекту, коду и скорости)
и конфигураций железа через структурированные запросы к SQLite-базе результатов.

Запуск:  python mcp_server.py
"""

import ast
import json
import re
import sqlite3
from pathlib import Path

from mcp.server.mcpserver import MCPServer

from benchmarks import REGISTRY

ROOT = Path(__file__).parent
DB_PATH = ROOT / "bench.db"

mcp = MCPServer(
    name="local-llm-bench",
    instructions=(
        "Это MCP-сервер бенчмарка локальных LLM-моделей. "
        "Позволяет анализировать и сравнивать модели: "
        "- compare_intelligence: глубокое сравнение интеллекта (L1/L2/L3, сложные задачи, удержание контекста). "
        "- compare_code: прямое сравнение сгенерированного кода двух моделей для конкретной задачи. "
        "- compare_models: сводное сравнение качества и скорости. "
        "- compare_hosts: сравнение железа (tok/s, TTFT). "
        "- get_leaderboard: общий рейтинг. "
        "- query: произвольные SQL-запросы к bench.db. "
        "Схему БД смотри в ресурсе bench://schema."
    ),
)


SCHEMA_TEXT = """\
# Схема базы данных bench.db

## hosts — конфигурации ПК
| Колонка    | Тип     | Описание |
|------------|---------|----------|
| id         | TEXT PK | Уникальный ID |
| label      | TEXT    | Описание железа (напр. "Ryzen 7 250 | 32 GB | 780m Radeon iGPU") |
| created_at | TEXT    | Дата создания |
| is_active  | INTEGER | 1 = активная конфигурация |

## results — результаты тестов качества
| Колонка      | Тип     | Описание |
|--------------|---------|----------|
| model        | TEXT    | Идентификатор модели |
| benchmark    | TEXT    | ID бенчмарка (vm, sql, kv, scheduler, priority_scheduler, c_framing, js_async, lua_game_ai) |
| level        | TEXT    | Уровень (level1, level2, level3) |
| tested_at    | TEXT    | Дата тестирования |
| passed       | INTEGER | Пройдено тестов (авто-оценка) |
| total        | INTEGER | Всего тестов |
| failures     | TEXT    | JSON-массив описаний провалов |
| manual_score | INTEGER | Ручная оценка 1-10 (для manual уровней) |
| comment      | TEXT    | Комментарий к ручной оценке |

**PK:** (model, benchmark, level)

## speed_results — замеры скорости генерации
| Колонка                      | Тип  | Описание |
|------------------------------|------|----------|
| host_id                      | TEXT | FK → hosts.id |
| model                        | TEXT | Идентификатор модели |
| benchmark                    | TEXT | ID бенчмарка |
| level                        | TEXT | Уровень |
| tested_at                    | TEXT | Дата замера |
| input_tokens                 | INT  | Токены промпта |
| total_output_tokens          | INT  | Сгенерированные токены |
| reasoning_output_tokens      | INT  | Токены reasoning/thinking |
| tokens_per_second            | REAL | Скорость генерации |
| time_to_first_token_seconds  | REAL | Задержка до первого токена |
| model_load_time_seconds      | REAL | Время загрузки модели |

**PK:** (host_id, model, benchmark, level)
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
    """Ищет модель по точному совпадению или нечёткому запросу."""
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
        # Если есть префиксное совпадение
        prefix_matches = [r["model"] for r in fuzzy if r["model"].endswith(q) or q in r["model"].split("/")[-1]]
        if len(prefix_matches) == 1:
            return prefix_matches[0]
        return fuzzy[0]["model"]
    return None


def _find_code_file(model: str, benchmark: str, level: str) -> tuple[Path | None, str | None]:
    """Находит файл решения модели и определяет язык."""
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


# ────────────────────── Resources ──────────────────────


@mcp.resource("bench://schema")
def schema() -> str:
    """Схема базы данных — таблицы, колонки, типы. Используй для написания SQL-запросов."""
    return SCHEMA_TEXT


@mcp.resource("bench://leaderboard")
def leaderboard_resource() -> str:
    """Краткая сводка общего рейтинга моделей."""
    return get_leaderboard()


# ────────────────────── Tools ──────────────────────


@mcp.tool()
def list_models() -> str:
    """Список всех протестированных моделей со средним качеством и разбивкой по сложным тестам L3."""
    conn = _conn()
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
            return "В базе пока нет моделей."
        lines = [
            "| # | Модель | Тестов | Среднее качество | Сложные тесты (L3) |",
            "|---|--------|--------|------------------|--------------------|",
        ]
        for i, r in enumerate(rows, 1):
            l3_str = f"{r['l3_quality']:.1f}% ({r['l3_count']} т.)" if r["l3_quality"] is not None else "—"
            lines.append(f"| {i} | `{r['model']}` | {r['tests']} | {r['avg_quality']:.1f}% | {l3_str} |")
        lines.append(f"\nВсего моделей: {len(rows)}")
        return "\n".join(lines)
    finally:
        conn.close()


@mcp.tool()
def list_hosts() -> str:
    """Список конфигураций ПК (железа) с количеством замеров скорости."""
    conn = _conn()
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
            return "Конфигурации ПК не найдены."
        lines = []
        for r in rows:
            active = " **(активная)**" if r["is_active"] else ""
            lines.append(f"- `{r['id']}` — **{r['label']}**, {r['samples']} замеров{active}")
        return "\n".join(lines)
    finally:
        conn.close()


@mcp.tool()
def list_benchmarks() -> str:
    """Список всех доступных бенчмарков, их уровней, языков программирования и статистики."""
    conn = _conn()
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
            "| ID | Бенчмарк | Язык | Уровень | Протестировано | Средний балл |",
            "|----|----------|------|---------|----------------|--------------|",
        ]
        for b in REGISTRY:
            for lvl in b.levels:
                key = (b.id, lvl.id)
                if key in stats:
                    models, avg_sc = stats[key]
                    sc_str = f"{avg_sc:.1f}%"
                    tested_str = f"{models} мод."
                else:
                    sc_str = "—"
                    tested_str = "0 мод. (готов к запуску)"
                lines.append(f"| `{b.id}` | {b.short} | {b.code_lang} | {lvl.name} | {tested_str} | {sc_str} |")
        return "\n".join(lines)
    finally:
        conn.close()


@mcp.tool()
def get_leaderboard() -> str:
    """Полный рейтинг моделей по качеству — все бенчмарки, среднее, ранжирование."""
    conn = _conn()
    try:
        results = conn.execute("""
            SELECT model, benchmark, level,
                   passed, total, manual_score
            FROM results
            ORDER BY model, benchmark, level
        """).fetchall()
        if not results:
            return "Результатов нет."

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
            "| # | Модель | " + " | ".join(col_hdr) + " | Среднее | Тестов |",
            "|---|--------|" + "|".join(["---"] * len(columns)) + "|---------|--------|",
        ]
        for i, (model, entries, avg, cnt) in enumerate(rows, 1):
            scores = [entries.get(c, (None, "—"))[1] for c in columns]
            lines.append(f"| {i} | {model} | " + " | ".join(scores) + f" | {avg:.0f}% | {cnt} |")

        return "\n".join(lines)
    finally:
        conn.close()


@mcp.tool()
def compare_intelligence(model_a: str, model_b: str, host_id: str = "") -> str:
    """Глубокое сравнение интеллекта двух моделей:
    - Head-to-head победы/поражения на общих тестах
    - Разбор по уровням сложности (L1 базовый vs L2 логика vs L3 алгоритмы/архитектура)
    - Удержание сложности (Retention rate: сдувается ли модель на L3 или держит качество)
    - Разбор категорий (VM/системы, базы данных/SQL, планировщики, структуры данных)
    - Анализ критических провалов и ошибок
    - Статистика рассуждений (reasoning tokens) и соотношение интеллект/скорость.

    Args:
        model_a: Имя первой модели (или подстрока).
        model_b: Имя второй модели (или подстрока).
        host_id: (опционально) ID хоста для сравнения скорости генерации.
    """
    conn = _conn()
    try:
        resolved_a = _find_model(conn, model_a)
        resolved_b = _find_model(conn, model_b)

        if not resolved_a:
            return f"Модель '{model_a}' не найдена в базе."
        if not resolved_b:
            return f"Модель '{model_b}' не найдена в базе."
        if resolved_a == resolved_b:
            return f"Обе модели указывают на одну и ту же модель: '{resolved_a}'."

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
                f"У моделей `{resolved_a}` и `{resolved_b}` нет общих пройденных тестов!\n"
                f"- `{resolved_a}` прошла {len(results_a)} тестов\n"
                f"- `{resolved_b}` прошла {len(results_b)} тестов"
            )

        # Подсчёт очков
        wins_a = 0
        wins_b = 0
        ties = 0

        level_scores_a: dict[str, list[float]] = {"level1": [], "level2": [], "level3": []}
        level_scores_b: dict[str, list[float]] = {"level1": [], "level2": [], "level3": []}

        category_map = {
            "vm": "Системное/Интерпретаторы",
            "sql": "СУБД/SQL-движки",
            "kv": "Структуры данных/Транзакции",
            "scheduler": "Планирование задач",
            "priority_scheduler": "Приоритеты/Очереди",
            "c_framing": "C99/Сетевой протокол/WASM",
            "js_async": "JS/Асинхронность/Concurrency",
            "lua_game_ai": "Lua/Игровой AI/Корутины",
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

            cat = category_map.get(bench, "Другое")
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
                winner = "ничья"

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

        # Агрегаты
        total_a = sum(sum(v) for v in level_scores_a.values())
        total_b = sum(sum(v) for v in level_scores_b.values())
        avg_a = total_a / len(common_keys)
        avg_b = total_b / len(common_keys)

        lines = [
            f"# 🧠 Анализ интеллекта: {resolved_a} vs {resolved_b}\n",
            f"Сравнение на базе **{len(common_keys)} общих тестов**.\n",
            "## 🏆 Общий счёт (Head-to-Head)\n",
            f"- **{resolved_a}**: **{wins_a}** побед (средний балл: **{avg_a:.1f}%**)",
            f"- **{resolved_b}**: **{wins_b}** побед (средний балл: **{avg_b:.1f}%**)",
            f"- Ничьих: **{ties}**\n",
        ]

        # Вердикт
        diff = avg_a - avg_b
        if abs(diff) < 2.0 and wins_a == wins_b:
            verdict = "🤝 **Модели примерно равны по интеллекту** (минимальная разница)."
        elif diff > 0:
            verdict = f"⭐ **{resolved_a} умнее** на **+{diff:.1f}%** (выиграла {wins_a} из {len(common_keys)} тестов)."
        else:
            verdict = (
                f"⭐ **{resolved_b} умнее** на **+{abs(diff):.1f}%** (выиграла {wins_b} из {len(common_keys)} тестов)."
            )
        lines.append(f"> {verdict}\n")

        # Разбор по уровням сложности (L1 vs L2 vs L3)
        lines.append("## 📊 Анализ устойчивости к сложности (Level Retention)\n")
        lines.append("| Уровень сложности | Описание | " + f"`{resolved_a}` | `{resolved_b}` | Разница |")
        lines.append("|-------------------|----------|------------------------|------------------------|---------|")

        level_descriptions = {
            "level1": "Базовые требования / синтаксис",
            "level2": "Краевые случаи / ветвления / стейт",
            "level3": "Сложная архитектура / алгоритмы",
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
                    else "равны"
                )
                lines.append(
                    f"| **{lvl.upper()}** ({len(va)} т.) | {level_descriptions.get(lvl, '')} | "
                    f"**{al:.1f}%** | **{bl:.1f}%** | {diff_str} |"
                )

        # Вычисление деградации L1 -> L3
        l1_a = sum(level_scores_a["level1"]) / len(level_scores_a["level1"]) if level_scores_a["level1"] else 0
        l3_a = sum(level_scores_a["level3"]) / len(level_scores_a["level3"]) if level_scores_a["level3"] else None
        l1_b = sum(level_scores_b["level1"]) / len(level_scores_b["level1"]) if level_scores_b["level1"] else 0
        l3_b = sum(level_scores_b["level3"]) / len(level_scores_b["level3"]) if level_scores_b["level3"] else None

        if l3_a is not None and l3_b is not None:
            drop_a = l1_a - l3_a
            drop_b = l1_b - l3_b
            lines.append("\n**Тест на истинный интеллект (падение качества на сложных задачах L3):**")
            lines.append(f"- `{resolved_a}`: падение с L1 ({l1_a:.0f}%) до L3 ({l3_a:.0f}%) на **-{drop_a:.1f}%**")
            lines.append(f"- `{resolved_b}`: падение с L1 ({l1_b:.0f}%) до L3 ({l3_b:.0f}%) на **-{drop_b:.1f}%**")
            if drop_a < drop_b - 5:
                lines.append(
                    f"💡 `{resolved_a}` гораздо лучше удерживает сложную логику и алгоритмы (меньше деградирует на L3)."
                )
            elif drop_b < drop_a - 5:
                lines.append(
                    f"💡 `{resolved_b}` гораздо лучше удерживает сложную логику и алгоритмы (меньше деградирует на L3)."
                )

        # Разбор по доменам
        lines.append("\n## 🎯 Сильные стороны по категориям\n")
        lines.append(f"| Категория | Тестов | `{resolved_a}` | `{resolved_b}` | Лидер |")
        lines.append("|-----------|--------|------------------------|------------------------|-------|")
        for cat in sorted(cat_scores_a.keys()):
            va = cat_scores_a[cat]
            vb = cat_scores_b[cat]
            ca = sum(va) / len(va)
            cb = sum(vb) / len(vb)
            dc = ca - cb
            if abs(dc) < 1.0:
                ldr = "паритет"
            elif dc > 0:
                ldr = f"**{resolved_a.split('/')[-1]}** (+{dc:.0f}%)"
            else:
                ldr = f"**{resolved_b.split('/')[-1]}** (+{abs(dc):.0f}%)"
            lines.append(f"| {cat} | {len(va)} | {ca:.1f}% | {cb:.1f}% | {ldr} |")

        # Решающие тесты
        if decisive_a or decisive_b:
            lines.append("\n## 💥 Решающие тесты (разрыв > 30%)\n")
            if decisive_a:
                lines.append(f"**Где разгромно победила `{resolved_a}`:**")
                for d in decisive_a:
                    lines.append(f"- {d}")
            if decisive_b:
                lines.append(f"**Где разгромно победила `{resolved_b}`:**")
                for d in decisive_b:
                    lines.append(f"- {d}")

        # Критические провалы
        lines.append("\n## ⚠️ Ошибки и надёжность\n")
        lines.append(
            f"- `{resolved_a}`: провалено отдельных тест-кейсов: **{failures_a_count}**, полных нулей (0%): **{zero_a}**"
        )
        lines.append(
            f"- `{resolved_b}`: провалено отдельных тест-кейсов: **{failures_b_count}**, полных нулей (0%): **{zero_b}**"
        )

        # Скорость и reasoning tokens
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
            lines.append("\n## ⚡ Скорость и рассуждения (Thinking / Reasoning)\n")
            lines.append("| Модель | Скорость (tok/s) | TTFT | Reasoning токены | Выходные токены |")
            lines.append("|--------|------------------|------|-------------------|-----------------|")
            for m in [resolved_a, resolved_b]:
                sp = speed_stats.get(m)
                if sp and sp["avg_tps"]:
                    rsn = f"{sp['avg_reasoning']:.0f}" if sp["avg_reasoning"] else "0"
                    lines.append(
                        f"| `{m}` | **{sp['avg_tps']:.1f}** | {sp['avg_ttft']:.3f}s | {rsn} | {sp['avg_output']:.0f} |"
                    )
                else:
                    lines.append(f"| `{m}` | — | — | — | — |")

        # Таблица всех общих тестов
        lines.append("\n<details><summary><b>📋 Развернуть детальную таблицу всех общих тестов</b></summary>\n")
        lines.append("| Бенчмарк | Уровень | " + f"`{resolved_a}` | `{resolved_b}` | Победитель |")
        lines.append("|----------|---------|------------------------|------------------------|------------|")
        for bench, lvl, sa, sb, pa, pb, winner in detail_rows:
            lines.append(f"| {bench} | {lvl} | {sa} ({pa:.0f}%) | {sb} ({pb:.0f}%) | {winner} |")
        lines.append("\n</details>")

        return "\n".join(lines)
    finally:
        conn.close()


@mcp.tool()
def compare_code(model_a: str, model_b: str, benchmark: str, level: str) -> str:
    """Сравнить код двух моделей, сгенерированный для одной и той же задачи бенчмарка.
    Показывает решения обеих моделей, их результаты тестов, провалы, метрики кода
    (строки, синтаксическая валидность AST, функции) и рекомендации по анализу архитектуры.

    Args:
        model_a: Имя первой модели.
        model_b: Имя второй модели.
        benchmark: ID бенчмарка (напр. 'vm', 'sql', 'kv', 'scheduler', 'priority_scheduler', 'c_framing', 'js_async', 'lua_game_ai').
        level: Уровень сложности ('level1', 'level2', 'level3').
    """
    conn = _conn()
    try:
        resolved_a = _find_model(conn, model_a)
        resolved_b = _find_model(conn, model_b)

        if not resolved_a:
            return f"Модель '{model_a}' не найдена."
        if not resolved_b:
            return f"Модель '{model_b}' не найдена."

        # Результаты тестов
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
            return f"Файлы решений не найдены ни для одной модели ({benchmark}/{level})."

        lines = [
            f"# 💻 Сравнение кода: {benchmark} / {level}\n",
            f"**Модель A:** `{resolved_a}`  \n**Модель B:** `{resolved_b}`\n",
            "## 📊 Сводка результатов тестирования\n",
            "| Метрика | " + f"`{resolved_a}` | `{resolved_b}` |",
            "|---------|------------------------|------------------------|",
        ]

        # Оценки
        score_a_str = _score_text(res_a) if res_a else "не тестировалась"
        score_b_str = _score_text(res_b) if res_b else "не тестировалась"
        pct_a = f"{_pct(res_a):.0f}%" if res_a else "—"
        pct_b = f"{_pct(res_b):.0f}%" if res_b else "—"
        lines.append(f"| Результат тестов | **{score_a_str}** ({pct_a}) | **{score_b_str}** ({pct_b}) |")

        # Метрики кода A и B
        lines_a = len(code_a.splitlines()) if code_a else 0
        lines_b = len(code_b.splitlines()) if code_b else 0

        def _check_syntax(code: str | None, ext: str | None) -> tuple[str, list[str]]:
            if not code:
                return "Нет файла", []
            if ext == "py":
                try:
                    tree = ast.parse(code)
                    defs = [n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.ClassDef))]
                    return "Синтаксис корректен (Python AST)", defs
                except SyntaxError as e:
                    return f"Синтаксическая ошибка: {e.msg}", []
            elif ext == "js":
                try:
                    import quickjs

                    ctx = quickjs.Context()
                    ctx.set_time_limit(1)
                    ctx.eval(code)
                    return "Синтаксис корректен (JS)", []
                except Exception as e:
                    return f"Ошибка JS: {e}", []
            elif ext == "lua":
                try:
                    import lupa

                    rt = lupa.LuaRuntime(register_builtins=False)
                    rt.execute(code)
                    return "Синтаксис корректен (Lua)", []
                except Exception as e:
                    return f"Ошибка Lua: {e}", []
            elif ext == "c":
                return "C99 исходник", []
            return "Текстовый формат", []

        ast_ok_a, defs_a = _check_syntax(code_a, ext_a)
        ast_ok_b, defs_b = _check_syntax(code_b, ext_b)

        lines.append(f"| Строк кода | {lines_a} | {lines_b} |")
        lines.append(f"| Синтаксис | {ast_ok_a} | {ast_ok_b} |")
        if defs_a or defs_b:
            lines.append(f"| Функции/Классы | {len(defs_a)} | {len(defs_b)} |")

        # Провалы тестов
        fails_a = json.loads(res_a["failures"]) if res_a and res_a["failures"] else []
        fails_b = json.loads(res_b["failures"]) if res_b and res_b["failures"] else []

        if fails_a or fails_b:
            lines.append("\n## ❌ Проваленные тесты\n")
            if fails_a:
                lines.append(f"**Провалы `{resolved_a}` ({len(fails_a)}):**")
                for f in fails_a:
                    lines.append(f"- `{f}`")
            else:
                lines.append(f"**`{resolved_a}`**: все тесты пройдены успешно! ✅")

            if fails_b:
                lines.append(f"\n**Провалы `{resolved_b}` ({len(fails_b)}):**")
                for f in fails_b:
                    lines.append(f"- `{f}`")
            else:
                lines.append(f"**`{resolved_b}`**: все тесты пройдены успешно! ✅")

        # Код модели A
        lines.append(f"\n## 📄 Код модели: `{resolved_a}`\n")
        if code_a:
            lines.append(f"```{ext_a or 'python'}\n{code_a.strip()}\n```\n")
        else:
            lines.append("*Файл решения отсутствует.*\n")

        # Код модели B
        lines.append(f"## 📄 Код модели: `{resolved_b}`\n")
        if code_b:
            lines.append(f"```{ext_b or 'python'}\n{code_b.strip()}\n```\n")
        else:
            lines.append("*Файл решения отсутствует.*\n")

        lines.append("## 🔍 Инструкция для ИИ-анализа этого кода:")
        lines.append(
            "1. Сравни архитектуру: какая модель написала более модульный и расширяемый код.\n"
            "2. Найди причину падения тестов у более слабой модели (баг в логике, краевой случай, гонка, переполнение).\n"
            "3. Оцени качество кода: читаемость, обработка исключений, соответствие PEP8/идиомам."
        )

        return "\n".join(lines)
    finally:
        conn.close()


@mcp.tool()
def compare_models(models: str, host_id: str = "") -> str:
    """Сравнить несколько моделей по качеству (и скорости, если указан host_id).

    Args:
        models: Через запятую — имена моделей (напр. "qwen3-1.7b, gemma-4-e2b").
                Поддерживается нечёткий поиск.
        host_id: (опционально) ID конфигурации ПК для сравнения скорости.
    """
    raw_list = [m.strip() for m in models.split(",") if m.strip()]
    if len(raw_list) < 2:
        return "Укажите минимум 2 модели через запятую."

    conn = _conn()
    try:
        model_list = []
        for raw in raw_list:
            found = _find_model(conn, raw)
            if found:
                model_list.append(found)
            else:
                return f"Модель '{raw}' не найдена."

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
            return f"Нет результатов для: {', '.join(model_list)}"

        by_model: dict[str, dict[tuple[str, str], tuple[float, str]]] = {}
        all_tests: set[tuple[str, str]] = set()
        for r in results:
            key = (r["benchmark"], r["level"])
            by_model.setdefault(r["model"], {})[key] = (_pct(r), _score_text(r))
            all_tests.add(key)

        active = [m for m in model_list if m in by_model]
        if len(active) < 2:
            return f"Найдены результаты только для: {', '.join(by_model.keys())}. Нужно минимум 2."

        tests = sorted(all_tests)

        lines = [f"# Сравнение: {' vs '.join(active)}\n", "## Качество\n"]
        lines.append("| Бенчмарк | Уровень | " + " | ".join(active) + " | Лучше |")
        lines.append("|----------|---------|" + "|".join(["---"] * len(active)) + "|-------|")

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
                    winner = "ничья"
                else:
                    winner = winners[0].split("/")[-1][:20]
                    wins[winners[0]] += 1
            else:
                winner = "—"

            lines.append(f"| {bench} | {level} | " + " | ".join(scores) + f" | {winner} |")

        lines.append("\n## Итоги\n")
        avgs = {}
        for m in active:
            vals = totals[m]
            avg = sum(vals) / len(vals) if vals else 0
            avgs[m] = avg
            lines.append(f"- **{m}**: среднее {avg:.1f}%, побед {wins[m]}/{len(tests)}")

        best = max(avgs, key=lambda k: avgs[k])
        second = max((v for k, v in avgs.items() if k != best), default=0)
        diff = avgs[best] - second
        lines.append(f"\n**Лучше по качеству: {best}** (+{diff:.1f}%)")

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
                lines.append(f"\n## Скорость ({hl})\n")
                lines.append("| Модель | tok/s | TTFT | Замеров |")
                lines.append("|--------|-------|------|---------|")
                for sr in speed_rows:
                    ttft = f"{sr['avg_ttft']:.3f}s" if sr["avg_ttft"] else "—"
                    lines.append(f"| {sr['model']} | {sr['avg_tps']:.1f} | {ttft} | {sr['samples']} |")
                if len(speed_rows) >= 2 and speed_rows[1]["avg_tps"]:
                    ratio = speed_rows[0]["avg_tps"] / speed_rows[1]["avg_tps"]
                    lines.append(f"\n**Быстрее: {speed_rows[0]['model']}** (x{ratio:.1f})")

        return "\n".join(lines)
    finally:
        conn.close()


@mcp.tool()
def compare_hosts(host_ids: str) -> str:
    """Сравнить конфигурации ПК по скорости генерации на общих моделях.

    Args:
        host_ids: Через запятую — ID конфигураций (напр. "56a307df6486, e9d2b834bf61").
    """
    id_list = [h.strip() for h in host_ids.split(",") if h.strip()]
    if len(id_list) < 2:
        return "Укажите минимум 2 ID конфигураций через запятую."

    conn = _conn()
    try:
        ph = ",".join("?" * len(id_list))
        hosts = {}
        for row in conn.execute(f"SELECT id, label FROM hosts WHERE id IN ({ph})", id_list):
            hosts[row["id"]] = row["label"]

        missing = [h for h in id_list if h not in hosts]
        if missing:
            return f"Неизвестные ID: {', '.join(missing)}"

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
            return "Нет общих моделей/тестов на всех выбранных конфигурациях."

        by_model: dict[str, list[tuple[str, str, str]]] = {}
        for key in common:
            by_model.setdefault(key[0], []).append(key)

        labels = [hosts[h] for h in id_list]
        lines = [f"# Сравнение железа: {' vs '.join(labels)}\n", "## Скорость генерации (tok/s)\n"]
        lines.append("| Модель | Тестов | " + " | ".join(labels) + " | Быстрее |")
        lines.append("|--------|--------|" + "|".join(["---"] * len(id_list)) + "|---------|")

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

        lines.append("\n## Итоги\n")
        avgs = {}
        for hid in id_list:
            vals = all_speeds[hid]
            avg = sum(vals) / len(vals) if vals else 0
            avgs[hid] = avg
            lines.append(f"- **{hosts[hid]}**: среднее {avg:.1f} tok/s, быстрее в {wins[hid]}/{len(by_model)} моделях")

        best = max(avgs, key=lambda k: avgs[k])
        lines.append(f"\n**Победитель по скорости: {hosts[best]}**")
        return "\n".join(lines)
    finally:
        conn.close()


@mcp.tool()
def get_model_details(model: str) -> str:
    """Подробные результаты конкретной модели — все тесты, провалы, скорость.

    Args:
        model: Имя модели (или подстрока для нечёткого поиска).
    """
    conn = _conn()
    try:
        model_key = _find_model(conn, model)
        if not model_key:
            return f"Модель '{model}' не найдена."

        results = conn.execute(
            """
            SELECT benchmark, level, tested_at, passed, total, failures, manual_score, comment
            FROM results WHERE model = ?
            ORDER BY benchmark, level
        """,
            (model_key,),
        ).fetchall()

        lines = [f"# {model_key}\n", "## Результаты тестов\n"]
        lines.append("| Бенчмарк | Уровень | Результат | Дата |")
        lines.append("|----------|---------|-----------|------|")

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
        lines.append(f"\n**Среднее: {avg:.1f}%** по {len(percents)} тестам")

        if all_failures:
            lines.append(f"\n## Проваленные тесты ({len(all_failures)})\n")
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
            lines.append("\n## Скорость\n")
            lines.append("| Конфигурация | Бенчмарк | Уровень | tok/s | TTFT | Токены вх/вых |")
            lines.append("|--------------|----------|---------|-------|------|---------------|")
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
        conn.close()


@mcp.tool()
def read_answer(model: str, benchmark: str, level: str) -> str:
    """Прочитать код/ответ, который модель сгенерировала для бенчмарка.

    Args:
        model: Имя модели.
        benchmark: ID бенчмарка (vm, sql, kv, c_framing, js_async, lua_game_ai и т.д.).
        level: Уровень (level1, level2, level3).
    """
    path, ext = _find_code_file(model, benchmark, level)
    if path and path.exists():
        content = path.read_text(encoding="utf-8")
        return f"## {model} — {benchmark}/{level}\n\nФайл: `{path.name}`\n\n```{ext or 'text'}\n{content}\n```"

    return f"Файл ответа не найден: {model} / {benchmark} / {level}"


@mcp.tool()
def query(sql: str) -> str:
    """Выполнить произвольный SELECT-запрос к базе бенчмарков.
    Схему таблиц смотри в ресурсе bench://schema.

    Args:
        sql: SQL-запрос (только SELECT).
    """
    if not sql.strip().upper().startswith("SELECT"):
        return "Ошибка: разрешены только SELECT-запросы."

    conn = _conn()
    try:
        cursor = conn.execute(sql.strip())
        rows = cursor.fetchall()
        if not rows:
            return "Запрос вернул 0 строк."

        columns = [desc[0] for desc in cursor.description]
        lines = ["| " + " | ".join(columns) + " |", "|" + "|".join(["---"] * len(columns)) + "|"]
        for row in rows[:200]:
            vals = [str(row[c]) if row[c] is not None else "—" for c in columns]
            lines.append("| " + " | ".join(vals) + " |")

        result = "\n".join(lines)
        if len(rows) > 200:
            result += f"\n\n... и ещё {len(rows) - 200} строк (обрезано)"
        result += f"\n\n({len(rows)} строк)"
        return result
    except sqlite3.Error as e:
        return f"SQL ошибка: {e}"
    finally:
        conn.close()


if __name__ == "__main__":
    mcp.run()
