"""Local LLM Benchmark Runner.

Минималистичный, надёжный и быстрый интерфейс для запуска тестов на локальных LLM.
Фокусируется на активной модели в LM Studio с возможностью запуска от 1 теста до всего пакета.
Каждый тест сохраняется атомарно, прерывание (Ctrl+C) безопасно сохраняет прогресс.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

import questionary
from questionary import Choice
from rich.console import Console
from rich.panel import Panel

import lmstudio
from benchmarks import REGISTRY
from benchmarks.base import Benchmark, GenerationStats, SpeedSample, StoredResult, TestResult
from database import Database
from host_configs import HostConfig, HostConfigStore
from html_report import generate_html_report, open_report_in_browser
from lmstudio import Model
from storage import ResultStore, SpeedResultStore
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
store = ResultStore(db=db, answers_root=ROOT, raw_answers_dir=ROOT / "raw_answers")
speed_store = SpeedResultStore(db)
host_store = HostConfigStore(db)


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


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
        Choice("🟢 Локальный LM Studio (http://127.0.0.1:1234)", value="http://127.0.0.1:1234"),
        Choice("🦙 Локальный Ollama (http://127.0.0.1:11434/v1)", value="http://127.0.0.1:11434/v1"),
        Choice("🌐 Ввести адрес вручную (другой ПК / IP в локальной сети)", value="custom"),
        Choice("🔙 Назад", value=None),
    ]
    chosen = questionary.select(f"Текущий адрес: {current}. Выбери действие:", choices=choices).ask()
    if chosen == "custom":
        new_url = questionary.text("Введи URL сервера (например http://192.168.1.50:1234):", default=current).ask()
        if new_url and new_url.strip():
            lmstudio.set_base_url(new_url.strip())
            chosen = lmstudio.get_base_url()
    elif chosen:
        lmstudio.set_base_url(chosen)

    if chosen:
        if lmstudio.is_server_online():
            console.print(f"[bold green]✔ Сервер доступен:[/bold green] {lmstudio.get_base_url()}")
        else:
            console.print(
                f"[yellow]⚠️ Адрес сохранён ({lmstudio.get_base_url()}), но сервер сейчас не отвечает.[/yellow]"
            )
    return lmstudio.get_base_url()


def detect_or_select_model() -> Model | None:
    if not lmstudio.is_server_online():
        console.print(f"[yellow]⚠️  Сервер ({lmstudio.get_base_url()}) не отвечает.[/yellow]")
        choice = questionary.select(
            "Что сделать?",
            choices=[
                Choice("🌐 Сменить адрес сервера (IP/порт)", value="server"),
                Choice("Повторить попытку подключения", value="retry"),
                Choice("Ввести ключ модели вручную", value="manual"),
                Choice("Открыть HTML-отчёт без запуска тестов", value="report"),
                Choice("Выход", value="exit"),
            ],
        ).ask()
        if choice == "server":
            configure_server_url()
            return detect_or_select_model()
        elif choice == "manual":
            key = questionary.text("Введи имя/ключ модели (как в LM Studio):").ask()
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
        choices = [Choice(f"🟢 {m.key} (загружена)", value=m) for m in loaded]
        choices.append(Choice("✏️  Выбрать другую / ввести вручную", value="other"))
        chosen = questionary.select("В LM Studio загружено несколько моделей. Выбери активную:", choices=choices).ask()
        if chosen != "other":
            return chosen

    # If no loaded models or user chose other
    all_models = lmstudio.list_llm_models()
    choices = [Choice(m.key, value=m) for m in all_models]
    choices.append(Choice("✏️  Ввести ключ вручную", value="manual"))
    choices.append(Choice("🔙 Назад", value=None))
    chosen = questionary.select("Выбери модель для тестирования:", choices=choices).ask()
    if chosen == "manual":
        key = questionary.text("Введи имя/ключ модели:").ask()
        return Model(type="llm", key=key.strip()) if key and key.strip() else None
    return chosen


def ensure_level_answer(
    model: Model, benchmark: Benchmark, level_id: str, host: HostConfig, force: bool = False
) -> Path | None:
    level = benchmark.level_by_id(level_id)
    answer_path, raw_path = store.paths_for(benchmark, model.key, level_id)

    if not force and answer_path.exists() and store.has_result(benchmark, model.key, level_id):
        return answer_path

    messages = []
    if level.requires:
        prev_answer = ensure_level_answer(model, benchmark, level.requires, host, force=False)
        if prev_answer is None:
            return None
        _, prev_raw = store.paths_for(benchmark, model.key, level.requires)
        prev_content = prev_raw.read_text(encoding="utf-8") if prev_raw.exists() else ""
        messages.append({"role": "user", "content": benchmark.level_by_id(level.requires).prompt})
        messages.append({"role": "assistant", "content": prev_content})

    messages.append({"role": "user", "content": level.prompt})

    try:
        response = lmstudio.ask_model(model.key, messages)
    except Exception as e:
        console.print(f"    [red]Ошибка API LM Studio:[/red] {e}")
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
            speed_store.save(sample)

    code = benchmark.extract_code(response.content)
    answer_path.write_text(code, encoding="utf-8")
    return answer_path


def execute_test(model: Model, benchmark: Benchmark, level_id: str, host: HostConfig, force: bool = False) -> bool:
    level = benchmark.level_by_id(level_id)
    tag = f"[bold cyan]{benchmark.short}[/bold cyan] / [bold]{level.name}[/bold]"

    if not force and store.has_result(benchmark, model.key, level_id):
        res = store.load(benchmark, model.key, level_id)
        pct = res.percent() if res else 0
        pct_color = "green" if pct >= 80 else "yellow" if pct >= 50 else "red"
        console.print(
            f"  ⏭  {tag} -> [dim]пропущено (уже пройдено:[/dim] [{pct_color}]{res.format()}[/{pct_color}][dim])[/dim]"
        )
        return True

    console.print(f"  ⏳ {tag} ... ожидаем генерацию...", end="\r")

    answer_path = ensure_level_answer(model, benchmark, level_id, host, force=force)

    if answer_path is None or not answer_path.exists():
        console.print(f"  ❌ {tag} -> [red]Не удалось получить ответ модели[/red]")
        return False

    # Speed & reasoning metrics
    speed_row = db.conn.execute(
        "SELECT tokens_per_second, time_to_first_token_seconds, reasoning_output_tokens FROM speed_results WHERE model = ? AND benchmark = ? AND level = ?",
        (model.key, benchmark.id, level_id),
    ).fetchone()
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
        test_result = TestResult(0, 1, [f"Исключение раннера тестов: {e}"])

    stored = StoredResult(
        model=model.key,
        benchmark=benchmark.id,
        level=level_id,
        tested_at=now_str(),
        evaluation=test_result,
    )
    store.save(benchmark, model.key, level_id, stored)

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


def run_queue(model: Model, queue: list[tuple[Benchmark, str]], host: HostConfig, force: bool = False) -> None:
    total = len(queue)
    if total == 0:
        console.print("\n[green]✨ Нет тестов для выполнения — все уже пройдены![/green]")
        return

    console.print(f"\n[bold]🚀 Запуск очереди из {total} тестов для модели[/bold] [cyan]{model.key}[/cyan]:")
    completed = 0
    try:
        for idx, (b, lvl_id) in enumerate(queue, 1):
            console.print(f"\n[bold blue][{idx}/{total}][/bold blue]", end=" ")
            ok = execute_test(model, b, lvl_id, host, force=force)
            if ok:
                completed += 1
    except KeyboardInterrupt:
        console.print("\n\n[bold yellow]⏸  Выполнение прервано пользователем (Ctrl+C)![/bold yellow]")
        console.print(f"[green]✔ Все завершённые тесты ({completed}/{total}) надёжно сохранены в базе.[/green]\n")
        return

    console.print(f"\n[bold green]🎉 Очередь завершена! Успешно обработано: {completed}/{total}[/bold green]")
    generate_html_report(db)
    console.print("[dim]📊 HTML-отчёт обновлён (report.html)[/dim]")


def main_menu(model: Model, host: HostConfig) -> None:
    store.ensure_dirs(REGISTRY)

    while True:
        # Check model progress
        tested_count = 0
        total_count = sum(len(b.levels) for b in REGISTRY)
        for b in REGISTRY:
            for level in b.levels:
                if store.has_result(b, model.key, level.id):
                    tested_count += 1

        pct_done = (tested_count / total_count * 100) if total_count else 0

        header_text = (
            f"[bold white]🎯 Активная модель:[/bold white] [bold cyan]{model.key}[/bold cyan]\n"
            f"[bold white]🖥️  Хост:[/bold white] [dim]{host.label}[/dim]  |  "
            f"[bold white]🌐 Сервер:[/bold white] [cyan]{lmstudio.get_base_url()}[/cyan]\n"
            f"[bold white]Прогресс:[/bold white] [bold green]{tested_count}/{total_count}[/bold green] ({pct_done:.0f}%)"
        )
        console.print()
        console.print(Panel(header_text, border_style="cyan", title="Local LLM Benchmark Runner"))

        choices = [
            Choice("▶  1. Запустить ВСЁ непройденное (Run Missing)", value="run_missing"),
            Choice("📦 2. Запустить блок (Бенчмарк целиком: L1 + L2 + L3)", value="run_suite"),
            Choice("🎯 3. Запустить одно конкретное задание", value="run_single"),
            Choice("🔄 4. Перезапустить всё заново (с перезаписью)", value="run_force_all"),
            Choice("📊 5. Открыть единый дашборд (Рейтинг, Скорость устройств, Код)", value="open_report"),
            Choice("🔄 6. Синхронизировать с Git (records/ <-> bench.db)", value="sync_db"),
            Choice("⚙️  7. Настройки (Сменить модель / хост / сервер)", value="change_config"),
            Choice("❌ 0. Выход", value="exit"),
        ]

        action = questionary.select("Выбери действие:", choices=choices).ask()
        if action in ("exit", None):
            console.print("[dim]До встречи![/dim]")
            break

        if action == "run_missing":
            queue = []
            for b in REGISTRY:
                for level in b.levels:
                    if not store.has_result(b, model.key, level.id):
                        queue.append((b, level.id))
            run_queue(model, queue, host, force=False)

        elif action == "run_suite":
            suite_choices = [
                Choice(f"{b.short:10} | {b.code_lang:10} | {b.name} ({len(b.levels)} ур.)", value=b) for b in REGISTRY
            ]
            suite_choices.append(Choice("🔙 Назад", value=None))
            selected_bench = questionary.select("Выбери бенчмарк для запуска:", choices=suite_choices).ask()
            if selected_bench:
                queue = [(selected_bench, level.id) for level in selected_bench.levels]
                run_queue(model, queue, host, force=True)

        elif action == "run_single":
            suite_choices = [Choice(f"{b.short} ({b.code_lang})", value=b) for b in REGISTRY]
            suite_choices.append(Choice("🔙 Назад", value=None))
            selected_bench = questionary.select("Выбери бенчмарк:", choices=suite_choices).ask()
            if selected_bench:
                lvl_choices = [Choice(f"{level.name}", value=level.id) for level in selected_bench.levels]
                lvl_choices.append(Choice("🔙 Назад", value=None))
                lvl_id = questionary.select("Выбери уровень:", choices=lvl_choices).ask()
                if lvl_id:
                    run_queue(model, [(selected_bench, lvl_id)], host, force=True)

        elif action == "run_force_all":
            confirm = questionary.confirm("Перезапустить абсолютно все бенчмарки для этой модели?").ask()
            if confirm:
                queue = []
                for b in REGISTRY:
                    for level in b.levels:
                        queue.append((b, level.id))
                run_queue(model, queue, host, force=True)

        elif action == "open_report":
            report_path = generate_html_report(db)
            console.print(f"[green]✔ Отчёт сгенерирован: {report_path}[/green]")
            open_report_in_browser(report_path)

        elif action == "sync_db":
            res = sync_db_and_records(db)
            console.print("[bold green]✔ Синхронизация завершена:[/bold green]")
            console.print(
                f"   Импортировано из records/: {res['imported']['results']} результатов, {res['imported']['speeds']} замеров скорости"
            )
            console.print(
                f"   Экспортировано в records/: {res['exported']['results']} результатов, {res['exported']['speeds']} замеров скорости"
            )

        elif action == "change_config":
            sub = questionary.select(
                "Что изменить?",
                choices=[
                    Choice("Сменить модель", value="model"),
                    Choice("Сменить хост (железо)", value="host"),
                    Choice(f"🌐 Сменить адрес сервера (сейчас: {lmstudio.get_base_url()})", value="server"),
                    Choice("🔙 Назад", value=None),
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
                h_choices.append(Choice("➕ Создать новый хост", value="new"))
                sel_h = questionary.select("Выбери активный хост:", choices=h_choices).ask()
                if sel_h == "new":
                    lbl = questionary.text("Название хоста (железа):").ask()
                    if lbl and lbl.strip():
                        nh = HostConfig.create(lbl)
                        host_store.add(nh)
                        host_store.set_active(nh.id)
                        host = nh
                elif sel_h:
                    host_store.set_active(sel_h)
                    host = host_store.get(sel_h)


def main():
    # CLI аргументы: python main.py sync
    if len(sys.argv) > 1 and sys.argv[1] in ("sync", "--sync"):
        res = sync_db_and_records(db)
        console.print("[bold green]✔ База данных синхронизирована с records/:[/bold green]")
        console.print(
            f"   Импортировано:  {res['imported']['results']} результатов, {res['imported']['speeds']} замеров, {res['imported']['hosts']} хостов"
        )
        console.print(
            f"   Экспортировано: {res['exported']['results']} результатов, {res['exported']['speeds']} замеров, {res['exported']['hosts']} хостов"
        )
        return

    # CLI аргументы: python main.py report
    if len(sys.argv) > 1 and sys.argv[1] in ("report", "--report"):
        sync_db_and_records(db)
        report_path = generate_html_report(db)
        console.print(f"[green]✔ Отчёт сгенерирован: {report_path}[/green]")
        open_report_in_browser(report_path)
        return

    # Авто-синхронизация при старте
    try:
        sync_db_and_records(db)
    except Exception as e:
        console.print(f"[yellow]⚠️  Предупреждение синхронизации: {e}[/yellow]")

    host = get_or_choose_host()
    model = detect_or_select_model()
    if not model:
        return
    main_menu(model, host)


if __name__ == "__main__":
    main()
