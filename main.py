"""Local LLM Benchmark Runner.

Minimal, reliable, and fast CLI for running benchmark suites against local LLMs.
Focuses on the active model in LM Studio with support for running single tests or entire suites.
Each test is saved atomically; interruptions (Ctrl+C) safely preserve progress.
"""

import sys
from pathlib import Path

import questionary
from questionary import Choice
from rich.console import Console
from rich.panel import Panel

import lmstudio
from benchmarks import REGISTRY
from database import Database
from host_configs import HostConfig, HostConfigStore
from html_report import generate_html_report, open_report_in_browser
from lmstudio import Model
from runner import run_queue, set_default_db
from storage import ResultStore, RunStore, SpeedResultStore
from sync import sync_db_and_records

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

console = Console(legacy_windows=False)
ROOT = Path(__file__).parent
db = Database(ROOT / "bench.db")
set_default_db(db)
store = ResultStore(db=db, answers_root=ROOT, raw_answers_dir=ROOT / "raw_answers")
speed_store = SpeedResultStore(db)
host_store = HostConfigStore(db)
run_store = RunStore(db)
run_store.cleanup_stale_runs()


def get_or_choose_host() -> HostConfig:
    active = host_store.get_active()
    if active:
        return active
    hosts = host_store.load_all()
    if hosts:
        host_store.set_active(hosts[0].id)
        return hosts[0]
    # Create default host
    new_host = HostConfig.create("Default Local Host")
    host_store.add(new_host)
    host_store.set_active(new_host.id)
    return new_host


def configure_server_url() -> str:
    current = lmstudio.get_base_url()
    choices = [
        Choice("🟢 Local LM Studio (http://127.0.0.1:1234)", value="http://127.0.0.1:1234"),
        Choice("🦙 Local Ollama (http://127.0.0.1:11434/v1)", value="http://127.0.0.1:11434/v1"),
        Choice("🌐 Enter URL manually (remote PC / LAN IP)", value="custom"),
        Choice("🔙 Back", value=None),
    ]
    chosen = questionary.select(f"Current address: {current}. Choose action:", choices=choices).ask()
    if chosen == "custom":
        new_url = questionary.text("Enter server URL (e.g. http://192.168.1.50:1234):", default=current).ask()
        if new_url and new_url.strip():
            lmstudio.set_base_url(new_url.strip())
            chosen = lmstudio.get_base_url()
    elif chosen:
        lmstudio.set_base_url(chosen)

    if chosen:
        if lmstudio.is_server_online():
            console.print(f"[bold green]✔ Server available:[/bold green] {lmstudio.get_base_url()}")
        else:
            console.print(
                f"[yellow]⚠️ Address saved ({lmstudio.get_base_url()}), but server is currently unreachable.[/yellow]"
            )
    return lmstudio.get_base_url()


def detect_or_select_model() -> Model | None:
    if not lmstudio.is_server_online():
        console.print(f"[yellow]⚠️  Server ({lmstudio.get_base_url()}) is not responding.[/yellow]")
        choice = questionary.select(
            "What would you like to do?",
            choices=[
                Choice("🌐 Change server address (IP/port)", value="server"),
                Choice("Retry connection", value="retry"),
                Choice("Enter model key manually", value="manual"),
                Choice("Open HTML report without running tests", value="report"),
                Choice("Exit", value="exit"),
            ],
        ).ask()
        if choice == "server":
            configure_server_url()
            return detect_or_select_model()
        elif choice == "manual":
            key = questionary.text("Enter model name/key (as shown in LM Studio):").ask()
            if key and key.strip():
                return Model(type="llm", key=key.strip())
        elif choice == "retry":
            return detect_or_select_model()
        elif choice == "report":
            out = generate_html_report(db)
            open_report_in_browser(out)
            return None
        return None

    # Check loaded models
    loaded = lmstudio.get_loaded_models()
    if len(loaded) == 1:
        return loaded[0]
    elif len(loaded) > 1:
        choices = [Choice(f"🟢 {m.key} (loaded)", value=m) for m in loaded]
        choices.append(Choice("✏️  Choose another / enter manually", value="other"))
        chosen = questionary.select("Multiple models loaded in LM Studio. Choose active:", choices=choices).ask()
        if chosen != "other":
            return chosen

    # If no loaded models or user chose other
    all_models = lmstudio.list_llm_models()
    choices = [Choice(m.key, value=m) for m in all_models]
    choices.append(Choice("✏️  Enter key manually", value="manual"))
    choices.append(Choice("🔙 Back", value=None))
    chosen = questionary.select("Choose model for testing:", choices=choices).ask()
    if chosen == "manual":
        key = questionary.text("Enter model name/key:").ask()
        return Model(type="llm", key=key.strip()) if key and key.strip() else None
    return chosen


