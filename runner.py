"""Benchmark test runner engine.

Orchestrates model querying, multi-turn level dependencies, code extraction,
sandboxed test execution, and run session tracking.
"""

import json
from dataclasses import replace
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
    GENERATION_FAILED_PREFIX,
    TRUNCATED_PREFIX,
    ResultStore,
    RunStore,
    SpeedResultStore,
    compute_suite_hash,
    detect_backend,
    detect_quantization,
    get_suite_version,
    is_infra_failure,
)

# A truncated generation is retried with a doubled token budget, up to this cap.
MAX_TOKENS_RETRY_CAP = 65536

ROOT = Path(__file__).parent
_default_console = Console(legacy_windows=False)
_default_db: Database | None = None
_default_store: ResultStore | None = None
_default_speed_store: SpeedResultStore | None = None
_default_run_store: RunStore | None = None


def get_default_db() -> Database:
    global _default_db
    if _default_db is None:
        _default_db = Database(ROOT / "bench.db")
    return _default_db


def set_default_db(db: Database) -> None:
    global _default_db, _default_store, _default_speed_store, _default_run_store
    _default_db = db
    _default_store = ResultStore(db=db, answers_root=ROOT, raw_answers_dir=ROOT / "raw_answers")
    _default_speed_store = SpeedResultStore(db)
    _default_run_store = RunStore(db)


def get_default_store() -> ResultStore:
    global _default_store
    if _default_store is None:
        _default_store = ResultStore(db=get_default_db(), answers_root=ROOT, raw_answers_dir=ROOT / "raw_answers")
    return _default_store


def get_default_speed_store() -> SpeedResultStore:
    global _default_speed_store
    if _default_speed_store is None:
        _default_speed_store = SpeedResultStore(get_default_db())
    return _default_speed_store


def get_default_run_store() -> RunStore:
    global _default_run_store
    if _default_run_store is None:
        _default_run_store = RunStore(get_default_db())
    return _default_run_store


