# llm-probe — План проекта

> Инструмент для тестирования локальных LLM-моделей (кодинг), особенно малых (1B–30B).
> Стек: Python · uv · FastAPI · SQLModel · SQLite · Typer CLI · Веб-интерфейс в браузере

---

## Стек

| Слой | Библиотека | Зачем |
|---|---|---|
| Управление проектом | `uv` | venv + зависимости + скрипты |
| Web API | `FastAPI` | async HTTP + SSE + автодока |
| ORM / схема БД | `SQLModel` | SQLAlchemy + Pydantic в одном |
| CLI | `Typer` | типизированный CLI без бойлерплейта |
| HTTP клиент | `httpx` | async, type-safe, LM Studio клиент |
| Eval sandbox | `multiprocessing` | stdlib, изоляция exec() |
| Парсинг кода из MD | `re` / stdlib | извлечь ```python ... ``` блоки |

> Никакого `subprocess → python worker.py`. Eval делается нативно через `multiprocessing.Process`.

---

## Структура проекта

```
llm-probe/
├── src/
│   └── llm_probe/
│       ├── __init__.py
│       ├── main.py               # точка входа FastAPI app
│       ├── cli.py                # Typer CLI (run, leaderboard, export, ui)
│       │
│       ├── models/               # SQLModel таблицы (= Pydantic модели одновременно)
│       │   ├── __init__.py
│       │   ├── run.py            # Run, RunCreate, RunRead
│       │   └── host.py           # HostConfig
│       │
│       ├── db/                   # Database layer
│       │   ├── __init__.py
│       │   ├── engine.py         # create_engine, init_db()
│       │   └── crud.py           # get_runs, create_run, get_leaderboard
│       │
│       ├── lmstudio/             # LM Studio REST клиент
│       │   ├── __init__.py
│       │   ├── client.py         # LMStudioClient (httpx.AsyncClient)
│       │   └── types.py          # Model, ChatRequest, ChatResponse
│       │
│       ├── runner/               # Orchestration
│       │   ├── __init__.py
│       │   ├── runner.py         # pass@k оркестрация
│       │   ├── extractor.py      # извлечение кода из markdown
│       │   └── sandbox.py        # eval через multiprocessing
│       │
│       ├── benchmarks/           # Определения бенчмарков
│       │   ├── __init__.py
│       │   ├── registry.py       # BenchmarkRegistry
│       │   ├── base.py           # Benchmark ABC, TestCase dataclass
│       │   ├── bug_hunt.py
│       │   ├── completion.py
│       │   ├── algorithm.py
│       │   ├── refactor.py
│       │   └── test_writer.py
│       │
│       └── api/                  # FastAPI роутеры
│           ├── __init__.py
│           ├── models.py         # GET /api/models
│           ├── benchmarks.py     # GET /api/benchmarks
│           ├── runs.py           # POST /api/run, GET /api/run/{id}/stream
│           ├── results.py        # GET /api/results, GET /api/leaderboard
│           └── deps.py           # Depends (db session, lmstudio client)
│
├── benchmarks/                   # Данные бенчмарков (задачи + тест-кейсы)
│   ├── bug_hunt/
│   │   ├── l1_cases.json
│   │   ├── l2_cases.json
│   │   └── l3_cases.json
│   ├── completion/
│   ├── refactor/
│   ├── algorithm/
│   └── test_writer/
│
├── web/                          # Фронтенд (статика, отдаётся FastAPI)
│   ├── index.html
│   ├── app.js
│   └── style.css
│
├── pyproject.toml
├── uv.lock
└── README.md
```

---

## Фазы разработки

### Фаза 1 — Фундамент (SQLModel + LM Studio клиент)

**Задачи:**
- [ ] `uv init llm-probe --package` — создать проект со src layout
- [ ] Добавить зависимости: `fastapi`, `uvicorn[standard]`, `sqlmodel`, `httpx`, `typer`
- [ ] Спроектировать SQLModel модели (= таблицы + Pydantic схемы одновременно)
- [ ] Реализовать LM Studio клиент (`lmstudio/client.py`):
  - `GET /api/v1/models` — список моделей
  - `POST /api/v1/chat` — генерация
  - `POST /api/v1/models/unload` — выгрузка
  - Таймаут + retry логика
