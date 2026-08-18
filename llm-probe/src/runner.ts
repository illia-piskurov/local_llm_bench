import { writeFile } from "node:fs/promises";
import { join } from "node:path";
import { evaluate } from "./evaluator/index.js";
import { extractCode } from "./extractor.js";
import { syncLeaderboard } from "./leaderboard.js";
import type { ModelClient } from "./model-client.js";
import { buildMessages, buildRepairFeedback, buildRepairMessages } from "./prompts.js";
import { renderReport } from "./report.js";
import { renderHtmlReport } from "./html-report.js";
import { RunStorage } from "./storage.js";
import { getTask } from "./tasks.js";
import type { CandidateRecord, EvaluationResult, Task } from "./types.js";

export interface RunOptions {
  readonly client: ModelClient;
  readonly model: string;
  readonly tasks: ReadonlyArray<Task>;
  readonly samples: number;
  readonly repairs?: number;
  readonly temperature: number;
  readonly maxTokens: number;
  readonly baseUrl: string;
  readonly hardware?: string;
  readonly runsDir: string;
  /** Optional signal — abort to stop after the current candidate and write a partial run. */
  readonly signal?: AbortSignal;
  readonly onProgress?: (candidate: CandidateRecord) => void;
}

export interface ResumeOptions {
  readonly storage: RunStorage;
  readonly client: ModelClient;
  readonly runsDir: string;
  /** Optional signal — abort to stop after the current candidate and write a partial run. */
  readonly signal?: AbortSignal;
  readonly onProgress?: (candidate: CandidateRecord) => void;
}

interface ExecutionContext {
  readonly storage: RunStorage;
  readonly client: ModelClient;
  readonly model: string;
  readonly tasks: ReadonlyArray<Task>;
  readonly samples: number;
  readonly repairs: number;
  readonly temperature: number;
  readonly maxTokens: number;
  readonly runsDir: string;
  readonly signal?: AbortSignal;
  readonly onProgress?: (candidate: CandidateRecord) => void;
  readonly skipKeys?: ReadonlySet<string>;
}

export async function runBenchmark(options: RunOptions): Promise<RunStorage> {
  const repairs = options.repairs ?? 0;
  const storage = await RunStorage.create({
    runsDir: options.runsDir,
    model: options.model,
    baseUrl: options.baseUrl,
    ...(options.hardware !== undefined ? { hardware: options.hardware } : {}),
    temperature: options.temperature,
    maxTokens: options.maxTokens,
    samples: options.samples,
    ...(repairs > 0 ? { repairs } : {}),
    taskIds: options.tasks.map((task) => task.id)
  });

  return runExecutionLoop({
    storage,
    client: options.client,
    model: options.model,
    tasks: options.tasks,
    samples: options.samples,
    repairs,
    temperature: options.temperature,
    maxTokens: options.maxTokens,
    runsDir: options.runsDir,
    ...(options.signal !== undefined ? { signal: options.signal } : {}),
    ...(options.onProgress !== undefined ? { onProgress: options.onProgress } : {})
  });
}

export async function resumeBenchmark(options: ResumeOptions): Promise<RunStorage> {
  const { storage } = options;
  const manifest = storage.getManifest();

  if (manifest.status === "completed") {
    return storage;
  }

  await storage.setRunning();

  const skipKeys = new Set(manifest.candidates.map((c) => `${c.taskId}#${c.attempt}`));
  const tasks = manifest.taskIds
    .map((id) => getTask(id))
    .filter((task): task is Task => task !== undefined);

  return runExecutionLoop({
    storage,
    client: options.client,
    model: manifest.model,
    tasks,
    samples: manifest.samples,
    repairs: manifest.repairs ?? 0,
    temperature: manifest.temperature,
    maxTokens: manifest.maxTokens,
    runsDir: options.runsDir,
    skipKeys,
    ...(options.signal !== undefined ? { signal: options.signal } : {}),
    ...(options.onProgress !== undefined ? { onProgress: options.onProgress } : {})
  });
}

