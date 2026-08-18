import {
  cancel,
  confirm,
  intro,
  isCancel,
  log,
  multiselect,
  outro,
  select,
  spinner,
  text
} from "@clack/prompts";
import { loadConfig, resolveProfile, saveHardware } from "./config.js";
import { renderComparisonReport, runCompare } from "./compare.js";
import { syncLeaderboard } from "./leaderboard.js";
import { OpenAiCompatibleClient } from "./model-client.js";
import { renderReport } from "./report.js";
import { resumeBenchmark, runBenchmark } from "./runner.js";
import { RunStorage } from "./storage.js";
import { coreTasks } from "./tasks.js";
import type { CandidateRecord, Task } from "./types.js";

const DEFAULT_BASE_URL = "http://127.0.0.1:1234/v1";
const DEFAULT_TIMEOUT_MS = 120_000;

export async function runInteractive(): Promise<void> {
  if (!process.stdout.isTTY) {
    process.stderr.write(
      "Interactive mode requires a terminal. Run `probe --help` for command-line usage.\n"
    );
    process.exitCode = 1;
    return;
  }

  intro(" llm-probe ");

  const config = await loadConfig();
  const profileResolved = resolveProfile(config);
  const baseUrl = profileResolved?.baseUrl ?? DEFAULT_BASE_URL;
  const apiKey = profileResolved?.apiKey;
  const timeoutMs = config.defaults?.timeoutMs ?? DEFAULT_TIMEOUT_MS;
  const runsDir = config.defaults?.runsDir ?? "runs";

  const allRuns = await RunStorage.list(runsDir);
  const partialRuns = allRuns.filter((r) => r.status !== "completed");

  const action = await select({
    message: "What would you like to do?",
    options: [
      { value: "run",         label: "Run benchmark on single model" },
      { value: "compare",     label: "Compare multiple models (Matrix benchmark)" },
      ...(partialRuns.length > 0
        ? [{ value: "resume", label: `Resume a partial run (${partialRuns.length} available)` }]
        : []),
      { value: "leaderboard", label: "View model rankings / Leaderboard" },
      { value: "inspect",     label: "Inspect a run" },
      { value: "tasks",       label: "Browse tasks" },
      { value: "models",      label: "List available models" },
    ]
  });
  if (isCancel(action)) { cancel(); return; }

  try {
    switch (action as string) {
      case "run":         await interactiveRun(baseUrl, apiKey, timeoutMs, runsDir, config); break;
      case "compare":     await interactiveCompare(baseUrl, apiKey, timeoutMs, runsDir, config); break;
      case "resume":      await interactiveResume(baseUrl, apiKey, timeoutMs, runsDir); break;
      case "leaderboard": await showLeaderboard(runsDir); break;
      case "inspect":     await interactiveInspect(runsDir); break;
      case "tasks":       showTasks(); break;
      case "models":      await showModels(baseUrl, apiKey, timeoutMs); break;
    }
  } catch (error) {
    log.error(error instanceof Error ? (error.stack ?? error.message) : String(error));
    process.exitCode = 1;
  }

  outro("Done!");
}

// ── Run benchmark ─────────────────────────────────────────────────────────────

