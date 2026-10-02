"""Data access and analytics layer for benchmark reporting.

Extracts test results, hardware metrics, and run history from SQLite,
aggregating them into structured domain objects decoupled from HTML presentation.
"""

import html
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from benchmarks import BY_ID, REGISTRY
from database import Database

ROOT = Path(__file__).parent


@dataclass
class ReportData:
    leaderboard: list[dict[str, Any]]
    runs_data: list[dict[str, Any]]
    active_hosts: list[Any]
    device_stats: dict[str, Any]
    model_host_matrix: dict[str, dict[str, Any]]
    client_json: str
    runs_table_rows: str
    total_tests_count: int = 0


def get_solution_code_and_meta(
    model: str, bench_id: str, level_id: str, answers_root: Path = ROOT / "models_answers"
) -> tuple[str | None, str, int, str | None]:
    b = BY_ID.get(bench_id)
    ext = b.file_ext if b else "txt"
    key_safe = model.replace("/", "_").replace(":", "_").replace("@", "_")
    filename = f"{key_safe}_{bench_id}_{level_id}.{ext}"
    p = answers_root / filename
    code = None
    if p.exists():
        try:
            code = p.read_text(encoding="utf-8")
        except Exception:
            pass

    reasoning_text = None
    reasoning_path = p.with_suffix(".reasoning.txt")
    if reasoning_path.exists():
        try:
            reasoning_text = reasoning_path.read_text(encoding="utf-8")
        except Exception:
            pass

    return code, ext, len(code.splitlines()) if code else 0, reasoning_text


def load_leaderboard_data(conn) -> tuple[list[dict[str, Any]], int]:
    # Joined strictly by run_id to avoid multi-host Cartesian product
    rows = conn.execute("""
        SELECT r.run_id, r.model, r.benchmark, r.level, r.tested_at, r.passed, r.total, r.failures,
               s.tokens_per_second, s.time_to_first_token_seconds, s.reasoning_output_tokens,
               COALESCE(s.host_id, run.host_id) AS host_id,
               run.quantization, run.backend, run.generation_params
        FROM results r
        JOIN runs run ON r.run_id = run.id
        LEFT JOIN speed_results s
          ON r.run_id = s.run_id AND r.benchmark = s.benchmark AND r.level = s.level
        ORDER BY r.model, r.tested_at DESC
    """).fetchall()

    models_data: dict[str, dict] = {}
    for r in rows:
        m = r["model"]
        if m not in models_data:
            models_data[m] = {
                "results": {},
                "total_passed": 0,
                "total_tests": 0,
                "speeds": [],
                "total_reasoning_tokens": 0,
                "latest_test": r["tested_at"],
                "quantization": r["quantization"],
                "backend": r["backend"],
            }
        key = (r["benchmark"], r["level"])
        if key in models_data[m]["results"]:
            continue

        pct = (r["passed"] / r["total"] * 100) if r["total"] and r["total"] > 0 else 0.0
        failures = json.loads(r["failures"]) if r["failures"] else []

        models_data[m]["results"][key] = {
            "benchmark": r["benchmark"],
            "level": r["level"],
            "passed": r["passed"],
            "total": r["total"],
            "percent": pct,
            "failures": failures,
            "tok_per_sec": r["tokens_per_second"],
            "ttft": r["time_to_first_token_seconds"],
            "reasoning_tokens": r["reasoning_output_tokens"],
            "tested_at": r["tested_at"],
            "quantization": r["quantization"],
            "backend": r["backend"],
            "run_id": r["run_id"],
        }
        models_data[m]["total_passed"] += r["passed"]
        models_data[m]["total_tests"] += r["total"]
        if r["tokens_per_second"]:
            models_data[m]["speeds"].append(r["tokens_per_second"])
        if r["reasoning_output_tokens"]:
            models_data[m]["total_reasoning_tokens"] += r["reasoning_output_tokens"]

    leaderboard = []
    for m, d in models_data.items():
        avg_pct = (d["total_passed"] / d["total_tests"] * 100) if d["total_tests"] > 0 else 0.0
        avg_speed = (sum(d["speeds"]) / len(d["speeds"])) if d["speeds"] else None
        leaderboard.append(
            {
                "model": m,
                "avg_pct": avg_pct,
                "passed": d["total_passed"],
                "total": d["total_tests"],
                "tests_count": len(d["results"]),
                "avg_speed": avg_speed,
                "total_reasoning_tokens": d["total_reasoning_tokens"],
                "quantization": d.get("quantization"),
                "backend": d.get("backend"),
                "data": d,
            }
        )
    leaderboard.sort(key=lambda x: (x["avg_pct"], x["tests_count"]), reverse=True)
    return leaderboard, len(rows)


