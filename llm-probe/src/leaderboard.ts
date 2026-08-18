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

function escapeHtml(str: string | null | undefined): string {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

/**
 * Generate a self-contained HTML leaderboard page.
 */
export function generateLeaderboardHtml(manifests: ReadonlyArray<RunManifest>): string {
  const allEntries = manifests
    .map(extractEntry)
    .filter((e): e is LeaderboardEntry => e !== undefined && e.tasksPassed >= 0);

  const deduplicatedMap = new Map<string, LeaderboardEntry>();
  for (const entry of allEntries) {
    const key = `${entry.model}@@@${entry.hardware}`;
    const existing = deduplicatedMap.get(key);
    if (!existing || entry.qualitySpeedScore > existing.qualitySpeedScore) {
      deduplicatedMap.set(key, entry);
    }
  }
  const entries = Array.from(deduplicatedMap.values());
  const masterSorted = [...entries].sort((a, b) => b.qualitySpeedScore - a.qualitySpeedScore);
  const byQuality  = [...entries].sort((a, b) => b.accuracyPct - a.accuracyPct || b.qualitySpeedScore - a.qualitySpeedScore);
  const bySpeed    = [...entries].sort((a, b) => b.meanTps - a.meanTps || a.medianLatencyMs - b.medianLatencyMs);
  const byTokens   = [...entries].sort((a, b) => a.tokensPerTask - b.tokensPerTask || b.accuracyPct - a.accuracyPct);

  const updatedAt = new Date().toISOString().slice(0, 19).replace("T", " ") + " UTC";

  const medal = (i: number) => i === 0 ? "🥇" : i === 1 ? "🥈" : i === 2 ? "🥉" : `${i + 1}`;

  function masterRow(e: LeaderboardEntry, i: number): string {
    const accColor = e.accuracyPct >= 60 ? "var(--accent-green)" : e.accuracyPct >= 30 ? "var(--accent-amber)" : "var(--accent-red)";
    const bar = `<div class="acc-bar"><div class="acc-fill" style="width:${e.accuracyPct}%;background:${accColor}"></div></div>`;
    return `<tr>
      <td class="rank-cell">${medal(i)}</td>
      <td><code class="model-name">${escapeHtml(e.model)}</code></td>
      <td class="hw-cell">${escapeHtml(e.hardware)}</td>
      <td><span class="acc-wrap"><strong style="color:${accColor}">${e.accuracyPct}%</strong><span class="acc-frac">${e.tasksPassed}/${e.totalTasks}</span>${bar}</span></td>
      <td><strong>${e.meanTps}</strong> <span class="unit">tok/s</span></td>
      <td>${e.meanLatencyMs > 0 ? e.meanLatencyMs.toLocaleString() + " ms" : "—"}</td>
      <td>${e.totalTokens > 0 ? e.totalTokens.toLocaleString() : "—"}</td>
      <td><strong class="qs-score">${e.qualitySpeedScore}</strong></td>
    </tr>`;
  }

  function qualityRow(e: LeaderboardEntry, i: number): string {
    const accColor = e.accuracyPct >= 60 ? "var(--accent-green)" : e.accuracyPct >= 30 ? "var(--accent-amber)" : "var(--accent-red)";
    return `<tr>
      <td class="rank-cell">${medal(i)}</td>
      <td><code class="model-name">${escapeHtml(e.model)}</code></td>
      <td class="hw-cell">${escapeHtml(e.hardware)}</td>
      <td><strong style="color:${accColor}">${e.accuracyPct}%</strong></td>
      <td>${e.tasksPassed}/${e.totalTasks}</td>
      <td><strong class="qs-score">${e.qualitySpeedScore}</strong></td>
    </tr>`;
  }

  function speedRow(e: LeaderboardEntry, i: number): string {
    return `<tr>
      <td class="rank-cell">${medal(i)}</td>
      <td><code class="model-name">${escapeHtml(e.model)}</code></td>
      <td class="hw-cell">${escapeHtml(e.hardware)}</td>
      <td><strong style="color:var(--accent-blue)">${e.meanTps}</strong> <span class="unit">tok/s</span></td>
      <td>${e.medianLatencyMs > 0 ? e.medianLatencyMs.toLocaleString() + " ms" : "—"}</td>
      <td>${e.meanLatencyMs > 0 ? e.meanLatencyMs.toLocaleString() + " ms" : "—"}</td>
    </tr>`;
  }

  function tokenRow(e: LeaderboardEntry, i: number): string {
    return `<tr>
      <td class="rank-cell">${medal(i)}</td>
      <td><code class="model-name">${escapeHtml(e.model)}</code></td>
      <td class="hw-cell">${escapeHtml(e.hardware)}</td>
      <td>${e.tokensPerTask > 0 ? `<strong>${e.tokensPerTask.toLocaleString()}</strong> <span class="unit">tok/task</span>` : "—"}</td>
      <td>${e.totalTokens > 0 ? e.totalTokens.toLocaleString() : "—"}</td>
      <td>${e.accuracyPct}%</td>
    </tr>`;
  }

  const noData = `<p class="empty-msg">No completed benchmark runs found yet.</p>`;

  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>llm-probe Leaderboard</title>
  <style>
    :root {
      --bg-main: #090d16;
      --bg-card: #111827;
      --bg-panel: #0d1322;
      --border: #1f293d;
      --text-main: #f3f4f6;
      --text-muted: #9ca3af;
      --text-dim: #6b7280;
      --accent-blue: #38bdf8;
      --accent-green: #10b981;
      --accent-red: #f43f5e;
      --accent-amber: #f59e0b;
      --radius: 10px;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background: var(--bg-main);
      color: var(--text-main);
      line-height: 1.5;
      padding: 32px 24px;
    }
    .container { max-width: 1400px; margin: 0 auto; }

    /* ── Header ── */
    .page-header {
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 28px 32px;
      margin-bottom: 28px;
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
    }
    .page-header h1 { font-size: 1.9rem; font-weight: 800; display: flex; align-items: center; gap: 12px; }
    .page-header .meta { font-size: 0.85rem; color: var(--text-muted); margin-top: 4px; }
    .updated-badge {
      background: var(--bg-panel);
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 6px 14px;
      font-size: 0.8rem;
      color: var(--text-dim);
      white-space: nowrap;
    }

    /* ── KPI strip ── */
    .kpi-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
      gap: 14px;
      margin-bottom: 28px;
    }
    .kpi-card {
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 18px 20px;
      transition: transform .15s, border-color .15s;
    }
    .kpi-card:hover { transform: translateY(-2px); border-color: #2e3d5a; }
    .kpi-label { font-size: 0.75rem; text-transform: uppercase; letter-spacing: .06em; color: var(--text-muted); margin-bottom: 6px; }
    .kpi-value { font-size: 1.8rem; font-weight: 800; }
    .kpi-sub   { font-size: 0.78rem; color: var(--text-dim); margin-top: 2px; }

    /* ── Section ── */
    .section {
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      margin-bottom: 20px;
      overflow: hidden;
    }
    .section-header {
      padding: 18px 24px;
      border-bottom: 1px solid var(--border);
      display: flex;
      align-items: baseline;
      gap: 10px;
    }
    .section-header h2 { font-size: 1.1rem; font-weight: 700; }
    .section-header .hint { font-size: 0.8rem; color: var(--text-muted); }

    /* ── Table ── */
    .table-wrap { overflow-x: auto; }
    table { width: 100%; border-collapse: collapse; font-size: 0.88rem; }
    thead th {
      padding: 10px 16px;
      text-align: left;
      font-size: 0.75rem;
      text-transform: uppercase;
      letter-spacing: .05em;
      color: var(--text-dim);
      border-bottom: 1px solid var(--border);
      background: var(--bg-panel);
      white-space: nowrap;
    }
    tbody tr { border-bottom: 1px solid var(--border); transition: background .1s; }
    tbody tr:last-child { border-bottom: none; }
    tbody tr:hover { background: rgba(255,255,255,.03); }
    td { padding: 12px 16px; vertical-align: middle; }

    .rank-cell { font-size: 1.1rem; text-align: center; width: 52px; }
    .model-name { font-family: ui-monospace, Consolas, monospace; font-size: 0.85rem; color: var(--accent-blue); background: transparent; }
    .hw-cell { font-size: 0.78rem; color: var(--text-muted); max-width: 240px; }
    .unit { font-size: 0.78rem; color: var(--text-dim); }
    .qs-score { color: var(--accent-amber); font-size: 1rem; }

    .acc-wrap { display: flex; align-items: center; gap: 8px; white-space: nowrap; }
    .acc-frac { font-size: 0.78rem; color: var(--text-dim); }
    .acc-bar { flex: 1; min-width: 60px; max-width: 120px; height: 5px; background: var(--bg-panel); border-radius: 3px; overflow: hidden; }
    .acc-fill { height: 100%; border-radius: 3px; transition: width .3s; }

    .empty-msg { padding: 24px; color: var(--text-muted); font-style: italic; }

    @media (max-width: 768px) {
      body { padding: 16px 12px; }
      .hw-cell { display: none; }
    }
  </style>
</head>
<body>
<div class="container">

  <header class="page-header">
    <div>
      <h1>🏆 llm-probe Leaderboard</h1>
      <div class="meta">${entries.length} model${entries.length !== 1 ? "s" : ""} benchmarked · best run per model shown</div>
    </div>
    <div class="updated-badge">Updated: ${escapeHtml(updatedAt)}</div>
  </header>

  <div class="kpi-grid">
    <div class="kpi-card">
      <div class="kpi-label">Models Ranked</div>
      <div class="kpi-value" style="color:var(--accent-blue)">${entries.length}</div>
      <div class="kpi-sub">unique model × hardware</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Top Accuracy</div>
      <div class="kpi-value" style="color:var(--accent-green)">${masterSorted[0]?.accuracyPct ?? 0}%</div>
      <div class="kpi-sub">${escapeHtml(masterSorted[0]?.model ?? "—")}</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Top Speed</div>
      <div class="kpi-value" style="color:var(--accent-blue)">${bySpeed[0]?.meanTps ?? 0} <span style="font-size:1rem;font-weight:400">t/s</span></div>
      <div class="kpi-sub">${escapeHtml(bySpeed[0]?.model ?? "—")}</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Best Q/S Score</div>
      <div class="kpi-value" style="color:var(--accent-amber)">${masterSorted[0]?.qualitySpeedScore ?? 0}</div>
      <div class="kpi-sub">${escapeHtml(masterSorted[0]?.model ?? "—")}</div>
    </div>
  </div>

  <!-- Master Table -->
  <div class="section">
    <div class="section-header">
      <h2>📊 Master Table</h2>
      <span class="hint">All metrics · sorted by Q/S Score</span>
    </div>
    <div class="table-wrap">
      ${entries.length === 0 ? noData : `<table>
        <thead><tr>
          <th>#</th><th>Model</th><th>Hardware</th><th>Accuracy</th><th>Speed</th><th>Mean Latency</th><th>Total Tokens</th><th>Q/S Score</th>
        </tr></thead>
        <tbody>${masterSorted.map(masterRow).join("")}</tbody>
      </table>`}
    </div>
  </div>

  <!-- Quality Ranking -->
  <div class="section">
    <div class="section-header">
      <h2>🎯 Quality Ranking</h2>
      <span class="hint">Accuracy / Pass Rate · higher is better</span>
    </div>
    <div class="table-wrap">
      ${entries.length === 0 ? noData : `<table>
        <thead><tr>
          <th>Rank</th><th>Model</th><th>Hardware</th><th>Pass Rate</th><th>Tasks Passed</th><th>Q/S Score</th>
        </tr></thead>
        <tbody>${byQuality.map(qualityRow).join("")}</tbody>
      </table>`}
    </div>
  </div>

  <!-- Speed Ranking -->
  <div class="section">
    <div class="section-header">
      <h2>⚡ Speed Ranking</h2>
      <span class="hint">Generation throughput in tokens/sec · higher is faster</span>
    </div>
    <div class="table-wrap">
      ${entries.length === 0 ? noData : `<table>
        <thead><tr>
          <th>Rank</th><th>Model</th><th>Hardware</th><th>Throughput</th><th>Median Latency</th><th>Mean Latency</th>
        </tr></thead>
        <tbody>${bySpeed.map(speedRow).join("")}</tbody>
      </table>`}
    </div>
  </div>

  <!-- Token Efficiency -->
  <div class="section">
    <div class="section-header">
      <h2>💡 Token Efficiency</h2>
      <span class="hint">Fewest tokens per task · more concise solutions rank higher</span>
    </div>
    <div class="table-wrap">
      ${entries.length === 0 ? noData : `<table>
        <thead><tr>
          <th>Rank</th><th>Model</th><th>Hardware</th><th>Tokens / Task</th><th>Total Tokens</th><th>Accuracy</th>
        </tr></thead>
        <tbody>${byTokens.map(tokenRow).join("")}</tbody>
      </table>`}
    </div>
  </div>

</div>
</body>
</html>`;
}

/**
 * Scan runs directory, update runs/LEADERBOARD.md and runs/LEADERBOARD.html,
 * and return the absolute path to the HTML file.
 */
export async function syncLeaderboard(runsDir: string): Promise<{ markdown: string; htmlPath: string }> {
  const manifests = await RunStorage.list(runsDir);
  const markdown = generateLeaderboard(manifests);
  const html = generateLeaderboardHtml(manifests);
  const dir = resolve(runsDir);
  const htmlPath = join(dir, "LEADERBOARD.html");
  try {
    await writeFile(join(dir, "LEADERBOARD.md"), markdown, "utf8");
    await writeFile(htmlPath, html, "utf8");
  } catch {
    // Non-critical if filesystem error
  }
  return { markdown, htmlPath };
}

