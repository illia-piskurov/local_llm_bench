import type { ChatMessage, EvaluationResult, Task } from "./types.js";

const SYSTEM_PROMPT = "You write correct JavaScript solutions. Return only one ESM JavaScript module and no explanation or Markdown.";

export function buildMessages(task: Task): ReadonlyArray<ChatMessage> {
  const examples = task.examples.map((example) => `input: ${JSON.stringify(example.input)}\noutput: ${JSON.stringify(example.expected)}`).join("\n\n");
  return [
    { role: "system", content: SYSTEM_PROMPT },
    {
      role: "user",
      content: `${task.prompt}\n\nImplement exactly:\nexport function solve(input) { /* return a JSON-compatible value */ }\n\nRules: use synchronous JavaScript ES2023 only; do not use imports, require, files, network, subprocesses, async, or timers; do not mutate input.\n\nExamples:\n${examples}`
    }
  ];
}

export function buildRepairFeedback(
  task: Task,
  status: string,
  error?: string,
  evaluation?: EvaluationResult
): string {
  const lines: string[] = [];
  lines.push("Your solution failed execution / test validation:");

  if (status === "compile_error") {
    lines.push(`- Syntax / Module Error: ${error || "The module could not be compiled or did not export solve(input)"}`);
  } else if (status === "extract_error") {
    lines.push(`- Extraction Error: ${error || "Could not find 'export function solve(input)' in your response"}`);
  } else if (status === "timeout") {
    lines.push(`- Timeout: Execution exceeded the time limit per test case (possible infinite loop or inefficient recursion)`);
  } else if (status === "runtime_error") {
    lines.push(`- Runtime Exception: ${error || "An unhandled error occurred during solve(input)"}`);
  } else if (status === "invalid_output") {
    lines.push(`- Invalid Output: ${error || "Function returned non-JSON value (e.g. undefined/function/circular)"}`);
  } else if (status === "failed") {
    const failedTests = (evaluation?.tests ?? []).filter((t) => !t.passed);
    lines.push(`- Test Failures (${failedTests.length}/${evaluation?.total ?? 0} failed):`);
    for (const ft of failedTests.slice(0, 3)) {
      lines.push(`  * [${ft.id}] ${ft.error || "Wrong output"}`);
    }
  } else {
    lines.push(`- Error: ${error || status}`);
  }

  lines.push(
    "",
    "Please fix the bug(s) in `export function solve(input)`. Return only the complete corrected JavaScript code in a ```javascript ... ``` code block with no explanations or Markdown outside the block."
  );
  return lines.join("\n");
}

export function buildRepairMessages(
  initialMessages: ReadonlyArray<ChatMessage>,
  history: ReadonlyArray<{ code: string; feedback: string }>
): ReadonlyArray<ChatMessage> {
  const messages: ChatMessage[] = [...initialMessages];
  for (const item of history) {
    messages.push({
      role: "assistant",
      content: `\`\`\`javascript\n${item.code}\n\`\`\``
    });
    messages.push({
      role: "user",
      content: item.feedback
    });
  }
  return messages;
}

