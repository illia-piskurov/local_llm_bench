"""Data access and analytics layer for benchmark reporting.

Extracts test results, hardware metrics, and run history from SQLite,
aggregating them into structured domain objects decoupled from HTML presentation.

Scoring contract (shared by the leaderboard, model deep-dive and run history):
- A task is one (benchmark, level) pair; every task weighs the same.
- A scored task contributes ``passed / total * 100``.
- A truncated or failed generation contributes 0% (it must never raise a model's score).
- A pure ``[INFRA FAILURE]`` (a harness problem, not the model's fault) is excluded and only flagged.
"""

import html
import json
import math
import re
import statistics
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from benchmarks import BY_ID, REGISTRY
from database import Database
from storage import detect_quantization, failure_kind

ROOT = Path(__file__).parent

ALL = "*"
TOTAL_TASKS = sum(len(b.levels) for b in REGISTRY)
# Models that completed less of the suite are listed separately instead of being ranked.
MIN_COVERAGE = 0.75
# Speed cells backed by fewer samples are shown dimmed and never get the "fastest" mark.
MIN_SPEED_SAMPLES = 3


@dataclass
class ReportData:
    leaderboard: list[dict[str, Any]]
    runs_data: list[dict[str, Any]]
    hosts: list[dict[str, Any]]
    device_stats: dict[str, Any]
    matrix: list[dict[str, Any]]
    client_json: str
    blobs_json: str
    runs_table_rows: str
    total_tests_count: int = 0


def backend_family(backend: str | None) -> str:
    """Strips the version/build suffix: 'Ollama v0.40.14' -> 'Ollama', 'LM Studio (69d945a)' -> 'LM Studio'."""
    if not backend:
        return "unknown"
    family = re.sub(r"\s*(?:\(.*\)|v?\d[\w.\-]*)\s*$", "", backend.strip())
    return family or backend.strip()


def split_host_label(label: str) -> dict[str, str]:
    """Splits a 'chip | memory | gpu' host label into parts for display."""
    parts = [p.strip() for p in (label or "").split("|")]
    return {
        "chip": parts[0] if parts else "",
        "memory": parts[1] if len(parts) > 1 else "",
        "gpu": parts[2] if len(parts) > 2 else "",
    }


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


def _loads(raw: Any, default: Any) -> Any:
    if not raw:
        return default
    if not isinstance(raw, str):
        return raw
    try:
        return json.loads(raw)
    except Exception:
        return default


def task_percent(kind: str | None, passed: int | None, total: int | None) -> float | None:
    """Score of one task in percent, or None when it must be excluded (pure infra failure)."""
    if kind == "infra":
        return None
    if kind in ("truncated", "failed"):
        return 0.0
    return (passed / total * 100) if total and total > 0 and passed is not None else 0.0


def weighted_tps(samples: list[tuple[float | None, int | None]]) -> float | None:
    """Throughput over (tokens_per_second, output_tokens) samples.

    Token-weighted (total tokens / total generation time) so long generations count more than
    short ones; falls back to a plain mean when token counts are missing.
    """
    valid = [(tps, tok) for tps, tok in samples if tps and tps > 0]
    if not valid:
        return None
    with_tokens = [(tps, tok) for tps, tok in valid if tok and tok > 0]
    if with_tokens:
        return sum(tok for _, tok in with_tokens) / sum(tok / tps for tps, tok in with_tokens)
    return sum(tps for tps, _ in valid) / len(valid)


