import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import questionary
import requests
from questionary import Choice
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

import bench
import kv_bench
import scheduler_bench

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

console = Console(legacy_windows=False)

BASE_URL = "http://127.0.0.1:1234"
ANSWERS_DIR = Path(__file__).parent / "models_answers"
HTML_ANSWERS_DIR = Path(__file__).parent / "html_answers"
RAW_ANSWERS_DIR = Path(__file__).parent / "raw_answers"
RESULTS_DIR = Path(__file__).parent / "results"


# --- VM benchmark (см. vm.md) ---------------------------------------------

VM_LEVEL1_PROMPT = """\
Реализуй интерпретатор простого стекового языка в одном Python файле.

Поддерживаемые инструкции (одна на строку, аргументы через пробел):
PUSH <n>  — положить число n на стек
POP       — снять значение со стека
ADD       — снять два значения, положить их сумму
SUB       — снять два значения (b, затем a), положить a - b
MUL       — снять два значения, положить произведение
DIV       — снять два значения (b, затем a), положить a / b (целочисленное деление)
DUP       — продублировать значение на вершине стека
SWAP      — поменять местами два верхних значения стека
PRINT     — вывести значение на вершине стека (не снимая его)

Программа передаётся как многострочный текст. Пустые строки и строки, начинающиеся с "#", — комментарии, их нужно игнорировать.

Требования:
- Один файл, без внешних зависимостей.
- Если стека не хватает для операции — кинуть понятную ошибку с номером строки.
- Деление на ноль — понятная ошибка с номером строки.
- Добавь функцию run(program: str) -> list[str], возвращающую список выведенных строк (то, что напечатал PRINT).

В ответе верни только код одним блоком ```python ... ```, без дополнительных пояснений вне блока.
"""

VM_LEVEL2_PROMPT = """\
Дополни свою реализацию поддержкой меток и условных переходов:

LABEL <name>   — определяет метку в текущей позиции (ничего не делает при выполнении)
JMP <name>     — безусловный переход к метке
JZ <name>      — снять значение со стека, перейти к метке, если оно == 0
JNZ <name>     — снять значение со стека, перейти к метке, если оно != 0

Не меняй поведение уже реализованных инструкций и сохрани сигнатуру run(program: str) -> list[str].

В ответе верни только код одним блоком ```python ... ```, без дополнительных пояснений вне блока.
"""


def _vm_test_runner(answer_path, tests, name):
    try:
        run_fn = bench.load_run(str(answer_path))
    except Exception as e:
        console.print(f"  [red]error:[/red] не удалось загрузить решение: {e}")
        return 0, len(tests), [f"не удалось загрузить решение: {e}"]
    return bench.run_suite(name, tests, run_fn)


# --- Scheduler benchmark (топологическая сортировка + критический путь) ---

SCHEDULER_LEVEL1_PROMPT = """\
Реализуй планировщик задач с зависимостями в одном Python файле.

def topo_sort(tasks: dict[str, list[str]]) -> list[str] | None

tasks — словарь, где ключ — имя задачи (строка), а значение — список имён задач,
от которых она зависит (эти задачи должны быть выполнены раньше).

Функция должна вернуть список имён всех задач в порядке, при котором каждая задача
идёт строго после всех своих зависимостей (топологическая сортировка).
Если в графе зависимостей есть цикл — верни None.

Требования:
- Один файл, без внешних зависимостей (никаких networkx и т.п.).
- Порядок среди задач, не зависящих друг от друга, может быть любым — важно только,
  чтобы зависимости шли раньше зависимых от них задач.

В ответе верни только код одним блоком ```python ... ```, без дополнительных пояснений вне блока.
"""

SCHEDULER_LEVEL2_PROMPT = """\
Дополни свою реализацию функцией расчёта критического пути:

def critical_path(tasks: dict[str, tuple[int, list[str]]]) -> int | None

tasks — словарь, где значение — кортеж (длительность_задачи, список_зависимостей).
Функция должна вернуть длину критического пути — суммарную длительность самой долгой
по времени цепочки зависимых друг от друга задач (classic critical path method).
Если в графе зависимостей есть цикл — верни None.

Не меняй сигнатуру и поведение topo_sort.

В ответе верни только код одним блоком ```python ... ```, без дополнительных пояснений вне блока.
"""


