import sys
from datetime import datetime
from pathlib import Path

import questionary
from questionary import Choice
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

import lmstudio
from benchmarks import BY_ID, REGISTRY
from benchmarks.base import Benchmark, GenerationStats, ManualResult, SpeedSample, StoredResult, TestResult
from host_configs import HostConfig, HostConfigStore
from lmstudio import Model
from storage import ResultStore, SpeedResultStore

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

console = Console(legacy_windows=False)

ROOT = Path(__file__).parent
store = ResultStore(
    answers_root=ROOT,
    raw_answers_dir=ROOT / "raw_answers",
    results_dir=ROOT / "results",
)
speed_store = SpeedResultStore(ROOT / "speed_results")
host_store = HostConfigStore(ROOT / "host_configs.json", ROOT / "active_host.json")

BACK = "__back__"


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def score_color(percent: float) -> str:
    if percent >= 80:
        return "green"
    if percent >= 40:
        return "yellow"
    return "red"


def make_bar(percent: float, width: int = 20) -> Text:
    filled = round(width * percent / 100)
    bar = "█" * filled + "░" * (width - filled)
    return Text(bar, style=score_color(percent))


def level_status_text(benchmark: Benchmark, model_key: str, level_id: str) -> Text:
    result = store.load(benchmark, model_key, level_id)
    if result is None:
        return Text("не тестировался", style="dim")
    color = score_color(result.percent())
    return Text(f"{result.format()} ({result.tested_at})", style=color)


def level_status_plain(benchmark: Benchmark, model_key: str, level_id: str) -> str:
    result = store.load(benchmark, model_key, level_id)
    if result is None:
        return "не тестировался"
    return f"{result.format()} ({result.tested_at})"


def generate_stats(response_stats: dict | None) -> GenerationStats:
    if not response_stats:
        return GenerationStats()
    return GenerationStats(
        input_tokens=response_stats.get("input_tokens"),
        total_output_tokens=response_stats.get("total_output_tokens"),
        reasoning_output_tokens=response_stats.get("reasoning_output_tokens"),
        tokens_per_second=response_stats.get("tokens_per_second"),
        time_to_first_token_seconds=response_stats.get("time_to_first_token_seconds"),
        model_load_time_seconds=response_stats.get("model_load_time_seconds"),
    )


def save_speed_sample(host: HostConfig, model: Model, benchmark: Benchmark, level_id: str, response_stats: dict | None) -> None:
    stats = generate_stats(response_stats)
    if stats.tokens_per_second is None:
        return

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
    console.print(
        f"  [cyan]speed:[/cyan] {model.key} / {host.label} -> {stats.tokens_per_second:.2f} tok/s"
    )


def ensure_active_host() -> HostConfig | None:
    active = host_store.get_active()
    if active is not None:
        return active
    return choose_host_config()


def ensure_level_answer(model: Model, benchmark: Benchmark, level_id: str, host: HostConfig) -> Path | None:
    """Гарантирует наличие ответа модели для данного уровня, генерируя предыдущие уровни
    при необходимости. Возвращает путь к файлу с кодом или None при ошибке."""
    level = benchmark.level_by_id(level_id)
    answer_path, raw_path, _ = store.paths_for(benchmark, model.key, level_id)
    speed_path = speed_store.path_for(host.id, model.key, benchmark.id, level_id)

    if answer_path.exists() and speed_path.exists():
        return answer_path

    messages = []
    if level.requires:
        prev_answer_path = ensure_level_answer(model, benchmark, level.requires, host)
        if prev_answer_path is None:
            return None
        _, prev_raw_path, _ = store.paths_for(benchmark, model.key, level.requires)
        messages.append({"role": "user", "content": benchmark.level_by_id(level.requires).prompt})
        messages.append({"role": "assistant", "content": prev_raw_path.read_text(encoding="utf-8")})

    messages.append({"role": "user", "content": level.prompt})

    console.print(f"  Отправляю задание [bold]«{level.name}»[/bold] модели (ждём ответ, таймаут не ограничен)...")
    try:
        response = lmstudio.ask_model(model.key, messages)
    except Exception as e:
        console.print(f"  [red]error:[/red] модель не ответила: {e}")
        return None

    raw_path.write_text(response.content, encoding="utf-8")
    save_speed_sample(host, model, benchmark, level_id, response.stats)
    code = benchmark.extract_code(response.content)
    answer_path.write_text(code, encoding="utf-8")
    console.print(f"  Ответ сохранён в [cyan]{answer_path}[/cyan] (сырой ответ — в [dim]{raw_path}[/dim])")
    return answer_path