- [ ] Базовый Typer CLI с командами `run`, `results`, `ui`

**SQLModel схема (= таблица + Pydantic модель в одном):**

```python
# models/run.py
from sqlmodel import SQLModel, Field
from datetime import datetime
from uuid import UUID, uuid4

class Run(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    model_id: str
    bench_id: str          # 'bug_hunt', 'algorithm', ...
    level_id: str          # 'l1', 'l2', 'l3'
    attempt: int           # 1..k (для pass@k)
    temperature: float
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Метрики скорости
    tok_per_sec: float | None = None
    ttft_ms: float | None = None
    load_time_ms: float | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None

    # Результат
    passed: int | None = None
    total: int | None = None
    error_log: str | None = None

    # Сырые данные
    raw_response: str | None = None
    extracted_code: str | None = None
```

**Leaderboard через SQLModel/SQLAlchemy:**

```python
# db/crud.py
from sqlmodel import select, func, Session, col
from ..models.run import Run

def get_leaderboard(session: Session) -> list[dict]:
    stmt = (
        select(
            Run.model_id,
            Run.bench_id,
            Run.level_id,
            func.max(Run.passed == Run.total).label("pass_at_1"),
            func.avg(col(Run.passed) / col(Run.total)).label("avg_accuracy"),
        )
        .where(Run.total > 0)
        .group_by(Run.model_id, Run.bench_id, Run.level_id)
    )
    return session.exec(stmt).all()
```

---

### Фаза 2 — Eval Sandbox (multiprocessing)

**Нет отдельного subprocess.** Eval встроен нативно в Python:

```
runner.py
  │
  ├── extract code from LLM response  (extractor.py)
  │
  └── sandbox.py
        multiprocessing.Process(target=_run_in_sandbox)
          ├── exec(code, namespace)
          ├── run each test case
          └── return via multiprocessing.Queue
```

**sandbox.py:**

```python
import multiprocessing as mp
from dataclasses import dataclass, field

@dataclass
class SandboxResult:
    passed: int
    total: int
    errors: list[str] = field(default_factory=list)

def _worker(code: str, tests: list[dict], queue: mp.Queue) -> None:
    namespace: dict = {}
    errors: list[str] = []
    passed = 0

    try:
        exec(code, namespace)  # noqa: S102
    except Exception as e:
        queue.put(SandboxResult(0, len(tests), [str(e)]))
        return

    for test in tests:
        try:
            exec(test["code"], namespace)  # noqa: S102
            passed += 1
        except Exception as e:
            errors.append(str(e))

    queue.put(SandboxResult(passed, len(tests), errors))


def evaluate(code: str, tests: list[dict], timeout: float = 5.0) -> SandboxResult:
    queue: mp.Queue = mp.Queue()
    proc = mp.Process(target=_worker, args=(code, tests, queue))
    proc.start()
    proc.join(timeout)

    if proc.is_alive():
        proc.kill()
        return SandboxResult(0, len(tests), ["Timeout"])

    return queue.get()
```

**pass@k оркестрация (runner.py):**

```
k=3 попытки с температурами [0.2, 0.5, 0.8]
  └── для каждой попытки:
        1. async запрос к LM Studio (httpx)
        2. Извлечение кода из markdown (extractor.py)
        3. Eval в sandbox (multiprocessing)
        4. Сохранение в SQLite (SQLModel session)

Итоговые метрики:
  pass@1  = хотя бы одна попытка прошла все тесты
  pass@k  = все k попыток прошли все тесты
  avg     = среднее (passed/total) по всем попыткам
```

---

### Фаза 3 — Бенчмарки

**Базовый класс:**

