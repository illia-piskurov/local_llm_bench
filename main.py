"""Local LLM Benchmark Runner.

Minimal, reliable, and fast CLI for running benchmark suites against local LLMs.
Focuses on the active model in LM Studio with support for running single tests or entire suites.
Each test is saved atomically; interruptions (Ctrl+C) safely preserve progress.
"""

import json
import sys
from pathlib import Path
from typing import Any

import questionary
from questionary import Choice
from rich.console import Console
from rich.panel import Panel

import lmstudio
from benchmarks import REGISTRY
from database import Database
from host_configs import HostConfig, HostConfigStore
from html_report import generate_html_report, open_report_in_browser
from lmstudio import GenerationConfig, Model
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

# questionary falls back to the title when a Choice value is None, so "Back" entries carry this sentinel instead.
BACK = "__back__"


def select_choice(message: str, choices: list[Choice]) -> Any:
    """Single-choice prompt that returns None for both the Back entry and a cancelled prompt (Ctrl-C)."""
    answer = questionary.select(message, choices=choices).ask()
    return None if isinstance(answer, str) and answer == BACK else answer


# Ollama has no per-model presets, so the generation settings are chosen when a run starts. The last answers of
# this session are offered as the next defaults.
THINK_MODES = [
    Choice("Medium effort", value="medium"),
    Choice("Low effort (small models may think only a few tokens)", value="low"),
    Choice("High effort", value="high"),
    Choice("On (the model's own effort)", value="on"),
    Choice("Off (no thinking)", value="off"),
    Choice("Auto (the model decides, whatever its default is)", value="auto"),
]
_last_ollama_settings: dict | None = None


def _is_number(text: str, minimum: int) -> bool | str:
    if text.strip().isdigit() and int(text) >= minimum:
        return True
    return f"Enter a whole number >= {minimum}"


def build_ollama_config(max_tokens: int, think: str, think_budget: int, num_ctx: int) -> GenerationConfig:
    return GenerationConfig(max_tokens=max_tokens, context_length=num_ctx, think=think, think_budget=think_budget)


def prompt_generation_config() -> GenerationConfig | None:
    """Returns the settings for the next run, or None when the prompt is cancelled (Ctrl-C).

    LM Studio keeps its own presets, so nothing is asked and nothing is sent; Ollama asks for the token budget,
    thinking mode, thinking budget and context window.
    """
    global _last_ollama_settings
    if not lmstudio.is_ollama():
        return GenerationConfig()

    d = _last_ollama_settings or lmstudio.ollama_run_defaults()
    console.print("\n[bold]🦙 Ollama generation settings for this run[/bold]")
    max_tokens = questionary.text(
        "Max output tokens (thinking + answer):", default=str(d["max_tokens"]), validate=lambda t: _is_number(t, 1)
    ).ask()
    if max_tokens is None:
        return None
    think = questionary.select("Thinking mode:", choices=THINK_MODES, default=d["think"]).ask()
    if think is None:
        return None
    think_budget = d["think_budget"]
    if think != "off":
        answer = questionary.text(
            "Thinking budget (max thinking tokens, 0 = unlimited; over it the question is re-asked without thinking):",
            default=str(think_budget),
            validate=lambda t: _is_number(t, 0),
        ).ask()
        if answer is None:
            return None
        think_budget = int(answer)
    num_ctx = questionary.text(
        "Context window (num_ctx):", default=str(d["num_ctx"]), validate=lambda t: _is_number(t, 512)
    ).ask()
    if num_ctx is None:
        return None

    _last_ollama_settings = {
        "max_tokens": int(max_tokens),
        "think": think,
        "think_budget": think_budget,
        "num_ctx": int(num_ctx),
    }
    return build_ollama_config(**_last_ollama_settings)


def start_run(model: Model, queue: list, host: HostConfig, force: bool) -> None:
    """Asks for the generation settings (Ollama only) and runs the queue."""
    gen_config = prompt_generation_config()
    if gen_config is None:
        console.print("[dim]Run cancelled.[/dim]")
        return
    run_queue(model, queue, host, force=force, gen_config=gen_config)


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
        Choice("🔙 Back", value=BACK),
    ]
    chosen = select_choice(f"Current address: {current}. Choose action:", choices=choices)
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
        choice = select_choice(
            "What would you like to do?",
            choices=[
                Choice("🌐 Change server address (IP/port)", value="server"),
                Choice("Retry connection", value="retry"),
                Choice("Enter model key manually", value="manual"),
                Choice("Open HTML report without running tests", value="report"),
                Choice("🗑️ Manage / Delete results", value="manage_deletion"),
                Choice("Exit", value="exit"),
            ],
        )
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
        elif choice == "manage_deletion":
            manage_deletion_menu()
            return detect_or_select_model()
        return None

    # Check loaded models
    loaded = lmstudio.get_loaded_models()
    if len(loaded) == 1:
        return loaded[0]
    elif len(loaded) > 1:
        choices = [Choice(f"🟢 {m.key} (loaded)", value=m) for m in loaded if m.key]
        choices.append(Choice("✏️  Choose another / enter manually", value="other"))
        choices.append(Choice("🔙 Back", value=BACK))
        chosen = select_choice("Multiple models loaded in LM Studio. Choose active:", choices=choices)
        if chosen not in ("other", None):
            return chosen
        if chosen is None:
            return None

    # If no loaded models or user chose other
    all_models = lmstudio.list_llm_models()
    choices = [Choice(m.key, value=m) for m in all_models if m.key]
    choices.append(Choice("✏️  Enter key manually", value="manual"))
    choices.append(Choice("🔙 Back", value=BACK))
    chosen = select_choice("Choose model for testing:", choices=choices)
    if chosen == "manual":
        key = questionary.text("Enter model name/key:").ask()
        return Model(type="llm", key=key.strip()) if key and key.strip() else None
    return chosen


