import { getTask } from "./tasks.js";
import type { CandidateRecord, RunManifest, TaskCategory } from "./types.js";

export function renderReport(manifest: RunManifest): string {
  const { candidates, samples, taskIds } = manifest;
  const lines: string[] = [];

  // ── Header ──────────────────────────────────────────────────────────────
  lines.push(
    "# llm-probe benchmark report",
    "",
    `| | |`,
    `|---|---|`,
    `| **Run** | \`${manifest.id}\` |`,
    `| **Status** | ${manifest.status} |`,
    `| **Model** | \`${manifest.model}\` |`,
    ...(manifest.hardware ? [`| **Hardware** | ${manifest.hardware} |`] : []),
    `| **Started** | ${manifest.startedAt} |`,
    ...(manifest.completedAt ? [`| **Completed** | ${manifest.completedAt} |`] : []),
    `| **Samples (k)** | ${samples} |`,
    `| **Tasks** | ${taskIds.length} |`,
    ""
  );

  // ── success@1, success@repair, and success@k ─────────────────────────────
  const taskResults = computeTaskResults(candidates, taskIds, samples);
  const successAt1 = taskResults.filter((t) => t.passedAt1).length;
  const successWithRepair = taskResults.filter((t) => t.passedWithRepair).length;
  const successAtK = taskResults.filter((t) => t.passedAtK).length;
  const totalTasks = taskIds.length;
  const initialFailedCount = totalTasks - successAt1;
  const repairedCount = successWithRepair - successAt1;

  lines.push(
    "## Accuracy",
    "",
    `| Metric | Value |`,
    `|---|---|`,
    `| **success@1 (0-shot)** | ${successAt1}/${totalTasks} (${pct(successAt1, totalTasks)}) |`,
    ...(manifest.repairs && manifest.repairs > 0
      ? [
          `| **success@repair (≤${manifest.repairs} repairs)** | ${successWithRepair}/${totalTasks} (${pct(successWithRepair, totalTasks)}) |`,
          `| **Repair Recovery Rate** | ${repairedCount}/${initialFailedCount} (${pct(repairedCount, initialFailedCount)}) |`
        ]
      : []),
    ...(samples > 1 ? [`| **success@${samples}** | ${successAtK}/${totalTasks} (${pct(successAtK, totalTasks)}) |`] : []),
    ""
  );

  // ── Category breakdown ───────────────────────────────────────────────────
  const categoriesMap = new Map<string, TaskResult[]>();
  for (const tr of taskResults) {
    const cat = getTask(tr.taskId)?.category ?? "other";
    const group = categoriesMap.get(cat) ?? [];
    group.push(tr);
    categoriesMap.set(cat, group);
  }

  if (categoriesMap.size > 1) {
    lines.push(
      "## Accuracy by category",
      "",
      `| Category | ${samples > 1 ? "pass@1 | pass@k" : "Pass rate"} | Tasks |`,
      `|---|${samples > 1 ? "---|---" : "---"}|---|`
    );
    for (const [cat, items] of categoriesMap) {
      const p1 = items.filter((t) => t.passedAt1).length;
      const pk = items.filter((t) => t.passedAtK).length;
      const count = items.length;
      if (samples > 1) {
        lines.push(`| **${cat}** | ${p1}/${count} (${pct(p1, count)}) | ${pk}/${count} (${pct(pk, count)}) | ${count} |`);
      } else {
        lines.push(`| **${cat}** | ${p1}/${count} (${pct(p1, count)}) | ${count} |`);
      }
    }
    lines.push("");
  }

  // ── Latency & token speed ─────────────────────────────────────────────────
  const genTimes = candidates.map((c) => c.generationMs).filter((v): v is number => v !== undefined);
  const tpsList = candidates.map((c) => c.tokensPerSec).filter((v): v is number => v !== undefined);
  const tokensList = candidates.map((c) => c.completionTokens).filter((v): v is number => v !== undefined);
  if (genTimes.length > 0) {
    const mean = Math.round(genTimes.reduce((a, b) => a + b, 0) / genTimes.length);
    const sorted = [...genTimes].sort((a, b) => a - b);
    const median = sorted[Math.floor(sorted.length / 2)]!;
    const meanTps = tpsList.length > 0 ? Math.round(tpsList.reduce((a, b) => a + b, 0) / tpsList.length) : undefined;
    const totalTokens = tokensList.length > 0 ? tokensList.reduce((a, b) => a + b, 0) : undefined;
    const accuracyPct = totalTasks > 0 ? (successAt1 / totalTasks) * 100 : 0;
    const qsScore = meanTps !== undefined && accuracyPct > 0
      ? Math.round(accuracyPct * Math.pow(meanTps / 20, 0.6) * 10) / 10
      : 0;

    lines.push(
      "## Latency & throughput",
      "",
      `| | |`,
      `|---|---|`,
      `| Mean generation | ${mean} ms |`,
      `| Median generation | ${median} ms |`,
      `| Min / Max | ${sorted[0]} ms / ${sorted[sorted.length - 1]} ms |`,
      ...(meanTps !== undefined ? [`| Mean tok/s | **${meanTps}** tok/s |`] : []),
      ...(totalTokens !== undefined ? [`| Total completion tokens | ${totalTokens} (${Math.round(totalTokens / totalTasks)} tok/task) |`] : []),
      ...(meanTps !== undefined ? [`| **Quality/Speed Score** | **${qsScore}** |`] : []),
      ""
    );
  }

  // ── Failure breakdown ────────────────────────────────────────────────────
  const failureCounts: Record<string, number> = {};
  let finishLengthCount = 0;
  for (const c of candidates) {
    if (c.status !== "passed") {
      failureCounts[c.status] = (failureCounts[c.status] ?? 0) + 1;
    }
    if (c.finishReason === "length") finishLengthCount++;
  }
  const failureEntries = Object.entries(failureCounts).sort((a, b) => b[1] - a[1]);
  if (failureEntries.length > 0) {
    lines.push(
      "## Failure breakdown",
      "",
      `| Failure type | Count |`,
      `|---|---|`,
      ...failureEntries.map(([type, count]) => `| ${type} | ${count} |`),
      ...(finishLengthCount > 0 ? [`| finish_reason=length | ${finishLengthCount} |`] : []),
      ""
    );
  }

  // ── Per-task table ───────────────────────────────────────────────────────
  lines.push(
    "## Results by task",
    "",
    `| Task | ${samples > 1 ? "pass@1 | pass@k" : "Status"} | Tests | Gen ms | tok/s | Finish |`,
    `|---|${samples > 1 ? "---|---" : "---"}|---|---|---|---|`
  );
  for (const tr of taskResults) {
    const first = tr.firstCandidate;
    const genMs = first?.generationMs !== undefined ? `${first.generationMs}` : "—";
    const tps = first?.tokensPerSec !== undefined ? `${first.tokensPerSec}` : "—";
    const finish = first?.finishReason ?? "—";
    const tests = first ? `${first.passed ?? 0}/${first.total ?? 0}` : "—";
    if (samples > 1) {
      lines.push(`| ${tr.taskId} | ${tr.passedAt1 ? "✓" : "✗"} | ${tr.passedAtK ? "✓" : "✗"} | ${tests} | ${genMs} | ${tps} | ${finish} |`);
    } else {
      const status = first?.status ?? "—";
      lines.push(`| ${tr.taskId} | ${status} | ${tests} | ${genMs} | ${tps} | ${finish} |`);
    }
  }
  lines.push("");

  // ── Failures detail ──────────────────────────────────────────────────────
  const failed = taskResults.filter((t) => !t.passedAtK);
  if (failed.length > 0) {
    lines.push("## Failure details", "");
    for (const t of failed) {
      const worst = t.candidates.find((c) => c.status !== "passed") ?? t.candidates[0];
      if (worst) {
        lines.push(`- \`${t.taskId}\`: ${worst.status}${
          worst.error ? ` — ${worst.error.slice(0, 120)}` : ""
        }`);
      }
    }
    lines.push("");
  }

  return lines.join("\n");
}