def load_runs_history(conn) -> tuple[list[dict[str, Any]], str]:
    runs_rows = conn.execute("""
        SELECT r.id, r.host_id, h.label AS host_label, r.model_key, r.model_name,
               r.quantization, r.backend, r.generation_params, r.suite_version,
               r.started_at, r.completed_at, r.status,
               COUNT(res.benchmark) as tests_completed,
               AVG(CASE WHEN res.total > 0 THEN (res.passed * 100.0 / res.total) ELSE 0 END) as avg_score,
               AVG(s.tokens_per_second) as avg_speed
        FROM runs r
        LEFT JOIN hosts h ON r.host_id = h.id
        LEFT JOIN results res ON r.id = res.run_id
        LEFT JOIN speed_results s ON r.id = s.run_id AND res.benchmark = s.benchmark AND res.level = s.level
        GROUP BY r.id
        ORDER BY r.started_at DESC
    """).fetchall()

    runs_data = []
    runs_table_rows = ""
    for r in runs_rows:
        params = {}
        if r["generation_params"]:
            try:
                params = (
                    json.loads(r["generation_params"])
                    if isinstance(r["generation_params"], str)
                    else r["generation_params"]
                )
            except Exception:
                params = {}

        temp_str = f"temp={params.get('temperature', '—')}"
        seed_str = f"seed={params.get('seed', '—')}"
        max_t_str = f"max={params.get('max_tokens', '—')}"
        hp_summary = f"{temp_str}, {seed_str}, {max_t_str}"

        art = params.get("artifact", {})
        art_parts = []
        if art.get("architecture"):
            art_parts.append(str(art["architecture"]))
        if art.get("size_bytes"):
            art_parts.append(f"{art['size_bytes'] / (1024**3):.1f} GB")
        if art.get("format"):
            art_parts.append(str(art["format"]))
        art_summary = " | ".join(art_parts) if art_parts else "—"

        status_color = (
            "var(--green)"
            if r["status"] == "completed"
            else "var(--yellow)"
            if r["status"] == "in_progress"
            else "var(--red)"
        )
        avg_speed_val = round(r["avg_speed"], 1) if r["avg_speed"] is not None else None
        speed_text = f"{avg_speed_val} tok/s" if avg_speed_val else "—"

        run_item = {
            "id": r["id"],
            "host_id": r["host_id"],
            "host_label": r["host_label"] or r["host_id"],
            "model_key": r["model_key"],
            "model_name": r["model_name"] or r["model_key"],
            "quantization": r["quantization"] or "—",
            "backend": r["backend"] or "—",
            "suite_version": r["suite_version"] or "—",
            "started_at": r["started_at"],
            "completed_at": r["completed_at"] or "—",
            "status": r["status"],
            "tests_completed": r["tests_completed"],
            "avg_score": round(r["avg_score"], 1) if r["avg_score"] is not None else 0.0,
            "avg_speed": avg_speed_val,
            "hp_summary": hp_summary,
            "art_summary": art_summary,
            "generation_params": params,
        }
        runs_data.append(run_item)

        runs_table_rows += f"""
          <tr>
            <td style="font-family:monospace; font-size:12px; color:var(--accent); font-weight:600;">{html.escape(r["id"])}</td>
            <td style="color:var(--text-muted); font-size:13px;">{html.escape(r["started_at"])}</td>
            <td style="font-weight:600; color:#f0f6fc;">{html.escape(r["model_key"])}</td>
            <td><span class="badge" style="background:#21262d; color:#58a6ff; border:1px solid #30363d;">{html.escape(run_item["quantization"])}</span></td>
            <td style="font-size:13px; color:var(--text-muted);">{html.escape(run_item["host_label"])}</td>
            <td style="font-size:13px;">{html.escape(run_item["backend"])}</td>
            <td style="font-size:12px; color:var(--text-muted); line-height:1.4;">
              <span style="color:#e6edf3; font-weight:500;">{html.escape(hp_summary)}</span><br>
              <span style="font-size:11px; opacity:0.8;">{html.escape(art_summary)}</span>
            </td>
            <td>{r["tests_completed"]}</td>
            <td><span style="font-weight:600;">{run_item["avg_score"]}%</span></td>
            <td style="color:var(--text-muted); font-weight:500;">{speed_text}</td>
            <td><span style="color:{status_color}; font-weight:600; font-size:12px; text-transform:uppercase;">{html.escape(r["status"])}</span></td>
          </tr>"""

    return runs_data, runs_table_rows


