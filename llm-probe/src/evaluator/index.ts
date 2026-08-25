import { Worker } from "node:worker_threads";
import type { EvaluationRequest, EvaluationResult } from "../types.js";

const CANDIDATE_TIMEOUT_MS = 2_000;

export async function evaluate(request: EvaluationRequest): Promise<EvaluationResult> {
  return new Promise((resolve) => {
    const worker = new Worker(new URL("./worker.js", import.meta.url), {
      workerData: request
    });
    const startedAt = performance.now();
    let settled = false;

    const finish = (result: EvaluationResult): void => {
      if (settled) return;
      settled = true;
      clearTimeout(timeout);
      resolve(result);
    };

    const timeout = setTimeout(() => {
      void worker.terminate();
      finish({
        status: "timeout",
        passed: 0,
        total: request.task.tests.length,
        tests: [],
        durationMs: Math.round(performance.now() - startedAt),
        error: `Candidate exceeded ${CANDIDATE_TIMEOUT_MS}ms wall-clock limit`
      });
    }, CANDIDATE_TIMEOUT_MS);

    worker.once("message", (result: EvaluationResult) => finish(result));
    worker.once("error", (error) => finish({
      status: "worker_error",
      passed: 0,
      total: request.task.tests.length,
      tests: [],
      durationMs: Math.round(performance.now() - startedAt),
      error: error.message
    }));
    worker.once("exit", (code) => {
      if (code !== 0 && !settled) {
        finish({
          status: "worker_error",
          passed: 0,
          total: request.task.tests.length,
          tests: [],
          durationMs: Math.round(performance.now() - startedAt),
          error: `Evaluator worker exited with code ${code}`
        });
      }
    });
  });
}