```python
# benchmarks/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class TestCase:
    code: str          # assert или exec-код для проверки

@dataclass
class BenchmarkTask:
    id: str
    level: str         # 'l1' | 'l2' | 'l3'
    prompt: str
    tests: list[TestCase]

class Benchmark(ABC):
    id: str
    levels: list[str] = ["l1", "l2", "l3"]

    @abstractmethod
    def load_tasks(self, level: str) -> list[BenchmarkTask]: ...
```

#### Bug Hunt (Python)
Дан сломанный код → модель исправляет → запускаем тесты.

| Уровень | Тип бага | Пример |
|---------|----------|--------|
| L1 | Логическая ошибка | `>` вместо `>=`, off-by-one в цикле |
| L2 | Алгоритмический | Неправильный edge case в рекурсии, пропущена проверка None |
| L3 | Структурный | Неверная инвариантность состояния в классе |

Каждый уровень: 10 задач × 5 тест-кейсов = 50 assertions.

#### Code Completion / FIM (Python)
Дан prefix + suffix → модель дописывает середину.

| Уровень | Контекст |
|---------|----------|
| L1 | Простая функция с докстрингом, очевидная реализация |
| L2 | Метод класса, зависит от `self.*` полей |
| L3 | Вспомогательная функция, используется 3 другими функциями в контексте |

#### Algorithm (Python)
| Уровень | Задача |
|---------|--------|
| L1 | BFS/DFS (найди кратчайший путь в графе) |
| L2 | Динамическое программирование (LCS, knapsack) |
| L3 | Задача с ограничениями (интервальное планирование, bin packing) |

#### Refactor (Python)
Дан рабочий но неэффективный/грязный код → улучши.

| Уровень | Задача |
|---------|--------|
| L1 | O(n²) → O(n) (убрать вложенный цикл) |
| L2 | Дублирование кода → DRY, вынести логику |
| L3 | Плохая архитектура → правильные абстракции |

Оценка: тесты должны пройти + проверяем сложность (измеряем время на больших n).

#### Unit Test Writer (Python)
Дана функция → напиши тесты → запускаем написанные тесты против эталонной реализации + против намеренно сломанной.

| Уровень | Сложность функции |
|---------|-------------------|
| L1 | Чистая функция, несколько edge cases |
| L2 | Класс с состоянием |
| L3 | Функция с несколькими режимами работы и ошибочными состояниями |

Оценка:
- Тесты проходят против правильной реализации (нет false positives)
- Тесты падают против сломанной реализации (нет false negatives)

---

### Фаза 4 — Web UI (FastAPI отдаёт статику)

**Страницы:**

1. **Dashboard** `/` — общий рейтинг моделей
   - Таблица: модель × бенчмарк, ячейка = pass@1 / pass@k
   - Сортировка по avg accuracy
   - Фильтр по размеру модели, бенчмарку

2. **Model Detail** `/model/:id` — карточка модели
   - Графики: точность по уровням (Chart.js)
   - Скорость: tok/s, TTFT
   - История прогонов

3. **Run** `/run` — запуск нового бенчмарка
   - Выбор модели (dropdown из LM Studio)
   - Выбор бенчмарков (чекбоксы)
   - k (число попыток): 1 / 3 / 5
   - Прогресс в реальном времени (SSE — нативный в FastAPI)

4. **Compare** `/compare` — сравнение двух моделей
   - Рядом: все метрики, где одна лучше другой

**API (FastAPI роутеры):**
```
GET  /api/models              ← список из LM Studio
GET  /api/benchmarks          ← доступные бенчмарки
POST /api/run                 ← запустить прогон
GET  /api/run/{id}/stream     ← SSE прогресс (StreamingResponse)
GET  /api/results             ← все результаты (фильтры через query params)
GET  /api/results/{model_id}  ← по модели
GET  /api/leaderboard         ← агрегированный рейтинг
DELETE /api/results/{model_id} ← удалить результаты
```

**SSE прогресс — нативно в FastAPI:**

```python
from fastapi.responses import StreamingResponse
import json

@router.get("/api/run/{run_id}/stream")
async def stream_run(run_id: str):
    async def event_generator():
        async for event in runner.stream_progress(run_id):
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

---

### Фаза 5 — CLI (Typer)

```python
# cli.py
import typer
app = typer.Typer()