def load_hardware_matrix(conn) -> tuple[dict[str, Any], dict[str, dict[str, Any]], list[Any]]:
    hosts_rows = conn.execute("SELECT id, label, created_at FROM hosts ORDER BY created_at").fetchall()
    speed_matrix_rows = conn.execute("""
        SELECT s.model, s.host_id,
               AVG(s.tokens_per_second) AS avg_tps,
               AVG(s.time_to_first_token_seconds) AS avg_ttft,
               COUNT(*) AS cnt
        FROM speed_results s
        GROUP BY s.model, s.host_id
    """).fetchall()

    device_stats = {}
    for h in hosts_rows:
        device_stats[h["id"]] = {"label": h["label"], "tps_list": [], "count": 0}

    model_host_matrix: dict[str, dict[str, Any]] = {}
    for r in speed_matrix_rows:
        m = r["model"]
        hid = r["host_id"]
        if m not in model_host_matrix:
            model_host_matrix[m] = {}
        model_host_matrix[m][hid] = {
            "tps": r["avg_tps"],
            "ttft": r["avg_ttft"],
            "count": r["cnt"],
        }
        if hid in device_stats and r["avg_tps"]:
            device_stats[hid]["tps_list"].append(r["avg_tps"])
            device_stats[hid]["count"] += r["cnt"]

    active_hosts = [h for h in hosts_rows if h["id"] in device_stats and device_stats[h["id"]]["count"] > 0]
    return device_stats, model_host_matrix, active_hosts


def load_report_data(db: Database) -> ReportData:
    conn = db.conn
    leaderboard, total_tests = load_leaderboard_data(conn)
    runs_data, runs_table_rows = load_runs_history(conn)
    device_stats, model_host_matrix, active_hosts = load_hardware_matrix(conn)

    # Prepare client-side payload
    client_models_payload = {}
    for entry in leaderboard:
        m = entry["model"]
        res_dict = {}
        for (b_id, l_id), res in entry["data"]["results"].items():
            code, ext, lines_count, reasoning_text = get_solution_code_and_meta(m, b_id, l_id)
            res_dict[f"{b_id}/{l_id}"] = {
                "passed": res["passed"],
                "total": res["total"],
                "percent": round(res["percent"], 1),
                "failures": res["failures"],
                "tok_per_sec": round(res["tok_per_sec"], 1) if res["tok_per_sec"] else None,
                "ttft": round(res["ttft"], 2) if res["ttft"] else None,
                "reasoning_tokens": res.get("reasoning_tokens"),
                "reasoning_text": reasoning_text,
                "code": code,
                "ext": ext,
                "lines": lines_count,
            }
        client_models_payload[m] = {
            "avg_pct": round(entry["avg_pct"], 1),
            "passed": entry["passed"],
            "total": entry["total"],
            "tests_count": entry["tests_count"],
            "avg_speed": round(entry["avg_speed"], 1) if entry["avg_speed"] else None,
            "total_reasoning_tokens": entry.get("total_reasoning_tokens", 0),
            "results": res_dict,
        }

    benchmarks_metadata = []
    for b in REGISTRY:
        benchmarks_metadata.append(
            {
                "id": b.id,
                "short": b.short,
                "name": b.name,
                "lang": b.code_lang,
                "ext": b.file_ext,
                "levels": [{"id": level.id, "name": level.name} for level in b.levels],
            }
        )

    client_json = json.dumps(
        {
            "models": client_models_payload,
            "benchmarks": benchmarks_metadata,
            "runs": runs_data,
        },
        ensure_ascii=False,
    )

    return ReportData(
        leaderboard=leaderboard,
        runs_data=runs_data,
        active_hosts=active_hosts,
        device_stats=device_stats,
        model_host_matrix=model_host_matrix,
        client_json=client_json,
        runs_table_rows=runs_table_rows,
        total_tests_count=total_tests,
    )
