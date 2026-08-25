import { getTask } from "./tasks.js";
import type { CandidateRecord, EvaluationResult, EvaluationStatus, RunManifest, Task } from "./types.js";
import { extractEntry } from "./leaderboard.js";

export interface CandidateDetailedData {
  readonly taskId: string;
  readonly attempt: number;
  readonly repairAttempt?: number | undefined;
  readonly repairedFrom?: EvaluationStatus | "provider_error" | "extract_error" | undefined;
  readonly prompt?: string | undefined;
  readonly code?: string | undefined;
  readonly responseRaw?: string | undefined;
  readonly evaluation?: EvaluationResult | undefined;
  readonly error?: { message?: string } | undefined;
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

export function renderHtmlReport(
  manifest: RunManifest,
  candidateDetails: ReadonlyArray<CandidateDetailedData> = []
): string {
  const { candidates, samples, taskIds, model, hardware, startedAt, completedAt, status, id: runId } = manifest;

  const detailsMap = new Map<string, CandidateDetailedData>();
  for (const d of candidateDetails) {
    detailsMap.set(`${d.taskId}#${d.attempt}#${d.repairAttempt ?? 0}`, d);
  }

  // Compute metrics
  const totalTasks = taskIds.length;
  const taskMap = new Map<string, CandidateRecord[]>();
  for (const c of candidates) {
    const list = taskMap.get(c.taskId) ?? [];
    list.push(c);
    taskMap.set(c.taskId, list);
  }

  let passedAt1Count = 0;
  let passedWithRepairCount = 0;
  let passedAtKCount = 0;
  for (const tid of taskIds) {
    const list = taskMap.get(tid) ?? [];
    const zeroShot = list.find((c) => (c.repairAttempt ?? 0) === 0) ?? list[0];
    if (zeroShot?.status === "passed") passedAt1Count++;
    if (list.some((c) => c.status === "passed")) {
      passedWithRepairCount++;
      passedAtKCount++;
    }
  }

  const passAt1Pct = totalTasks > 0 ? Math.round((passedAt1Count / totalTasks) * 100) : 0;
  const passWithRepairPct = totalTasks > 0 ? Math.round((passedWithRepairCount / totalTasks) * 100) : 0;
  const passAtKPct = totalTasks > 0 ? Math.round((passedAtKCount / totalTasks) * 100) : 0;
  const initialFailedCount = totalTasks - passedAt1Count;
  const repairedCount = passedWithRepairCount - passedAt1Count;
  const recoveryRatePct = initialFailedCount > 0 ? Math.round((repairedCount / initialFailedCount) * 100) : 0;

  const genTimes = candidates.map((c) => c.generationMs).filter((v): v is number => v !== undefined);
  const tpsList = candidates.map((c) => c.tokensPerSec).filter((v): v is number => v !== undefined);
  const tokensList = candidates.map((c) => c.completionTokens).filter((v): v is number => v !== undefined);

  const meanGenMs = genTimes.length > 0 ? Math.round(genTimes.reduce((a, b) => a + b, 0) / genTimes.length) : 0;
  const sortedGen = [...genTimes].sort((a, b) => a - b);
  const medianGenMs = sortedGen.length > 0 ? sortedGen[Math.floor(sortedGen.length / 2)]! : 0;
  const meanTps = tpsList.length > 0 ? Math.round(tpsList.reduce((a, b) => a + b, 0) / tpsList.length) : 0;
  const totalTokens = tokensList.reduce((a, b) => a + b, 0);
  const avgTokensPerTask = totalTasks > 0 ? Math.round(totalTokens / totalTasks) : 0;

  const qsScore = meanTps > 0 && passAt1Pct > 0
    ? Math.round(passAt1Pct * Math.pow(meanTps / 20, 0.6) * 10) / 10
    : 0;

  // Category stats
  const categoryStats = new Map<string, { total: number; passed: number }>();
  for (const tid of taskIds) {
    const taskObj = getTask(tid);
    const cat = taskObj?.category ?? "other";
    const cur = categoryStats.get(cat) ?? { total: 0, passed: 0 };
    cur.total++;
    const list = taskMap.get(tid) ?? [];
    if (list[0]?.status === "passed") cur.passed++;
    categoryStats.set(cat, cur);
  }

  // Generate task card data
  const taskCardsHtml = taskIds.map((taskId) => {
    const taskObj = getTask(taskId);
    const taskCandidates = taskMap.get(taskId) ?? [];
    const firstCand = taskCandidates[0];
    const candStatus = firstCand?.status ?? "not_run";
    const isPassed = candStatus === "passed";
    const category = taskObj?.category ?? "other";
    const title = taskObj?.title ?? taskId;
    const promptText = taskObj?.prompt ?? "";
    const refCode = taskObj?.referenceCode ?? "";

    // Candidate details
    const sampleItems = taskCandidates.map((cand) => {
      const detail = detailsMap.get(`${taskId}#${cand.attempt}#${cand.repairAttempt ?? 0}`);
      const code = detail?.code || "";
      const rawResp = detail?.responseRaw || "";
      const evalData = detail?.evaluation;
      const tests = evalData?.tests || [];

      const testsRows = tests.map((t) => `
        <tr class="test-row ${t.passed ? "test-passed" : "test-failed"}">
          <td class="test-icon">${t.passed ? "✓" : "✗"}</td>
          <td class="test-id"><code>${escapeHtml(t.id)}</code></td>
          <td class="test-status"><span class="badge ${t.passed ? "badge-success" : "badge-danger"}">${t.passed ? "Passed" : "Failed"}</span></td>
          <td class="test-error">${t.error ? `<span class="err-msg">${escapeHtml(t.error)}</span>` : '<span class="text-dim">None</span>'}</td>
        </tr>
      `).join("");

      const attemptBadge = (cand.repairAttempt ?? 0) > 0
        ? `<span class="badge badge-amber">🔧 Repair #${cand.repairAttempt}</span>`
        : `<span class="badge" style="background:var(--bg-panel);color:var(--text-muted);border:1px solid var(--border);">🎯 Initial (0-shot)</span>`;

      return `
        <div class="sample-content" data-sample="${cand.attempt}" data-repair="${cand.repairAttempt ?? 0}">
          <div class="meta-row">
            <span><strong>Execution:</strong> ${attemptBadge}</span>
            <span><strong>Status:</strong> <span class="badge ${cand.status === "passed" ? "badge-success" : "badge-danger"}">${cand.status}</span></span>
            <span><strong>Tests:</strong> ${cand.passed ?? 0}/${cand.total ?? 0}</span>
            ${cand.generationMs !== undefined ? `<span><strong>Gen Time:</strong> ${cand.generationMs} ms</span>` : ""}
            ${cand.tokensPerSec !== undefined ? `<span><strong>Speed:</strong> ${cand.tokensPerSec} tok/s</span>` : ""}
            ${cand.completionTokens !== undefined ? `<span><strong>Tokens:</strong> ${cand.completionTokens}</span>` : ""}
            ${cand.repairedFrom ? `<span style="color:var(--accent-amber);font-size:0.8rem;">(repaired from ${cand.repairedFrom})</span>` : ""}
          </div>

          ${cand.error ? `<div class="alert alert-danger"><strong>Error:</strong> ${escapeHtml(cand.error)}</div>` : ""}

          <div class="code-tabs">
            <div class="tab-buttons">
              <button type="button" class="tab-btn active" onclick="switchCodeTab(this, 'cand-code-${taskId}-${cand.attempt}')">Solution Code</button>
              <button type="button" class="tab-btn" onclick="switchCodeTab(this, 'ref-code-${taskId}-${cand.attempt}')">Reference Code</button>
              ${rawResp ? `<button type="button" class="tab-btn" onclick="switchCodeTab(this, 'raw-resp-${taskId}-${cand.attempt}')">Raw LLM Response</button>` : ""}
            </div>
            <div id="cand-code-${taskId}-${cand.attempt}" class="tab-panel active">
              <div class="code-header">
                <span>JavaScript (ES2023)</span>
                <button type="button" class="copy-btn" onclick="copyCode(this)">Copy</button>
              </div>
              <pre><code>${escapeHtml(code || "// No extracted code available")}</code></pre>
            </div>
            <div id="ref-code-${taskId}-${cand.attempt}" class="tab-panel">
              <div class="code-header">
                <span>Reference Implementation</span>
                <button type="button" class="copy-btn" onclick="copyCode(this)">Copy</button>
              </div>
              <pre><code>${escapeHtml(refCode || "// No reference code available")}</code></pre>
            </div>
            ${rawResp ? `
            <div id="raw-resp-${taskId}-${cand.attempt}" class="tab-panel">
              <div class="code-header">
                <span>Raw Response</span>
                <button type="button" class="copy-btn" onclick="copyCode(this)">Copy</button>
              </div>
              <pre><code>${escapeHtml(rawResp)}</code></pre>
            </div>` : ""}
          </div>

          ${tests.length > 0 ? `
          <div class="tests-section">
            <h4>Test Case Breakdown (${tests.filter((t) => t.passed).length}/${tests.length})</h4>
            <div class="table-wrap">
              <table class="tests-table">
                <thead>
                  <tr>
                    <th></th>
                    <th>Test ID</th>
                    <th>Status</th>
                    <th>Detail / Mismatch</th>
                  </tr>
                </thead>
                <tbody>
                  ${testsRows}
                </tbody>
              </table>
            </div>
          </div>` : ""}
        </div>
      `;
    }).join("");

    return `
      <div class="task-card" data-task-id="${escapeHtml(taskId)}" data-category="${escapeHtml(category)}" data-status="${candStatus}">
        <div class="task-header" onclick="toggleTaskCard(this)">
          <div class="task-header-left">
            <span class="status-indicator ${isPassed ? "indicator-success" : "indicator-danger"}"></span>
            <span class="task-id">${escapeHtml(taskId)}</span>
            <span class="task-title">${escapeHtml(title)}</span>
          </div>
          <div class="task-header-right">
            <span class="cat-pill">${escapeHtml(category)}</span>
            <span class="badge ${isPassed ? "badge-success" : "badge-danger"}">${firstCand ? `${firstCand.passed ?? 0}/${firstCand.total ?? 0}` : "—"}</span>
            ${firstCand?.tokensPerSec ? `<span class="tps-pill">${firstCand.tokensPerSec} t/s</span>` : ""}
            <span class="chevron">▼</span>
          </div>
        </div>
        <div class="task-body">
          <div class="prompt-box">
            <div class="prompt-title">Task Specification</div>
            <p>${escapeHtml(promptText)}</p>
          </div>
          ${sampleItems}
        </div>
      </div>
    `;
  }).join("");

  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>llm-probe report: ${escapeHtml(model)}</title>
  <style>
    :root {
      --bg-main: #090d16;
      --bg-card: #111827;
      --bg-card-hover: #172033;
      --bg-panel: #0d1322;
      --border: #1f293d;
      --border-focus: #3b82f6;
      --text-main: #f3f4f6;
      --text-muted: #9ca3af;
      --text-dim: #6b7280;
      --accent-blue: #38bdf8;
      --accent-green: #10b981;
      --accent-green-bg: rgba(16, 185, 129, 0.12);
      --accent-red: #f43f5e;
      --accent-red-bg: rgba(244, 63, 94, 0.12);
      --accent-amber: #f59e0b;
      --accent-amber-bg: rgba(245, 158, 11, 0.12);
      --code-bg: #070a12;
      --radius: 10px;
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background-color: var(--bg-main);
      color: var(--text-main);
      line-height: 1.5;
      padding: 32px 24px;
    }

    .container {
      max-width: 1280px;
      margin: 0 auto;
    }

    /* Header */
    .header {
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 24px 28px;
      margin-bottom: 24px;
      display: flex;
      flex-wrap: wrap;
      justify-content: space-between;
      align-items: center;
      gap: 16px;
    }

    .title-area h1 {
      font-size: 1.75rem;
      font-weight: 700;
      color: var(--text-main);
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .model-badge {
      font-size: 1.1rem;
      color: var(--accent-blue);
      font-family: ui-monospace, Consolas, monospace;
      font-weight: 600;
    }

    .meta-tags {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 10px;
      font-size: 0.85rem;
      color: var(--text-muted);
    }

    .meta-tag {
      background: var(--bg-panel);
      border: 1px solid var(--border);
      padding: 4px 10px;
      border-radius: 6px;
    }

    /* KPI Grid */
    .kpi-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 16px;
      margin-bottom: 24px;
    }

    .kpi-card {
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 20px;
      display: flex;
      flex-direction: column;
      gap: 6px;
      transition: transform 0.15s ease, border-color 0.15s ease;
    }

    .kpi-card:hover {
      border-color: #2e3d5a;
      transform: translateY(-2px);
    }

    .kpi-label {
      font-size: 0.8rem;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--text-muted);
    }