@app.command()
def run(
    model: str = typer.Option(..., help="ID модели из LM Studio"),
    bench: list[str] = typer.Option(["all"]),
    k: int = typer.Option(3, help="Число попыток"),
): ...

@app.command()
def leaderboard(): ...

@app.command()
def ui(): ...  # запускает uvicorn + открывает браузер

@app.command()
def export(format: str = "csv", output: str = "results.csv"): ...
```

```bash
# Запустить бенчмарк
uv run llm-probe run --model "llama-3.2-3b" --bench bug_hunt --bench algorithm --k 3

# Все бенчмарки для всех моделей
uv run llm-probe run --bench all --k 3

# Открыть веб-интерфейс
uv run llm-probe ui

# Показать рейтинг в терминале
uv run llm-probe leaderboard

# Конфигурация железа
uv run llm-probe config set-host "RTX 4090 + Ryzen 9"

# Экспорт
uv run llm-probe export --format csv --output results.csv
```

---

## Зависимости

### pyproject.toml

```toml
[project]
name = "llm-probe"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115",
    "uvicorn[standard]>=0.30",
    "sqlmodel>=0.0.21",
    "httpx>=0.27",
    "typer>=0.12",
]

[project.scripts]
llm-probe = "llm_probe.cli:app"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.uv]
dev-dependencies = [
    "pytest>=8",
    "pytest-asyncio>=0.23",
    "ruff>=0.5",
    "mypy>=1.10",
]
```

---

## Порядок реализации

```
Неделя 1:  Фаза 1 — uv проект + SQLModel схема + LM Studio клиент
Неделя 1:  Фаза 2 — sandbox (multiprocessing) + pass@k runner
Неделя 2:  Фаза 3 — все 5 бенчмарков с тест-кейсами
Неделя 2:  Фаза 4 — Web UI (dashboard + run страница)
Неделя 3:  Фаза 5 — CLI polish + compare + export
Неделя 3:  Тестирование на реальных моделях + итерация
```

---

## Что убираем из старого проекта

| Было | Почему убираем |
|------|----------------|
| `brackets.py` | Слишком просто, не даёт дифференциации |
| `snake.py` (HTML игра) | Субъективная ручная оценка |
| `questionary` TUI | Заменяем веб-интерфейсом |
| JSON-файлы для хранения | Заменяем SQLite |
| Одиночный прогон | Заменяем pass@k |
| `eval/worker.py` subprocess | Заменяем нативным `multiprocessing` |

## Что сохраняем

| Было | Почему оставляем |
|------|-----------------|
| Идея инкрементальных уровней L1→L2→L3 | Отличная идея |
| Цепочка контекста между уровнями | Реалистично для real-world use |
| `multiprocessing` sandbox подход | Разумный баланс для локального инструмента |
| Метрики скорости (tok/s, TTFT) | Важно для малых моделей |
| Composite efficiency score | Хорошая идея, улучшим формулу |

---

## Resilience-архитектура

> Инструмент работает на слабом железе, генерация долгая, код от LLM непредсказуемый.
> Программа **никогда не должна падать** — только сохранять ошибку и идти дальше.

### 1. LM Studio клиент — никакого таймаута на генерацию

```python
# lmstudio/client.py

# CONNECT_TIMEOUT — время на установку соединения (быстрое, 10с)
# READ_TIMEOUT    — None, т.к. генерация может идти час
TIMEOUTS = httpx.Timeout(connect=10.0, read=None, write=30.0, pool=5.0)

class LMStudioClient:
    def __init__(self, base_url: str) -> None:
        self._client = httpx.AsyncClient(base_url=base_url, timeout=TIMEOUTS)

    async def generate(self, request: ChatRequest) -> ChatResponse:
        # Не кидает TimeoutException при долгой генерации
        # Кидает ConnectError если LM Studio недоступен — обрабатываем выше
        response = await self._client.post("/api/v1/chat/completions", ...)
        response.raise_for_status()
        return ChatResponse.model_validate(response.json())
