# llm-probe — Node.js / QuickJS plan

> Маленький локальный benchmark для coding LLM. Инструмент запрашивает модель,
> безопасно исполняет сгенерированный JavaScript в QuickJS и сохраняет
> воспроизводимый результат. Первичный сценарий — сравнение локальных моделей
> через LM Studio или любой OpenAI-compatible API.

## Цель и границы проекта

`llm-probe` отвечает на практический вопрос: **насколько хорошо конкретная
модель пишет небольшие корректные JavaScript-функции и с какой скоростью?**

В первой версии проект намеренно не является:

- IDE, агентом или системой автопочинки репозитория;
- платформой для запуска произвольных программ с доступом к файлам и сети;
- веб-приложением с аккаунтами, базой данных и сервером;
- универсальным benchmark'ом для Python, TypeScript, npm и shell-задач.

Это делает код небольшим, результаты понятными, а исполнение кода модели
контролируемым.

## Основные решения

| Область | Решение | Причина |
|---|---|---|
| Язык инструмента | Node.js + TypeScript | Один runtime для CLI, API-клиента и executor'а; типы полезны для форматов runs/tasks. |
| Язык решений модели | JavaScript ES2023 | Не нужен transpile; результат не зависит от версии TypeScript или npm. |
| Исполнение решений | `quickjs-emscripten` | QuickJS в WASM-контексте без Node API по умолчанию. |
| Жёсткая страховка | отдельный `node:worker_threads` Worker на candidate | Зависший или аварийный eval не блокирует главный CLI-процесс. |
| Взаимодействие | CLI-first | Нет HTTP-сервера, фронтенда, ORM и постоянных сервисов. |
| Хранение | JSON + JSONL + исходники кандидатов | Прозрачно, переносимо, без SQLite и миграций. |
| Модельный API | OpenAI-compatible Chat Completions | Сначала LM Studio; затем Ollama/vLLM/другие совместимые endpoints через config. |
| Повторяемость | сохранять prompt, параметры, raw response, код, версии suite/runtime | Любой результат можно проверить и объяснить. |

### Почему не Deno в MVP

Deno удобен для исполнения полноценных программ с permission flags. Но здесь
модель должна решать алгоритмическую задачу чистой функцией: ей не нужны файлы,
сеть, subprocess, npm или Web API. QuickJS для этого проще, быстрее по
инфраструктуре и имеет меньшую capability surface.

Deno может появиться позже как **отдельный executor** для отдельной suite с
явно заданными разрешениями. Он не должен менять контракт QuickJS suite.

## Пользовательский сценарий

```text
probe models
    └─ показывает модели, доступные на OpenAI-compatible endpoint

probe tasks --suite core
    └─ показывает задачи и их краткое описание

probe run --model qwen2.5-coder-7b --suite core --samples 3
    ├─ для каждой задачи получает 3 независимых ответа модели
    ├─ запускает каждый ответ в QuickJS
    ├─ проверяет hidden tests
    └─ записывает run в runs/<run-id>/

probe report runs/<run-id>
    └─ печатает Markdown summary; опционально создаёт один static HTML report

probe inspect runs/<run-id> --task graph-shortest-path
    └─ показывает prompt, ответ модели, код, ошибки и результаты тестов
```

CLI достаточно для MVP. Отчёт в Markdown хорошо читается в GitHub и в
терминале; один self-contained `report.html` можно добавить позднее без
React/Vue, web server или database.

## Архитектура

```text
CLI (node)
  │
  ├─ config loader ─────── profiles: LM Studio, Ollama, vLLM ...
  ├─ task registry ─────── trusted task definitions + hidden tests
  ├─ run orchestrator
  │    ├─ prompt builder
  │    ├─ OpenAI-compatible model client
  │    ├─ response parser
  │    └─ evaluator
  │          └─ Node Worker (one candidate)
  │               └─ QuickJS WASM runtime (one candidate)
  │                    └─ untrusted `solve(input)`
  ├─ result writer ─────── JSON/JSONL/source files
  └─ reporter ─────────── terminal + Markdown (later static HTML)
```

### Предлагаемая структура

