import { writeFile } from "node:fs/promises";
import { join, resolve } from "node:path";
import { RunStorage } from "./storage.js";
import type { RunManifest } from "./types.js";

export interface LeaderboardEntry {
  readonly runId: string;
  readonly model: string;
  readonly hardware: string;
  readonly startedAt: string;
  readonly status: "completed" | "partial" | "running";
  readonly tasksPassed: number;
  readonly totalTasks: number;
  readonly accuracyPct: number; // 0..100
  readonly meanTps: number;
  readonly meanLatencyMs: number;
  readonly medianLatencyMs: number;
  readonly totalTokens: number;
  readonly tokensPerTask: number;
  readonly qualitySpeedScore: number; // Combined balance score
}

/**
 * Calculates a unified Quality-to-Speed score:
 * Base accuracy (0-100) weighted by throughput relative to baseline (20 tok/s).
 * Higher accuracy and higher tok/s both increase the score.
 */
export function calculateQualitySpeedScore(accuracyPct: number, tokPerSec: number): number {
  if (accuracyPct <= 0 || tokPerSec <= 0) return 0;
  // Multiplier: normalized speed factor with soft saturation
  const speedFactor = Math.pow(tokPerSec / 20, 0.6);
  return Math.round(accuracyPct * speedFactor * 10) / 10;
}

export function extractEntry(manifest: RunManifest): LeaderboardEntry | undefined {
  const { candidates, taskIds } = manifest;
  if (!taskIds || taskIds.length === 0 || candidates.length === 0) return undefined;

  const totalTasks = taskIds.length;
  const passedTasks = taskIds.filter((id) =>
    candidates.some((c) => c.taskId === id && c.status === "passed")
  ).length;

  const accuracyPct = Math.round((passedTasks / totalTasks) * 1000) / 10;

  const genTimes = candidates
    .map((c) => c.generationMs)
    .filter((v): v is number => v !== undefined);
  const tpsList = candidates
    .map((c) => c.tokensPerSec)
    .filter((v): v is number => v !== undefined);
  const tokenList = candidates
    .map((c) => c.completionTokens)
    .filter((v): v is number => v !== undefined);

  const meanLatencyMs = genTimes.length > 0
    ? Math.round(genTimes.reduce((a, b) => a + b, 0) / genTimes.length)
    : 0;

  const sortedLatencies = [...genTimes].sort((a, b) => a - b);
  const medianLatencyMs = sortedLatencies.length > 0
    ? sortedLatencies[Math.floor(sortedLatencies.length / 2)]!
    : 0;

  const meanTps = tpsList.length > 0
    ? Math.round((tpsList.reduce((a, b) => a + b, 0) / tpsList.length) * 10) / 10
    : 0;

  const totalTokens = tokenList.length > 0
    ? tokenList.reduce((a, b) => a + b, 0)
    : 0;

  const tokensPerTask = totalTasks > 0
    ? Math.round(totalTokens / totalTasks)
    : 0;

  const qualitySpeedScore = calculateQualitySpeedScore(accuracyPct, meanTps);

  return {
    runId: manifest.id,
    model: manifest.model,
    hardware: manifest.hardware || "Unspecified Hardware",
    startedAt: manifest.startedAt.slice(0, 10),
    status: manifest.status,
    tasksPassed: passedTasks,
    totalTasks,
    accuracyPct,
    meanTps,
    meanLatencyMs,
    medianLatencyMs,
    totalTokens,
    tokensPerTask,
    qualitySpeedScore
  };
}

/**
 * Generate comprehensive Leaderboard Markdown with 4 distinct rankings.
 */