async function interactiveRun(
  baseUrl: string,
  apiKey: string | undefined,
  timeoutMs: number,
  runsDir: string,
  config: Awaited<ReturnType<typeof loadConfig>>
): Promise<void> {
  // 1. Model
  const model = await pickModel(baseUrl, apiKey, timeoutMs);
  if (model == null) return;

  // 2. Tasks
  const scopeChoice = await select({
    message: "Which tasks?",
    options: [
      { value: "all",  label: `All tasks (${coreTasks.length})` },
      { value: "pick", label: "Choose specific tasks…" },
    ]
  });
  if (isCancel(scopeChoice)) { cancel(); return; }

  let tasks: Task[];
  if (scopeChoice === "pick") {
    const picked = await multiselect({
      message: "Select tasks  (space = toggle, a = all, enter = confirm)",
      options: coreTasks.map(t => ({
        value: t.id,
        label: `[${t.category.padEnd(12)}] ${t.title}`,
        hint: t.id
      })),
      initialValues: coreTasks.map(t => t.id),
      required: true
    });
    if (isCancel(picked)) { cancel(); return; }
    tasks = (picked as string[])
      .map(id => coreTasks.find(t => t.id === id))
      .filter((t): t is Task => t !== undefined);
  } else {
    tasks = [...coreTasks];
  }

  // 3. Samples
  const samplesStr = await text({
    message: "Samples per task",
    defaultValue: "1",
    placeholder: "1",
    validate: v => {
      const n = Number(v || "1");
      if (!Number.isInteger(n) || n < 1) return "Must be a positive integer";
    }
  });
  if (isCancel(samplesStr)) { cancel(); return; }
  const samples = Number(samplesStr || "1");

  // 4. Temperature
  const tempStr = await text({
    message: "Temperature",
    defaultValue: String(config.defaults?.temperature ?? 0.2),
    placeholder: "0.2",
    validate: v => {
      const n = Number(v || "0.2");
      if (!Number.isFinite(n) || n < 0) return "Must be a non-negative number";
    }
  });
  if (isCancel(tempStr)) { cancel(); return; }
  const temperature = Number(tempStr || "0.2");

  // 5. Max tokens
  const maxTokensStr = await text({
    message: "Max tokens",
    defaultValue: String(config.defaults?.maxTokens ?? 2048),
    placeholder: "2048",
    validate: v => {
      const n = Number(v || "2048");
      if (!Number.isInteger(n) || n < 64) return "Must be an integer ≥ 64";
    }
  });
  if (isCancel(maxTokensStr)) { cancel(); return; }
  const maxTokens = Number(maxTokensStr || "2048");

  // 6. Hardware (for fair speed & latency tracking)
  const hardware = await pickHardware(config);
  if (hardware == null) return;

  // 7. Confirm
  const go = await confirm({
    message: `Run ${tasks.length} task(s) × ${samples} sample(s) on ${model} [${hardware}]?`
  });
  if (isCancel(go) || !go) { cancel(); return; }

  // 8. Progress
  const total = tasks.length * samples;
  const taskOrder = tasks.flatMap(t =>
    Array.from({ length: samples }, (_, i) => ({ taskId: t.id, attempt: i + 1 }))
  );
  let completed = 0;

  const s = spinner();
  const firstLabel = taskOrder[0]?.taskId ?? "";
  s.start(`[1/${total}] ${firstLabel}…`);

  const controller = new AbortController();
  process.once("SIGINT", () => {
    log.warn("\nInterrupt — saving partial run after current candidate…");
    controller.abort();
  });

  const storage = await runBenchmark({
    client: new OpenAiCompatibleClient(baseUrl, {
      timeoutMs,
      ...(apiKey !== undefined ? { apiKey } : {})
    }),
    model,
    tasks,
    samples,
    temperature,
    maxTokens,
    baseUrl,
    hardware,
    runsDir,
    signal: controller.signal,
    onProgress: (candidate) => {
      // Format result line
      const icon = candidate.status === "passed" ? "✓" : "✗";
      const code = candidate.status === "passed" ? 0 : 2;
      const parts: string[] = [];
      if (candidate.total !== undefined) parts.push(`${candidate.passed ?? 0}/${candidate.total}`);
      if (candidate.generationMs !== undefined) parts.push(`${candidate.generationMs}ms`);
      if (candidate.tokensPerSec !== undefined) parts.push(`${candidate.tokensPerSec} tok/s`);
      const label = samples > 1
        ? `${candidate.taskId} #${candidate.attempt}`
        : candidate.taskId;
      const line = `${label.padEnd(34)} ${parts.join("  ")}`;
      if (candidate.status === "passed") s.stop(`✓ ${line}`);
      else s.error(`✗ ${line}`);

      completed++;
      if (completed < total) {
        const next = taskOrder[completed]!;
        const nextLabel = samples > 1
          ? `${next.taskId} #${next.attempt}`
          : next.taskId;
        s.start(`[${completed + 1}/${total}] ${nextLabel}…`);
      }
    }
  });

  // 8. Summary
  const manifest = storage.getManifest();
  const passedCount = manifest.candidates.filter(c => c.status === "passed").length;
  const tpsValues = manifest.candidates
    .map(c => c.tokensPerSec)
    .filter((v): v is number => v !== undefined);
  const meanTps = tpsValues.length > 0
    ? Math.round(tpsValues.reduce((a, b) => a + b, 0) / tpsValues.length)
    : undefined;

  const statusLabel = manifest.status === "partial" ? "Partial run" : "Complete";
  log.success(
    `${statusLabel}  ·  success@1: ${passedCount}/${manifest.candidates.length}` +
    (meanTps !== undefined ? `  ·  ${meanTps} tok/s avg` : "")
  );
  log.info(`Saved: ${storage.dir}`);

  const failures = manifest.candidates.filter(c => c.status !== "passed");
  if (failures.length > 0) {
    log.warn(`Failed: ${failures.map(c => c.taskId).join(", ")}`);
  }

  const showFull = await confirm({ message: "Show full report?" });
  if (!isCancel(showFull) && showFull) {
    log.message("\n" + renderReport(manifest));
  }

  if (manifest.status === "partial") process.exitCode = 2;
}

