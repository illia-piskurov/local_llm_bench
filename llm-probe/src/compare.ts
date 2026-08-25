import { writeFile } from "node:fs/promises";
import { join, resolve } from "node:path";
import { extractEntry, syncLeaderboard } from "./leaderboard.js";
import { renderHtmlComparisonReport } from "./html-report.js";
import type { ModelClient } from "./model-client.js";
import { runBenchmark } from "./runner.js";
import type { RunStorage } from "./storage.js";
import { coreTasks, getTask } from "./tasks.js";
import type { CandidateRecord, RunManifest, Task } from "./types.js";

export interface CompareOptions {
  readonly client: ModelClient;
  readonly models: ReadonlyArray<string>;
  readonly tasks: ReadonlyArray<Task>;
  readonly samples: number;
  readonly temperature: number;
  readonly maxTokens: number;
  readonly baseUrl: string;
  readonly hardware: string;
  readonly runsDir: string;
  readonly signal?: AbortSignal;
  readonly onModelStart?: (model: string, index: number, total: number) => void;
  readonly onProgress?: (model: string, candidate: CandidateRecord, modelIndex: number, totalModels: number) => void;
}

export async function runCompare(options: CompareOptions): Promise<ReadonlyArray<RunStorage>> {
  const storages: RunStorage[] = [];
  const { models, tasks, samples, temperature, maxTokens, baseUrl, hardware, runsDir, signal, onModelStart, onProgress } = options;

  for (let i = 0; i < models.length; i++) {
    if (signal?.aborted) break;

    const model = models[i]!;
    onModelStart?.(model, i + 1, models.length);

    try {
      const storage = await runBenchmark({
        client: options.client,
        model,
        tasks,
        samples,
        temperature,
        maxTokens,
        baseUrl,
        hardware,
        runsDir,
        ...(signal !== undefined ? { signal } : {}),
        onProgress: (candidate) => onProgress?.(model, candidate, i + 1, models.length)
      });
      storages.push(storage);
    } catch (err) {
      // Continue to next model if one model fails completely
      if (signal?.aborted) break;
    }
  }

  // Generate unified comparison report file
  const manifests = storages.map((s) => s.getManifest());
  const reportMarkdown = renderComparisonReport(manifests, tasks);
  const reportHtml = renderHtmlComparisonReport(manifests, tasks);

  try {
    const timestamp = new Date().toISOString().replace(/[:.]/g, "-").slice(0, 19);
    const compareMdPath = join(resolve(runsDir), `compare_${timestamp}.md`);
    const compareHtmlPath = join(resolve(runsDir), `compare_${timestamp}.html`);
    await writeFile(compareMdPath, reportMarkdown, "utf8");
    await writeFile(compareHtmlPath, reportHtml, "utf8");
    await syncLeaderboard(runsDir);
  } catch {
    // Non-critical if file writing fails
  }

  return storages;
}

export function renderComparisonReport(
  manifests: ReadonlyArray<RunManifest>,
  taskList: ReadonlyArray<Task> = coreTasks
): string {
  const entries = manifests
    .map(extractEntry)
    .filter((e): e is NonNullable<typeof e> => e !== undefined);

  if (entries.length === 0) {
    return "# Model Comparison Report\n\nNo valid run results to compare.\n";
  }

  const lines: string[] = [];

  lines.push(
    "# 🔬 Model Benchmark Comparison Matrix",
    "",
    `> Compared **${entries.length} models** across **${taskList.length} tasks** | Hardware: \`${entries[0]?.hardware || "Mixed"}\``,
    "",
    "---",
    "",
    "## 📊 Summary Table",
    "",
    "| Model | Accuracy (pass@1) | Speed (tok/s) | Mean Latency | Total Tokens | Tokens / Task | Q/S Score |",
    "|---|:---:|:---:|:---:|:---:|:---:|:---:|"
  );

  // Sort entries by Q/S score descending
  const sortedEntries = [...entries].sort((a, b) => b.qualitySpeedScore - a.qualitySpeedScore);
  for (const e of sortedEntries) {
    lines.push(
      `| \`${e.model}\` | **${e.tasksPassed}/${e.totalTasks}** (${e.accuracyPct}%) | **${e.meanTps}** tok/s | ${e.meanLatencyMs} ms | ${e.totalTokens} | ${e.tokensPerTask} | **${e.qualitySpeedScore}** |`
    );
  }
  lines.push("");

  // ── Task-by-Task Matrix ───────────────────────────────────────────────────
  lines.push(
    "## 🧩 Task-by-Task Matrix",
    "",
    "| Task | Category | " + sortedEntries.map((e) => `\`${e.model}\``).join(" | ") + " |",
    "|---|---| " + sortedEntries.map(() => ":---:").join(" | ") + " |"
  );

  for (const task of taskList) {
    const rowCols: string[] = [`**${task.id}**`, `_${task.category}_`];
    for (const entry of sortedEntries) {
      const manifest = manifests.find((m) => m.id === entry.runId);
      const candidates = manifest?.candidates.filter((c) => c.taskId === task.id) ?? [];
      const hasPassed = candidates.some((c) => c.status === "passed");
      const lastCand = candidates[candidates.length - 1];

      if (hasPassed) {
        const speed = lastCand?.tokensPerSec ? ` (${lastCand.tokensPerSec} t/s)` : "";
        rowCols.push(`✅ PASS${speed}`);
      } else if (lastCand?.status === "provider_error") {
        rowCols.push(`⚠️ ERR`);
      } else if (lastCand?.status === "compile_error") {
        rowCols.push(`❌ SYNTAX`);
      } else if (lastCand?.status === "extract_error") {
        rowCols.push(`❌ EXTRACT`);
      } else if (lastCand?.status === "timeout") {
        rowCols.push(`⏳ TIMEOUT`);
      } else if (lastCand) {
        rowCols.push(`❌ FAIL (${lastCand.passed ?? 0}/${lastCand.total ?? 0})`);
      } else {
        rowCols.push(`-`);
      }
    }
    lines.push(`| ${rowCols.join(" | ")} |`);
  }
  lines.push("");

  return lines.join("\n");
}