def get_recorded_models(database: Database) -> list[str]:
    models = set()
    try:
        for row in database.conn.execute("SELECT DISTINCT model FROM results").fetchall():
            if row[0]:
                models.add(row[0])
        for row in database.conn.execute("SELECT DISTINCT model FROM speed_results").fetchall():
            if row[0]:
                models.add(row[0])
        for row in database.conn.execute("SELECT DISTINCT model_key FROM runs").fetchall():
            if row[0]:
                models.add(row[0])
    except Exception:
        pass

    records_dir = ROOT / "records"
    for sub in ("results", "speeds"):
        d = records_dir / sub
        if d.exists():
            for p in d.glob("*.json"):
                try:
                    data = json.loads(p.read_text(encoding="utf-8"))
                    m = data.get("model") or data.get("model_key")
                    if m:
                        models.add(m)
                except Exception:
                    pass
    d_runs = records_dir / "runs"
    if d_runs.exists():
        for p in d_runs.glob("*.json"):
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                m = data.get("model_key")
                if m:
                    models.add(m)
            except Exception:
                pass
    return sorted(list(models))


def manage_deletion_menu(current_model: Model | None = None) -> Model | None:
    DELETE_MODEL = "__delete_model__"
    DELETE_LEVEL = "__delete_level__"
    DELETE_ALL = "__delete_all__"

    while True:
        all_models = get_recorded_models(db)
        if not all_models:
            console.print("[yellow]No recorded results or models found to delete.[/yellow]")
            return current_model

        choices = [
            Choice("🗑️  1. Delete ALL results of a specific model", value=DELETE_MODEL),
            Choice("🎯 2. Delete results of a specific test / level for a model", value=DELETE_LEVEL),
            Choice("⚠️  3. Reset ALL benchmark results (wipe database and records)", value=DELETE_ALL),
            Choice("🔙 Back", value=BACK),
        ]

        action = select_choice("Manage / Delete results:", choices=choices)
        if action in (None, BACK):
            return current_model

        if action == DELETE_MODEL:
            model_choices = [Choice(m, value=m) for m in all_models]
            model_choices.append(Choice("🔙 Back", value=BACK))
            selected_model = select_choice("Select model to delete all results and runs for:", choices=model_choices)
            if selected_model in (None, BACK):
                continue

            confirm = questionary.confirm(
                f"Are you sure you want to completely delete all results, speeds, and runs for '{selected_model}'?",
                default=False,
                auto_enter=False,
            ).ask()
            if confirm:
                count_res = store.clear_model(selected_model, REGISTRY)
                count_speed = speed_store.clear_model(selected_model)
                count_runs = run_store.clear_model(selected_model)
                console.print(
                    f"[bold green]✔ Successfully deleted '{selected_model}':[/bold green] "
                    f"{count_res} result/answer files, {count_speed} speed records, {count_runs} runs removed."
                )
                if current_model and current_model.key == selected_model:
                    console.print(
                        f"[yellow]⚠️ Active model '{selected_model}' was deleted. Please select a new active model.[/yellow]"
                    )
                    new_m = detect_or_select_model()
                    if new_m:
                        current_model = new_m

        elif action == DELETE_LEVEL:
            model_choices = [Choice(m, value=m) for m in all_models]
            model_choices.append(Choice("🔙 Back", value=BACK))
            selected_model = select_choice("Select model:", choices=model_choices)
            if selected_model in (None, BACK):
                continue

            level_choices = []
            for b in REGISTRY:
                for lvl in b.levels:
                    res = store.load(b, selected_model, lvl.id)
                    status = f"{res.format()} ({res.tested_at})" if res else "not tested"
                    level_choices.append(
                        Choice(
                            f"[{b.short}] {b.name} — {lvl.name}: {status}",
                            value=(b, lvl.id),
                        )
                    )
            level_choices.append(Choice("🔙 Back", value=BACK))

            selected_level = select_choice("Select level to delete:", choices=level_choices)
            if selected_level in (None, BACK):
                continue

            b, l_id = selected_level
            confirm = questionary.confirm(
                f"Delete result [{b.short} - {l_id}] for model '{selected_model}'?",
                default=False,
                auto_enter=False,
            ).ask()
            if confirm:
                count_res = store.clear(b, selected_model, l_id)
                count_speed = speed_store.clear_level(selected_model, b.id, l_id)
                console.print(
                    f"[bold green]✔ Deleted [{b.short} - {l_id}] for '{selected_model}':[/bold green] "
                    f"{count_res} result files, {count_speed} speed records removed."
                )

        elif action == DELETE_ALL:
            confirm = questionary.confirm(
                "WARNING: This will permanently delete ALL results, speeds, runs, and answers for ALL models! Continue?",
                default=False,
                auto_enter=False,
            ).ask()
            if confirm:
                double_confirm = questionary.confirm(
                    "Are you ABSOLUTELY sure? This cannot be undone.",
                    default=False,
                    auto_enter=False,
                ).ask()
                if double_confirm:
                    count_res = store.clear_all(REGISTRY)
                    count_speed = speed_store.clear_all()
                    count_runs = run_store.clear_all()
                    console.print(
                        f"[bold red]✔ Benchmark wiped: deleted {count_res} result files, "
                        f"{count_speed} speed records, {count_runs} runs.[/bold red]"
                    )
                    new_m = detect_or_select_model()
                    if new_m:
                        current_model = new_m