def load_result_rows(conn) -> list[dict[str, Any]]:
    """All results, newest first, joined strictly by run_id to avoid a multi-host Cartesian product."""
    rows = conn.execute("""
        SELECT r.run_id, r.model, r.benchmark, r.level, r.tested_at, r.passed, r.total, r.failures,
               s.tokens_per_second, s.time_to_first_token_seconds, s.reasoning_output_tokens,
               s.total_output_tokens,
               run.host_id AS host_id, run.quantization, run.backend, run.generation_params
        FROM results r
        JOIN runs run ON r.run_id = run.id
        LEFT JOIN speed_results s
          ON r.run_id = s.run_id AND r.benchmark = s.benchmark AND r.level = s.level
        ORDER BY r.tested_at DESC
    """).fetchall()

    result = []
    for r in rows:
        failures = _loads(r["failures"], [])
        kind = failure_kind(failures)
        result.append(
            {
                "run_id": r["run_id"],
                "model": r["model"],
                "benchmark": r["benchmark"],
                "level": r["level"],
                "tested_at": r["tested_at"],
                "passed": r["passed"],
                "total": r["total"],
                "failures": failures,
                "kind": kind,
                "percent": task_percent(kind, r["passed"], r["total"]),
                "tok_per_sec": r["tokens_per_second"],
                "ttft": r["time_to_first_token_seconds"],
                "reasoning_tokens": r["reasoning_output_tokens"],
                "output_tokens": r["total_output_tokens"],
                "host_id": r["host_id"],
                "quantization": r["quantization"],
                "backend": r["backend"],
                "backend_family": backend_family(r["backend"]),
            }
        )
    return result


def build_leaderboard(rows: list[dict[str, Any]], host: str = ALL, backend: str = ALL) -> list[dict[str, Any]]:
    """Leaderboard over the newest result of every (model, task), optionally limited to a host / backend."""
    latest: dict[tuple[str, str, str], dict[str, Any]] = {}
    for r in rows:  # rows are newest first, so the first one seen wins
        if host != ALL and r["host_id"] != host:
            continue
        if backend != ALL and r["backend_family"] != backend:
            continue
        latest.setdefault((r["model"], r["benchmark"], r["level"]), r)

    by_model: dict[str, list[dict[str, Any]]] = {}
    for (model, _, _), r in latest.items():
        by_model.setdefault(model, []).append(r)

    leaderboard = []
    for model, rs in by_model.items():
        scored = [r for r in rs if r["kind"] != "infra"]
        pcts = [r["percent"] for r in scored]
        avg_pct = sum(pcts) / len(pcts) if pcts else 0.0
        genuine = [r for r in scored if r["kind"] is None and r["total"]]

        samples_by_host: dict[str, list[tuple[float | None, int | None]]] = {}
        for r in rs:
            if r["tok_per_sec"]:
                samples_by_host.setdefault(r["host_id"], []).append((r["tok_per_sec"], r["output_tokens"]))
        speed_by_host = {h: tps for h, s in samples_by_host.items() if (tps := weighted_tps(s)) is not None}
        if host != ALL:
            avg_speed = speed_by_host.get(host)
        else:
            avg_speed = statistics.median(speed_by_host.values()) if speed_by_host else None

        newest = max(rs, key=lambda r: r["tested_at"])
        coverage = len(scored) / TOTAL_TASKS if TOTAL_TASKS else 0.0
        leaderboard.append(
            {
                "model": model,
                "avg_pct": avg_pct,
                "passed": sum(r["passed"] for r in genuine),
                "total": sum(r["total"] for r in genuine),
                "tests_count": len(scored),
                "coverage": coverage,
                "ranked": coverage >= MIN_COVERAGE,
                "truncated": sum(1 for r in rs if r["kind"] == "truncated"),
                "failed": sum(1 for r in rs if r["kind"] == "failed"),
                "infra": sum(1 for r in rs if r["kind"] == "infra"),
                "avg_speed": avg_speed,
                "speed_by_host": speed_by_host,
                "total_reasoning_tokens": sum(r["reasoning_tokens"] or 0 for r in rs),
                "quantization": newest["quantization"] or detect_quantization(model),
                "backend": newest["backend_family"],
                "backends": sorted({r["backend_family"] for r in rs}),
                "hosts": sorted({r["host_id"] for r in rs}),
                "tasks": {f"{r['benchmark']}/{r['level']}": r for r in rs},
            }
        )
    leaderboard.sort(key=lambda x: (x["ranked"], x["avg_pct"], x["tests_count"]), reverse=True)
    return leaderboard


def load_leaderboard_data(conn) -> tuple[list[dict[str, Any]], int]:
    rows = load_result_rows(conn)
    return build_leaderboard(rows), len(rows)