interface TaskResult {
  taskId: string;
  candidates: ReadonlyArray<CandidateRecord>;
  firstCandidate: CandidateRecord | undefined;
  passedAt1: boolean;
  passedWithRepair: boolean;
  passedAtK: boolean;
  repairsUsed: number;
}

function computeTaskResults(
  candidates: ReadonlyArray<CandidateRecord>,
  taskIds: ReadonlyArray<string>,
  _samples: number
): TaskResult[] {
  return taskIds.map((taskId) => {
    const taskCandidates = candidates.filter((c) => c.taskId === taskId);
    const zeroShotCandidates = taskCandidates.filter((c) => (c.repairAttempt ?? 0) === 0);
    const firstCandidate = zeroShotCandidates[0] ?? taskCandidates[0];
    const passedAt1 = firstCandidate?.status === "passed";
    const passedWithRepair = taskCandidates.some((c) => c.status === "passed");
    const passedAtK = taskCandidates.some((c) => c.status === "passed");
    const repairsUsed = taskCandidates.filter((c) => (c.repairAttempt ?? 0) > 0).length;
    return { taskId, candidates: taskCandidates, firstCandidate, passedAt1, passedWithRepair, passedAtK, repairsUsed };
  });
}

function pct(num: number, den: number): string {
  if (den === 0) return "0%";
  return `${Math.round((num / den) * 100)}%`;
}