    .kpi-value {
      font-size: 1.85rem;
      font-weight: 800;
      color: var(--text-main);
    }

    .kpi-sub {
      font-size: 0.8rem;
      color: var(--text-dim);
    }

    .kpi-card.highlight {
      border-color: rgba(56, 189, 248, 0.4);
      background: linear-gradient(135deg, rgba(56, 189, 248, 0.06), var(--bg-card));
    }

    .kpi-card.highlight .kpi-value {
      color: var(--accent-blue);
    }

    /* Category breakdown */
    .section-title {
      font-size: 1.2rem;
      font-weight: 700;
      margin-bottom: 14px;
      color: var(--text-main);
    }

    .cat-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
      gap: 14px;
      margin-bottom: 28px;
    }

    .cat-card {
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 14px 16px;
      cursor: pointer;
      transition: all 0.15s ease;
    }

    .cat-card:hover {
      border-color: var(--accent-blue);
      background: var(--bg-card-hover);
    }

    .cat-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 0.9rem;
      font-weight: 600;
      margin-bottom: 8px;
    }

    .progress-bar {
      height: 6px;
      background: var(--bg-panel);
      border-radius: 3px;
      overflow: hidden;
    }

    .progress-fill {
      height: 100%;
      background: var(--accent-green);
      border-radius: 3px;
      transition: width 0.3s ease;
    }

    /* Filters Bar */
    .controls-bar {
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 14px 20px;
      margin-bottom: 16px;
      display: flex;
      flex-wrap: wrap;
      justify-content: space-between;
      align-items: center;
      gap: 14px;
    }

    .search-input {
      background: var(--bg-panel);
      border: 1px solid var(--border);
      color: var(--text-main);
      padding: 8px 14px;
      border-radius: 6px;
      font-size: 0.9rem;
      min-width: 240px;
      outline: none;
    }

    .search-input:focus {
      border-color: var(--accent-blue);
    }

    .filter-buttons {
      display: flex;
      gap: 8px;
    }

    .btn-filter {
      background: var(--bg-panel);
      border: 1px solid var(--border);
      color: var(--text-muted);
      padding: 6px 14px;
      border-radius: 6px;
      cursor: pointer;
      font-size: 0.85rem;
      font-weight: 500;
      transition: all 0.15s ease;
    }

    .btn-filter:hover, .btn-filter.active {
      background: var(--accent-blue);
      color: #000;
      border-color: var(--accent-blue);
    }

    /* Task Cards */
    .task-cards {
      display: flex;
      flex-direction: column;
      gap: 10px;
    }

    .task-card {
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      overflow: hidden;
      transition: border-color 0.15s ease;
    }

    .task-card:hover {
      border-color: #2e3d5a;
    }

    .task-header {
      padding: 14px 18px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      cursor: pointer;
      user-select: none;
      background: var(--bg-card);
    }

    .task-header-left {
      display: flex;
      align-items: center;
      gap: 12px;
      flex: 1;
    }

    .task-header-right {
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .status-indicator {
      width: 10px;
      height: 10px;
      border-radius: 50%;
      display: inline-block;
    }

    .indicator-success { background: var(--accent-green); box-shadow: 0 0 8px rgba(16, 185, 129, 0.4); }
    .indicator-danger { background: var(--accent-red); box-shadow: 0 0 8px rgba(244, 63, 94, 0.4); }

    .task-id {
      font-family: ui-monospace, Consolas, monospace;
      font-weight: 700;
      font-size: 0.95rem;
      color: var(--text-main);
    }

    .task-title {
      font-size: 0.9rem;
      color: var(--text-muted);
    }

    .cat-pill {
      background: var(--bg-panel);
      color: var(--text-muted);
      border: 1px solid var(--border);
      font-size: 0.75rem;
      padding: 3px 8px;
      border-radius: 4px;
    }

    .tps-pill {
      font-family: ui-monospace, Consolas, monospace;
      font-size: 0.8rem;
      color: var(--accent-blue);
    }

    .badge {
      padding: 3px 8px;
      border-radius: 4px;
      font-size: 0.8rem;
      font-weight: 600;
    }

    .badge-success { background: var(--accent-green-bg); color: var(--accent-green); border: 1px solid rgba(16, 185, 129, 0.3); }
    .badge-danger { background: var(--accent-red-bg); color: var(--accent-red); border: 1px solid rgba(244, 63, 94, 0.3); }
    .badge-amber { background: var(--accent-amber-bg); color: var(--accent-amber); border: 1px solid rgba(245, 158, 11, 0.3); }

    .chevron {
      color: var(--text-dim);
      font-size: 0.75rem;
      transition: transform 0.2s ease;
    }

    .task-card.expanded .chevron {
      transform: rotate(180deg);
    }

    .task-body {
      display: none;
      padding: 18px;
      background: var(--bg-panel);
      border-top: 1px solid var(--border);
    }

    .task-card.expanded .task-body {
      display: block;
    }

    .prompt-box {
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 14px 16px;
      margin-bottom: 16px;
      font-size: 0.9rem;
    }

    .prompt-title {
      font-weight: 700;
      font-size: 0.8rem;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--text-muted);
      margin-bottom: 6px;
    }

    .meta-row {
      display: flex;
      flex-wrap: wrap;
      gap: 16px;
      margin-bottom: 14px;
      font-size: 0.85rem;
      color: var(--text-muted);
      background: var(--bg-card);
      padding: 10px 14px;
      border-radius: 6px;
      border: 1px solid var(--border);
    }

    .alert {
      padding: 10px 14px;
      border-radius: 6px;
      margin-bottom: 14px;
      font-size: 0.85rem;
    }

    .alert-danger {
      background: var(--accent-red-bg);
      border: 1px solid rgba(244, 63, 94, 0.3);
      color: var(--accent-red);
    }

    /* Code tabs */
    .code-tabs {
      background: var(--code-bg);
      border: 1px solid var(--border);
      border-radius: 6px;
      overflow: hidden;
      margin-bottom: 16px;
    }

    .tab-buttons {
      display: flex;
      background: var(--bg-card);
      border-bottom: 1px solid var(--border);
    }

    .tab-btn {
      background: none;
      border: none;
      color: var(--text-muted);
      padding: 9px 16px;
      font-size: 0.85rem;
      font-weight: 600;
      cursor: pointer;
      border-right: 1px solid var(--border);
      transition: all 0.15s ease;
    }

    .tab-btn:hover {
      background: var(--bg-card-hover);
      color: var(--text-main);
    }

    .tab-btn.active {
      background: var(--code-bg);
      color: var(--accent-blue);
      border-bottom: 2px solid var(--accent-blue);
    }

    .tab-panel {
      display: none;
      padding: 14px 16px;
    }

    .tab-panel.active {
      display: block;
    }

    .code-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;
      font-size: 0.75rem;
      color: var(--text-dim);
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }

    .copy-btn {
      background: var(--bg-panel);
      border: 1px solid var(--border);
      color: var(--text-muted);
      padding: 2px 8px;
      border-radius: 4px;
      font-size: 0.75rem;
      cursor: pointer;
    }

    .copy-btn:hover {
      color: var(--text-main);
      border-color: var(--accent-blue);
    }

    pre {
      font-family: ui-monospace, Consolas, Monaco, monospace;
      font-size: 0.85rem;
      color: #e2e8f0;
      overflow-x: auto;
      white-space: pre-wrap;
      line-height: 1.5;
    }

    /* Tests table */
    .tests-section h4 {
      font-size: 0.9rem;
      font-weight: 700;
      margin-bottom: 8px;
      color: var(--text-main);
    }

    .table-wrap {
      overflow-x: auto;
      border: 1px solid var(--border);
      border-radius: 6px;
    }

    .tests-table {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.85rem;
    }

    .tests-table th, .tests-table td {
      padding: 8px 12px;
      text-align: left;
      border-bottom: 1px solid var(--border);
    }

    .tests-table th {
      background: var(--bg-card);
      color: var(--text-muted);
      font-weight: 600;
      font-size: 0.75rem;
      text-transform: uppercase;
    }

    .tests-table tr:last-child td {
      border-bottom: none;
    }

    .test-icon { width: 24px; text-align: center; font-weight: 800; }
    .test-passed .test-icon { color: var(--accent-green); }
    .test-failed .test-icon { color: var(--accent-red); }

    .err-msg {
      color: var(--accent-red);
      font-family: ui-monospace, Consolas, monospace;
      font-size: 0.8rem;
    }

    .footer {
      margin-top: 40px;
      text-align: center;
      font-size: 0.8rem;
      color: var(--text-dim);
    }
  </style>