def _run_params_summary(params: dict[str, Any]) -> tuple[str, str]:
    hp_summary = (
        f"temp={params.get('temperature', '—')}, seed={params.get('seed', '—')}, max={params.get('max_tokens', '—')}"
    )
    art = params.get("artifact") or {}
    art_parts = []
    if art.get("architecture"):
        art_parts.append(str(art["architecture"]))
    if art.get("size_bytes"):
        art_parts.append(f"{art['size_bytes'] / (1024**3):.1f} GB")
    if art.get("format"):
        art_parts.append(str(art["format"]))
    return hp_summary, " | ".join(art_parts) if art_parts else "—"


def load_runs_history(conn) -> tuple[list[dict[str, Any]], str]:
    runs_rows = conn.execute("""
        SELECT r.id, r.host_id, h.label AS host_label, r.model_key, r.model_name,
               r.quantization, r.backend, r.generation_params, r.suite_version,
               r.started_at, r.completed_at, r.status
        FROM runs r
        LEFT JOIN hosts h ON r.host_id = h.id
        ORDER BY r.started_at DESC
    """).fetchall()

    per_run: dict[str, list[dict[str, Any]]] = {}
    for res in conn.execute("""
        SELECT res.run_id, res.passed, res.total, res.failures,
               s.tokens_per_second, s.total_output_tokens
        FROM results res
        LEFT JOIN speed_results s
          ON res.run_id = s.run_id AND res.benchmark = s.benchmark AND res.level = s.level
    """).fetchall():
        kind = failure_kind(_loads(res["failures"], []))
        per_run.setdefault(res["run_id"], []).append(
            {
                "kind": kind,
                "percent": task_percent(kind, res["passed"], res["total"]),
                "tps": res["tokens_per_second"],
                "tokens": res["total_output_tokens"],
            }
        )

    runs_data = []
    runs_table_rows = ""
    for r in runs_rows:
        params = _loads(r["generation_params"], {})
        if not isinstance(params, dict):
            params = {}
        hp_summary, art_summary = _run_params_summary(params)

        rs = per_run.get(r["id"], [])
        pcts = [x["percent"] for x in rs if x["percent"] is not None]
        avg_score = round(sum(pcts) / len(pcts), 1) if pcts else None
        tests_completed = sum(1 for x in rs if x["kind"] is None)
        tests_truncated = sum(1 for x in rs if x["kind"] in ("truncated", "failed"))
        speed = weighted_tps([(x["tps"], x["tokens"]) for x in rs])
        avg_speed_val = round(speed, 1) if speed is not None else None

        status_color = (
            "var(--green)"
            if r["status"] == "completed"
            else "var(--yellow)"
            if r["status"] == "in_progress"
            else "var(--red)"
        )
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
            "tests_completed": tests_completed,
            "tests_truncated": tests_truncated,
            "avg_score": avg_score,
            "avg_speed": avg_speed_val,
            "hp_summary": hp_summary,
            "art_summary": art_summary,
            "generation_params": params,
        }
        runs_data.append(run_item)

        score_text = f"{avg_score}%" if avg_score is not None else "—"
        speed_text = f"{avg_speed_val} tok/s" if avg_speed_val else "—"
        trunc_note = (
            f' <span style="color:var(--yellow); font-size:11px;" title="truncated or failed generations (scored 0%)">'
            f"✂ {tests_truncated}</span>"
            if tests_truncated
            else ""
        )
        runs_table_rows += f"""
          <tr>
            <td style="font-family:monospace; font-size:12px; color:var(--accent); font-weight:600;">{html.escape(r["id"])}</td>
            <td style="color:var(--text-muted); font-size:13px;">{html.escape(r["started_at"] or "")}</td>
            <td style="font-weight:600; color:#f0f6fc;">{html.escape(r["model_key"])}</td>
            <td><span class="badge" style="background:#21262d; color:#58a6ff; border:1px solid #30363d;">{html.escape(run_item["quantization"])}</span></td>
            <td style="font-size:13px; color:var(--text-muted);">{html.escape(run_item["host_label"])}</td>
            <td style="font-size:13px;">{html.escape(run_item["backend"])}</td>
            <td style="font-size:12px; color:var(--text-muted); line-height:1.4;">
              <span style="color:#e6edf3; font-weight:500;">{html.escape(hp_summary)}</span><br>
              <span style="font-size:11px; opacity:0.8;">{html.escape(art_summary)}</span>
            </td>
            <td data-v="{tests_completed}">{tests_completed}{trunc_note}</td>
            <td data-v="{avg_score if avg_score is not None else ""}"><span style="font-weight:600;">{score_text}</span></td>
            <td data-v="{avg_speed_val or ""}" style="color:var(--text-muted); font-weight:500;">{speed_text}</td>
            <td><span style="color:{status_color}; font-weight:600; font-size:12px; text-transform:uppercase;">{html.escape(r["status"])}</span></td>
          </tr>"""

    return runs_data, runs_table_rows