// ── Resume partial run ────────────────────────────────────────────────────────

async function interactiveResume(
  baseUrl: string,
  apiKey: string | undefined,
  timeoutMs: number,
  runsDir: string
): Promise<void> {
  const manifests = await RunStorage.list(runsDir);
  const partial = manifests.filter((m) => m.status !== "completed");
  if (partial.length === 0) {
    log.info("No partial runs found to resume.");
    return;
  }

  const choice = await select({
    message: "Select a partial run to resume",
    options: partial.map((m) => {
      const total = m.taskIds.length * m.samples;
      const done = m.candidates.length;
      return {
        value: m.id,
        label: `${m.id}`,
        hint: `${m.model} · ${done}/${total} done`
      };
    })
  });
  if (isCancel(choice)) { cancel(); return; }

  const storage = await RunStorage.open(runsDir, choice as string);
  const manifest = storage.getManifest();
  const completedKeys = new Set(manifest.candidates.map((c) => `${c.taskId}#${c.attempt}`));

  const allPairs = manifest.taskIds.flatMap((taskId) =>
    Array.from({ length: manifest.samples }, (_, i) => ({ taskId, attempt: i + 1 }))
  );
  const remaining = allPairs.filter((p) => !completedKeys.has(`${p.taskId}#${p.attempt}`));

  if (remaining.length === 0) {
    log.info("All tasks in this run are already evaluated!");
    return;
  }

  const go = await confirm({
    message: `Resume ${remaining.length} remaining candidate(s) for ${manifest.model}?`
  });
  if (isCancel(go) || !go) { cancel(); return; }

  let completed = 0;
  const s = spinner();
  s.start(`[1/${remaining.length}] ${remaining[0]?.taskId}…`);

  const controller = new AbortController();
  process.once("SIGINT", () => {
    log.warn("\nInterrupt — saving partial run after current candidate…");
    controller.abort();
  });

  await resumeBenchmark({
    storage,
    client: new OpenAiCompatibleClient(manifest.baseUrl || baseUrl, {
      timeoutMs,
      ...(apiKey !== undefined ? { apiKey } : {})
    }),
    runsDir,
    signal: controller.signal,
    onProgress: (candidate) => {
      const parts: string[] = [];
      if (candidate.total !== undefined) parts.push(`${candidate.passed ?? 0}/${candidate.total}`);
      if (candidate.generationMs !== undefined) parts.push(`${candidate.generationMs}ms`);
      if (candidate.tokensPerSec !== undefined) parts.push(`${candidate.tokensPerSec} tok/s`);
      const label = manifest.samples > 1
        ? `${candidate.taskId} #${candidate.attempt}`
        : candidate.taskId;
      const line = `${label.padEnd(34)} ${parts.join("  ")}`;
      if (candidate.status === "passed") s.stop(`✓ ${line}`);
      else s.error(`✗ ${line}`);

      completed++;
      if (completed < remaining.length) {
        const next = remaining[completed]!;
        const nextLabel = manifest.samples > 1
          ? `${next.taskId} #${next.attempt}`
          : next.taskId;
        s.start(`[${completed + 1}/${remaining.length}] ${nextLabel}…`);
      }
    }
  });

  const updatedManifest = storage.getManifest();
  const passedCount = updatedManifest.candidates.filter((c) => c.status === "passed").length;
  const tpsValues = updatedManifest.candidates
    .map((c) => c.tokensPerSec)
    .filter((v): v is number => v !== undefined);
  const meanTps = tpsValues.length > 0
    ? Math.round(tpsValues.reduce((a, b) => a + b, 0) / tpsValues.length)
    : undefined;

  log.success(
    `Done! Status: ${updatedManifest.status}  ·  Passed: ${passedCount}/${updatedManifest.candidates.length}` +
    (meanTps !== undefined ? `  ·  ${meanTps} tok/s avg` : "")
  );
  log.info(`Saved: ${storage.dir}`);

  const showFull = await confirm({ message: "Show full report?" });
  if (!isCancel(showFull) && showFull) {
    log.message("\n" + renderReport(updatedManifest));
  }

  if (updatedManifest.status === "partial") process.exitCode = 2;
}