def _scheduler_level1_runner(answer_path):
    try:
        fn = scheduler_bench.load_function(str(answer_path), "topo_sort")
    except Exception as e:
        console.print(f"  [red]error:[/red] не удалось загрузить решение: {e}")
        return 0, len(scheduler_bench.LEVEL1_TESTS)
    return scheduler_bench.run_level1_suite(fn)


def _scheduler_level2_runner(answer_path):
    try:
        fn = scheduler_bench.load_function(str(answer_path), "critical_path")
    except Exception as e:
        console.print(f"  [red]error:[/red] не удалось загрузить решение: {e}")
        return 0, len(scheduler_bench.LEVEL2_TESTS)
    return scheduler_bench.run_level2_suite(fn)


# --- Key-Value store benchmark (транзакции: BEGIN/COMMIT/ROLLBACK) --------

KV_LEVEL1_PROMPT = """\
Реализуй in-memory key-value хранилище с вложенными транзакциями в одном Python файле.

Поддерживаемые команды (одна на строку, аргументы через пробел):
SET <key> <value>  — установить значение ключа
GET <key>          — вывести текущее значение ключа, или "NULL", если ключ не установлен
DELETE <key>       — удалить ключ (если ключа нет — ничего не делать, без ошибки)
BEGIN              — начать новую (возможно вложенную) транзакцию
COMMIT             — зафиксировать самую внутреннюю открытую транзакцию, слив её изменения
                     в родительскую транзакцию (а не сразу в глобальное хранилище, если
                     это вложенная транзакция). Если открытых транзакций нет — вывести
                     "NO TRANSACTION"
ROLLBACK           — откатить самую внутреннюю открытую транзакцию, отменив все изменения,
                     сделанные внутри неё. Если открытых транзакций нет — вывести
                     "NO TRANSACTION"

Пустые строки — игнорировать.

Требования:
- Один файл, без внешних зависимостей.
- Транзакции можно вкладывать друг в друга произвольно глубоко.
- Изменения внутри транзакции должны быть видны через GET сразу же (даже до COMMIT),
  но должны полностью отменяться при ROLLBACK.
- Добавь функцию run(program: str) -> list[str], возвращающую список строк вывода —
  по одной строке для каждой команды GET, а также для COMMIT/ROLLBACK, если они вывели
  "NO TRANSACTION" (остальные команды вывода не производят).

В ответе верни только код одним блоком ```python ... ```, без дополнительных пояснений вне блока.
"""

KV_LEVEL2_PROMPT = """\
Дополни свою реализацию двумя новыми командами:

COUNT <value>  — вывести количество ключей, чьё текущее значение (с учётом открытых
                транзакций) равно <value>
WATCH <key>    — начать наблюдение за ключом. С этого момента при любом SET или DELETE,
                которые меняют видимое в данный момент значение этого ключа (включая
                изменения внутри ещё не зафиксированных транзакций), сразу вывести строку:
                "WATCH <key> <старое_значение> -> <новое_значение>"
                где вместо отсутствующего значения используется "NULL".
                Если SET устанавливает то же значение, что было — уведомление не выводится.
                Уведомления о WATCH выводятся сразу в момент выполнения SET/DELETE, а не
                при COMMIT/ROLLBACK.

Не меняй поведение уже реализованных команд и сохрани сигнатуру run(program: str) -> list[str].

В ответе верни только код одним блоком ```python ... ```, без дополнительных пояснений вне блока.
"""


def _kv_test_runner(answer_path, tests, name):
    try:
        run_fn = bench.load_run(str(answer_path))
    except Exception as e:
        console.print(f"  [red]error:[/red] не удалось загрузить решение: {e}")
        return 0, len(tests)
    return bench.run_suite(name, tests, run_fn)


# --- Snake benchmark (одностраничная HTML-игра, оценивается вручную) ------