```text
llm-probe/
├─ src/
│  ├─ cli.ts                    # commands and terminal formatting
│  ├─ config.ts                 # config file, endpoint profiles
│  ├─ types.ts                  # shared discriminated unions and JSON types
│  ├─ model-client.ts           # OpenAI-compatible client via global fetch
│  ├─ prompts.ts                # stable prompt templates
│  ├─ extractor.ts              # strict code extraction/validation
│  ├─ runner.ts                 # task × sample orchestration
│  ├─ storage.ts                # writes run directory and JSONL
│  ├─ report.ts                 # terminal/Markdown report
│  ├─ evaluator/
│  │  ├─ index.ts               # timeout boundary and Worker protocol
│  │  ├─ worker.ts              # receives a candidate, owns QuickJS
│  │  └─ quickjs.ts             # runtime/context setup and solve() calls
│  └─ tasks/
│     ├─ registry.ts
│     ├─ types.ts
│     └─ core/                  # trusted task definitions
│        ├─ index.ts
│        ├─ strings.ts
│        ├─ collections.ts
│        └─ algorithms.ts
├─ tests/
│  ├─ extractor.test.ts
│  ├─ evaluator.test.ts
│  ├─ runner.test.ts
│  └─ tasks.test.ts
├─ runs/                        # gitignored generated results
├─ probe.config.example.json
├─ package.json
├─ tsconfig.json
└─ README.md
```

## Минимальный стек

```text
Runtime dependency:  quickjs-emscripten
Dev dependency:      typescript
Built-ins:           fetch, node:fs, node:path, node:worker_threads,
                     node:util, node:crypto, node:test
```

Не нужны FastAPI, Express, React, database, ORM, Docker, CLI framework,
валидатор схем или HTTP-клиент. Первую CLI можно разобрать через
`node:util.parseArgs`; запросы выполнять встроенным `fetch`.

Зафиксировать поддерживаемую версию Node в `package.json`:

```json
{
  "engines": { "node": ">=22" }
}
```

## Контракт задачи и решения

Задача всегда просит экспортировать **ровно одну синхронную чистую функцию**:

```js
export function solve(input) {
  // input и return должны быть JSON-compatible
}
```

Ограничения guest-кода:

- только JavaScript ES2023;
- без `import`/`require`, npm, TypeScript, файлов, сети и subprocess;
- без `async`, таймеров и фоновых задач;
- вход не мутировать;
- возвращать JSON-compatible значение: `null`, boolean, number, string,
  array или plain object;
- не печатать Markdown и объяснения в ответе модели.

Модель получает текст задачи, контракт, ограничения и 2–3 примера. Она **не
получает hidden tests**. Ответ сохраняется полностью, но парсер ожидает один
JavaScript code block; при отсутствии блока допускается весь ответ как код.

Позднее, когда конкретный provider надёжно поддерживает structured output,
можно перейти на JSON-объект `{ "code": "..." }`. Это не нужно для MVP.

### Trusted test harness

Тесты не являются строками JavaScript, которые исполняются вместе с модельным
кодом. Это доверенные TypeScript-данные и проверки хоста:

```ts
type Json = null | boolean | number | string | Json[] | { [key: string]: Json }

type TestCase = {
  id: string
  input: Json
  expected?: Json
  checker?: "deepEqual" | "unorderedArray" | "custom"
}

type Task = {
  id: string
  suite: "core"
  title: string
  prompt: string
  examples: Array<{ input: Json; output: Json }>
  publicTests: TestCase[]
  hiddenTests: TestCase[]
  limits: { evalMs: number; memoryMb: number }
}
```

`custom` выбирает checker по имени из registry доверенного кода; task file не
может передать произвольную функцию или eval-строку. Это исключает ситуацию,
когда решение модели запускает собственный test harness.

## QuickJS executor

### Что получает и чего не получает код модели

QuickJS context не получает объекты Node: `process`, `require`, `fs`, `net`,
`child_process`, `Buffer`, environment variables и shell. Не добавлять в
контекст `console`, imports или host callbacks, пока они действительно не
нужны.

Host передаёт JSON через созданные QuickJS handles, вызывает экспортированную
`solve` и забирает JSON-compatible результат. Перед каждым тестом вход
клонируется: решение не должно узнать последующий тест через mutation.

### Лимиты и жизненный цикл

```text
1. Главный процесс создаёт Worker для candidate.
2. Worker загружает QuickJS WASM и создаёт новый runtime/context.
3. Runtime получает memory limit, stack limit и interrupt deadline.
4. Worker компилирует candidate и на каждом test case вызывает solve(input).
5. Worker отправляет структурированный Result главному процессу.
6. Главный процесс уничтожает Worker при wall-clock timeout.
7. Handles, context и runtime освобождаются в finally.
```