```

**Почему `read=None`:** малые модели на слабом железе могут генерить минутами. Таймаут убьёт легитимный прогон. Пользователь сам контролирует процесс через `Ctrl+C`.

---

### 2. Цепочка запусков — структура

```
llm-probe run --bench bug_hunt,algorithm --k 3
  │
  └── RunChain
        ├── Job(bench=bug_hunt, level=l1, attempt=1)
        ├── Job(bench=bug_hunt, level=l1, attempt=2)
        ├── Job(bench=bug_hunt, level=l1, attempt=3)
        ├── Job(bench=bug_hunt, level=l2, attempt=1)
        │   ...
        ├── Job(bench=algorithm, level=l1, attempt=1)
        │   ...
        └── Job(bench=algorithm, level=l3, attempt=3)
```

Каждый `Job` — атомарная единица. Сбой одного **не прерывает цепочку**.

```python
# runner/runner.py
@dataclass
class Job:
    bench_id: str
    level_id: str
    attempt: int
    temperature: float

@dataclass
class JobResult:
    job: Job
    run_id: UUID | None        # None если не записалось в БД
    status: Literal["ok", "llm_error", "eval_error", "save_error"]
    error: str | None = None

async def run_chain(jobs: list[Job], ...) -> list[JobResult]:
    results: list[JobResult] = []
    for job in jobs:
        result = await _run_single_job_safe(job, ...)
        results.append(result)
        await _emit_progress(result)   # SSE / лог
    return results
```

---

### 3. Изоляция ошибок на каждом уровне

Каждый job проходит через 4 стадии, каждая обёрнута в `try/except`:

```python
async def _run_single_job_safe(job: Job, ...) -> JobResult:
    run_id: UUID | None = None

    # Стадия 1: запрос к LM Studio
    try:
        response = await lm_client.generate(...)
        raw_response = response.content
    except httpx.ConnectError:
        return JobResult(job, None, "llm_error", "LM Studio недоступен")
    except httpx.HTTPStatusError as e:
        return JobResult(job, None, "llm_error", f"HTTP {e.response.status_code}")
    except Exception as e:
        return JobResult(job, None, "llm_error", str(e))

    # Стадия 2: извлечение кода из markdown
    extracted = extract_code(raw_response)   # возвращает "" если не найдено, не кидает

    # Стадия 3: eval в sandbox (multiprocessing — изолирован по умолчанию)
    try:
        sandbox_result = evaluate(extracted, tests, timeout=5.0)
    except Exception as e:
        # evaluate() сам не должен падать, но на всякий случай
        sandbox_result = SandboxResult(0, len(tests), [str(e)])

    # Стадия 4: сохранение в SQLite
    try:
        run = Run(
            bench_id=job.bench_id,
            ...
            passed=sandbox_result.passed,
            total=sandbox_result.total,
            error_log="\n".join(sandbox_result.errors) or None,
            raw_response=raw_response,
            extracted_code=extracted,
        )
        session.add(run)
        session.commit()
        run_id = run.id
    except Exception as e:
        # БД недоступна — результат теряем, но программа живёт
        logger.error("Failed to save run: %s", e)
        return JobResult(job, None, "save_error", str(e))

    status = "ok" if extracted else "eval_error"
    return JobResult(job, run_id, status)
```

---

### 4. Sandbox — защита от плохого кода LLM

`multiprocessing.Process` уже даёт изоляцию. Дополнительно:

```python
def evaluate(code: str, tests: list[dict], timeout: float = 5.0) -> SandboxResult:
    if not code.strip():
        return SandboxResult(0, len(tests), ["No code extracted"])

    queue: mp.Queue = mp.Queue()
    proc = mp.Process(target=_worker, args=(code, tests, queue), daemon=True)
    proc.start()
    proc.join(timeout)

    if proc.is_alive():
        proc.kill()
        proc.join()   # ждём реального завершения после kill
        return SandboxResult(0, len(tests), [f"Timeout after {timeout}s"])

    if proc.exitcode != 0 and queue.empty():
        # Дочерний процесс крашнулся (segfault, OOM, sys.exit())
        return SandboxResult(0, len(tests), [f"Process crashed (exit {proc.exitcode})"])

    try:
        return queue.get_nowait()
    except Exception:
        return SandboxResult(0, len(tests), ["No result from sandbox"])