SNAKE_LEVEL1_PROMPT = """\
Реализуй классическую игру "Змейка" в одном HTML файле (HTML + CSS + JS всё внутри
одного файла, без внешних библиотек, CDN и подключений через интернет).

Требования:
- Управление змейкой стрелками на клавиатуре (или WASD).
- Змейка растёт при поедании еды; столкновение со стеной или с собой — game over.
- Отображение текущего счёта на экране.
- Возможность перезапустить игру после game over (например, по нажатию клавиши).
- Файл должен открываться и работать сразу после сохранения и открытия в браузере
  двойным кликом — без сборки, без сервера, без npm.

В ответе верни только код одним блоком ```html ... ```, без дополнительных пояснений вне блока.
"""

SNAKE_LEVEL2_PROMPT = """\
Дополни свою реализацию визуальными эффектами, не меняя базовую механику игры:
- анимации/плавные переходы движения змейки или появления еды;
- эффект при поедании еды (вспышка, частицы, изменение цвета и т.п.);
- красиво оформленный экран Game Over (с анимацией);
- любые другие визуальные улучшения на твой вкус (тени, градиенты, свечение и т.п.).

Игра должна остаться полностью рабочей и по-прежнему быть одним HTML файлом без
внешних зависимостей.

В ответе верни только код одним блоком ```html ... ```, без дополнительных пояснений вне блока.
"""


# --- Реестр бенчмарков ------------------------------------------------------
# requires: id предыдущего уровня в этом же бенчмарке, чей промпт и ответ
# подмешиваются в диалог перед промптом текущего уровня.

BENCHMARKS = {
    "vm": {
        "name": "Стековая VM (PUSH/ADD/.../LABEL/JMP)",
        "short": "VM",
        "levels": {
            "level1": {
                "name": "Level 1 (базовые инструкции)",
                "prompt": VM_LEVEL1_PROMPT,
                "requires": None,
                "runner": lambda answer_path: _vm_test_runner(answer_path, bench.LEVEL1_TESTS, "Level 1"),
            },
            "level2": {
                "name": "Level 2 (LABEL/JMP/JZ/JNZ)",
                "prompt": VM_LEVEL2_PROMPT,
                "requires": "level1",
                "runner": lambda answer_path: _vm_test_runner(
                    answer_path, bench.LEVEL1_TESTS + bench.LEVEL2_TESTS, "Level 2"
                ),
            },
        },
        "level_order": ["level1", "level2"],
    },
    "scheduler": {
        "name": "Планировщик задач (topo sort + critical path)",
        "short": "Scheduler",
        "levels": {
            "level1": {
                "name": "Level 1 (topo_sort + циклы)",
                "prompt": SCHEDULER_LEVEL1_PROMPT,
                "requires": None,
                "runner": _scheduler_level1_runner,
            },
            "level2": {
                "name": "Level 2 (critical_path)",
                "prompt": SCHEDULER_LEVEL2_PROMPT,
                "requires": "level1",
                "runner": _scheduler_level2_runner,
            },
        },
        "level_order": ["level1", "level2"],
    },
    "kv": {
        "name": "KV-хранилище с транзакциями (SET/GET/BEGIN/COMMIT/ROLLBACK)",
        "short": "KV",
        "levels": {
            "level1": {
                "name": "Level 1 (SET/GET/DELETE + транзакции)",
                "prompt": KV_LEVEL1_PROMPT,
                "requires": None,
                "runner": lambda answer_path: _kv_test_runner(answer_path, kv_bench.LEVEL1_TESTS, "Level 1"),
            },
            "level2": {
                "name": "Level 2 (COUNT/WATCH)",
                "prompt": KV_LEVEL2_PROMPT,
                "requires": "level1",
                "runner": lambda answer_path: _kv_test_runner(
                    answer_path, kv_bench.LEVEL1_TESTS + kv_bench.LEVEL2_TESTS, "Level 2"
                ),
            },
        },
        "level_order": ["level1", "level2"],
    },
    "snake": {
        "name": "Змейка на HTML (оценивается вручную)",
        "short": "Snake",
        "answers_dir": HTML_ANSWERS_DIR,
        "file_ext": "html",
        "code_lang": "html",
        "levels": {
            "level1": {
                "name": "Level 1 (базовая игра)",
                "prompt": SNAKE_LEVEL1_PROMPT,
                "requires": None,
                "manual": True,
            },
            "level2": {
                "name": "Level 2 (визуальные эффекты)",
                "prompt": SNAKE_LEVEL2_PROMPT,
                "requires": "level1",
                "manual": True,
            },
        },
        "level_order": ["level1", "level2"],
    },
}
BENCHMARK_ORDER = ["vm", "scheduler", "kv", "snake"]


