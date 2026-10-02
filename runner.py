"""Benchmark test runner engine.

Orchestrates model querying, multi-turn level dependencies, code extraction,
sandboxed test execution, and run session tracking.
"""

import json
from datetime import datetime
from pathlib import Path

from rich.console import Console

import lmstudio
from benchmarks.base import Benchmark, GenerationStats, SpeedSample, StoredResult, TestResult
from database import Database
from host_configs import HostConfig
from html_report import generate_html_report
from lmstudio import GenerationConfig, Model, get_model_artifact_info
from storage import (
    ResultStore,
    RunStore,
    SpeedResultStore,
    compute_suite_hash,
    detect_backend,
    detect_quantization,
    get_suite_version,
)

ROOT = Path(__file__).parent
_default_console = Console(legacy_windows=False)
_default_db = Database(ROOT / "bench.db")
_default_store = ResultStore(db=_default_db, answers_root=ROOT, raw_answers_dir=ROOT / "raw_answers")
_default_speed_store = SpeedResultStore(_default_db)
_default_run_store = RunStore(_default_db)


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def ensure_level_answer(
    model: Model,
    benchmark: Benchmark,
    level_id: str,
    host: HostConfig,
    run_id: str | None = None,
    force: bool = False,
    gen_config: GenerationConfig | None = None,
    store: ResultStore | None = None,
    speed_store: SpeedResultStore | None = None,
    console: Console | None = None,
) -> Path | None:
    store = store or _default_store
    speed_store = speed_store or _default_speed_store
    console = console or _default_console

    level = benchmark.level_by_id(level_id)
    answer_path, raw_path = store.paths_for(benchmark, model.key, level_id)

    if not force and answer_path.exists() and store.has_result(benchmark, model.key, level_id, run_id=run_id):
        return answer_path

    messages = []
    if level.requires:
        prev_answer = ensure_level_answer(
            model,
            benchmark,
            level.requires,
            host,
            run_id=run_id,
            force=False,
            gen_config=gen_config,
            store=store,
            speed_store=speed_store,
            console=console,
        )
        if prev_answer is None:
            return None
        _, prev_raw = store.paths_for(benchmark, model.key, level.requires)
        prev_content = prev_raw.read_text(encoding="utf-8") if prev_raw.exists() else ""
        messages.append({"role": "user", "content": benchmark.level_by_id(level.requires).prompt})
        messages.append({"role": "assistant", "content": prev_content})

    messages.append({"role": "user", "content": level.prompt})

    try:
        response = lmstudio.ask_model(model.key, messages, config=gen_config)
    except TimeoutError as e:
        console.print(f"    [bold red]Inference timeout error:[/bold red] {e}")
        return None
    except Exception as e:
        console.print(f"    [red]Inference API error:[/red] {e}")
        return None

    raw_path.write_text(response.content, encoding="utf-8")
    if response.reasoning:
        raw_path.with_suffix(".reasoning.txt").write_text(response.reasoning, encoding="utf-8")
    if response.raw:
        raw_path.with_suffix(".api.json").write_text(
            json.dumps(response.raw, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    # Save speed stats
    if response.stats:
        stats = GenerationStats.from_dict(response.stats)
        if stats and stats.tokens_per_second:
            sample = SpeedSample(
                host_id=host.id,
                host_label=host.label,
                model=model.key,
                benchmark=benchmark.id,
                level=level_id,
                tested_at=now_str(),
                stats=stats,
            )
            speed_store.save(sample, run_id=run_id)

    code = benchmark.extract_code(response.content)
    answer_path.write_text(code, encoding="utf-8")
    return answer_path


def execute_test(
    model: Model,
    benchmark: Benchmark,
    level_id: str,
    host: HostConfig,
    run_id: str | None = None,
    force: bool = False,
    gen_config: GenerationConfig | None = None,
    store: ResultStore | None = None,
    speed_store: SpeedResultStore | None = None,
    db: Database | None = None,
    console: Console | None = None,
) -> bool:
    store = store or _default_store
    speed_store = speed_store or _default_speed_store
    db = db or _default_db
    console = console or _default_console

    level = benchmark.level_by_id(level_id)
    tag = f"[bold cyan]{benchmark.short}[/bold cyan] / [bold]{level.name}[/bold]"

    if not force and store.has_result(benchmark, model.key, level_id, run_id=run_id):
        res = store.load(benchmark, model.key, level_id, run_id=run_id)
        pct = res.percent() if res else 0
        pct_color = "green" if pct >= 80 else "yellow" if pct >= 50 else "red"
        console.print(
            f"  ⏭  {tag} -> [dim]skipped (already passed:[/dim] [{pct_color}]{res.format()}[/{pct_color}][dim])[/dim]"
        )
        return True

    console.print(f"  ⏳ {tag} ... waiting for generation...", end="\r")

    answer_path = ensure_level_answer(
        model,
        benchmark,
        level_id,
        host,
        run_id=run_id,
        force=force,
        gen_config=gen_config,
        store=store,
        speed_store=speed_store,
        console=console,
    )

    if answer_path is None or not answer_path.exists():
        console.print(f"  ❌ {tag} -> [red]Failed to get response from model (timeout or error)[/red]")
        if run_id:
            test_result = TestResult(0, 1, ["Model generation failed or timed out"])
            stored = StoredResult(
                model=model.key,
                benchmark=benchmark.id,
                level=level_id,
                tested_at=now_str(),
                evaluation=test_result,
            )
            store.save(benchmark, model.key, level_id, stored, run_id=run_id)
        return False

    # Speed & reasoning metrics
    speed_query = """
        SELECT tokens_per_second, time_to_first_token_seconds, reasoning_output_tokens
        FROM speed_results
        WHERE model = ? AND benchmark = ? AND level = ?
    """
    params: list = [model.key, benchmark.id, level_id]
    if run_id:
        speed_query += " AND run_id = ?"
        params.append(run_id)
    speed_query += " ORDER BY tested_at DESC LIMIT 1"
    speed_row = db.conn.execute(speed_query, params).fetchone()

    speed_info = ""
    if speed_row and speed_row["tokens_per_second"]:
        think_info = ""
        if speed_row["reasoning_output_tokens"]:
            think_info = f" | [magenta]🧠 {speed_row['reasoning_output_tokens']} think tok[/magenta]"
        speed_info = f"[dim]({speed_row['tokens_per_second']:.1f} tok/s | TTFT {speed_row['time_to_first_token_seconds']:.2f}s{think_info})[/dim] "

    # Run tests
    try:
        test_result = benchmark.run_tests(level_id, answer_path)
    except Exception as e:
        test_result = TestResult(0, 1, [f"Test runner exception: {e}"])

    stored = StoredResult(
        model=model.key,
        benchmark=benchmark.id,
        level=level_id,
        tested_at=now_str(),
        evaluation=test_result,
    )
    store.save(benchmark, model.key, level_id, stored, run_id=run_id)

    pct = test_result.percent()
    if pct >= 80:
        icon = "[green]✅[/green]"
        score_styled = f"[bold green]{test_result.format()} ({pct:.0f}%)[/bold green]"
    elif pct >= 40:
        icon = "[yellow]⚠️[/yellow]"
        score_styled = f"[bold yellow]{test_result.format()} ({pct:.0f}%)[/bold yellow]"
    else:
        icon = "[red]❌[/red]"
        score_styled = f"[bold red]{test_result.format()} ({pct:.0f}%)[/bold red]"

    fail_summary = ""
    if test_result.failures:
        first_fail = test_result.failures[0].split("\n")[0]
        if len(first_fail) > 60:
            first_fail = first_fail[:57] + "..."
        fail_summary = f" [dim red]FAIL: {first_fail}[/dim red]"

    console.print(f"  {icon} {tag} -> {score_styled} {speed_info}{fail_summary}")
    return True


def run_queue(
    model: Model,
    queue: list[tuple[Benchmark, str]],
    host: HostConfig,
    force: bool = False,
    gen_config: GenerationConfig | None = None,
    store: ResultStore | None = None,
    speed_store: SpeedResultStore | None = None,
    run_store: RunStore | None = None,
    db: Database | None = None,
    console: Console | None = None,
) -> None:
    store = store or _default_store
    speed_store = speed_store or _default_speed_store
    run_store = run_store or _default_run_store
    db = db or _default_db
    console = console or _default_console

    total = len(queue)
    if total == 0:
        console.print("\n[green]✨ No tests to execute — all have already passed![/green]")
        return

    cfg = gen_config or GenerationConfig()
    art_info = get_model_artifact_info(model.key)
    quant = art_info.quantization or detect_quantization(model.key)
    backend = detect_backend(lmstudio.get_base_url())
    suite_ver = get_suite_version()
    suite_h = compute_suite_hash()

    gen_params = cfg.to_dict()
    gen_params["artifact"] = art_info.to_dict()
    gen_params["suite_hash"] = suite_h

    run = run_store.create(
        host_id=host.id,
        model_key=model.key,
        model_name=art_info.display_name or model.key,
        quantization=quant,
        backend=backend,
        generation_params=gen_params,
        suite_version=suite_ver,
    )

    console.print(
        f"\n[bold]🚀 Starting Run [yellow]{run.id}[/yellow] ({total} tests) for model[/bold] [cyan]{model.key}[/cyan]:"
    )
    details = []
    if quant:
        details.append(f"Quant: [bold cyan]{quant}[/bold cyan]")
    if art_info.architecture:
        details.append(f"Arch: [bold]{art_info.architecture}[/bold]")
    if art_info.size_bytes:
        size_gb = art_info.size_bytes / (1024**3)
        details.append(f"Size: [bold]{size_gb:.1f} GB[/bold]")
    if backend:
        details.append(f"Backend: [bold]{backend}[/bold]")
    if suite_ver:
        details.append(f"Suite: [dim]{suite_ver}[/dim]")
    details.append(f"Params: [dim]temp={cfg.temperature}, seed={cfg.seed}, max_tok={cfg.max_tokens}[/dim]")
    if details:
        console.print(f"   [dim]{' | '.join(details)}[/dim]")

    completed = 0
    try:
        for idx, (b, lvl_id) in enumerate(queue, 1):
            console.print(f"\n[bold blue][{idx}/{total}][/bold blue]", end=" ")
            ok = execute_test(
                model,
                b,
                lvl_id,
                host,
                run_id=run.id,
                force=force,
                gen_config=cfg,
                store=store,
                speed_store=speed_store,
                db=db,
                console=console,
            )
            if ok:
                completed += 1
        run_store.complete(run.id, status="completed")
    except KeyboardInterrupt:
        run_store.complete(run.id, status="interrupted")
        console.print("\n\n[bold yellow]⏸  Execution interrupted by user (Ctrl+C)![/bold yellow]")
        console.print(
            f"[green]✔ Run marked as interrupted. All completed tests ({completed}/{total}) are safely stored.[/green]\n"
        )
        return
    except Exception as e:
        run_store.complete(run.id, status="failed")
        raise e

    console.print(f"\n[bold green]🎉 Queue completed! Successfully processed: {completed}/{total}[/bold green]")
    generate_html_report(db)
    console.print("[dim]📊 HTML report updated (report.html)[/dim]")
