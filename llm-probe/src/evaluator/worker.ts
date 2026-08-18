import { parentPort, workerData } from "node:worker_threads";
import { getQuickJS } from "quickjs-emscripten";
import type { EvaluationRequest, EvaluationResult, Json, TestResult } from "../types.js";

const request = workerData as EvaluationRequest;

function isJson(value: unknown): value is Json {
  if (value === null || typeof value === "boolean" || typeof value === "string") return true;
  if (typeof value === "number") return Number.isFinite(value);
  if (Array.isArray(value)) return value.every(isJson);
  if (typeof value !== "object") return false;
  return Object.getPrototypeOf(value) === Object.prototype && Object.values(value).every(isJson);
}

function errorText(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}

function quickJsError(value: unknown): string {
  if (typeof value === "object" && value !== null && "message" in value) {
    const message = value.message;
    if (typeof message === "string") return message;
  }
  return String(value);
}

async function run(): Promise<EvaluationResult> {
  const startedAt = performance.now();
  const limits = request.task.limits;
  const testMs = limits?.testMs ?? 100;
  const memoryBytes = (limits?.memoryMb ?? 16) * 1024 * 1024;
  const stackBytes = (limits?.stackKb ?? 512) * 1024;
  const QuickJS = await getQuickJS();
  const runtime = QuickJS.newRuntime();
  let deadline = Date.now() + testMs;
  runtime.setMemoryLimit(memoryBytes);
  runtime.setMaxStackSize(stackBytes);
  runtime.setInterruptHandler(() => Date.now() > deadline);
  const context = runtime.newContext();

  try {
    deadline = Date.now() + testMs;
    const moduleResult = context.evalCode(request.code, "candidate.mjs", { type: "module" });
    if (moduleResult.error) {
      const error = quickJsError(context.dump(moduleResult.error));
      moduleResult.error.dispose();
      return result("compile_error", [], startedAt, error);
    }
    const exports = moduleResult.value;
    const solve = context.getProp(exports, "solve");
    exports.dispose();
    if (context.typeof(solve) !== "function") {
      solve.dispose();
      return result("compile_error", [], startedAt, "Candidate must export function solve(input)");
    }

    const testResults: TestResult[] = [];
    for (const test of request.task.tests) {
      deadline = Date.now() + testMs;
      const inputResult = context.evalCode(`JSON.parse(${JSON.stringify(JSON.stringify(test.input))})`);
      if (inputResult.error) {
        const error = quickJsError(context.dump(inputResult.error));
        inputResult.error.dispose();
        solve.dispose();
        return result("worker_error", testResults, startedAt, error);
      }
      const callResult = context.callFunction(solve, context.undefined, inputResult.value);
      inputResult.value.dispose();
      if (callResult.error) {
        const error = quickJsError(context.dump(callResult.error));
        callResult.error.dispose();
        solve.dispose();
        const status = /interrupted/i.test(error) ? "timeout" : "runtime_error";
        return result(status, testResults, startedAt, error);
      }
      const output = context.dump(callResult.value);
      callResult.value.dispose();
      if (!isJson(output)) {
        solve.dispose();
        return result("invalid_output", testResults, startedAt, `Test ${test.id} returned a non-JSON value`);
      }
      const passed = JSON.stringify(output) === JSON.stringify(test.expected);
      testResults.push(passed ? { id: test.id, passed } : { id: test.id, passed, error: `Expected ${JSON.stringify(test.expected)}, got ${JSON.stringify(output)}` });
    }
    solve.dispose();
    return result(testResults.every((test) => test.passed) ? "passed" : "failed", testResults, startedAt);
  } catch (error) {
    return result("worker_error", [], startedAt, errorText(error));
  } finally {
    context.dispose();
    runtime.dispose();
  }
}

function result(status: EvaluationResult["status"], tests: readonly TestResult[], startedAt: number, error?: string): EvaluationResult {
  const passed = tests.filter((test) => test.passed).length;
  return {
    status,
    passed,
    total: request.task.tests.length,
    tests,
    durationMs: Math.round(performance.now() - startedAt),
    ...(error ? { error } : {})
  };
}

void run().then((evaluation) => parentPort?.postMessage(evaluation));
