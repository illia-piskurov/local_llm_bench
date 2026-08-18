# llm-probe

Локальный CLI для проверки JavaScript-решений coding-моделей в QuickJS.

## Сейчас реализовано

- `probe tasks` — список 10 задач core suite;
- `probe eval --task <id> --code <file>` — запуск `export function solve(input)`
  в изолированном QuickJS Worker;
- лимиты памяти, стека и времени, а также структурированные ошибки исполнения.

## Запуск

```powershell
npm.cmd install
npm.cmd run dev -- tasks
npm.cmd run dev -- eval --task first-unique-char --code .\examples\first-unique-char.js
```

После сборки:

```powershell
npm.cmd run build
node .\dist\cli.js tasks
```

Код решения должен экспортировать синхронную функцию:

```js
export function solve(input) {
  return input.text.length;
}
```

## LM Studio и сохранённые runs

Включите локальный server в LM Studio. По умолчанию используется OpenAI-compatible
endpoint `http://127.0.0.1:1234/v1`.

```powershell
npm.cmd run dev -- models
npm.cmd run dev -- run --model "your-model-id" --task first-unique-char --samples 1
npm.cmd run dev -- runs
npm.cmd run dev -- inspect latest --task first-unique-char
```

Каждый запуск сохраняется в игнорируемой Git папке `runs/<run-id>/`: там есть
`manifest.json`, append-only `events.jsonl`, raw response, extracted code,
request, evaluation и `report.md`. Ключи и заголовки авторизации не пишутся.

Подробная архитектура и следующие этапы: [plan-node.md](./plan-node.md).