</head>
<body>
  <div class="container">
    <!-- Header -->
    <header class="header">
      <div class="title-area">
        <h1>llm-probe <span class="model-badge">${escapeHtml(model)}</span></h1>
        <div class="meta-tags">
          <span class="meta-tag">Run: <code>${escapeHtml(runId)}</code></span>
          <span class="meta-tag">Status: <strong style="color: ${status === "completed" ? "var(--accent-green)" : "var(--accent-amber)"}">${escapeHtml(status)}</strong></span>
          ${hardware ? `<span class="meta-tag">Hardware: <code>${escapeHtml(hardware)}</code></span>` : ""}
          <span class="meta-tag">Started: ${escapeHtml(startedAt)}</span>
          ${completedAt ? `<span class="meta-tag">Completed: ${escapeHtml(completedAt)}</span>` : ""}
          <span class="meta-tag">Samples: ${samples}</span>
        </div>
      </div>
    </header>

    <!-- KPI Grid -->
    <section class="kpi-grid">
      <div class="kpi-card highlight">
        <span class="kpi-label">pass@1 (0-shot)</span>
        <span class="kpi-value">${passAt1Pct}%</span>
        <span class="kpi-sub">${passedAt1Count} / ${totalTasks} tasks passed</span>
      </div>
      ${(manifest.repairs && manifest.repairs > 0) ? `
      <div class="kpi-card highlight" style="border-color:rgba(245, 158, 11, 0.4);background:linear-gradient(135deg, rgba(245, 158, 11, 0.06), var(--bg-card));">
        <span class="kpi-label" style="color:var(--accent-amber);">pass@repair (≤${manifest.repairs})</span>
        <span class="kpi-value" style="color:var(--accent-amber);">${passWithRepairPct}%</span>
        <span class="kpi-sub">${passedWithRepairCount} / ${totalTasks} (${repairedCount} recovered)</span>
      </div>
      <div class="kpi-card">
        <span class="kpi-label">Recovery Rate</span>
        <span class="kpi-value">${recoveryRatePct}%</span>
        <span class="kpi-sub">${repairedCount} / ${initialFailedCount} failed rescued</span>
      </div>` : ""}
      ${samples > 1 ? `
      <div class="kpi-card">
        <span class="kpi-label">pass@${samples} Accuracy</span>
        <span class="kpi-value">${passAtKPct}%</span>
        <span class="kpi-sub">${passedAtKCount} / ${totalTasks} tasks passed</span>
      </div>` : ""}
      <div class="kpi-card">
        <span class="kpi-label">Throughput</span>
        <span class="kpi-value">${meanTps > 0 ? meanTps : "—"} <span style="font-size:1rem;font-weight:500;">tok/s</span></span>
        <span class="kpi-sub">Mean generation speed</span>
      </div>
      <div class="kpi-card">
        <span class="kpi-label">Latency</span>
        <span class="kpi-value">${medianGenMs > 0 ? medianGenMs : "—"} <span style="font-size:1rem;font-weight:500;">ms</span></span>
        <span class="kpi-sub">Median per candidate</span>
      </div>
      <div class="kpi-card">
        <span class="kpi-label">Total Tokens</span>
        <span class="kpi-value">${totalTokens.toLocaleString()}</span>
        <span class="kpi-sub">~${avgTokensPerTask} tokens / task</span>
      </div>
      <div class="kpi-card highlight">
        <span class="kpi-label">Quality/Speed Score</span>
        <span class="kpi-value">${qsScore}</span>
        <span class="kpi-sub">Normalized Q/S composite</span>
      </div>
    </section>

    <!-- Categories -->
    <section>
      <h2 class="section-title">Accuracy by Category</h2>
      <div class="cat-grid">
        ${Array.from(categoryStats.entries()).map(([cat, stat]) => {
          const pct = stat.total > 0 ? Math.round((stat.passed / stat.total) * 100) : 0;
          return `
            <div class="cat-card" onclick="filterByCategory('${escapeHtml(cat)}')">
              <div class="cat-header">
                <span>${escapeHtml(cat)}</span>
                <span><strong>${stat.passed}/${stat.total}</strong> (${pct}%)</span>
              </div>
              <div class="progress-bar">
                <div class="progress-fill" style="width: ${pct}%"></div>
              </div>
            </div>
          `;
        }).join("")}
      </div>
    </section>

    <!-- Filter Controls -->
    <section class="controls-bar">
      <input type="text" id="task-search" class="search-input" placeholder="Search task ID or title..." oninput="filterTasks()" />
      <div class="filter-buttons">
        <button type="button" class="btn-filter active" data-filter="all" onclick="filterByStatus('all')">All (${totalTasks})</button>
        <button type="button" class="btn-filter" data-filter="passed" onclick="filterByStatus('passed')">Passed (${passedAt1Count})</button>
        <button type="button" class="btn-filter" data-filter="failed" onclick="filterByStatus('failed')">Failed (${totalTasks - passedAt1Count})</button>
      </div>
    </section>

    <!-- Tasks List -->
    <main class="task-cards" id="tasks-container">
      ${taskCardsHtml}
    </main>

    <footer class="footer">
      Generated by <strong>llm-probe</strong> • Local LLM JavaScript Benchmark
    </footer>
  </div>

  <script>
    let currentStatusFilter = 'all';
    let currentCategoryFilter = 'all';

    function toggleTaskCard(headerEl) {
      const card = headerEl.closest('.task-card');
      card.classList.toggle('expanded');
    }

    function switchCodeTab(btn, targetPanelId) {
      const tabsContainer = btn.closest('.code-tabs');
      tabsContainer.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      tabsContainer.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
      btn.classList.add('active');
      const panel = document.getElementById(targetPanelId);
      if (panel) panel.classList.add('active');
    }

    function copyCode(btn) {
      const panel = btn.closest('.tab-panel');
      const codeEl = panel.querySelector('code');
      if (codeEl) {
        navigator.clipboard.writeText(codeEl.innerText).then(() => {
          const original = btn.innerText;
          btn.innerText = 'Copied!';
          setTimeout(() => btn.innerText = original, 1500);
        });
      }
    }

    function filterByStatus(status) {
      currentStatusFilter = status;
      document.querySelectorAll('.btn-filter').forEach(b => {
        b.classList.toggle('active', b.dataset.filter === status);
      });
      filterTasks();
    }

    function filterByCategory(cat) {
      currentCategoryFilter = (currentCategoryFilter === cat) ? 'all' : cat;
      filterTasks();
    }

    function filterTasks() {
      const query = document.getElementById('task-search').value.toLowerCase().trim();
      const cards = document.querySelectorAll('.task-card');

      cards.forEach(card => {
        const taskId = card.dataset.taskId.toLowerCase();
        const category = card.dataset.category.toLowerCase();
        const status = card.dataset.status;

        const matchesQuery = !query || taskId.includes(query) || card.innerText.toLowerCase().includes(query);
        const matchesStatus = (currentStatusFilter === 'all') ||
                              (currentStatusFilter === 'passed' && status === 'passed') ||
                              (currentStatusFilter === 'failed' && status !== 'passed');
        const matchesCat = (currentCategoryFilter === 'all') || (category === currentCategoryFilter.toLowerCase());

        if (matchesQuery && matchesStatus && matchesCat) {
          card.style.display = 'block';
        } else {
          card.style.display = 'none';
        }
      });
    }
  </script>