@dataclass
class Model:
    type: str
    key: str

    @classmethod
    def from_dict(cls, data: dict):
        return cls(type=data.get("type"), key=data.get("key"))


def list_llm_models() -> list[Model]:
    models = requests.get(f"{BASE_URL}/api/v1/models").json()
    return [Model.from_dict(m) for m in models["models"] if m["type"] == "llm"]


def safe_filename(key: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]", "_", key)


def extract_code(text: str, lang: str = "python") -> str:
    """Достаёт код из ```<lang> ... ``` блока (последнего, если их несколько — модель могла
    сначала показать черновик/другой язык, а затем финальный вариант).
    Если явного блока с этой меткой языка нет — берёт последний блок без метки языка.
    Если блоков нет вообще — возвращает текст как есть."""
    lang_blocks = re.findall(rf"```{re.escape(lang)}\s*\n(.*?)```", text, re.DOTALL)
    if lang_blocks:
        return lang_blocks[-1].strip() + "\n"

    any_blocks = re.findall(r"```(?:\w*)\s*\n(.*?)```", text, re.DOTALL)
    if any_blocks:
        return any_blocks[-1].strip() + "\n"

    return text.strip() + "\n"


def ask_model(model_key: str, messages: list[dict]) -> str:
    response = requests.post(
        f"{BASE_URL}/v1/chat/completions",
        json={"model": model_key, "messages": messages, "temperature": 0.2},
        timeout=None,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


def loaded_instance_ids(model_key: str) -> list[str]:
    models = requests.get(f"{BASE_URL}/api/v1/models", timeout=30).json()["models"]
    for m in models:
        if m["key"] == model_key:
            return [instance["id"] for instance in m.get("loaded_instances", [])]
    return []


def unload_model(model_key: str) -> None:
    try:
        instance_ids = loaded_instance_ids(model_key)
    except Exception as e:
        console.print(f"  [yellow]warn:[/yellow] не удалось получить loaded_instances: {e}")
        return

    if not instance_ids:
        console.print(f"  [yellow]warn:[/yellow] нет загруженных инстансов для {model_key}, выгружать нечего.")
        return

    for instance_id in instance_ids:
        try:
            requests.post(
                f"{BASE_URL}/api/v1/models/unload",
                json={"instance_id": instance_id},
                timeout=60,
            )
        except Exception as e:
            console.print(f"  [yellow]warn:[/yellow] не удалось выгрузить инстанс {instance_id}: {e}")


def paths_for(model_key: str, benchmark_id: str, level_id: str) -> tuple[Path, Path, Path]:
    benchmark = BENCHMARKS[benchmark_id]
    answers_dir = benchmark.get("answers_dir", ANSWERS_DIR)
    file_ext = benchmark.get("file_ext", "py")
    key = safe_filename(model_key)
    answer_path = answers_dir / f"{key}_{benchmark_id}_{level_id}.{file_ext}"
    raw_path = RAW_ANSWERS_DIR / f"{key}_{benchmark_id}_{level_id}.txt"
    result_path = RESULTS_DIR / f"{key}_{benchmark_id}_{level_id}.json"
    return answer_path, raw_path, result_path


def load_result(result_path: Path) -> dict | None:
    if not result_path.exists():
        return None
    return json.loads(result_path.read_text(encoding="utf-8"))


def all_saved_results() -> list[dict]:
    """Все результаты, сохранённые на диске (results/*.json), независимо от того,
    доступна ли сейчас соответствующая модель в LM Studio."""
    results = []
    for path in sorted(RESULTS_DIR.glob("*.json")):
        try:
            results.append(json.loads(path.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError):
            continue
    return results


def save_result(result_path: Path, model_key: str, benchmark_id: str, level_id: str, passed: int, total: int) -> None:
    result_path.write_text(
        json.dumps(
            {
                "model": model_key,
                "benchmark": benchmark_id,
                "level": level_id,
                "tested_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "passed": passed,
                "total": total,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def save_manual_result(result_path: Path, model_key: str, benchmark_id: str, level_id: str, score: int, comment: str) -> None:
    result_path.write_text(
        json.dumps(
            {
                "model": model_key,
                "benchmark": benchmark_id,
                "level": level_id,
                "tested_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "manual_score": score,
                "comment": comment,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def ensure_level_answer(model: Model, benchmark_id: str, level_id: str) -> Path | None:
    """Гарантирует наличие ответа модели для данного уровня, генерируя предыдущие уровни
    при необходимости. Возвращает путь к файлу с кодом или None при ошибке."""
    benchmark = BENCHMARKS[benchmark_id]
    level = benchmark["levels"][level_id]
    answer_path, raw_path, _ = paths_for(model.key, benchmark_id, level_id)

    if answer_path.exists():
        return answer_path

    messages = []
    if level["requires"]:
        prev_id = level["requires"]
        prev_answer_path = ensure_level_answer(model, benchmark_id, prev_id)
        if prev_answer_path is None:
            return None
        _, prev_raw_path, _ = paths_for(model.key, benchmark_id, prev_id)
        messages.append({"role": "user", "content": benchmark["levels"][prev_id]["prompt"]})
        messages.append({"role": "assistant", "content": prev_raw_path.read_text(encoding="utf-8")})

    messages.append({"role": "user", "content": level["prompt"]})

    console.print(f"  Отправляю задание [bold]«{level['name']}»[/bold] модели (ждём ответ, таймаут не ограничен)...")
    try:
        answer_text = ask_model(model.key, messages)
    except Exception as e:
        console.print(f"  [red]error:[/red] модель не ответила: {e}")
        return None

    raw_path.write_text(answer_text, encoding="utf-8")
    code = extract_code(answer_text, lang=benchmark.get("code_lang", "python"))
    answer_path.write_text(code, encoding="utf-8")
    console.print(f"  Ответ сохранён в [cyan]{answer_path}[/cyan] (сырой ответ — в [dim]{raw_path}[/dim])")
    return answer_path


def clear_level(model: Model, benchmark_id: str, level_id: str) -> None:
    for path in paths_for(model.key, benchmark_id, level_id):
        path.unlink(missing_ok=True)


def run_manual_level(model: Model, benchmark_id: str, level_id: str, answer_path: Path) -> None:
    console.print(f"\n  Ответ сохранён в файл:\n    [cyan]{answer_path}[/cyan]")
    console.print("  Открой этот файл в браузере и оцени результат вручную.")

    score = None
    while score is None:
        score = questionary.select(
            "Оценка от 1 до 10:",
            choices=[Choice(title=str(i), value=i) for i in range(1, 11)],
        ).ask()

    comment = questionary.text("Комментарий (необязательно):").ask() or ""

    _, _, result_path = paths_for(model.key, benchmark_id, level_id)
    save_manual_result(result_path, model.key, benchmark_id, level_id, score, comment)
    console.print(
        f"\n  Результат [bold]{model.key}[/bold] / {BENCHMARKS[benchmark_id]['levels'][level_id]['name']}: "
        f"[bold]{score}/10[/bold]"
    )


def run_level(model: Model, benchmark_id: str, level_id: str) -> None:
    benchmark = BENCHMARKS[benchmark_id]
    level = benchmark["levels"][level_id]
    console.rule(f"[bold]{model.key}[/bold] — {benchmark['name']} / {level['name']}")

    answer_path = ensure_level_answer(model, benchmark_id, level_id)
    if answer_path is None:
        return

    console.print("  Выгружаю модель из памяти...")
    unload_model(model.key)

    if level.get("manual"):
        run_manual_level(model, benchmark_id, level_id, answer_path)
        return

    passed, total = level["runner"](answer_path)
    color = "green" if total and passed == total else ("yellow" if passed else "red")
    console.print(f"\n  Результат [bold]{model.key}[/bold] / {level['name']}: [{color}]{passed}/{total}[/{color}]")

    _, _, result_path = paths_for(model.key, benchmark_id, level_id)
    save_result(result_path, model.key, benchmark_id, level_id, passed, total)


def score_percent(result: dict) -> float:
    if "manual_score" in result:
        return result["manual_score"] / 10 * 100
    if result.get("total"):
        return result["passed"] / result["total"] * 100
    return 0.0


def format_score(result: dict) -> str:
    if "manual_score" in result:
        return f"{result['manual_score']}/10"
    return f"{result['passed']}/{result['total']}"


def score_color(percent: float) -> str:
    if percent >= 80:
        return "green"
    if percent >= 40:
        return "yellow"
    return "red"


def level_status_text(model_key: str, benchmark_id: str, level_id: str) -> Text:
    _, _, result_path = paths_for(model_key, benchmark_id, level_id)
    result = load_result(result_path)
    if result is None:
        return Text("не тестировался", style="dim")
    percent = score_percent(result)
    color = score_color(percent)
    return Text(f"{format_score(result)} ({result['tested_at']})", style=color)


def level_status_plain(model_key: str, benchmark_id: str, level_id: str) -> str:
    _, _, result_path = paths_for(model_key, benchmark_id, level_id)
    result = load_result(result_path)
    if result is None:
        return "не тестировался"
    return f"{format_score(result)} ({result['tested_at']})"


def print_models_menu(benchmark_id: str, models: list[Model]) -> None:
    benchmark = BENCHMARKS[benchmark_id]

    table = Table(title=f"Модели в LM Studio — {benchmark['name']}", box=None, padding=(0, 1))
    table.add_column("#", justify="right", style="bold cyan")
    table.add_column("Модель", style="bold")
    for level_id in benchmark["level_order"]:
        table.add_column(benchmark["levels"][level_id]["name"])

    for i, model in enumerate(models, start=1):
        row = [str(i), model.key]
        row.extend(level_status_text(model.key, benchmark_id, level_id) for level_id in benchmark["level_order"])
        table.add_row(*row)

    console.print(table)

    known_keys = {m.key for m in models}
    archived_keys = sorted({
        r["model"]
        for r in all_saved_results()
        if r.get("benchmark") == benchmark_id and r["model"] not in known_keys
    })

    if archived_keys:
        archive_table = Table(
            title="Архивные результаты (модель сейчас недоступна в LM Studio)",
            box=None,
            padding=(0, 1),
            title_style="dim italic",
        )
        archive_table.add_column("Модель", style="dim")
        for level_id in benchmark["level_order"]:
            archive_table.add_column(benchmark["levels"][level_id]["name"])

        for model_key in archived_keys:
            row = [model_key]
            row.extend(level_status_text(model_key, benchmark_id, level_id) for level_id in benchmark["level_order"])
            archive_table.add_row(*row)

        console.print(archive_table)


def print_levels_menu(model: Model, benchmark_id: str) -> None:
    benchmark = BENCHMARKS[benchmark_id]
    table = Table(title=f"{model.key} — {benchmark['name']}", box=None, padding=(0, 1))
    table.add_column("#", justify="right", style="bold cyan")
    table.add_column("Уровень")
    table.add_column("Статус")
    for i, level_id in enumerate(benchmark["level_order"], start=1):
        table.add_row(str(i), benchmark["levels"][level_id]["name"], level_status_text(model.key, benchmark_id, level_id))
    console.print(table)


BACK = "__back__"


def choose_level(model: Model, benchmark_id: str) -> None:
    benchmark = BENCHMARKS[benchmark_id]
    while True:
        print_levels_menu(model, benchmark_id)

        choices = [
            Choice(
                title=f"{benchmark['levels'][level_id]['name']} — {level_status_plain(model.key, benchmark_id, level_id)}",
                value=level_id,
            )
            for level_id in benchmark["level_order"]
        ]
        choices.append(Choice(title="« Назад", value=BACK))

        level_id = questionary.select("Выберите уровень:", choices=choices).ask()

        if level_id in (None, BACK):
            return

        _, _, result_path = paths_for(model.key, benchmark_id, level_id)

        if result_path.exists():
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
                clear_level(model, benchmark_id, level_id)

        run_level(model, benchmark_id, level_id)


def choose_model(benchmark_id: str) -> None:
    while True:
        try:
            models = list_llm_models()
        except Exception as e:
            console.print(f"[red]Не удалось получить список моделей: {e}[/red]")
            sys.exit(1)

        if not models:
            console.print("[yellow]LM Studio не вернул ни одной LLM модели.[/yellow]")
            return

        print_models_menu(benchmark_id, models)

        benchmark = BENCHMARKS[benchmark_id]
        choices = [
            Choice(
                title=f"{model.key}  —  "
                + "  |  ".join(
                    f"{benchmark['levels'][level_id]['name']}: {level_status_plain(model.key, benchmark_id, level_id)}"
                    for level_id in benchmark["level_order"]
                ),
                value=i,
            )
            for i, model in enumerate(models)
        ]
        choices.append(Choice(title="« Назад к выбору теста", value=BACK))

        selected = questionary.select("Выберите модель:", choices=choices).ask()

        if selected in (None, BACK):
            return

        choose_level(models[selected], benchmark_id)


def make_bar(percent: float, width: int = 20) -> Text:
    filled = round(width * percent / 100)
    bar = "█" * filled + "░" * (width - filled)
    return Text(bar, style=score_color(percent))


def show_leaderboard() -> None:
    results = all_saved_results()
    if not results:
        console.print("[yellow]Пока нет ни одного сохранённого результата.[/yellow]")
        return

    columns = [
        (benchmark_id, level_id)
        for benchmark_id in BENCHMARK_ORDER
        for level_id in BENCHMARKS[benchmark_id]["level_order"]
    ]

    by_model: dict[str, dict[tuple[str, str], dict]] = {}
    for r in results:
        by_model.setdefault(r["model"], {})[(r["benchmark"], r["level"])] = r

    rows = []
    for model_key, entries in by_model.items():
        percents = [score_percent(r) for r in entries.values()]
        avg = sum(percents) / len(percents) if percents else 0.0
        rows.append((model_key, entries, avg))

    rows.sort(key=lambda row: row[2], reverse=True)

    table = Table(title="Рейтинг моделей (среднее по всем пройденным тестам)", padding=(0, 1))
    table.add_column("#", justify="right", style="bold cyan")
    table.add_column("Модель", style="bold")
    for benchmark_id, level_id in columns:
        table.add_column(f"{BENCHMARKS[benchmark_id]['short']}\nL{level_id[-1]}", justify="center")
    table.add_column("Средний %", justify="right")
    table.add_column("", min_width=22)

    for i, (model_key, entries, avg) in enumerate(rows, start=1):
        row = [str(i), model_key]
        for benchmark_id, level_id in columns:
            result = entries.get((benchmark_id, level_id))
            if result is None:
                row.append(Text("—", style="dim"))
            else:
                row.append(Text(format_score(result), style=score_color(score_percent(result))))
        row.append(Text(f"{avg:.0f}%", style=f"bold {score_color(avg)}"))
        row.append(make_bar(avg))
        table.add_row(*row)

    console.print(table)


def main():
    ANSWERS_DIR.mkdir(exist_ok=True)
    HTML_ANSWERS_DIR.mkdir(exist_ok=True)
    RAW_ANSWERS_DIR.mkdir(exist_ok=True)
    RESULTS_DIR.mkdir(exist_ok=True)

    console.print(Panel("[bold]Добро пожаловать в бенчмарк локальных моделей![/bold]", border_style="green"))

    LEADERBOARD = "__leaderboard__"
    EXIT = "__exit__"

    while True:
        choices = [Choice(title=BENCHMARKS[benchmark_id]["name"], value=benchmark_id) for benchmark_id in BENCHMARK_ORDER]
        choices.append(Choice(title="📊 Общий рейтинг моделей", value=LEADERBOARD))
        choices.append(Choice(title="Выход", value=EXIT))

        choice = questionary.select("Выберите тест:", choices=choices).ask()

        if choice in (None, EXIT):
            console.print("Пока!")
            break

        if choice == LEADERBOARD:
            show_leaderboard()
            continue

        choose_model(choice)


if __name__ == "__main__":
    main()