```

**Что защищает:**
- `infinite loop` → killed по таймауту
- `sys.exit()` / `os._exit()` → дочерний процесс, не наш
- `segfault` / `MemoryError` → exitcode != 0, обрабатываем
- `import os; os.system(...)` → выполняется, но в изолированном процессе
- `raise SystemExit` → только в дочернем процессе

---

### 5. Прерывание цепочки пользователем (Ctrl+C)

```python
async def run_chain(jobs: list[Job], ...) -> list[JobResult]:
    results: list[JobResult] = []
    try:
        for i, job in enumerate(jobs):
            logger.info("[%d/%d] %s/%s attempt %d", i+1, len(jobs), ...)
            result = await _run_single_job_safe(job, ...)
            results.append(result)
    except asyncio.CancelledError:
        logger.warning("Chain interrupted by user after %d/%d jobs", len(results), len(jobs))
        # Уже сохранённые результаты в SQLite никуда не делись
    except KeyboardInterrupt:
        logger.warning("KeyboardInterrupt — saving progress...")
    finally:
        return results   # возвращаем что успели
```

---

### 6. Статус цепочки — что показываем пользователю

Прогресс через SSE (веб) или `rich` прогресс-бар (CLI):

```
[3/15] bug_hunt/l1 attempt 2 ... ✓  passed 4/5  (12.3 tok/s)
[4/15] bug_hunt/l1 attempt 3 ... ✓  passed 5/5  (11.8 tok/s)
[5/15] bug_hunt/l2 attempt 1 ... ✗  llm_error: LM Studio недоступен
[6/15] bug_hunt/l2 attempt 2 ... ✓  passed 2/5  (10.1 tok/s)
...
Chain complete: 13 ok, 1 llm_error, 1 eval_error (0 crashes)
```

Итоговый summary после цепочки:
```python
@dataclass
class ChainSummary:
    total: int
    ok: int
    llm_errors: int
    eval_errors: int
    save_errors: int
    duration_sec: float
```

---

### 7. Переподключение к LM Studio

Если LM Studio временно недоступен (перезагрузка модели) — не падаем, retry с backoff:

```python
async def generate_with_retry(
    client: LMStudioClient,
    request: ChatRequest,
    *,
    max_retries: int = 3,
    backoff_sec: float = 5.0,
) -> ChatResponse:
    for attempt in range(max_retries):
        try:
            return await client.generate(request)
        except httpx.ConnectError:
            if attempt == max_retries - 1:
                raise
            wait = backoff_sec * (attempt + 1)
            logger.warning("LM Studio недоступен, retry через %.0fs...", wait)
            await asyncio.sleep(wait)
    raise RuntimeError("unreachable")
```

---

### Сводная таблица: что может пойти не так

| Сценарий | Что делаем |
|---|---|
| LM Studio не запущен | `ConnectError` → `llm_error`, продолжаем цепочку |
| LM Studio перезагружает модель | retry × 3 с backoff 5/10/15с |
| Генерация идёт 10 минут | Нормально, `read=None`, ждём |
| LLM вернул пустой ответ | `extracted=""`, `eval_error: No code extracted` |
| LLM вернул синтаксически неверный Python | `exec()` кидает `SyntaxError` в sandbox → 0/N |
| LLM написал `while True: pass` | Killed по таймауту 5с |
| LLM написал `import os; os.system("rm -rf /")` | Выполняется в дочернем процессе (риск!) — будущий TODO: seccomp/docker |
| LLM написал `sys.exit(1)` | Дочерний процесс падает, exitcode != 0, обрабатываем |
| SQLite заблокирована | `save_error`, результат теряем, лог |
| Ctrl+C в середине цепочки | Graceful stop, всё сохранённое остаётся |
| OOM в sandbox | Process killed по exit code, обрабатываем |