Стартовые консервативные лимиты для correctness suite:

```text
QuickJS heap:        16 MiB
QuickJS stack:       512 KiB
На один test case:   100 ms CPU deadline
На candidate всего:  2 s wall-clock (включая Worker overhead)
```

Это не окончательные benchmark-числа: их нужно подтвердить на reference
solutions. У задач с легитимным большим входом лимит задаётся на task, но не
может произвольно повышаться ответом модели.

Worker — это вторичный предел над QuickJS interrupt handler. Он нужен для
устойчивости инструмента: зависший eval или ошибка в binding не должны
останавливать весь benchmark. Создавать один Worker на candidate проще и
чище, чем pool: генерация LLM обычно на порядки дольше startup Worker, а
контаминация состояния между solutions исключена.

### Threat model

QuickJS executor предназначен для ошибок и обычного недоверенного LLM-кода;
он не является обещанием абсолютной защиты против атакующего, использующего
уязвимость Node/WASM/QuickJS. Для локального benchmark'а это подходящий баланс.
Если в будущем будут запускаться чужие, намеренно враждебные submissions,
нужен дополнительный OS/container/VM слой.

## Модельный клиент и конфигурация

Первым нужен один OpenAI-compatible client. Он принимает `baseUrl`, API key
из environment variable и model id; `LM Studio` — просто default profile.

```json
{
  "profiles": {
    "lmstudio": {
      "baseUrl": "http://127.0.0.1:1234/v1",
      "apiKeyEnv": "LM_STUDIO_API_KEY"
    }
  },
  "defaults": {
    "profile": "lmstudio",
    "temperature": 0.2,
    "maxTokens": 2048
  }
}
```

На каждый completion сохранять:

- полный prompt и system prompt;
- model id, endpoint profile, temperature, seed (если provider его поддержал),
  max tokens;
- HTTP/model error в структурированном виде;
- raw response, extracted code, latency и доступные usage/timing fields;
- версию task suite, Node и `quickjs-emscripten`.

Запросы одной модели в MVP выполнять последовательно. Это честнее для локальных
серверов: параллельные запросы меняют latency и часто ухудшают generation.

## Benchmark suites

### MVP: `core/function`

Это единственная обязательная suite первого релиза. Модель реализует
`solve(input)` с JSON входом и выходом. Первые 20–30 задач пишутся вручную и
проходят reference implementation.

Покрытие должно быть разнообразным, а не просто делением на «лёгкое/сложное»:

| Категория | Примеры |
|---|---|
| Строки и массивы | нормализация, run-length encoding, скользящее окно, edge cases |
| Коллекции | frequency map, дедупликация, group-by, set/map semantics |
| Числа и интервалы | парсинг, диапазоны, merge intervals, переполнения в пределах JS Number |
| Структуры | stack/queue, дерево в JSON, простое состояние |
| Алгоритмы | BFS/DFS, shortest path без весов, topological ordering, LCS/knapsack на ограниченных input |
| Корректность API | `null`, пустые коллекции, дубликаты, отрицательные значения, не мутировать input |

У каждой задачи: понятный contract, два-три примера, несколько обычных hidden
cases и отдельно edge/performance cases. Правильная reference solution должна
пройти все проверки; несколько намеренно плохих решений должны стабильно
падать хотя бы на одном hidden test.

### После MVP: `core/bugfix`

Модель получает функцию с конкретным багом и должна вернуть исправленный
модуль с `solve`. Это полезный второй режим, но его не надо делать до того,
как executor и task-format проверены на `function` suite.

### Отложить

- refactor: сложно объективно измерить качество дизайна;
- FIM: нужен отдельный формат prompt и парсинга;
- unit-test writer: нужен mutation testing и отдельная модель оценки;
- TypeScript/npm/browser tasks: требуют другие capabilities и другой executor;
- Python: это отдельный track с иной изоляцией и несопоставимыми задачами.

## Тесты и валидность набора задач

Каждая task definition проходит автоматическую проверку:

1. Reference solution проходит все public и hidden tests.
2. Набор mutants (off-by-one, неверное сравнение, mutation input, неверная
   обработка empty/null, медленный алгоритм) не проходит хотя бы один тест.