def run_manual_level(model: Model, benchmark: Benchmark, level_id: str, answer_path: Path) -> None:
    console.print(f"\n  Ответ сохранён в файл:\n    [cyan]{answer_path}[/cyan]")
    console.print("  Открой этот файл в браузере и оцени результат вручную.")

    score = None
    while score is None:
        score = questionary.select(
            "Оценка от 1 до 10:",
            choices=[Choice(title=str(i), value=i) for i in range(1, 11)],
        ).ask()

    comment = questionary.text("Комментарий (необязательно):").ask() or ""

    result = StoredResult(
        model=model.key,
        benchmark=benchmark.id,
        level=level_id,
        tested_at=now_str(),
        evaluation=ManualResult(score=score, comment=comment),
    )
    store.save(benchmark, model.key, level_id, result)
    console.print(f"\n  Результат [bold]{model.key}[/bold] / {benchmark.level_by_id(level_id).name}: [bold]{score}/10[/bold]")


def run_level(model: Model, benchmark: Benchmark, level_id: str) -> None:
    level = benchmark.level_by_id(level_id)
    console.rule(f"[bold]{model.key}[/bold] — {benchmark.name} / {level.name}")

    host = ensure_active_host()
    if host is None:
        return

    answer_path = ensure_level_answer(model, benchmark, level_id, host)
    if answer_path is None:
        return

    console.print("  Выгружаю модель из памяти...")
    lmstudio.unload_model(model.key, console=console)

    if level_id in benchmark.manual_levels:
        run_manual_level(model, benchmark, level_id, answer_path)
        return

    test_result: TestResult = benchmark.run_tests(level_id, answer_path)
    color = score_color(test_result.percent())
    console.print(f"\n  Результат [bold]{model.key}[/bold] / {level.name}: [{color}]{test_result.format()}[/{color}]")

    result = StoredResult(
        model=model.key,
        benchmark=benchmark.id,
        level=level_id,
        tested_at=now_str(),
        evaluation=test_result,
    )
    store.save(benchmark, model.key, level_id, result)


def format_host_label(host: HostConfig, active_id: str | None) -> str:
    prefix = "* " if host.id == active_id else "  "
    return f"{prefix}{host.label} [{host.id}]"


def create_host_config() -> HostConfig | None:
    label = questionary.text("Введите конфигурацию ПК (например, Ryzen 7 7840U | 32 GB | RTX 4070):").ask()
    if not label:
        return None
    host = HostConfig.create(label)
    host_store.add(host)
    host_store.set_active(host.id)
    console.print(f"  Конфигурация сохранена: [bold]{host.label}[/bold] ([cyan]{host.id}[/cyan])")
    return host


def choose_host_config() -> HostConfig | None:
    while True:
        hosts = host_store.load_all()
        active_id = host_store.load_active_id()

        choices = [Choice(title="Создать новую конфигурацию", value="__new__")]
        for host in hosts:
            choices.append(Choice(title=format_host_label(host, active_id), value=host.id))
        choices.append(Choice(title="« Назад", value=BACK))

        selected = questionary.select("Выберите конфигурацию ПК:", choices=choices).ask()

        if selected in (None, BACK):
            return host_store.get_active()
        if selected == "__new__":
            host = create_host_config()
            if host is not None:
                return host
            continue

        host = host_store.get(selected)
        if host is None:
            continue
        host_store.set_active(host.id)
        return host


def quality_averages_by_model() -> dict[str, float]:
    by_model: dict[str, list[float]] = {}
    for result in store.all_saved():
        by_model.setdefault(result.model, []).append(result.percent())
    return {model: sum(values) / len(values) for model, values in by_model.items() if values}