// ── Model picker ──────────────────────────────────────────────────────────────

async function pickModel(
  baseUrl: string,
  apiKey: string | undefined,
  timeoutMs: number
): Promise<string | null> {
  const s = spinner();
  s.start(`Fetching models from ${baseUrl}…`);

  let modelIds: string[] = [];
  try {
    const client = new OpenAiCompatibleClient(baseUrl, {
      timeoutMs: Math.min(timeoutMs, 5_000),
      ...(apiKey !== undefined ? { apiKey } : {})
    });
    const models = await client.listModels();
    modelIds = models.map(m => m.id);
    s.stop(`${modelIds.length} model(s) available`);
  } catch {
    s.error(`Could not reach ${baseUrl} — enter model ID manually`);
  }

  const options = [
    ...modelIds.map(id => ({ value: id, label: id })),
    { value: "__manual__", label: "Enter model ID manually…" }
  ];

  const choice = await select({ message: "Select model", options });
  if (isCancel(choice)) { cancel(); return null; }

  if (choice === "__manual__") {
    const manual = await text({
      message: "Model ID",
      placeholder: "mistralai/ministral-3-3b",
      validate: v => { if (!v?.trim()) return "Model ID cannot be empty"; }
    });
    if (isCancel(manual)) { cancel(); return null; }
    return (manual as string).trim();
  }

  return choice as string;
}

// ── Inspect run ───────────────────────────────────────────────────────────────