3. Тесты детерминированы: фиксированный seed, одинаковый результат при
   повторном запуске.
4. Лимиты позволяют reference solution запас по времени, но ловят намеренно
   неэффективную реализацию там, где сложность — часть задачи.
5. Output checker не зависит от порядка там, где порядок не является
   требованием задачи.

Не показывать hidden tests в prompt и не использовать один общий фиксированный
набор для всех задач. Для задач, где возможно «угадывание» входов, генерировать
часть hidden cases по сохранённому seed на запуске.

## Метрики

Для одной попытки (`candidate`):

- `pass`: прошли ли все tests;
- `passed / total`: диагностическая доля пройденных тестов;
- `compile_error`, `runtime_error`, `timeout`, `memory_limit`, `invalid_output`;
- generation latency и provider usage, если доступны.

Для task suite:

- `success@1`: доля задач, прошедших с первой генерацией;
- `success@k`: доля задач, где хотя бы один из `k` независимых candidates
  прошёл все tests;
- mean/median generation latency и токены/сек только в рамках одного provider
  и одинаковых параметров;
- breakdown по категориям и типам failure.

Не называть «все k прошли» `pass@k`: это отдельная, редко полезная метрика
stability. Если позже нужен стандартный статистический estimator pass@k,
добавить его отдельно и документировать формулу/условия.

## Формат run

```text
runs/2026-08-18T10-30-00Z_qwen2.5-coder-7b/
├─ meta.json              # command, machine, versions, config without secrets
├─ results.jsonl          # one CandidateResult per line
├─ prompts/
│  └─ <task-id>.txt
├─ candidates/
│  └─ <task-id>/
│     ├─ 01.raw.txt
│     ├─ 01.extracted.js
│     └─ 01.result.json
├─ report.md
└─ report.html            # optional, later
```

`results.jsonl` — append-only. При Ctrl+C уже завершённые candidates не
теряются; последующий `probe report` всё равно строит частичный отчёт.

## Маленький MVP

MVP считается готовым, когда можно одной командой прогнать одну локальную
модель по 10 задачам и получить воспроизводимый Markdown report.

### Этап 1 — скелет (без реальной модели)

- [ ] Инициализировать Node/TypeScript проект, `npm` lockfile, strict tsconfig.
- [ ] Реализовать `probe tasks` и task registry с 3 hand-written tasks.
- [ ] Реализовать `probe run --code <file>`: локальный JS candidate проходит
      через QuickJS и trusted tests.
- [ ] Добавить Worker protocol, QuickJS memory/stack/interrupt limits,
      wall-clock timeout и структурированные ошибки.
- [ ] Добавить unit tests: normal result, syntax error, thrown error,
      infinite loop, invalid JSON-like result, mutation input.

**Результат:** executor можно проверить без сети, LLM и UI.

### Этап 2 — один реальный полный прогон

- [ ] Реализовать OpenAI-compatible `models` и chat completion client.
- [ ] Реализовать стабильный prompt и code extractor.
- [ ] Добавить 10 качественных `core/function` tasks с reference/mutant tests.
- [ ] Реализовать `probe run --model ... --samples 1`.
- [ ] Сохранять полный run directory и генерировать `report.md`.

**Результат:** от запроса к LM Studio до accuracy report без ручных шагов.

### Этап 3 — полезный benchmark

- [ ] Добавить `--samples k` и `success@1` / `success@k`.
- [ ] Расширить `core/function` до 20–30 tasks.
- [ ] Добавить `probe inspect`, category breakdown и resume/partial report.
- [ ] Проверить benchmark минимум на двух моделях и вручную разобрать
      false positives/false negatives.

**Результат:** маленький, но честный инструмент для регулярного сравнения
локальных coding-моделей.

## Критерии «не расширять проект раньше времени»

Не добавлять web UI, SQLite, второй язык, Deno executor, Docker или
параллельный scheduler, пока не выполнены все условия:

1. 20+ задач имеют reference и mutant coverage;
2. минимум два реальных model run сохранены и воспроизводимы;
3. результаты CLI неудобно анализировать именно из-за формата, а не из-за
   слабости task suite;
4. есть конкретная задача, которую новая зависимость решает лучше встроенных
   возможностей Node.

Веб, если он появится, должен быть статическим viewer'ом готовых run folders,
а не вторым центром логики. Вся генерация, execution и запись результатов
остаются в CLI/engine.