def load_hardware_matrix(conn) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    """Speed matrix keyed by (model, backend, quantization, context) so unlike setups are never averaged together."""
    hosts_rows = conn.execute("SELECT id, label, created_at FROM hosts ORDER BY created_at").fetchall()
    speed_rows = conn.execute("""
        SELECT s.model, s.host_id, s.tokens_per_second, s.time_to_first_token_seconds, s.total_output_tokens,
               run.backend, run.quantization, run.generation_params
        FROM speed_results s
        JOIN runs run ON run.id = s.run_id
    """).fetchall()

    variants: dict[tuple, dict[str, Any]] = {}
    samples: dict[tuple[tuple, str], list[dict[str, Any]]] = {}
    for r in speed_rows:
        params = _loads(r["generation_params"], {})
        ctx = params.get("context_length") if isinstance(params, dict) else None
        quant = r["quantization"] or detect_quantization(r["model"]) or "—"
        key = (r["model"], backend_family(r["backend"]), quant, ctx)
        variants.setdefault(
            key, {"model": r["model"], "backend": key[1], "quantization": quant, "ctx": ctx, "cells": {}}
        )
        samples.setdefault((key, r["host_id"]), []).append(r)

    for (key, host_id), rs in samples.items():
        tps = weighted_tps([(x["tokens_per_second"], x["total_output_tokens"]) for x in rs])
        ttfts = [x["time_to_first_token_seconds"] for x in rs if x["time_to_first_token_seconds"] is not None]
        variants[key]["cells"][host_id] = {
            "tps": tps,
            "ttft": sum(ttfts) / len(ttfts) if ttfts else None,
            "count": len(rs),
        }

    matrix = sorted(variants.values(), key=lambda v: (v["model"], v["backend"], v["quantization"], v["ctx"] or 0))

    # Speed index: geometric mean of a host's speed relative to the average of the hosts that ran the same variant,
    # so a host that only ran small models is not mistaken for a fast one.
    ratios: dict[str, list[float]] = {}
    for v in matrix:
        eligible = {h: c["tps"] for h, c in v["cells"].items() if c["tps"] and c["count"] >= MIN_SPEED_SAMPLES}
        v["fastest_host"] = max(eligible, key=eligible.get) if len(eligible) >= 2 else None
        if len(eligible) >= 2:
            mean_tps = sum(eligible.values()) / len(eligible)
            for h, tps in eligible.items():
                ratios.setdefault(h, []).append(tps / mean_tps)

    device_stats: dict[str, Any] = {}
    for h in hosts_rows:
        tps_list = [v["cells"][h["id"]]["tps"] for v in matrix if h["id"] in v["cells"] and v["cells"][h["id"]]["tps"]]
        count = sum(v["cells"][h["id"]]["count"] for v in matrix if h["id"] in v["cells"])
        rs = ratios.get(h["id"], [])
        device_stats[h["id"]] = {
            "label": h["label"],
            **split_host_label(h["label"]),
            "median_tps": statistics.median(tps_list) if tps_list else None,
            "variants": len(tps_list),
            "count": count,
            "index": math.exp(sum(math.log(x) for x in rs) / len(rs)) if rs else None,
            "index_variants": len(rs),
        }

    active_hosts = [{"id": h["id"], "label": h["label"]} for h in hosts_rows if device_stats[h["id"]]["count"] > 0]
    return device_stats, matrix, active_hosts