def main_menu(model: Model, host: HostConfig) -> None:
    store.ensure_dirs(REGISTRY)

    while True:
        # Check model progress
        tested_count = 0
        total_count = sum(len(b.levels) for b in REGISTRY)
        for b in REGISTRY:
            for level in b.levels:
                if store.has_scored_result(b, model.key, level.id):
                    tested_count += 1

        pct_done = (tested_count / total_count * 100) if total_count else 0

        header_text = (
            f"[bold white]🎯 Active model:[/bold white] [bold cyan]{model.key}[/bold cyan]\n"
            f"[bold white]🖥️  Host:[/bold white] [dim]{host.label}[/dim]  |  "
            f"[bold white]🌐 Server:[/bold white] [cyan]{lmstudio.get_base_url()}[/cyan]\n"
            f"[bold white]Progress:[/bold white] [bold green]{tested_count}/{total_count}[/bold green] ({pct_done:.0f}%)"
        )
        console.print()
        console.print(Panel(header_text, border_style="cyan", title="Local LLM Benchmark Runner"))

        choices = [
            Choice("▶  1. Run missing tests (Run Missing)", value="run_missing"),
            Choice("📦 2. Run full benchmark suite (L1 + L2 + L3)", value="run_suite"),
            Choice("🎯 3. Run single specific test level", value="run_single"),
            Choice("🔄 4. Force rerun all benchmarks (overwrite)", value="run_force_all"),
            Choice("📊 5. Open unified dashboard (Leaderboard, Speed matrix, Code, Runs)", value="open_report"),
            Choice("📜 6. View Run History (all sessions & quantizations)", value="view_runs"),
            Choice("🔄 7. Sync with Git (records/ <-> bench.db)", value="sync_db"),
            Choice("⚙️  8. Settings (Change model / host / server)", value="change_config"),
            Choice("❌ 0. Exit", value="exit"),
        ]

        action = questionary.select("Choose action:", choices=choices).ask()
        if action in ("exit", None):
            console.print("[dim]Goodbye![/dim]")
            break

        if action == "view_runs":
            runs = run_store.list_runs(limit=15)
            if not runs:
                console.print("[dim]No runs recorded yet.[/dim]")
            else:
                from rich.table import Table

                t = Table(title="Recent Benchmark Runs")
                t.add_column("Run ID", style="cyan")
                t.add_column("Date", style="dim")
                t.add_column("Model", style="bold")
                t.add_column("Quant", style="yellow")
                t.add_column("Backend")
                t.add_column("Status")
                for r in runs:
                    st_style = "green" if r.status == "completed" else "yellow" if r.status == "in_progress" else "red"
                    t.add_row(
                        r.id[:24],
                        r.started_at[:16],
                        r.model_key[:30],
                        r.quantization or "—",
                        r.backend or "—",
                        f"[{st_style}]{r.status}[/{st_style}]",
                    )
                console.print(t)

        if action == "run_missing":
            queue = []
            for b in REGISTRY:
                for level in b.levels:
                    if not store.has_scored_result(b, model.key, level.id):
                        queue.append((b, level.id))
            run_queue(model, queue, host, force=False)

        elif action == "run_suite":
            suite_choices = [
                Choice(f"{b.short:10} | {b.code_lang:10} | {b.name} ({len(b.levels)} lvls)", value=b) for b in REGISTRY
            ]
            suite_choices.append(Choice("🔙 Back", value=None))
            selected_bench = questionary.select("Select benchmark to run:", choices=suite_choices).ask()
            if selected_bench:
                queue = [(selected_bench, level.id) for level in selected_bench.levels]
                run_queue(model, queue, host, force=True)

        elif action == "run_single":
            suite_choices = [Choice(f"{b.short} ({b.code_lang})", value=b) for b in REGISTRY]
            suite_choices.append(Choice("🔙 Back", value=None))
            selected_bench = questionary.select("Select benchmark:", choices=suite_choices).ask()
            if selected_bench:
                lvl_choices = [Choice(f"{level.name}", value=level.id) for level in selected_bench.levels]
                lvl_choices.append(Choice("🔙 Back", value=None))
                lvl_id = questionary.select("Select level:", choices=lvl_choices).ask()
                if lvl_id:
                    run_queue(model, [(selected_bench, lvl_id)], host, force=True)

        elif action == "run_force_all":
            confirm = questionary.confirm("Rerun absolutely all benchmarks for this model?").ask()
            if confirm:
                queue = []
                for b in REGISTRY:
                    for level in b.levels:
                        queue.append((b, level.id))
                run_queue(model, queue, host, force=True)

        elif action == "open_report":
            report_path = generate_html_report(db)
            console.print(f"[green]✔ Report generated: {report_path}[/green]")
            open_report_in_browser(report_path)

        elif action == "sync_db":
            res = sync_db_and_records(db)
            console.print("[bold green]✔ Synchronization completed:[/bold green]")
            console.print(
                f"   Imported from records/: {res['imported']['results']} results, {res['imported']['speeds']} speed samples"
            )
            console.print(
                f"   Exported to records/: {res['exported']['results']} results, {res['exported']['speeds']} speed samples"
            )

        elif action == "change_config":
            sub = questionary.select(
                "What would you like to change?",
                choices=[
                    Choice("Change model", value="model"),
                    Choice("Change host (hardware)", value="host"),
                    Choice(f"🌐 Change server URL (current: {lmstudio.get_base_url()})", value="server"),
                    Choice("🔙 Back", value=None),
                ],
            ).ask()
            if sub == "model":
                new_m = detect_or_select_model()
                if new_m:
                    model = new_m
            elif sub == "server":
                configure_server_url()
                new_m = detect_or_select_model()
                if new_m:
                    model = new_m
            elif sub == "host":
                hosts = host_store.load_all()
                h_choices = [Choice(h.label, value=h.id) for h in hosts]
                h_choices.append(Choice("➕ Create new host", value="new"))
                sel_h = questionary.select("Select active host:", choices=h_choices).ask()
                if sel_h == "new":
                    lbl = questionary.text("Host name (hardware label):").ask()
                    if lbl and lbl.strip():
                        nh = HostConfig.create(lbl)
                        host_store.add(nh)
                        host_store.set_active(nh.id)
                        host = nh
                elif sel_h:
                    host_store.set_active(sel_h)
                    host = host_store.get(sel_h)


def main():
    # CLI arguments: python main.py sync
    if len(sys.argv) > 1 and sys.argv[1] in ("sync", "--sync"):
        res = sync_db_and_records(db)
        console.print("[bold green]✔ Database synced with records/:[/bold green]")
        console.print(
            f"   Imported:  {res['imported']['results']} results, {res['imported']['speeds']} samples, {res['imported']['hosts']} hosts"
        )
        console.print(
            f"   Exported: {res['exported']['results']} results, {res['exported']['speeds']} samples, {res['exported']['hosts']} hosts"
        )
        return

    # CLI arguments: python main.py report
    if len(sys.argv) > 1 and sys.argv[1] in ("report", "--report"):
        sync_db_and_records(db)
        report_path = generate_html_report(db)
        console.print(f"[green]✔ Report generated: {report_path}[/green]")
        open_report_in_browser(report_path)
        return

    # Auto-sync at startup
    try:
        sync_db_and_records(db)
    except Exception as e:
        console.print(f"[yellow]⚠️  Sync warning: {e}[/yellow]")

    host = get_or_choose_host()
    model = detect_or_select_model()
    if not model:
        return
    main_menu(model, host)


if __name__ == "__main__":
    main()