def show_speed_leaderboard() -> None:
    host = choose_host_config()
    if host is None:
        console.print("[yellow]Сначала создайте или выберите конфигурацию ПК.[/yellow]")
        return

    samples = [
        sample
        for sample in speed_store.all_saved()
        if sample.host_id == host.id and sample.stats.tokens_per_second is not None
    ]
    if not samples:
        console.print(f"[yellow]Для конфигурации {host.label} пока нет speed-результатов.[/yellow]")
        return

    by_model: dict[str, list[SpeedSample]] = {}
    for sample in samples:
        by_model.setdefault(sample.model, []).append(sample)

    quality_by_model = quality_averages_by_model()
    rows = []
    for model_key, items in by_model.items():
        speeds = [item.stats.tokens_per_second for item in items if item.stats.tokens_per_second is not None]
        if not speeds:
            continue
        avg_speed = sum(speeds) / len(speeds)
        avg_quality = quality_by_model.get(model_key)
        rows.append((model_key, avg_speed, avg_quality, len(speeds)))

    rows.sort(key=lambda row: row[1], reverse=True)

    table = Table(title=f"Рейтинг скорости — {host.label}", padding=(0, 1))
    table.add_column("#", justify="right", style="bold cyan")
    table.add_column("Модель", style="bold")
    table.add_column("Токенов/с", justify="right")
    table.add_column("Оценка", justify="right")
    table.add_column("Сэмплов", justify="right")

    for i, (model_key, avg_speed, avg_quality, count) in enumerate(rows, start=1):
        quality_text = "—" if avg_quality is None else f"{avg_quality:.0f}%"
        quality_style = "dim" if avg_quality is None else score_color(avg_quality)
        table.add_row(
            str(i),
            model_key,
            f"{avg_speed:.2f}",
            Text(quality_text, style=quality_style),
            str(count),
        )

    console.print(table)


def print_models_menu(benchmark: Benchmark, models: list[Model]) -> None:
    table = Table(title=f"Модели в LM Studio — {benchmark.name}", box=None, padding=(0, 1))
    table.add_column("#", justify="right", style="bold cyan")
    table.add_column("Модель", style="bold")
    for level_id in benchmark.level_order:
        table.add_column(benchmark.level_by_id(level_id).name)

    for i, model in enumerate(models, start=1):
        row = [str(i), model.key]
        row.extend(level_status_text(benchmark, model.key, level_id) for level_id in benchmark.level_order)
        table.add_row(*row)

    console.print(table)

    known_keys = {m.key for m in models}
    archived_keys = sorted({
        r.model for r in store.all_saved() if r.benchmark == benchmark.id and r.model not in known_keys
    })

    if archived_keys:
        archive_table = Table(
            title="Архивные результаты (модель сейчас недоступна в LM Studio)",
            box=None,
            padding=(0, 1),
            title_style="dim italic",
        )
        archive_table.add_column("Модель", style="dim")
        for level_id in benchmark.level_order:
            archive_table.add_column(benchmark.level_by_id(level_id).name)

        for model_key in archived_keys:
            row = [model_key]
            row.extend(level_status_text(benchmark, model_key, level_id) for level_id in benchmark.level_order)
            archive_table.add_row(*row)

        console.print(archive_table)


def print_levels_menu(model: Model, benchmark: Benchmark) -> None:
    table = Table(title=f"{model.key} — {benchmark.name}", box=None, padding=(0, 1))
    table.add_column("#", justify="right", style="bold cyan")
    table.add_column("Уровень")
    table.add_column("Статус")
    for i, level_id in enumerate(benchmark.level_order, start=1):
        table.add_row(str(i), benchmark.level_by_id(level_id).name, level_status_text(benchmark, model.key, level_id))
    console.print(table)


def choose_level(model: Model, benchmark: Benchmark) -> None:
    while True:
        print_levels_menu(model, benchmark)

        choices = [
            Choice(
                title=f"{benchmark.level_by_id(level_id).name} — {level_status_plain(benchmark, model.key, level_id)}",
                value=level_id,
            )
            for level_id in benchmark.level_order
        ]
        choices.append(Choice(title="« Назад", value=BACK))

        level_id = questionary.select("Выберите уровень:", choices=choices).ask()

        if level_id in (None, BACK):
            return

        _, _, result_path = store.paths_for(benchmark, model.key, level_id)

        if result_path.exists():
            existing = store.load(benchmark, model.key, level_id)
            failures = existing.failures if existing else []
            if failures:
                console.print(f"\n  [yellow]Провалено тестов: {len(failures)}[/yellow]")
                for f in failures:
                    console.print(f"    [red]•[/red] {f}")

            redo = questionary.select(
                "Этот уровень уже протестирован:",
                choices=[
                    Choice(title="Перезапустить тесты на сохранённом коде", value="t"),
                    Choice(title="Запросить у модели заново", value="r"),
                    Choice(title="Отмена", value="c"),
                ],
            ).ask()
            if redo in (None, "c"):
                continue
            if redo == "r":
                console.print("  Удаляю сохранённые ответ/сырой ответ/результат для этого уровня...")
                store.clear(benchmark, model.key, level_id)

        run_level(model, benchmark, level_id)