</body>
</html>`;
}

export function renderHtmlComparisonReport(
  manifests: ReadonlyArray<RunManifest>,
  taskList: ReadonlyArray<Task> = []
): string {
  const entries = manifests
    .map(extractEntry)
    .filter((e): e is NonNullable<typeof e> => e !== undefined)
    .sort((a, b) => b.qualitySpeedScore - a.qualitySpeedScore);

  const totalModels = entries.length;
  const totalTasksCount = taskList.length;

  const summaryRows = entries.map((e, idx) => {
    const rank = idx === 0 ? "🥇" : idx === 1 ? "🥈" : idx === 2 ? "🥉" : `#${idx + 1}`;
    return `
      <tr>
        <td class="rank-col">${rank}</td>
        <td><strong class="model-name">${escapeHtml(e.model)}</strong></td>
        <td><span class="badge ${e.accuracyPct >= 80 ? "badge-success" : e.accuracyPct >= 50 ? "badge-amber" : "badge-danger"}">${e.tasksPassed}/${e.totalTasks} (${e.accuracyPct}%)</span></td>
        <td><strong style="color:var(--accent-blue);">${e.meanTps}</strong> tok/s</td>
        <td>${e.meanLatencyMs} ms</td>
        <td>${e.totalTokens.toLocaleString()}</td>
        <td>${e.tokensPerTask}</td>
        <td><strong class="qs-badge">${e.qualitySpeedScore}</strong></td>
      </tr>
    `;
  }).join("");

  const taskRows = taskList.map((task) => {
    const modelCells = entries.map((entry) => {
      const manifest = manifests.find((m) => m.id === entry.runId);
      const candidates = manifest?.candidates.filter((c) => c.taskId === task.id) ?? [];
      const hasPassed = candidates.some((c) => c.status === "passed");
      const lastCand = candidates[candidates.length - 1];

      if (hasPassed) {
        const speed = lastCand?.tokensPerSec ? `<div class="cell-sub">${lastCand.tokensPerSec} t/s</div>` : "";
        return `<td class="cell-pass"><span class="matrix-status pass">✓ PASS</span>${speed}</td>`;
      }
      if (lastCand?.status === "provider_error") return `<td class="cell-err"><span class="matrix-status err">ERR</span></td>`;
      if (lastCand?.status === "compile_error") return `<td class="cell-fail"><span class="matrix-status fail">SYNTAX</span></td>`;
      if (lastCand?.status === "extract_error") return `<td class="cell-fail"><span class="matrix-status fail">EXTRACT</span></td>`;
      if (lastCand?.status === "timeout") return `<td class="cell-warn"><span class="matrix-status warn">TIMEOUT</span></td>`;
      if (lastCand) {
        return `<td class="cell-fail"><span class="matrix-status fail">FAIL (${lastCand.passed ?? 0}/${lastCand.total ?? 0})</span></td>`;
      }
      return `<td><span class="text-dim">—</span></td>`;
    }).join("");

    return `
      <tr class="matrix-row" data-category="${escapeHtml(task.category)}">
        <td class="task-col"><code>${escapeHtml(task.id)}</code></td>
        <td><span class="cat-pill">${escapeHtml(task.category)}</span></td>
        ${modelCells}
      </tr>
    `;
  }).join("");

  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>llm-probe Matrix Comparison</title>
  <style>
    :root {
      --bg-main: #090d16;
      --bg-card: #111827;
      --bg-card-hover: #172033;
      --bg-panel: #0d1322;
      --border: #1f293d;
      --text-main: #f3f4f6;
      --text-muted: #9ca3af;
      --text-dim: #6b7280;
      --accent-blue: #38bdf8;
      --accent-green: #10b981;
      --accent-green-bg: rgba(16, 185, 129, 0.12);
      --accent-red: #f43f5e;
      --accent-red-bg: rgba(244, 63, 94, 0.12);
      --accent-amber: #f59e0b;
      --accent-amber-bg: rgba(245, 158, 11, 0.12);
      --radius: 10px;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background: var(--bg-main);
      color: var(--text-main);
      padding: 32px 24px;
      line-height: 1.5;
    }
    .container { max-width: 1400px; margin: 0 auto; }
    .header {
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 24px 28px;
      margin-bottom: 24px;
    }
    .header h1 { font-size: 1.8rem; font-weight: 800; }
    .header-sub { color: var(--text-muted); font-size: 0.95rem; margin-top: 6px; }

    .card {
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 20px;
      margin-bottom: 24px;
      overflow-x: auto;
    }
    .card-title { font-size: 1.2rem; font-weight: 700; margin-bottom: 16px; }

    table { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
    th, td { padding: 10px 14px; text-align: left; border-bottom: 1px solid var(--border); }
    th { background: var(--bg-panel); color: var(--text-muted); font-size: 0.8rem; text-transform: uppercase; }
    tr:last-child td { border-bottom: none; }

    .rank-col { font-size: 1.2rem; text-align: center; }
    .model-name { font-family: ui-monospace, Consolas, monospace; color: var(--accent-blue); }
    .qs-badge { font-size: 1.1rem; color: #fbbf24; }

    .matrix-table th, .matrix-table td { text-align: center; font-size: 0.85rem; }
    .matrix-table th.task-col, .matrix-table td.task-col { text-align: left; }
    .cat-pill { background: var(--bg-panel); border: 1px solid var(--border); font-size: 0.75rem; padding: 2px 8px; border-radius: 4px; color: var(--text-muted); }

    .matrix-status { display: inline-block; padding: 3px 8px; border-radius: 4px; font-weight: 700; font-size: 0.75rem; }
    .matrix-status.pass { background: var(--accent-green-bg); color: var(--accent-green); border: 1px solid rgba(16, 185, 129, 0.4); }
    .matrix-status.fail { background: var(--accent-red-bg); color: var(--accent-red); border: 1px solid rgba(244, 63, 94, 0.4); }
    .matrix-status.err { background: rgba(148, 163, 184, 0.15); color: #cbd5e1; }
    .matrix-status.warn { background: var(--accent-amber-bg); color: var(--accent-amber); }
    .cell-sub { font-size: 0.7rem; color: var(--accent-blue); margin-top: 2px; }

    .badge { padding: 3px 8px; border-radius: 4px; font-weight: 600; font-size: 0.8rem; }
    .badge-success { background: var(--accent-green-bg); color: var(--accent-green); }
    .badge-danger { background: var(--accent-red-bg); color: var(--accent-red); }
    .badge-amber { background: var(--accent-amber-bg); color: var(--accent-amber); }
  </style>
</head>
<body>
  <div class="container">
    <header class="header">
      <h1>🔬 Model Benchmark Comparison Matrix</h1>
      <div class="header-sub">Comparing <strong>${totalModels} models</strong> across <strong>${totalTasksCount} tasks</strong> | Hardware: <code>${escapeHtml(entries[0]?.hardware || "Mixed")}</code></div>
    </header>

    <div class="card">
      <div class="card-title">📊 Leaderboard & Speed Summary</div>
      <table>
        <thead>
          <tr>
            <th>Rank</th>
            <th>Model</th>
            <th>Accuracy (pass@1)</th>
            <th>Speed (tok/s)</th>
            <th>Mean Latency</th>
            <th>Total Tokens</th>
            <th>Tokens/Task</th>
            <th>Q/S Score</th>
          </tr>
        </thead>
        <tbody>
          ${summaryRows}
        </tbody>
      </table>
    </div>

    <div class="card">
      <div class="card-title">🧩 Task-by-Task Matrix</div>
      <table class="matrix-table">
        <thead>
          <tr>
            <th class="task-col">Task ID</th>
            <th>Category</th>
            ${entries.map((e) => `<th>${escapeHtml(e.model)}</th>`).join("")}
          </tr>
        </thead>
        <tbody>
          ${taskRows}
        </tbody>
      </table>
    </div>
  </div>
</body>
</html>`;
}
