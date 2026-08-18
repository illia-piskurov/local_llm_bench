import { readFile, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { parseArgs } from "node:util";
import { renderComparisonReport, runCompare } from "./compare.js";
import { loadConfig, resolveProfile } from "./config.js";
import { evaluate } from "./evaluator/index.js";
import { renderHtmlReport } from "./html-report.js";
import { runInteractive } from "./interactive.js";
import { syncLeaderboard } from "./leaderboard.js";
import { OpenAiCompatibleClient } from "./model-client.js";
import { renderReport } from "./report.js";
import { resumeBenchmark, runBenchmark } from "./runner.js";
import { RunStorage } from "./storage.js";
import { coreTasks, getTask } from "./tasks.js";
import type { CandidateRecord, Task } from "./types.js";

const DEFAULT_BASE_URL = "http://127.0.0.1:1234/v1";
const DEFAULT_TIMEOUT_MS = 120_000;

function usage(): void {
  console.log(`llm-probe

Usage:
  probe tasks
  probe eval --task <task-id> --code <solution.js>
  probe models [--base-url <url>] [--profile <name>]
  probe run --model <model-id> [--hardware <spec>] [--task <id>]... [--samples <n>] \
            [--repairs <n>] [--base-url <url>] [--profile <name>] [--temperature <n>] \
            [--max-tokens <n>] [--timeout-ms <n>] [--runs-dir <dir>]
  probe compare --models <model1,model2> [--hardware <spec>] [--task <id>]... \
                [--repairs <n>] [--base-url <url>] [--profile <name>] [--samples <n>]
  probe resume [run-id|latest] [--runs-dir <dir>]
  probe runs [--runs-dir <dir>]
  probe report [run-id|latest] [--runs-dir <dir>]
  probe leaderboard [--runs-dir <dir>]
  probe inspect <run-id|latest> [--task <id> --sample <n>] [--runs-dir <dir>]

Config file: probe.config.json (optional, loaded from current directory)
  See probe.config.example.json for the format.`);
}

async function main(): Promise<void> {
  const { positionals, values } = parseArgs({
    args: process.argv.slice(2),
    options: {
      task:         { type: "string", multiple: true },
      code:         { type: "string" },
      model:        { type: "string", multiple: true },
      models:       { type: "string" },
      samples:      { type: "string" },
      repairs:      { type: "string" },
      temperature:  { type: "string" },
      "max-tokens": { type: "string" },
      "base-url":   { type: "string" },
      "profile":    { type: "string" },
      hardware:     { type: "string" },
      resume:       { type: "string" },
      "timeout-ms": { type: "string" },
      "runs-dir":   { type: "string" },
      sample:       { type: "string" },
      help:         { type: "boolean", short: "h" }
    },
    allowPositionals: true,
    strict: true
  });

  const command = positionals[0];
  if (values.help) return usage();
  if (!command) return runInteractive();

  // Load probe.config.json (silently ignored if absent).
  const config = await loadConfig();

  // Resolve base URL: CLI flag > named profile > config default profile > hardcoded default.
  const profileResolved = resolveProfile(config, values["profile"]);
  const baseUrl = values["base-url"] ?? profileResolved?.baseUrl ?? DEFAULT_BASE_URL;
  const apiKey = profileResolved?.apiKey;
  const runsDir = values["runs-dir"] ?? config.defaults?.runsDir ?? "runs";
  const timeoutMs = positiveInteger(
    values["timeout-ms"] ?? String(config.defaults?.timeoutMs ?? DEFAULT_TIMEOUT_MS),
    "timeout-ms"
  );

  if (command === "tasks") {
    for (const task of coreTasks) {
      console.log(`${task.id.padEnd(30)} [${task.category.padEnd(12)}] ${task.title}`);
    }
    return;
  }
  if (command === "eval") return evaluateFile(requiredTask(values.task), values.code);
  if (command === "models") return listModels(baseUrl, apiKey, timeoutMs);
  if (command === "run") {
    if (values.resume) return resumeRun(values.resume, baseUrl, apiKey, runsDir, timeoutMs);
    return run(values, baseUrl, apiKey, runsDir, timeoutMs, config);
  }
  if (command === "compare" || command === "matrix") {
    return compare(values, baseUrl, apiKey, runsDir, timeoutMs, config);
  }
  if (command === "resume") {
    const selector = positionals[1] ?? values.resume ?? "latest";
    return resumeRun(selector, baseUrl, apiKey, runsDir, timeoutMs);
  }
  if (command === "runs") return listRuns(runsDir);
  if (command === "report") {
    const selector = positionals[1] ?? "latest";
    return showReport(selector, runsDir);
  }
  if (command === "leaderboard" || command === "lb") {
    const { markdown, htmlPath } = await syncLeaderboard(runsDir);
    console.log(markdown);
    console.log(`\nHTML leaderboard: ${htmlPath}`);
    return;
  }
  if (command === "inspect") return inspect(positionals[1], values.task?.[0], values.sample, runsDir);

  usage();
  process.exitCode = 1;
}

function requiredTask(taskIds: readonly string[] | undefined): string {
  if (taskIds?.length === 1) return taskIds[0]!;
  throw new Error("eval requires exactly one --task <task-id>");
}

async function evaluateFile(taskId: string, codePath: string | undefined): Promise<void> {
  if (!codePath) throw new Error("eval requires --code <solution.js>");
  const task = getTask(taskId);
  if (!task) throw new Error(`Unknown task: ${taskId}`);
  const code = await readFile(codePath, "utf8");
  const evaluation = await evaluate({ code, task });
  console.log(`${task.id}: ${evaluation.status} (${evaluation.passed}/${evaluation.total}, ${evaluation.durationMs}ms)`);
  for (const test of evaluation.tests) {
    console.log(`  ${test.passed ? "PASS" : "FAIL"} ${test.id}${test.error ? ` — ${test.error}` : ""}`);
  }
  if (evaluation.error) console.error(`  ${evaluation.error}`);
  if (evaluation.status !== "passed") process.exitCode = 1;
}

async function listModels(baseUrl: string, apiKey: string | undefined, timeoutMs: number): Promise<void> {
  const models = await new OpenAiCompatibleClient(baseUrl, { timeoutMs, ...(apiKey !== undefined ? { apiKey } : {}) }).listModels();
  if (models.length === 0) console.log("No models returned by provider.");
  for (const model of models) console.log(model.id);
}

async function run(
  values: {
    readonly model?: readonly string[];
    readonly models?: string;
    readonly task?: readonly string[];
    readonly samples?: string;
    readonly repairs?: string;
    readonly temperature?: string;
    readonly "max-tokens"?: string;
    readonly "profile"?: string;
    readonly hardware?: string;
  },
  baseUrl: string,
  apiKey: string | undefined,
  runsDir: string,
  timeoutMs: number,
  config: Awaited<ReturnType<typeof loadConfig>>
): Promise<void> {
  const model = values.model?.[0];
  if (!model) throw new Error("run requires --model <model-id>");

  const taskIds = values.task ?? coreTasks.map((task) => task.id);
  const tasks = taskIds.map((id) => getTask(id)).filter((task): task is Task => task !== undefined);
  if (tasks.length !== taskIds.length) {
    throw new Error(`Unknown task: ${taskIds.find((id) => !getTask(id))}`);
  }

  const samples = positiveInteger(values.samples ?? "1", "samples");
  const repairs = values.repairs !== undefined ? nonNegativeInteger(values.repairs, "repairs") : 0;
  const maxTokens = positiveInteger(
    values["max-tokens"] ?? String(config.defaults?.maxTokens ?? 2048),
    "max-tokens"
  );
  const temperature = finiteNumber(
    values.temperature ?? String(config.defaults?.temperature ?? 0.2),
    "temperature"
  );
  const hardware = values.hardware ?? config.hardware ?? config.defaults?.hardware;
  if (!hardware || !hardware.trim()) {
    throw new Error(
      "Hardware configuration is required for benchmark runs (for reliable speed & latency comparison).\n" +
      "Specify it via --hardware \"CPU | RAM | GPU\" or set \"hardware\" in probe.config.json."
    );
  }

  const client = new OpenAiCompatibleClient(baseUrl, { timeoutMs, ...(apiKey !== undefined ? { apiKey } : {}) });

  // Set up graceful Ctrl+C: abort the current HTTP request and finalise the run as partial.
  const controller = new AbortController();
  let shutdownRequested = false;
  process.once("SIGINT", () => {
    if (shutdownRequested) process.exit(1); // second Ctrl+C → force exit
    shutdownRequested = true;
    console.log("\n\nInterrupt received — finishing current candidate then saving partial run…");
    controller.abort();
  });

  const repInfo = repairs > 0 ? ` (with up to ${repairs} repair attempts)` : "";
  console.log(`Running ${tasks.length} task(s) × ${samples} sample(s)${repInfo} on ${model} [${hardware}] (timeout ${timeoutMs}ms)…`);

  const storage = await runBenchmark({
    client,
    model,
    tasks,
    samples,
    repairs,
    temperature,
    maxTokens,
    baseUrl,
    hardware,
    runsDir,
    signal: controller.signal,
    onProgress: (candidate) => printProgress(candidate)
  });

  const manifest = storage.getManifest();
  console.log(`\nSaved ${manifest.status} run: ${storage.dir}`);
  console.log(renderReport(manifest));

  // If we saved a partial run, exit with a non-zero code so CI/scripts can detect it.
  if (manifest.status === "partial") process.exitCode = 2;
}

async function compare(
  values: {
    readonly model?: readonly string[];
    readonly models?: string;
    readonly task?: readonly string[];
    readonly samples?: string;
    readonly temperature?: string;
    readonly "max-tokens"?: string;
    readonly "profile"?: string;
    readonly hardware?: string;
  },
  baseUrl: string,
  apiKey: string | undefined,
  runsDir: string,
  timeoutMs: number,
  config: Awaited<ReturnType<typeof loadConfig>>
): Promise<void> {
  const modelList = values.models
    ? values.models.split(",").map((m) => m.trim()).filter(Boolean)
    : (values.model ?? []);

  if (modelList.length === 0) {
    throw new Error("compare requires --models <model1,model2> or --model <id>...");
  }

  const taskIds = values.task ?? coreTasks.map((task) => task.id);
  const tasks = taskIds.map((id) => getTask(id)).filter((task): task is Task => task !== undefined);
  if (tasks.length !== taskIds.length) {
    throw new Error(`Unknown task: ${taskIds.find((id) => !getTask(id))}`);
  }

  const samples = positiveInteger(values.samples ?? "1", "samples");
  const maxTokens = positiveInteger(
    values["max-tokens"] ?? String(config.defaults?.maxTokens ?? 2048),
    "max-tokens"
  );
  const temperature = finiteNumber(
    values.temperature ?? String(config.defaults?.temperature ?? 0.2),
    "temperature"
  );
  const hardware = values.hardware ?? config.hardware ?? config.defaults?.hardware;
  if (!hardware || !hardware.trim()) {
    throw new Error(
      "Hardware configuration is required for benchmark runs (for reliable speed & latency comparison).\n" +
      "Specify it via --hardware \"CPU | RAM | GPU\" or set \"hardware\" in probe.config.json."
    );
  }

  const client = new OpenAiCompatibleClient(baseUrl, { timeoutMs, ...(apiKey !== undefined ? { apiKey } : {}) });

  const controller = new AbortController();
  let shutdownRequested = false;
  process.once("SIGINT", () => {
    if (shutdownRequested) process.exit(1);
    shutdownRequested = true;
    console.log("\n\nInterrupt received — finishing current candidate then saving partial runs…");
    controller.abort();
  });

  console.log(`\nComparing ${modelList.length} model(s) across ${tasks.length} task(s) on [${hardware}]…`);

  const storages = await runCompare({
    client,
    models: modelList,
    tasks,
    samples,
    temperature,
    maxTokens,
    baseUrl,
    hardware,
    runsDir,
    signal: controller.signal,
    onModelStart: (model, idx, total) => {
      console.log(`\n=== [${idx}/${total}] Benchmarking ${model} ===`);
    },
    onProgress: (_model, candidate) => printProgress(candidate)
  });

  const manifests = storages.map((s) => s.getManifest());
  console.log("\n" + renderComparisonReport(manifests, tasks));
}

async function resumeRun(
  selector: string,
  baseUrl: string,
  apiKey: string | undefined,
  runsDir: string,
  timeoutMs: number
): Promise<void> {
  const storage = await RunStorage.open(runsDir, selector);
  const manifest = storage.getManifest();

  if (manifest.status === "completed") {
    console.log(`Run ${manifest.id} is already completed (${manifest.candidates.length} candidates).`);
    return;
  }

  const client = new OpenAiCompatibleClient(manifest.baseUrl || baseUrl, {
    timeoutMs,
    ...(apiKey !== undefined ? { apiKey } : {})
  });

  const controller = new AbortController();
  let shutdownRequested = false;
  process.once("SIGINT", () => {
    if (shutdownRequested) process.exit(1);
    shutdownRequested = true;
    console.log("\n\nInterrupt received — finishing current candidate then saving partial run…");
    controller.abort();
  });

  const completedCount = manifest.candidates.length;
  const totalCount = manifest.taskIds.length * manifest.samples;
  const hwInfo = manifest.hardware ? ` on [${manifest.hardware}]` : "";
  console.log(
    `Resuming run ${manifest.id} (${completedCount}/${totalCount} candidates already done) on ${manifest.model}${hwInfo}…`
  );

  await resumeBenchmark({
    storage,
    client,
    runsDir,
    signal: controller.signal,
    onProgress: (candidate) => printProgress(candidate)
  });

  const updatedManifest = storage.getManifest();
  console.log(`\nSaved ${updatedManifest.status} run: ${storage.dir}`);
  console.log(renderReport(updatedManifest));

  if (updatedManifest.status === "partial") process.exitCode = 2;
}

async function listRuns(runsDir: string): Promise<void> {
  const runs = await RunStorage.list(runsDir);
  if (runs.length === 0) return console.log(`No runs in ${runsDir}.`);
  for (const run of runs) {
    console.log(`${run.id}  ${run.status.padEnd(9)}  ${run.model}  ${run.candidates.length} candidates`);
  }
}

async function showReport(selector: string, runsDir: string): Promise<void> {
  const storage = await RunStorage.open(runsDir, selector);
  const manifest = storage.getManifest();
  console.log(renderReport(manifest));
  const htmlPath = join(storage.dir, "report.html");
  try {
    const details = await storage.loadCandidateDetails();
    await writeFile(htmlPath, renderHtmlReport(manifest, details), "utf8");
    console.log(`\nInteractive HTML Report: ${htmlPath}`);
  } catch {
    // Non-critical
  }
}

async function inspect(
  selector: string | undefined,
  taskId: string | undefined,
  sample: string | undefined,
  runsDir: string
): Promise<void> {
  if (!selector) throw new Error("inspect requires <run-id|latest>");
  const storage = await RunStorage.open(runsDir, selector);
  if (!taskId) return console.log(renderReport(storage.getManifest()));
  const attempt = positiveInteger(sample ?? "1", "sample");
  const prefix = `candidates/${taskId}/${String(attempt).padStart(2, "0")}`;
  for (const filename of ["prompt.txt", "response.raw.txt", "solution.js", "evaluation.json", "error.json"]) {
    try {
      console.log(`\n--- ${filename} ---\n${await storage.readText(`${prefix}/${filename}`)}`);
    } catch { /* absent artifacts are expected for provider failures */ }
  }
}

function positiveInteger(value: string, name: string): number {
  const parsed = Number(value);
  if (!Number.isInteger(parsed) || parsed < 1) throw new Error(`${name} must be a positive integer`);
  return parsed;
}

function nonNegativeInteger(value: string, name: string): number {
  const parsed = Number(value);
  if (!Number.isInteger(parsed) || parsed < 0) throw new Error(`${name} must be a non-negative integer (0, 1, 2...)`);
  return parsed;
}

function finiteNumber(value: string, name: string): number {
  const parsed = Number(value);
  if (!Number.isFinite(parsed) || parsed < 0) throw new Error(`${name} must be a non-negative number`);
  return parsed;
}

function printProgress(candidate: CandidateRecord): void {
  const tests = candidate.total === undefined ? "" : ` ${candidate.passed ?? 0}/${candidate.total}`;
  const gen = candidate.generationMs !== undefined ? ` gen:${candidate.generationMs}ms` : "";
  const tps = candidate.tokensPerSec !== undefined ? ` ${candidate.tokensPerSec}tok/s` : "";
  const finish = candidate.finishReason && candidate.finishReason !== "stop" ? ` [${candidate.finishReason}]` : "";
  const repTag = (candidate.repairAttempt ?? 0) > 0 ? ` (Repair #${candidate.repairAttempt})` : "";
  const repFrom = candidate.repairedFrom ? ` [repaired from ${candidate.repairedFrom}]` : "";
  console.log(`${candidate.taskId} #${candidate.attempt}${repTag}: ${candidate.status}${repFrom}${tests}${gen}${tps}${finish} (${candidate.durationMs}ms total)`);
}

void main().catch((error: unknown) => {
  console.error(error instanceof Error ? error.stack ?? error.message : String(error));
  process.exitCode = 1;
});