def load_report_data(db: Database) -> ReportData:
    conn = db.conn
    rows = load_result_rows(conn)
    leaderboard = build_leaderboard(rows)
    runs_data, runs_table_rows = load_runs_history(conn)
    device_stats, matrix, active_hosts = load_hardware_matrix(conn)

    # Leaderboards for every host / backend filter combination, so the page only switches between them.
    host_ids = sorted({r["host_id"] for r in rows})
    backends = sorted({r["backend_family"] for r in rows})
    leaderboards: dict[str, list[dict[str, Any]]] = {}
    for h in [ALL, *host_ids]:
        for b in [ALL, *backends]:
            entries = leaderboard if (h, b) == (ALL, ALL) else build_leaderboard(rows, h, b)
            if entries:
                leaderboards[f"{h}|{b}"] = [
                    {k: v for k, v in e.items() if k != "tasks"} | {"thinker": e["total_reasoning_tokens"] > 0}
                    for e in entries
                ]

    models_payload: dict[str, Any] = {}
    blobs: dict[str, dict[str, Any]] = {}
    for entry in leaderboard:
        m = entry["model"]
        res_dict = {}
        for key, res in entry["tasks"].items():
            code, ext, lines_count, reasoning_text = get_solution_code_and_meta(m, res["benchmark"], res["level"])
            res_dict[key] = {
                "status": res["kind"] or "ok",
                "passed": res["passed"],
                "total": res["total"],
                "percent": round(res["percent"], 1) if res["percent"] is not None else 0.0,
                "failures": res["failures"],
                "tok_per_sec": round(res["tok_per_sec"], 1) if res["tok_per_sec"] else None,
                "ttft": round(res["ttft"], 2) if res["ttft"] else None,
                "reasoning_tokens": res["reasoning_tokens"],
                "ext": ext,
                "lines": lines_count,
                "has_code": bool(code),
                "has_reasoning": bool(reasoning_text),
                "host_id": res["host_id"],
                "backend": res["backend_family"],
                "quantization": res["quantization"] or "—",
                "tested_at": res["tested_at"],
            }
            if code or reasoning_text:
                blobs.setdefault(m, {})[key] = {"code": code, "reasoning_text": reasoning_text}
        models_payload[m] = {
            "avg_pct": round(entry["avg_pct"], 1),
            "passed": entry["passed"],
            "total": entry["total"],
            "tests_count": entry["tests_count"],
            "coverage": entry["coverage"],
            "ranked": entry["ranked"],
            "truncated": entry["truncated"],
            "failed": entry["failed"],
            "avg_speed": round(entry["avg_speed"], 1) if entry["avg_speed"] else None,
            "total_reasoning_tokens": entry["total_reasoning_tokens"],
            "results": res_dict,
        }

    benchmarks_metadata = [
        {
            "id": b.id,
            "short": b.short,
            "name": b.name,
            "lang": b.code_lang,
            "ext": b.file_ext,
            "levels": [{"id": level.id, "name": level.name} for level in b.levels],
        }
        for b in REGISTRY
    ]

    client_json = json.dumps(
        {
            "models": models_payload,
            "benchmarks": benchmarks_metadata,
            "runs": runs_data,
            "hosts": [{"id": h["id"], "label": h["label"]} for h in active_hosts],
            "all_host_labels": {hid: d["label"] for hid, d in device_stats.items()},
            "backends": backends,
            "leaderboards": leaderboards,
            "devices": device_stats,
            "matrix": matrix,
            "total_tasks": TOTAL_TASKS,
            "min_coverage": MIN_COVERAGE,
            "min_speed_samples": MIN_SPEED_SAMPLES,
        },
        ensure_ascii=False,
    )
    blobs_json = json.dumps(blobs, ensure_ascii=False)
    # Sanitize < to < to prevent premature </script> closing or inline HTML injection in <script> blocks
    client_json = client_json.replace("<", "\\u003c")
    blobs_json = blobs_json.replace("<", "\\u003c")

    return ReportData(
        leaderboard=leaderboard,
        runs_data=runs_data,
        hosts=active_hosts,
        device_stats=device_stats,
        matrix=matrix,
        client_json=client_json,
        blobs_json=blobs_json,
        runs_table_rows=runs_table_rows,
        total_tests_count=sum(e["tests_count"] + e["infra"] for e in leaderboard),
    )
