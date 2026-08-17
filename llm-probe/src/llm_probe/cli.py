"""Typer CLI — entry point for `llm-probe` command."""

import asyncio
import webbrowser
from typing import Optional

import typer
from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn, TimeElapsedColumn
from rich.table import Table

from llm_probe.benchmarks.registry import all_bench_ids
from llm_probe.db.engine import init_db, get_session
from llm_probe.db.crud import get_leaderboard, get_runs
from llm_probe.lmstudio.client import DEFAULT_BASE_URL, LMStudioClient
from llm_probe.runner.runner import ChainSummary, JobResult, build_jobs, run_chain

app = typer.Typer(
    name="llm-probe",
    help="Benchmark tool for local LLMs — coding tasks, pass@k, speed metrics",
    add_completion=False,
)
console = Console()


# ──────────────────────────────────────────────────────────────────
# llm-probe run
# ──────────────────────────────────────────────────────────────────

@app.command()
def run(
    model: str = typer.Option(..., "--model", "-m", help="LM Studio model ID"),
    bench: Optional[list[str]] = typer.Option(None, "--bench", "-b", help="Benchmark IDs (default: all)"),
    level: Optional[list[str]] = typer.Option(None, "--level", "-l", help="Levels: l1,l2,l3 (default: all)"),
    k: int = typer.Option(3, "--k", help="Number of attempts per task"),
    lm_url: str = typer.Option(DEFAULT_BASE_URL, "--lm-url", help="LM Studio base URL"),
    eval_timeout: float = typer.Option(5.0, "--eval-timeout", help="Sandbox eval timeout (seconds)"),
) -> None:
    """Run benchmark chain. Runs unattended — go grab a coffee!"""
    init_db()

    bench_ids = bench or all_bench_ids()
    levels = level or ["l1", "l2", "l3"]
    jobs = build_jobs(model, bench_ids, levels, k)

    console.print(f"\n[bold cyan]llm-probe[/] — model: [yellow]{model}[/]")
    console.print(f"  Benchmarks: [green]{', '.join(bench_ids)}[/]  Levels: {', '.join(levels)}  k={k}")
    console.print(f"  Total jobs: [bold]{len(jobs)}[/]  (each job = 1 task attempt)\n")

    summary = asyncio.run(_run_with_progress(jobs, model, lm_url, eval_timeout))
    _print_summary(summary)


async def _run_with_progress(
    jobs: list,
    model_id: str,
    lm_url: str,
    eval_timeout: float,
) -> ChainSummary:
    results: list[JobResult] = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        console=console,
        transient=False,
    ) as progress:
        task = progress.add_task("Running…", total=len(jobs))

        async def on_progress(result: JobResult) -> None:
            results.append(result)
            icon = "✓" if result.status == "ok" else "✗"
            speed = f"{result.tok_per_sec:.1f} tok/s" if result.tok_per_sec else ""
            pct = f"{result.passed}/{result.total}" if result.total else ""
            progress.update(
                task,
                advance=1,
                description=f"{icon} {result.label} {pct} {speed}",
            )

        async with LMStudioClient(lm_url) as client:
            summary = await run_chain(
                jobs, client,
                on_progress=on_progress,
                eval_timeout=eval_timeout,
            )

    return summary


def _print_summary(summary: ChainSummary) -> None:
    console.print()
    table = Table(title="Chain Summary", show_header=True, header_style="bold magenta")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("Total jobs", str(summary.total))
    table.add_row("OK (ran)", str(summary.ok))
    table.add_row("LLM errors", f"[red]{summary.llm_errors}[/]" if summary.llm_errors else "0")
    table.add_row("Eval errors", f"[yellow]{summary.eval_errors}[/]" if summary.eval_errors else "0")
    table.add_row("Save errors", f"[red]{summary.save_errors}[/]" if summary.save_errors else "0")
    table.add_row("Duration", f"{summary.duration_sec:.1f}s")

    console.print(table)

    if summary.llm_errors > 0:
        console.print("\n[yellow]Hint:[/] Some LLM requests failed. Is LM Studio running?")


# ──────────────────────────────────────────────────────────────────
# llm-probe leaderboard
# ──────────────────────────────────────────────────────────────────

@app.command()
def leaderboard() -> None:
    """Show model rankings in the terminal."""
    init_db()
    with get_session() as session:
        rows = get_leaderboard(session)

    if not rows:
        console.print("[yellow]No results yet. Run some benchmarks first.[/]")
        return

    table = Table(title="Leaderboard", show_header=True, header_style="bold cyan")
    for col_name in ("Model", "Bench", "Level", "Attempts", "pass@1", "Avg Accuracy", "Avg tok/s"):
        table.add_column(col_name)

    for row in rows:
        acc = row["avg_accuracy"]
        pass1 = row["pass_at_1"]
        table.add_row(
            row["model_id"],
            row["bench_id"],
            row["level_id"],
            str(row["attempts"]),
            "✓" if pass1 else "✗",
            f"{acc:.1%}" if acc is not None else "—",
            f"{row['avg_tok_per_sec']:.1f}" if row["avg_tok_per_sec"] else "—",
        )

    console.print(table)


# ──────────────────────────────────────────────────────────────────
# llm-probe ui
# ──────────────────────────────────────────────────────────────────

@app.command()
def ui(
    host: str = typer.Option("127.0.0.1", "--host"),
    port: int = typer.Option(8765, "--port"),
    no_browser: bool = typer.Option(False, "--no-browser"),
) -> None:
    """Start the web UI and open it in the browser."""
    import uvicorn
    from llm_probe.main import app as fastapi_app

    init_db()

    url = f"http://{host}:{port}"
    console.print(f"\n[bold cyan]llm-probe UI[/] → [link={url}]{url}[/link]")
    console.print("Press [bold]Ctrl+C[/] to stop.\n")

    if not no_browser:
        webbrowser.open(url)

    uvicorn.run(fastapi_app, host=host, port=port, log_level="warning")


# ──────────────────────────────────────────────────────────────────
# llm-probe export
# ──────────────────────────────────────────────────────────────────

@app.command()
def export(
    output: str = typer.Option("results.csv", "--output", "-o"),
    model_id: Optional[str] = typer.Option(None, "--model"),
) -> None:
    """Export results to CSV."""
    import csv
    from pathlib import Path

    init_db()
    with get_session() as session:
        runs = get_runs(session, model_id=model_id)

    if not runs:
        console.print("[yellow]No results to export.[/]")
        return

    path = Path(output)
    fieldnames = [
        "id", "model_id", "bench_id", "level_id", "attempt", "temperature",
        "created_at", "passed", "total", "status",
        "tok_per_sec", "ttft_ms", "input_tokens", "output_tokens",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for run in runs:
            writer.writerow({k: getattr(run, k, None) for k in fieldnames})

    console.print(f"[green]Exported {len(runs)} rows to {path.resolve()}[/]")


if __name__ == "__main__":
    app()