async function interactiveInspect(runsDir: string): Promise<void> {
  const s = spinner();
  s.start("Loading runs…");
  const runs = await RunStorage.list(runsDir);
  s.stop("");

  if (runs.length === 0) {
    log.warn(`No runs found in "${runsDir}". Run a benchmark first.`);
    return;
  }

  const runChoice = await select({
    message: "Select run",
    options: runs.slice(0, 15).map(r => {
      const passed = r.candidates.filter(c => c.status === "passed").length;
      return {
        value: r.id,
        label: r.model,
        hint: `${r.status}  ${passed}/${r.candidates.length}  ${r.startedAt.slice(0, 10)}`
      };
    })
  });
  if (isCancel(runChoice)) { cancel(); return; }

  const storage = await RunStorage.open(runsDir, runChoice as string);
  const manifest = storage.getManifest();

  const viewChoice = await select({
    message: "View",
    options: [
      { value: "report", label: "Full report" },
      { value: "task",   label: "Inspect a specific task" },
    ]
  });
  if (isCancel(viewChoice)) { cancel(); return; }

  if (viewChoice === "report") {
    log.message("\n" + renderReport(manifest));
    return;
  }

  // Task detail
  const candidateOptions = manifest.candidates.map(c => ({
    value: `${c.taskId}:${c.attempt}`,
    label: `${(c.taskId + (manifest.samples > 1 ? ` #${c.attempt}` : "")).padEnd(36)} ${c.status.padEnd(14)} ${c.passed ?? 0}/${c.total ?? 0}`
  }));

  const candidateChoice = await select({
    message: "Select task",
    options: candidateOptions
  });
  if (isCancel(candidateChoice)) { cancel(); return; }

  const [taskId, attemptStr] = (candidateChoice as string).split(":");
  const attempt = String(Number(attemptStr)).padStart(2, "0");
  const prefix = `candidates/${taskId}/${attempt}`;

  for (const filename of ["prompt.txt", "solution.js", "evaluation.json", "error.json"]) {
    try {
      const content = await storage.readText(`${prefix}/${filename}`);
      log.message(`\n─── ${filename} ───\n${content}`);
    } catch { /* file absent — normal for some artifacts */ }
  }
}

// ── Tasks list ────────────────────────────────────────────────────────────────

function showTasks(): void {
  const byCategory = new Map<string, Array<typeof coreTasks[0]>>();
  for (const t of coreTasks) {
    const group = byCategory.get(t.category) ?? [];
    group.push(t);
    byCategory.set(t.category, group);
  }
  for (const [category, ts] of byCategory) {
    log.info(`\n[${category}]`);
    for (const t of ts) log.step(`${t.id.padEnd(32)} ${t.title}`);
  }
}

// ── Models list ───────────────────────────────────────────────────────────────

async function showModels(
  baseUrl: string,
  apiKey: string | undefined,
  timeoutMs: number
): Promise<void> {
  const s = spinner();
  s.start(`Fetching models from ${baseUrl}…`);
  try {
    const client = new OpenAiCompatibleClient(baseUrl, {
      timeoutMs,
      ...(apiKey !== undefined ? { apiKey } : {})
    });
    const models = await client.listModels();
    s.stop(`${models.length} model(s)`);
    for (const m of models) log.step(m.id);
  } catch (err) {
    s.error("Failed to connect");
    log.error(err instanceof Error ? err.message : String(err));
  }
}

// ── Hardware selection ────────────────────────────────────────────────────────

async function pickHardware(
  config: Awaited<ReturnType<typeof loadConfig>>
): Promise<string | null> {
  const currentHardware = config.hardware ?? config.defaults?.hardware;
  const savedList = config.savedHardware ?? (currentHardware ? [currentHardware] : []);

  if (savedList.length === 0) {
    const entered = await text({
      message: "Specify hardware profile (for fair latency & tok/s tracking)",
      placeholder: "e.g. AMD Ryzen 7 250 | 32 GB 5600 | 780m Radeon",
      validate: (v) => {
        if (!v?.trim()) return "Hardware description cannot be empty";
      }
    });
    if (isCancel(entered)) { cancel(); return null; }
    const hwStr = (entered as string).trim();
    await saveHardware(hwStr);
    return hwStr;
  }

  const options = [
    ...savedList.map((hw) => ({
      value: hw,
      label: hw,
      ...(hw === currentHardware ? { hint: "current default" } : {})
    })),
    { value: "__new__", label: "Enter new hardware configuration…" }
  ];

  const choice = await select({
    message: "Select hardware profile (for fair tok/s comparison)",
    options
  });
  if (isCancel(choice)) { cancel(); return null; }

  if (choice === "__new__") {
    const entered = await text({
      message: "New hardware profile description",
      placeholder: "e.g. Apple M3 Max | 64GB Unified | 40-core GPU",
      validate: (v) => {
        if (!v?.trim()) return "Hardware description cannot be empty";
      }
    });
    if (isCancel(entered)) { cancel(); return null; }
    const hwStr = (entered as string).trim();
    await saveHardware(hwStr);
    return hwStr;
  }

  // Update default hardware in config
  await saveHardware(choice as string);
  return choice as string;
}