def choose_model(benchmark: Benchmark) -> None:
    while True:
        try:
            models = lmstudio.list_llm_models()
        except Exception as e:
            console.print(f"[red]Не удалось получить список моделей: {e}[/red]")
            sys.exit(1)

        if not models:
            console.print("[yellow]LM Studio не вернул ни одной LLM модели.[/yellow]")
            return

        print_models_menu(benchmark, models)

        choices = [
            Choice(
                title=f"{model.key}  —  "
                + "  |  ".join(
                    f"{benchmark.level_by_id(level_id).name}: {level_status_plain(benchmark, model.key, level_id)}"
                    for level_id in benchmark.level_order
                ),
                value=i,
            )
            for i, model in enumerate(models)
        ]
        choices.append(Choice(title="« Назад к выбору теста", value=BACK))

        selected = questionary.select("Выберите модель:", choices=choices).ask()

        if selected in (None, BACK):
            return

        choose_level(models[selected], benchmark)


def show_leaderboard() -> None:
    results = store.all_saved()
    if not results:
        console.print("[yellow]Пока нет ни одного сохранённого результата.[/yellow]")
        return

    columns = [
        (benchmark.id, level_id)
        for benchmark in REGISTRY
        for level_id in benchmark.level_order
    ]

    by_model: dict[str, dict[tuple[str, str], StoredResult]] = {}
    for r in results:
        by_model.setdefault(r.model, {})[(r.benchmark, r.level)] = r

    rows = []
    for model_key, entries in by_model.items():
        percents = [r.percent() for r in entries.values()]
        avg = sum(percents) / len(percents) if percents else 0.0
        rows.append((model_key, entries, avg))

    rows.sort(key=lambda row: row[2], reverse=True)

    table = Table(title="Рейтинг моделей (среднее по всем пройденным тестам)", padding=(0, 1))
    table.add_column("#", justify="right", style="bold cyan")
    table.add_column("Модель", style="bold")
    for benchmark_id, level_id in columns:
        table.add_column(f"{BY_ID[benchmark_id].short}\nL{level_id[-1]}", justify="center")
    table.add_column("Средний %", justify="right")
    table.add_column("", min_width=22)

    for i, (model_key, entries, avg) in enumerate(rows, start=1):
        row = [str(i), model_key]
        for benchmark_id, level_id in columns:
            result = entries.get((benchmark_id, level_id))
            if result is None:
                row.append(Text("—", style="dim"))
            else:
                row.append(Text(result.format(), style=score_color(result.percent())))
        row.append(Text(f"{avg:.0f}%", style=f"bold {score_color(avg)}"))
        row.append(make_bar(avg))
        table.add_row(*row)

    console.print(table)


def main():
    store.ensure_dirs(REGISTRY)
    speed_store.ensure_dir()

    console.print(Panel("[bold]Добро пожаловать в бенчмарк локальных моделей![/bold]", border_style="green"))

    LEADERBOARD = "__leaderboard__"
    SPEEDBOARD = "__speedboard__"
    HOSTS = "__hosts__"
    EXIT = "__exit__"

    while True:
        choices = [Choice(title=benchmark.name, value=benchmark.id) for benchmark in REGISTRY]
        choices.append(Choice(title="📊 Общий рейтинг моделей", value=LEADERBOARD))
        choices.append(Choice(title="⚡ Рейтинг скорости по конфигурации ПК", value=SPEEDBOARD))
        choices.append(Choice(title="🖥️ Конфигурации ПК", value=HOSTS))
        choices.append(Choice(title="Выход", value=EXIT))

        choice = questionary.select("Выберите тест:", choices=choices).ask()

        if choice in (None, EXIT):
            console.print("Пока!")
            break

        if choice == LEADERBOARD:
            show_leaderboard()
            continue

        if choice == SPEEDBOARD:
            show_speed_leaderboard()
            continue

        if choice == HOSTS:
            choose_host_config()
            continue

        choose_model(BY_ID[choice])


if __name__ == "__main__":
    main()