def main_menu(model: Model, host: HostConfig) -> None:
    store.ensure_dirs(REGISTRY)

    while True:
        if not host:
            host = get_or_choose_host()
        if not model:
            new_m = detect_or_select_model()
            if not new_m:
                break
            model = new_m

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
            Choice("🗑️  9. Manage results (Delete model / test data)", value="manage_deletion"),
            Choice("❌ 0. Exit", value="exit"),
        ]

        action = select_choice("Choose action:", choices=choices)
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
            start_run(model, queue, host, force=False)

        elif action == "run_suite":
            suite_choices = [
                Choice(f"{b.short:10} | {b.code_lang:10} | {b.name} ({len(b.levels)} lvls)", value=b) for b in REGISTRY
            ]
            suite_choices.append(Choice("🔙 Back", value=BACK))
            selected_bench = select_choice("Select benchmark to run:", choices=suite_choices)
            if selected_bench:
                queue = [(selected_bench, level.id) for level in selected_bench.levels]
                start_run(model, queue, host, force=True)

        elif action == "run_single":
            suite_choices = [Choice(f"{b.short} ({b.code_lang})", value=b) for b in REGISTRY]
            suite_choices.append(Choice("🔙 Back", value=BACK))
            selected_bench = select_choice("Select benchmark:", choices=suite_choices)
            if selected_bench:
                lvl_choices = [Choice(f"{level.name}", value=level.id) for level in selected_bench.levels]
                lvl_choices.append(Choice("🔙 Back", value=BACK))
                lvl_id = select_choice("Select level:", choices=lvl_choices)
                if lvl_id:
                    start_run(model, [(selected_bench, lvl_id)], host, force=True)

        elif action == "run_force_all":
            confirm = questionary.confirm(
                "Rerun absolutely all benchmarks for this model?",
                default=False,
                auto_enter=False,
            ).ask()
            if confirm:
                queue = []
                for b in REGISTRY:
                    for level in b.levels:
                        queue.append((b, level.id))
                start_run(model, queue, host, force=True)
            else:
                console.print("[dim]Action cancelled.[/dim]")

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
            sub = select_choice(
                "What would you like to change?",
                choices=[
                    Choice("Change model", value="model"),
                    Choice("Change host (hardware)", value="host"),
                    Choice(f"🌐 Change server URL (current: {lmstudio.get_base_url()})", value="server"),
                    Choice("🔙 Back", value=BACK),
                ],
            )
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
                h_choices.append(Choice("🔙 Back", value=BACK))
                sel_h = select_choice("Select active host:", choices=h_choices)
                if sel_h == "new":
                    lbl = questionary.text("Host name (hardware label):").ask()
                    if lbl and lbl.strip():
                        nh = HostConfig.create(lbl.strip())
                        host_store.add(nh)
                        host_store.set_active(nh.id)
                        host = nh
                elif sel_h:
                    new_h = host_store.get(sel_h)
                    if new_h:
                        host_store.set_active(sel_h)
                        host = new_h

        elif action == "manage_deletion":
            updated = manage_deletion_menu(current_model=model)
            if updated:
                model = updated


def main():
    # CLI arguments: python main.py delete
    if len(sys.argv) > 1 and sys.argv[1] in ("delete", "--delete"):
        manage_deletion_menu()
        return

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