// ── Leaderboard display ───────────────────────────────────────────────────────

async function showLeaderboard(runsDir: string): Promise<void> {
  const s = spinner();
  s.start("Generating benchmark leaderboard…");
  try {
    const md = await syncLeaderboard(runsDir);
    s.stop("Leaderboard synced to runs/LEADERBOARD.md");
    log.message(`\n${md}`);
  } catch (err) {
    s.error("Failed to generate leaderboard");
    log.error(err instanceof Error ? err.message : String(err));
  }
}

// ── Multi-model comparison ───────────────────────────────────────────────────

async function interactiveCompare(
  baseUrl: string,
  apiKey: string | undefined,
  timeoutMs: number,
  runsDir: string,
  config: Awaited<ReturnType<typeof loadConfig>>
): Promise<void> {
  const models = await pickMultipleModels(baseUrl, apiKey, timeoutMs);
  if (!models || models.length === 0) return;

  const scopeChoice = await select({
    message: "Which tasks?",
    options: [
      { value: "all",  label: `All tasks (${coreTasks.length})` },
      { value: "pick", label: "Choose specific tasks…" },
    ]
  });
  if (isCancel(scopeChoice)) { cancel(); return; }

  let tasks: Task[];
  if (scopeChoice === "pick") {
    const picked = await multiselect({
      message: "Select tasks  (space = toggle, a = all, enter = confirm)",
      options: coreTasks.map((t) => ({
        value: t.id,
        label: `[${t.category.padEnd(12)}] ${t.title}`,
        hint: t.id
      })),
      initialValues: coreTasks.map((t) => t.id),
      required: true
    });
    if (isCancel(picked)) { cancel(); return; }
    tasks = (picked as string[])
      .map((id) => coreTasks.find((t) => t.id === id))
      .filter((t): t is Task => t !== undefined);
  } else {
    tasks = [...coreTasks];
  }

  const samplesStr = await text({
    message: "Samples per task",
    defaultValue: "1",
    placeholder: "1",
    validate: (v) => {
      const n = Number(v || "1");
      if (!Number.isInteger(n) || n < 1) return "Must be a positive integer";
    }
  });
  if (isCancel(samplesStr)) { cancel(); return; }
  const samples = Number(samplesStr || "1");

  const tempStr = await text({
    message: "Temperature",
    defaultValue: String(config.defaults?.temperature ?? 0.2),
    placeholder: "0.2",
    validate: (v) => {
      const n = Number(v || "0.2");
      if (!Number.isFinite(n) || n < 0) return "Must be a non-negative number";
    }
  });
  if (isCancel(tempStr)) { cancel(); return; }
  const temperature = Number(tempStr || "0.2");

  const maxTokensStr = await text({
    message: "Max tokens",
    defaultValue: String(config.defaults?.maxTokens ?? 2048),
    placeholder: "2048",
    validate: (v) => {
      const n = Number(v || "2048");
      if (!Number.isInteger(n) || n < 64) return "Must be an integer ≥ 64";
    }
  });
  if (isCancel(maxTokensStr)) { cancel(); return; }
  const maxTokens = Number(maxTokensStr || "2048");

  const hardware = await pickHardware(config);
  if (hardware == null) return;

  const go = await confirm({
    message: `Run comparison matrix on ${models.length} models × ${tasks.length} tasks on [${hardware}]?`
  });
  if (isCancel(go) || !go) { cancel(); return; }

  const s = spinner();
  const controller = new AbortController();
  process.once("SIGINT", () => {
    log.warn("\nInterrupt received — saving partial runs…");
    controller.abort();
  });

  const storages = await runCompare({
    client: new OpenAiCompatibleClient(baseUrl, {
      timeoutMs,
      ...(apiKey !== undefined ? { apiKey } : {})
    }),
    models,
    tasks,
    samples,
    temperature,
    maxTokens,
    baseUrl,
    hardware,
    runsDir,
    signal: controller.signal,
    onModelStart: (model, idx, total) => {
      s.start(`[Model ${idx}/${total}] Starting ${model}…`);
    },
    onProgress: (model, candidate, modelIdx, totalModels) => {
      const parts: string[] = [];
      if (candidate.total !== undefined) parts.push(`${candidate.passed ?? 0}/${candidate.total}`);
      if (candidate.generationMs !== undefined) parts.push(`${candidate.generationMs}ms`);
      if (candidate.tokensPerSec !== undefined) parts.push(`${candidate.tokensPerSec} tok/s`);
      const label = `[${modelIdx}/${totalModels} ${model}] ${candidate.taskId}`;
      const line = `${label.padEnd(48)} ${parts.join("  ")}`;
      if (candidate.status === "passed") s.stop(`✓ ${line}`);
      else s.error(`✗ ${line}`);
    }
  });

  const manifests = storages.map((st) => st.getManifest());
  const report = renderComparisonReport(manifests, tasks);

  log.success(`Comparison matrix completed for ${manifests.length} model(s)!`);
  log.message("\n" + report);
}