class GenerationTruncatedError(Exception):
    """The model output was cut off even after retrying with a larger token budget.

    This is a harness/budget limitation, not a code defect, so no tests are run on the output.
    """

    def __init__(self, message: str, response: lmstudio.ModelResponse | None = None) -> None:
        super().__init__(message)
        self.response = response


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _generate_with_retry(
    model_key: str,
    messages: list[dict],
    gen_config: GenerationConfig | None,
    console: Console,
) -> lmstudio.ModelResponse:
    """Queries the model, retrying with a doubled token budget while the output is truncated."""
    cfg = replace(gen_config) if gen_config else GenerationConfig()
    while True:
        response = lmstudio.ask_model(model_key, messages, config=cfg)
        if not response.truncated:
            return response
        next_budget = cfg.max_tokens * 2
        if next_budget > MAX_TOKENS_RETRY_CAP:
            raise GenerationTruncatedError(
                f"{response.truncated_reason}; still truncated at max_tokens={cfg.max_tokens} "
                f"(retry cap {MAX_TOKENS_RETRY_CAP})",
                response,
            )
        console.print(
            f"    [yellow]Output truncated ({response.truncated_reason}); "
            f"retrying with max_tokens={next_budget}[/yellow]"
        )
        cfg = replace(cfg, max_tokens=next_budget, timeout_seconds=cfg.timeout_seconds * 2)


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
    is_prerequisite: bool = False,
    quantization: str | None = None,
) -> Path | None:
    """Returns the path of the extracted answer for a level, generating it when needed.

    An existing answer is reused when it already has a scored result (from any run of this model)
    or when used as an unscored prerequisite and the raw completion is already on disk.
    ``force`` applies only to the requested level: prerequisite levels are always reused when available,
    so a single-level rerun does not regenerate (and silently overwrite) earlier levels.
    """
    store = store or get_default_store()
    speed_store = speed_store or get_default_speed_store()
    console = console or _default_console

    level = benchmark.level_by_id(level_id)
    answer_path, raw_path = store.paths_for(benchmark, model.key, level_id, quantization=quantization, run_id=run_id)

    if (
        not force
        and answer_path.exists()
        and raw_path.exists()
        and (
            store.has_scored_result(benchmark, model.key, level_id) or (is_prerequisite and raw_path.stat().st_size > 0)
        )
    ):
        return answer_path

    messages = []
    if level.requires:
        req_id = level.requires
        req_answer, req_raw = store.paths_for(benchmark, model.key, req_id, quantization=quantization, run_id=run_id)
        if not (req_raw.exists() and req_raw.read_text(encoding="utf-8").strip()):
            prev_answer = ensure_level_answer(
                model,
                benchmark,
                req_id,
                host,
                run_id=None,
                force=False,
                gen_config=gen_config,
                store=store,
                speed_store=speed_store,
                console=console,
                is_prerequisite=True,
                quantization=quantization,
            )
            if prev_answer is None:
                return None
        prev_content = req_raw.read_text(encoding="utf-8") if req_raw.exists() else ""
        messages.append({"role": "user", "content": benchmark.level_by_id(req_id).prompt})
        messages.append({"role": "assistant", "content": prev_content})

    messages.append({"role": "user", "content": level.prompt})

    try:
        response = _generate_with_retry(model.key, messages, gen_config, console)
    except GenerationTruncatedError as e:
        # Keep the partial output for inspection, but never leave it behind as a runnable answer.
        if e.response is not None:
            raw_path.write_text(e.response.content, encoding="utf-8")
            if e.response.reasoning:
                raw_path.with_suffix(".reasoning.txt").write_text(e.response.reasoning, encoding="utf-8")
        answer_path.unlink(missing_ok=True)
        raise GenerationTruncatedError(f"{benchmark.id}/{level_id}: {e}", e.response) from e
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

    # Save speed stats only for tests that are part of this run (not auxiliary prerequisites)
    if not is_prerequisite and run_id and response.stats:
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
    quantization: str | None = None,
) -> bool:
    store = store or get_default_store()
    speed_store = speed_store or get_default_speed_store()
    db = db or get_default_db()
    console = console or _default_console

    level = benchmark.level_by_id(level_id)
    tag = f"[bold cyan]{benchmark.short}[/bold cyan] / [bold]{level.name}[/bold]"

    # Resolve quantization if needed
    quant = quantization
    if not quant and run_id:
        r_store = RunStore(db)
        r_obj = r_store.get(run_id)
        if r_obj:
            quant = r_obj.quantization
    if not quant:
        quant = detect_quantization(model.key)

    # A run always starts empty, so "already done" must be looked up across earlier runs of this model.
    if not force and store.has_scored_result(benchmark, model.key, level_id):
        res = store.load(benchmark, model.key, level_id)
        if res is not None:
            pct = res.percent()
            pct_color = "green" if pct >= 80 else "yellow" if pct >= 50 else "red"
            done = f"[{pct_color}]{res.format()}[/{pct_color}]"
        else:
            done = "scored"
        console.print(f"  ⏭  {tag} -> [dim]skipped (already scored:[/dim] {done}[dim])[/dim]")
        return True

    console.print(f"  ⏳ {tag} ... waiting for generation...", end="\r")

    try:
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
            quantization=quant,
        )
    except GenerationTruncatedError as e:
        console.print(f"  ✂️  {tag} -> [yellow]Output truncated, not scored as code failure:[/yellow] {e}")
        if run_id:
            truncated = StoredResult(
                model=model.key,
                benchmark=benchmark.id,
                level=level_id,
                tested_at=now_str(),
                evaluation=TestResult(0, 0, [f"{TRUNCATED_PREFIX} {e}"]),
            )
            store.save(benchmark, model.key, level_id, truncated, run_id=run_id)
        return False

    if answer_path is None or not answer_path.exists():
        console.print(f"  ❌ {tag} -> [red]Failed to get response from model (timeout or error)[/red]")
        if run_id:
            test_result = TestResult(0, 0, [f"{GENERATION_FAILED_PREFIX} Model generation failed or timed out"])
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
    elif host and host.id:
        speed_query += " AND host_id = ?"
        params.append(host.id)
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
        test_result = TestResult(0, 0, [f"{GENERATION_FAILED_PREFIX} Test runner exception: {e}"])

    stored = StoredResult(
        model=model.key,
        benchmark=benchmark.id,
        level=level_id,
        tested_at=now_str(),
        evaluation=test_result,
    )
    store.save(benchmark, model.key, level_id, stored, run_id=run_id)

    pct = test_result.percent()
    if is_infra_failure(test_result.failures):
        icon = "[yellow]⚠️[/yellow]"
        score_styled = "[bold yellow]INFRA ERROR[/bold yellow]"
    elif pct >= 80:
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
        first_item = test_result.failures[0]
        first_fail_str = str(first_item) if first_item is not None else ""
        first_fail = first_fail_str.split("\n")[0]
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
    store = store or get_default_store()
    speed_store = speed_store or get_default_speed_store()
    run_store = run_store or get_default_run_store()
    db = db or get_default_db()
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
                quantization=quant,
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