export function generateLeaderboard(manifests: ReadonlyArray<RunManifest>): string {
  const allEntries = manifests
    .map(extractEntry)
    .filter((e): e is LeaderboardEntry => e !== undefined && e.tasksPassed >= 0);

  if (allEntries.length === 0) {
    return "# llm-probe Leaderboard\n\nNo completed benchmark runs found yet.\n";
  }

  // Deduplicate: keep best run per [Model + Hardware] combination
  const deduplicatedMap = new Map<string, LeaderboardEntry>();
  for (const entry of allEntries) {
    const key = `${entry.model}@@@${entry.hardware}`;
    const existing = deduplicatedMap.get(key);
    if (!existing || entry.qualitySpeedScore > existing.qualitySpeedScore) {
      deduplicatedMap.set(key, entry);
    }
  }
  const entries = Array.from(deduplicatedMap.values());

  const lines: string[] = [];

  lines.push(
    "# 🏆 llm-probe Benchmark Leaderboard",
    "",
    `> Updated: ${new Date().toISOString().slice(0, 19).replace("T", " ")} UTC | Total models/configurations benchmarked: **${entries.length}**`,
    "",
    "---",
    "",
    "## 📊 Master Table (All Metrics)",
    "",
    "| # | Model | Hardware | Accuracy | Speed | Mean Latency | Total Tokens | Q/S Score |",
    "|---|---|---|---|---|---|---|---|"
  );

  // Default sort by Quality/Speed Score
  const masterSorted = [...entries].sort((a, b) => b.qualitySpeedScore - a.qualitySpeedScore);
  masterSorted.forEach((e, idx) => {
    lines.push(
      `| **${idx + 1}** | \`${e.model}\` | ${e.hardware} | **${e.tasksPassed}/${e.totalTasks}** (${e.accuracyPct}%) | **${e.meanTps}** tok/s | ${e.meanLatencyMs} ms | ${e.totalTokens} | **${e.qualitySpeedScore}** |`
    );
  });
  lines.push("");

  // ── 1. Quality Ranking ─────────────────────────────────────────────────────
  lines.push(
    "## 🎯 1. Quality Ranking (Accuracy / Pass Rate)",
    "> Ranked strictly by success rate across benchmark tasks (higher is better).",
    "",
    "| Rank | Model | Hardware | Pass Rate | Tasks Passed | Q/S Score |",
    "|---|---|---|---|---|---|"
  );
  const byQuality = [...entries].sort((a, b) => b.accuracyPct - a.accuracyPct || b.qualitySpeedScore - a.qualitySpeedScore);
  byQuality.forEach((e, idx) => {
    const medal = idx === 0 ? "🥇 " : idx === 1 ? "🥈 " : idx === 2 ? "🥉 " : "";
    lines.push(
      `| ${medal}${idx + 1} | \`${e.model}\` | ${e.hardware} | **${e.accuracyPct}%** | ${e.tasksPassed}/${e.totalTasks} | ${e.qualitySpeedScore} |`
    );
  });
  lines.push("");

  // ── 2. Speed Ranking ───────────────────────────────────────────────────────
  lines.push(
    "## ⚡ 2. Speed Ranking (Generation Throughput)",
    "> Ranked strictly by generation throughput in tokens per second (higher is faster).",
    "",
    "| Rank | Model | Hardware | Throughput | Median Latency | Mean Latency |",
    "|---|---|---|---|---|---|"
  );
  const bySpeed = [...entries].sort((a, b) => b.meanTps - a.meanTps || a.medianLatencyMs - b.medianLatencyMs);
  bySpeed.forEach((e, idx) => {
    const medal = idx === 0 ? "🥇 " : idx === 1 ? "🥈 " : idx === 2 ? "🥉 " : "";
    lines.push(
      `| ${medal}${idx + 1} | \`${e.model}\` | ${e.hardware} | **${e.meanTps} tok/s** | ${e.medianLatencyMs} ms | ${e.meanLatencyMs} ms |`
    );
  });
  lines.push("");

  // ── 3. Token Efficiency Ranking ───────────────────────────────────────────
  lines.push(
    "## 💡 3. Token Efficiency Ranking (Conciseness)",
    "> Ranked by fewest tokens spent per task (more concise & focused solutions).",
    "",
    "| Rank | Model | Hardware | Tokens / Task | Total Tokens | Accuracy |",
    "|---|---|---|---|---|---|"
  );
  const byTokens = [...entries].sort((a, b) => a.tokensPerTask - b.tokensPerTask || b.accuracyPct - a.accuracyPct);
  byTokens.forEach((e, idx) => {
    const medal = idx === 0 ? "🥇 " : idx === 1 ? "🥈 " : idx === 2 ? "🥉 " : "";
    lines.push(
      `| ${medal}${idx + 1} | \`${e.model}\` | ${e.hardware} | **${e.tokensPerTask}** tok/task | ${e.totalTokens} | ${e.accuracyPct}% |`
    );
  });
  lines.push("");

  // ── 4. Quality/Speed Balanced Score ────────────────────────────────────────
  lines.push(
    "## ⚖️ 4. Balanced Quality/Speed Index (Q/S Score)",
    "> Composite index: $\\text{Score} = \\text{Accuracy(\\%)} \\times (\\text{tok/s} / 20)^{0.6}$. Rewards high quality with strong speed weighting.",
    "",
    "| Rank | Model | Hardware | Q/S Score | Accuracy | Speed |",
    "|---|---|---|---|---|---|"
  );
  const byScore = [...entries].sort((a, b) => b.qualitySpeedScore - a.qualitySpeedScore);
  byScore.forEach((e, idx) => {
    const medal = idx === 0 ? "🥇 " : idx === 1 ? "🥈 " : idx === 2 ? "🥉 " : "";
    lines.push(
      `| ${medal}${idx + 1} | \`${e.model}\` | ${e.hardware} | **${e.qualitySpeedScore}** | ${e.accuracyPct}% | ${e.meanTps} tok/s |`
    );
  });
  lines.push("");

  return lines.join("\n");
}

/**
 * Scan runs directory, update runs/LEADERBOARD.md file and return the content.
 */
export async function syncLeaderboard(runsDir: string): Promise<string> {
  const manifests = await RunStorage.list(runsDir);
  const markdown = generateLeaderboard(manifests);
  try {
    const filePath = join(resolve(runsDir), "LEADERBOARD.md");
    await writeFile(filePath, markdown, "utf8");
  } catch {
    // Non-critical if filesystem error
  }
  return markdown;
}