async function pickMultipleModels(
  baseUrl: string,
  apiKey: string | undefined,
  timeoutMs: number
): Promise<string[] | null> {
  const s = spinner();
  s.start(`Fetching available models from ${baseUrl}…`);

  let modelIds: string[] = [];
  try {
    const client = new OpenAiCompatibleClient(baseUrl, {
      timeoutMs: Math.min(timeoutMs, 5_000),
      ...(apiKey !== undefined ? { apiKey } : {})
    });
    const list = await client.listModels();
    modelIds = list.map((m) => m.id);
    s.stop(`Found ${modelIds.length} model(s)`);
  } catch {
    s.error("Could not fetch models automatically");
  }

  if (modelIds.length > 1) {
    const picked = await multiselect({
      message: "Select models to compare (space = toggle, a = all, enter = confirm)",
      options: [
        ...modelIds.map((id) => ({ value: id, label: id })),
        { value: "__manual__", label: "[+] Add another model by name…" }
      ],
      required: true
    });
    if (isCancel(picked)) { cancel(); return null; }

    const selected = (picked as string[]).filter((id) => id !== "__manual__");
    if ((picked as string[]).includes("__manual__")) {
      const extra = await text({
        message: "Additional model ID(s), comma-separated",
        placeholder: "e.g. qwen2.5-coder-7b, llama-3.2-3b",
        validate: (v) => {
          if (!v?.trim() && selected.length === 0) return "Provide at least one model";
        }
      });
      if (isCancel(extra)) { cancel(); return null; }
      if (extra && extra.trim()) {
        const extraList = extra.split(",").map((p) => p.trim()).filter(Boolean);
        selected.push(...extraList);
      }
    }
    return Array.from(new Set(selected));
  }

  const entered = await text({
    message: "Enter model IDs to compare (comma-separated)",
    placeholder: "e.g. mistralai/ministral-3-3b, qwen2.5-coder-7b",
    defaultValue: modelIds[0] ?? "",
    validate: (v) => {
      const parts = (v || "").split(",").map((p) => p.trim()).filter(Boolean);
      if (parts.length === 0) return "Please provide at least one model ID";
    }
  });
  if (isCancel(entered)) { cancel(); return null; }
  return (entered as string).split(",").map((p) => p.trim()).filter(Boolean);
}