async function runExecutionLoop(ctx: ExecutionContext): Promise<RunStorage> {
  const { storage, client, model, tasks, samples, repairs, temperature, maxTokens, runsDir, signal, onProgress, skipKeys } = ctx;

  try {
    outer: for (const task of tasks) {
      for (let attempt = 1; attempt <= samples; attempt += 1) {
        // Skip already-evaluated candidates during resume
        if (skipKeys?.has(`${task.id}#${attempt}`)) {
          continue;
        }

        // Check for abort before starting each candidate so we finish cleanly.
        if (signal?.aborted) break outer;

        const messages = buildMessages(task);
        const request = {
          model,
          messages,
          temperature,
          max_tokens: maxTokens,
          stream: false as const
        };
        const prompt = messages.find((message) => message.role === "user")?.content ?? "";
        await storage.event({ type: "request_started", taskId: task.id, attempt });
        let completion;
        try {
          completion = await client.complete(request, signal);
        } catch (error) {
          const record: CandidateRecord = {
            taskId: task.id,
            attempt,
            repairAttempt: 0,
            status: "provider_error",
            durationMs: 0,
            generationMs: 0,
            error: errorText(error)
          };
          await storage.writeCandidate(task.id, attempt, { request, prompt, error: errorRecord(error) });
          await storage.record(record);
          await storage.event({ type: "provider_error", taskId: task.id, attempt, detail: errorRecord(error) });
          onProgress?.(record);
          // If the error was caused by an abort signal, stop the loop.
          if (signal?.aborted) break outer;
          continue;
        }

        // Warn when the model stopped early due to token limit.
        if (completion.finishReason === "length") {
          onProgress?.({
            taskId: task.id,
            attempt,
            repairAttempt: 0,
            status: "extract_error",
            durationMs: completion.durationMs,
            generationMs: completion.durationMs,
            finishReason: completion.finishReason,
            error: "finish_reason=length: response was truncated; increase --max-tokens"
          });
        }

        await storage.event({
          type: "response_received",
          taskId: task.id,
          attempt,
          detail: {
            durationMs: completion.durationMs,
            finishReason: completion.finishReason ?? null,
            ...(completion.usage ? { usage: completion.usage } : {})
          }
        });

        let currentCode = extractCode(completion.content) ?? "";
        let currentStatus: CandidateRecord["status"] = currentCode ? "passed" : "extract_error";
        let currentError: string | undefined = !currentCode
          ? (completion.finishReason === "length"
              ? "Response was truncated (finish_reason=length); increase --max-tokens"
              : "Response did not contain export function solve(input)")
          : undefined;
        let currentEvaluation: EvaluationResult | undefined;

        if (!currentCode) {
          const record: CandidateRecord = {
            taskId: task.id,
            attempt,
            repairAttempt: 0,
            status: "extract_error",
            durationMs: completion.durationMs,
            generationMs: completion.durationMs,
            ...(completion.finishReason ? { finishReason: completion.finishReason } : {}),
            ...(currentError !== undefined ? { error: currentError } : {})
          };
          await storage.writeCandidate(task.id, attempt, { request, prompt, response: completion, error: { message: record.error } });
          await storage.record(record);
          await storage.event({ type: "extract_error", taskId: task.id, attempt, detail: { message: record.error ?? "" } });
          onProgress?.(record);
        } else {
          currentEvaluation = await evaluate({ code: currentCode, task });
          currentStatus = currentEvaluation.status;
          currentError = currentEvaluation.error;

          const completionTokens = extractCompletionTokens(completion.usage);
          const tokensPerSec = completionTokens && completion.durationMs > 0
            ? Math.round((completionTokens / completion.durationMs) * 1000)
            : undefined;
          const record: CandidateRecord = {
            taskId: task.id,
            attempt,
            repairAttempt: 0,
            status: currentEvaluation.status,
            durationMs: completion.durationMs + currentEvaluation.durationMs,
            generationMs: completion.durationMs,
            ...(completion.finishReason ? { finishReason: completion.finishReason } : {}),
            ...(completion.usage ? { usage: completion.usage } : {}),
            ...(completionTokens !== undefined ? { completionTokens } : {}),
            ...(tokensPerSec !== undefined ? { tokensPerSec } : {}),
            passed: currentEvaluation.passed,
            total: currentEvaluation.total,
            ...(currentEvaluation.error ? { error: currentEvaluation.error } : {})
          };
          await storage.writeCandidate(task.id, attempt, { request, prompt, response: completion, code: currentCode, evaluation: currentEvaluation });
          await storage.record(record);
          await storage.event({
            type: "evaluation_finished",
            taskId: task.id,
            attempt,
            detail: { status: currentEvaluation.status, passed: currentEvaluation.passed, total: currentEvaluation.total }
          });
          onProgress?.(record);
        }

        // ── Self-Repair Loop (if initial candidate failed and repairs > 0) ───
        if (currentStatus !== "passed" && repairs > 0 && !signal?.aborted) {
          const repairHistory: Array<{ code: string; feedback: string }> = [];
          const initialFailedStatus = currentStatus;

          for (let rep = 1; rep <= repairs; rep++) {
            if (signal?.aborted) break outer;

            const feedback = buildRepairFeedback(task, currentStatus, currentError, currentEvaluation);
            repairHistory.push({ code: currentCode || "// Failed to extract code", feedback });

            const repairMessages = buildRepairMessages(messages, repairHistory);
            const repairRequest = {
              model,
              messages: repairMessages,
              temperature,
              max_tokens: maxTokens,
              stream: false as const
            };

            await storage.event({ type: "repair_started", taskId: task.id, attempt, repairAttempt: rep });

            let repCompletion;
            try {
              repCompletion = await client.complete(repairRequest, signal);
            } catch (err) {
              await storage.event({
                type: "repair_finished",
                taskId: task.id,
                attempt,
                repairAttempt: rep,
                detail: { error: errorText(err) }
              });
              break;
            }

            const repCode = extractCode(repCompletion.content);
            if (!repCode) {
              currentStatus = "extract_error";
              currentError = "Repaired response did not contain export function solve(input)";
              const repRecord: CandidateRecord = {
                taskId: task.id,
                attempt,
                repairAttempt: rep,
                status: "extract_error",
                durationMs: repCompletion.durationMs,
                generationMs: repCompletion.durationMs,
                error: currentError,
                repairedFrom: initialFailedStatus
              };
              await storage.writeCandidate(task.id, attempt, { request: repairRequest, prompt: feedback, response: repCompletion, error: { message: repRecord.error } }, rep);
              await storage.record(repRecord);
              onProgress?.(repRecord);
              continue;
            }

            const repEval = await evaluate({ code: repCode, task });
            const repTokens = extractCompletionTokens(repCompletion.usage);
            const repTps = repTokens && repCompletion.durationMs > 0
              ? Math.round((repTokens / repCompletion.durationMs) * 1000)
              : undefined;

            const repRecord: CandidateRecord = {
              taskId: task.id,
              attempt,
              repairAttempt: rep,
              status: repEval.status,
              durationMs: repCompletion.durationMs + repEval.durationMs,
              generationMs: repCompletion.durationMs,
              ...(repCompletion.finishReason ? { finishReason: repCompletion.finishReason } : {}),
              ...(repCompletion.usage ? { usage: repCompletion.usage } : {}),
              ...(repTokens !== undefined ? { completionTokens: repTokens } : {}),
              ...(repTps !== undefined ? { tokensPerSec: repTps } : {}),
              passed: repEval.passed,
              total: repEval.total,
              ...(repEval.error ? { error: repEval.error } : {}),
              repairedFrom: initialFailedStatus
            };

            await storage.writeCandidate(task.id, attempt, { request: repairRequest, prompt: feedback, response: repCompletion, code: repCode, evaluation: repEval }, rep);
            await storage.record(repRecord);
            await storage.event({
              type: "repair_finished",
              taskId: task.id,
              attempt,
              repairAttempt: rep,
              detail: { status: repEval.status, passed: repEval.passed, total: repEval.total }
            });
            onProgress?.(repRecord);

            currentCode = repCode;
            currentStatus = repEval.status;
            currentError = repEval.error;
            currentEvaluation = repEval;

            if (repEval.status === "passed") {
              break; // Successfully repaired!
            }
          }
        }
      }
    }

    const finalStatus = signal?.aborted ? "partial" : "completed";
    await storage.finish(finalStatus);
  } catch (error) {
    await storage.event({ type: "run_error", detail: { message: errorText(error) } });
    await storage.finish("partial");
    await writeReports(storage);
    await syncLeaderboard(runsDir);
    throw error;
  }

  await writeReports(storage);
  await syncLeaderboard(runsDir);
  return storage;
}

async function writeReports(storage: RunStorage): Promise<void> {
  const manifest = storage.getManifest();
  await writeFile(join(storage.dir, "report.md"), renderReport(manifest), "utf8");
  try {
    const details = await storage.loadCandidateDetails();
    await writeFile(join(storage.dir, "report.html"), renderHtmlReport(manifest, details), "utf8");
  } catch {
    // Non-critical if HTML generation fails
  }
}

function errorText(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}

function errorRecord(error: unknown): { readonly message: string; readonly name?: string; readonly status?: number; readonly body?: string } {
  if (error instanceof Error) {
    const candidate = error as Error & { status?: unknown; body?: unknown };
    return {
      message: error.message,
      ...(error.name ? { name: error.name } : {}),
      ...(typeof candidate.status === "number" ? { status: candidate.status } : {}),
      ...(typeof candidate.body === "string" ? { body: candidate.body } : {})
    };
  }
  return { message: String(error) };
}

function extractCompletionTokens(usage: unknown): number | undefined {
  if (typeof usage !== "object" || usage === null) return undefined;
  const ct = (usage as Record<string, unknown>)["completion_tokens"];
  return typeof ct === "number" && ct > 0 ? ct : undefined;
}
