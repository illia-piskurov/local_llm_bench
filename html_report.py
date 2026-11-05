"""Unified interactive HTML dashboard for local LLM benchmark.

Combines:
1. 🏆 General quality leaderboard (score, coverage, truncation, speed) with host / backend filters.
2. ⚡ Speed comparison across devices (Hardware Matrix keyed by model, backend and quantization).
3. 🔍 Model deep-dive (cards for every benchmark, generated code, errors).
4. 🔀 Side-by-side model comparison with a line diff.
5. 📜 Run history.

Works fully offline in any browser, without external CDN or npm.
"""

import re
import webbrowser
from datetime import datetime
from pathlib import Path

from database import Database
from report_data import MIN_COVERAGE, TOTAL_TASKS, load_report_data

ROOT = Path(__file__).parent

_PLACEHOLDER_RE = re.compile(r"__([A-Z_]+)__")


def generate_html_report(db: Database, output_path: Path = ROOT / "report.html", sync_records: bool = True) -> Path:
    if sync_records:
        try:
            from sync import sync_db_and_records

            sync_db_and_records(db)
        except Exception:
            pass

    data = load_report_data(db)
    values = {
        "NOW": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "MODELS": str(len(data.leaderboard)),
        "DEVICES": str(len(data.hosts)),
        "RUNS": str(len(data.runs_data)),
        "RESULTS": str(data.total_tests_count),
        "MIN_COVERAGE_PCT": f"{MIN_COVERAGE * 100:.0f}",
        "TOTAL_TASKS": str(TOTAL_TASKS),
        "RUNS_ROWS": data.runs_table_rows,
        "CLIENT_JSON": data.client_json,
        "BLOBS_JSON": data.blobs_json,
    }
    # Single pass so a placeholder-looking string inside the data is never substituted.
    html_content = _PLACEHOLDER_RE.sub(lambda m: values.get(m.group(1), m.group(0)), _TEMPLATE)
    output_path.write_text(html_content, encoding="utf-8")
    return output_path


def open_report_in_browser(report_path: Path = ROOT / "report.html") -> None:
    webbrowser.open(report_path.resolve().as_uri())


_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Local LLM Benchmark Unified Dashboard</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    :root {
      --bg: #0d1117;
      --card-bg: #161b22;
      --card-border: #30363d;
      --text: #c9d1d9;
      --text-muted: #8b949e;
      --accent: #58a6ff;
      --green: #3fb950;
      --yellow: #d29922;
      --red: #f85149;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background-color: var(--bg);
      color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      line-height: 1.5;
      padding: 24px;
    }
    .container { max-width: 1350px; margin: 0 auto; }
    header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-bottom: 20px;
      border-bottom: 1px solid var(--card-border);
      margin-bottom: 24px;
    }
    h1 { font-size: 24px; font-weight: 600; color: #f0f6fc; }
    .subtitle { color: var(--text-muted); font-size: 14px; margin-top: 4px; }
    .badge {
      display: inline-block;
      padding: 2px 8px;
      font-size: 12px;
      font-weight: 500;
      border-radius: 12px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    .lang-python { background: #2b5b84; color: #fff; }
    .lang-c { background: #444; color: #fff; }
    .lang-javascript { background: #b89b14; color: #fff; }
    .lang-lua { background: #0000aa; color: #fff; }

    .score-pill {
      display: inline-block;
      padding: 3px 10px;
      border-radius: 12px;
      font-weight: 600;
      font-size: 13px;
    }
    .score-green { background: rgba(63, 185, 80, 0.2); color: var(--green); border: 1px solid var(--green); }
    .score-yellow { background: rgba(210, 153, 34, 0.2); color: var(--yellow); border: 1px solid var(--yellow); }
    .score-red { background: rgba(248, 81, 73, 0.2); color: var(--red); border: 1px solid var(--red); }

    .tabs { display: flex; gap: 12px; margin-bottom: 20px; }
    .tab-btn {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      color: var(--text);
      padding: 10px 18px;
      border-radius: 6px;
      cursor: pointer;
      font-weight: 600;
      font-size: 14px;
      transition: all 0.15s ease;
    }
    .tab-btn:hover { border-color: var(--accent); }
    .tab-btn.active {
      background: var(--accent);
      color: #0d1117;
      border-color: var(--accent);
    }

    .section { margin-bottom: 36px; }
    .section-title {
      font-size: 18px;
      color: #f0f6fc;
      margin-bottom: 14px;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }

    /* Table */
    table { width: 100%; border-collapse: collapse; background: var(--card-bg); border-radius: 8px; overflow: hidden; border: 1px solid var(--card-border); }
    th, td { padding: 11px 14px; text-align: left; font-size: 14px; border-bottom: 1px solid var(--card-border); }
    th { background: #1f242c; color: var(--text-muted); font-weight: 600; }
    tr:hover td { background: rgba(255, 255, 255, 0.02); }

    /* Cards Grid */
    .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(380px, 1fr)); gap: 16px; }
    .device-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px; margin-bottom: 24px; }
    .card {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 8px;
      padding: 16px;
    }
    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;
      padding-bottom: 8px;
      border-bottom: 1px solid var(--card-border);
    }
    .card-title { font-weight: 600; color: #f0f6fc; font-size: 15px; }

    .level-row {
      margin-bottom: 12px;
      padding-bottom: 8px;
      border-bottom: 1px dashed rgba(255,255,255,0.06);
    }
    .level-row:last-child { border-bottom: none; margin-bottom: 0; padding-bottom: 0; }
    .level-meta { display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 4px; }

    .progress-bar {
      height: 6px;
      background: rgba(255,255,255,0.1);
      border-radius: 3px;
      overflow: hidden;
      margin-bottom: 6px;
    }
    .progress-fill { height: 100%; }
    .fill-green { background: var(--green); }
    .fill-yellow { background: var(--yellow); }
    .fill-red { background: var(--red); }

    .code-box {
      margin-top: 8px;
      background: #090d12;
      border: 1px solid var(--card-border);
      border-radius: 6px;
      padding: 8px 12px;
      font-size: 12px;
    }
    .code-box summary { cursor: pointer; color: var(--accent); outline: none; font-weight: 500; }
    .code-box pre {
      margin-top: 8px;
      max-height: 280px;
      overflow-y: auto;
      color: #e6edf3;
      font-family: Consolas, monospace;
      white-space: pre-wrap;
    }

    .failures-list {
      margin-top: 4px;
      padding-left: 18px;
      color: var(--red);
      font-size: 12px;
    }

    select.model-picker {
      background: var(--card-bg);
      border: 1px solid var(--accent);
      color: #f0f6fc;
      padding: 6px 12px;
      border-radius: 6px;
      font-size: 14px;
      font-weight: 500;
      cursor: pointer;
    }

    .speed-tag {
      font-weight: 600;
      color: #58a6ff;
    }
    .speed-fastest {
      color: #3fb950;
      font-weight: 700;
    }

    /* Filters, sorting, diff */
    .filters {
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      align-items: center;
      margin-bottom: 14px;
    }
    .filters label { font-size: 12px; color: var(--text-muted); font-weight: 600; margin-right: 4px; }
    .filters select, .filters input {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      color: #f0f6fc;
      padding: 6px 10px;
      border-radius: 6px;
      font-size: 13px;
    }
    .note { font-size: 12px; color: var(--text-muted); margin-bottom: 12px; line-height: 1.5; }
    .muted { color: var(--text-muted); }
    .small { font-size: 11px; }
    th.sortable { cursor: pointer; user-select: none; white-space: nowrap; }
    th.sortable:hover { color: #f0f6fc; }
    th.sortable::after { content: " ↕"; opacity: 0.35; }
    th.sortable[data-dir="asc"]::after { content: " ▲"; opacity: 1; color: var(--accent); }
    th.sortable[data-dir="desc"]::after { content: " ▼"; opacity: 1; color: var(--accent); }
    tr.divider td { background: #1f242c; color: var(--text-muted); font-size: 12px; font-weight: 600; text-align: center; }
    tr.partial td { opacity: 0.72; }
    .tag-trunc { color: var(--yellow); font-weight: 600; font-size: 12px; }
    .speed-low { opacity: 0.55; }
    .index-pill { font-size: 26px; font-weight: 700; color: #58a6ff; }
    pre.diff {
      background: #090d12;
      border: 1px solid var(--card-border);
      border-radius: 6px;
      padding: 8px 0;
      max-height: 520px;
      overflow: auto;
      font-family: Consolas, monospace;
      font-size: 12px;
      line-height: 1.45;
    }
    pre.diff span { display: block; padding: 0 12px; white-space: pre-wrap; }
    pre.diff .diff-add { background: rgba(63, 185, 80, 0.15); color: #7ee787; }
    pre.diff .diff-del { background: rgba(248, 81, 73, 0.15); color: #ffa198; }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div>
        <h1>🚀 Local LLM Unified Dashboard</h1>
        <div class="subtitle">Quality, speed, and hardware comparison | Updated: __NOW__</div>
      </div>
      <div>
        <span class="badge" style="background:#238636; color:#fff; padding:6px 12px; font-size:13px;">
          Models: __MODELS__ | Devices: __DEVICES__ | Runs: __RUNS__ | Results: __RESULTS__
        </span>
      </div>
    </header>

    <div class="tabs">
      <button class="tab-btn active" data-tab="leaderboard">🏆 1. Leaderboard</button>
      <button class="tab-btn" data-tab="devices">⚡ 2. Hardware Matrix</button>
      <button class="tab-btn" data-tab="model-view">🔍 3. Model Deep-Dive & Code</button>
      <button class="tab-btn" data-tab="diff-view">🔀 4. Model Comparison (Diff)</button>
      <button class="tab-btn" data-tab="runs-view">📜 5. Run History</button>
    </div>

    <!-- TAB 1: LEADERBOARD -->
    <div id="tab-leaderboard" class="section">
      <div class="section-title">
        <span>Model ranking by generation quality</span>
      </div>
      <div class="filters">
        <span><label for="lb-host">Host</label><select id="lb-host"></select></span>
        <span><label for="lb-backend">Backend</label><select id="lb-backend"></select></span>
        <input type="text" id="search-input" placeholder="Search model..." style="width:240px;">
      </div>
      <div class="note">
        Score = mean of per-task scores (every task weighs the same). Truncated or failed generations score 0% and
        are never skipped; only harness failures are excluded. Models that completed less than __MIN_COVERAGE_PCT__% of
        the __TOTAL_TASKS__ suite tasks are listed below the ranking. Speed is token-weighted; with "All hosts" it is the
        median across hosts (hover for the per-host numbers), so pick a host to compare models fairly.
      </div>
      <table id="leaderboard-table">
        <thead>
          <tr>
            <th class="nosort" style="width: 45px;">#</th>
            <th>Model</th>
            <th>Score</th>
            <th>Checks Passed</th>
            <th>Tasks</th>
            <th>Truncated</th>
            <th>Speed</th>
            <th>Quant</th>
            <th>Backend</th>
            <th class="nosort">Details</th>
          </tr>
        </thead>
        <tbody></tbody>
      </table>
    </div>

    <!-- TAB 2: HARDWARE SPEED MATRIX -->
    <div id="tab-devices" class="section" style="display:none;">
      <div class="section-title">
        <span>Device Performance Profile (Generation Speed tok/s)</span>
      </div>
      <div class="note">
        Speed index compares a device with the average of the devices that ran the same model, backend and
        quantization (1.00× = average), so a device that only ran small models is not mistaken for a fast one.
      </div>
      <div class="device-grid" id="device-grid"></div>

      <div class="section-title" style="margin-top:28px;">
        <span>Model × Device (one row per model, backend, quantization and context)</span>
        <input type="text" id="device-search-input" placeholder="Filter models..." style="width:240px;">
      </div>
      <table id="devices-table">
        <thead></thead>
        <tbody></tbody>
      </table>
    </div>

    <!-- TAB 3: MODEL DEEP-DIVE -->
    <div id="tab-model-view" class="section" style="display:none;">
      <div class="section-title">
        <div style="display:flex; align-items:center; gap:12px;">
          <span>Model Engineering Profile:</span>
          <select id="model-select" class="model-picker"></select>
        </div>
        <div id="model-summary-badges"></div>
      </div>
      <div id="benchmarks-grid" class="grid"></div>
    </div>

    <!-- TAB 4: SIDE-BY-SIDE DIFF -->
    <div id="tab-diff-view" class="section" style="display:none;">
      <div class="card" style="margin-bottom:20px; border-left: 4px solid var(--accent);">
        <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap:16px; align-items:center;">
          <div>
            <label style="display:block; font-size:12px; color:var(--text-muted); margin-bottom:6px; font-weight:600;">MODEL A (Left):</label>
            <select id="diff-model-a" class="model-picker" style="width:100%;"></select>
          </div>
          <div>
            <label style="display:block; font-size:12px; color:var(--text-muted); margin-bottom:6px; font-weight:600;">MODEL B (Right):</label>
            <select id="diff-model-b" class="model-picker" style="width:100%;"></select>
          </div>
          <div>
            <label style="display:block; font-size:12px; color:var(--text-muted); margin-bottom:6px; font-weight:600;">TASK / LEVEL:</label>
            <select id="diff-task" class="model-picker" style="width:100%;"></select>
          </div>
        </div>
      </div>
      <div id="diff-lines" style="margin-bottom:16px;"></div>
      <div id="diff-container" style="display:grid; grid-template-columns: repeat(auto-fit, minmax(420px, 1fr)); gap:16px;"></div>
    </div>

    <!-- TAB 5: RUN HISTORY -->
    <div id="tab-runs-view" class="section" style="display:none;">
      <div class="section-title">
        <span>Execution Sessions & Benchmark Runs (__RUNS__ total runs)</span>
        <input type="text" id="runs-search-input" placeholder="Search by model, host, quant..." style="width:280px;">
      </div>
      <table id="runs-table">
        <thead>
          <tr>
            <th>Run ID</th>
            <th>Started At</th>
            <th>Model</th>
            <th>Quantization</th>
            <th>Host (Hardware)</th>
            <th>Backend</th>
            <th class="nosort">Hyperparameters & Artifact</th>
            <th>Tests</th>
            <th>Avg Score</th>
            <th>Avg Speed</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          __RUNS_ROWS__
        </tbody>
      </table>
    </div>
  </div>

  <script type="application/json" id="blobs-data">__BLOBS_JSON__</script>
  <script>
    const data = __CLIENT_JSON__;
    const ALL = '*';
    const TABS = ['leaderboard', 'devices', 'model-view', 'diff-view', 'runs-view'];

    // Code and reasoning traces are large, so they are parsed only when a detail view needs them.
    let blobsCache = null;
    function getBlob(model, key) {
      if (blobsCache === null) {
        try { blobsCache = JSON.parse(document.getElementById('blobs-data').textContent); } catch (e) { blobsCache = {}; }
      }
      return (blobsCache[model] || {})[key] || {};
    }

    function esc(str) {
      return String(str == null ? '' : str)
        .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
    }
    const hostLabel = id => data.all_host_labels[id] || id;
    const pillClass = pct => pct >= 80 ? 'score-green' : pct >= 40 ? 'score-yellow' : 'score-red';
    const fillClass = pct => pct >= 80 ? 'fill-green' : pct >= 40 ? 'fill-yellow' : 'fill-red';

    function makeSortable(table) {
      table.querySelectorAll('thead th').forEach((th, idx) => {
        if (th.classList.contains('nosort')) return;
        th.classList.add('sortable');
        th.addEventListener('click', () => {
          const dir = th.dataset.dir === 'asc' ? 'desc' : 'asc';
          table.querySelectorAll('thead th').forEach(t => { delete t.dataset.dir; });
          th.dataset.dir = dir;
          const tbody = table.tBodies[0];
          tbody.querySelectorAll('tr.divider').forEach(r => r.remove());
          const cellValue = r => {
            const c = r.cells[idx];
            return c.dataset.v !== undefined ? c.dataset.v : c.innerText.trim();
          };
          const rows = Array.from(tbody.rows);
          rows.sort((ra, rb) => {
            const a = cellValue(ra), b = cellValue(rb);
            const aEmpty = a === '' || a === '—', bEmpty = b === '' || b === '—';
            if (aEmpty || bEmpty) return aEmpty === bEmpty ? 0 : (aEmpty ? 1 : -1);
            const na = Number(a), nb = Number(b);
            const cmp = (!isNaN(na) && !isNaN(nb)) ? na - nb : a.localeCompare(b);
            return dir === 'asc' ? cmp : -cmp;
          });
          rows.forEach(r => tbody.appendChild(r));
        });
      });
    }
    function clearSort(table) {
      table.querySelectorAll('thead th').forEach(t => { delete t.dataset.dir; });
    }

    function switchTab(tab) {
      TABS.forEach(t => {
        document.getElementById('tab-' + t).style.display = t === tab ? 'block' : 'none';
      });
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.toggle('active', b.dataset.tab === tab));
      try { history.replaceState(null, '', '#' + tab); } catch (e) { /* file:// restrictions */ }
      if (tab === 'diff-view') renderDiff();
    }
    document.querySelectorAll('.tab-btn').forEach(b => b.addEventListener('click', () => switchTab(b.dataset.tab)));

    // ---------- Leaderboard ----------
    const lbState = { host: ALL, backend: ALL, q: '' };
    const lbHost = document.getElementById('lb-host');
    const lbBackend = document.getElementById('lb-backend');

    (function initLeaderboardFilters() {
      const keys = Object.keys(data.leaderboards).map(k => k.split('|'));
      const hostIds = [...new Set(keys.map(k => k[0]).filter(h => h !== ALL))];
      const backends = [...new Set(keys.map(k => k[1]).filter(b => b !== ALL))];
      const fill = (sel, options) => options.forEach(([v, label]) => {
        const o = document.createElement('option');
        o.value = v; o.textContent = label; sel.appendChild(o);
      });
      fill(lbHost, [[ALL, 'All hosts'], ...hostIds.map(h => [h, hostLabel(h)])]);
      fill(lbBackend, [[ALL, 'All backends'], ...backends.map(b => [b, b])]);
      lbHost.addEventListener('change', () => { lbState.host = lbHost.value; renderLeaderboard(); });
      lbBackend.addEventListener('change', () => { lbState.backend = lbBackend.value; renderLeaderboard(); });
      document.getElementById('search-input').addEventListener('input', e => {
        lbState.q = e.target.value.toLowerCase();
        renderLeaderboard();
      });
    })();

    function speedCell(e) {
      if (e.avg_speed == null) return '<td data-v="">—</td>';
      const perHost = Object.entries(e.speed_by_host).sort((a, b) => b[1] - a[1]);
      const tip = perHost.map(([h, v]) => hostLabel(h) + ': ' + v.toFixed(1) + ' tok/s').join('\n');
      const multi = lbState.host === ALL && perHost.length > 1;
      return `<td data-v="${e.avg_speed}" title="${esc(tip)}" style="color:var(--text-muted); font-weight:500;">
        ${e.avg_speed.toFixed(1)} tok/s${multi ? `<span class="muted small" style="display:block;">median of ${perHost.length} hosts</span>` : ''}</td>`;
    }

    function renderLeaderboard() {
      const table = document.getElementById('leaderboard-table');
      const tbody = table.tBodies[0];
      clearSort(table);
      const entries = data.leaderboards[lbState.host + '|' + lbState.backend] || [];
      let rank = 0;
      let dividerShown = false;
      let html = '';
      let shown = 0;
      entries.forEach((e, idx) => {
        if (e.ranked) rank++;
        if (lbState.q && !e.model.toLowerCase().includes(lbState.q)) return;
        shown++;
        if (!e.ranked && !dividerShown) {
          dividerShown = true;
          html += `<tr class="divider"><td colspan="10">Partial coverage — fewer than ${Math.round(data.min_coverage * 100)}% of the ${data.total_tasks} suite tasks, not ranked</td></tr>`;
        }
        const trunc = e.truncated + e.failed;
        const thinker = e.thinker
          ? ' <span class="badge" style="background:rgba(137,87,229,0.2); color:#d2a8ff; border:1px solid rgba(137,87,229,0.4);" title="Produces reasoning tokens">🧠 Thinker</span>'
          : '';
        html += `
          <tr class="${e.ranked ? '' : 'partial'}">
            <td data-v="${idx}" style="font-weight:600; color:var(--text-muted);">${e.ranked ? rank : '–'}</td>
            <td data-v="${esc(e.model)}" style="font-weight:600; color:#f0f6fc;">${esc(e.model)}${thinker}</td>
            <td data-v="${e.avg_pct}"><span class="score-pill ${pillClass(e.avg_pct)}">${e.avg_pct.toFixed(1)}%</span></td>
            <td data-v="${e.passed}">${e.passed} / ${e.total}</td>
            <td data-v="${e.coverage}" title="${e.tests_count} of ${data.total_tasks} suite tasks">${e.tests_count} / ${data.total_tasks}</td>
            <td data-v="${trunc}">${trunc ? `<span class="tag-trunc" title="Truncated or failed generations (scored 0%)">✂ ${trunc}</span>` : '<span class="muted">—</span>'}${e.infra ? ` <span class="muted small" title="Harness failures, excluded from the score">⚠ ${e.infra}</span>` : ''}</td>
            ${speedCell(e)}
            <td data-v="${esc(e.quantization || '')}" style="font-size:13px;">${esc(e.quantization || '—')}</td>
            <td data-v="${esc(e.backend || '')}" style="font-size:13px;">${esc((e.backends || []).join(', ') || '—')}</td>
            <td><a href="#model-view" class="details-link" data-model="${esc(e.model)}" style="color:var(--accent); text-decoration:none; font-size:13px; font-weight:500;">Details →</a></td>
          </tr>`;
      });
      if (!shown) {
        html = '<tr><td colspan="10" class="muted" style="text-align:center; padding:24px;">No results for this filter.</td></tr>';
      }
      tbody.innerHTML = html;
    }
    document.getElementById('leaderboard-table').tBodies[0].addEventListener('click', ev => {
      const link = ev.target.closest('a.details-link');
      if (!link) return;
      ev.preventDefault();
      selectModel(link.dataset.model);
    });
    makeSortable(document.getElementById('leaderboard-table'));

    // ---------- Hardware matrix ----------
    function renderDevices() {
      const grid = document.getElementById('device-grid');
      grid.innerHTML = data.hosts.map(h => {
        const d = data.devices[h.id];
        const sub = [d.memory, d.gpu].filter(Boolean).join(' · ');
        const index = d.index != null
          ? `<div class="index-pill">${d.index.toFixed(2)}<span style="font-size:14px; font-weight:400; color:var(--text-muted);">×</span></div>
             <div style="font-size:12px; color:var(--text-muted);">speed index (${d.index_variants} shared model setups)</div>`
          : `<div class="index-pill muted">—</div>
             <div style="font-size:12px; color:var(--text-muted);">speed index: no setup shared with another device (≥${data.min_speed_samples} samples)</div>`;
        return `
          <div class="card" style="border-top: 3px solid var(--accent);">
            <div style="font-weight:600; font-size:15px; color:#f0f6fc;" title="${esc(d.label)}">${esc(d.chip || d.label)}</div>
            <div style="font-size:12px; color:var(--text-muted); margin-bottom:8px;">${esc(sub)}</div>
            <div style="display:flex; justify-content:space-between; align-items:flex-end;">
              <div>${index}</div>
              <div style="font-size:12px; color:var(--text-muted); text-align:right;">
                median <strong>${d.median_tps != null ? d.median_tps.toFixed(1) : '—'}</strong> tok/s<br>
                <strong>${d.variants}</strong> setups · <strong>${d.count}</strong> samples
              </div>
            </div>
          </div>`;
      }).join('') || '<p class="muted">No speed data yet.</p>';

      const table = document.getElementById('devices-table');
      table.tHead.innerHTML = '<tr><th>Model</th><th>Backend</th><th>Quant</th><th>Ctx</th>' +
        data.hosts.map(h => `<th title="${esc(h.label)}">${esc((data.devices[h.id].chip) || h.label)}</th>`).join('') + '</tr>';
      renderMatrixRows();
      table.dataset.sortReady || (makeSortable(table), table.dataset.sortReady = '1');
    }

    function renderMatrixRows() {
      const table = document.getElementById('devices-table');
      clearSort(table);
      const q = document.getElementById('device-search-input').value.toLowerCase();
      const rows = data.matrix.filter(v => !q || v.model.toLowerCase().includes(q)).map(v => {
        const cells = data.hosts.map(h => {
          const c = v.cells[h.id];
          if (!c || !c.tps) return '<td data-v=""><span class="muted">—</span></td>';
          const low = c.count < data.min_speed_samples;
          const fastest = v.fastest_host === h.id;
          return `<td data-v="${c.tps}" class="${low ? 'speed-low' : ''}">
            <span class="${fastest ? 'speed-fastest' : 'speed-tag'}">${c.tps.toFixed(1)} tok/s${fastest ? ' 🏆' : ''}</span>
            <span style="font-size:12px; color:var(--text-muted); display:block;">${c.ttft != null ? 'TTFT ' + c.ttft.toFixed(2) + 's · ' : ''}n=${c.count}${low ? ' (low)' : ''}</span>
          </td>`;
        }).join('');
        return `<tr>
          <td data-v="${esc(v.model)}" style="font-weight:600; color:#f0f6fc;">${esc(v.model)}</td>
          <td style="font-size:13px;">${esc(v.backend)}</td>
          <td style="font-size:13px;">${esc(v.quantization)}</td>
          <td data-v="${v.ctx || ''}" style="font-size:13px;">${v.ctx || '—'}</td>
          ${cells}</tr>`;
      });
      table.tBodies[0].innerHTML = rows.join('') ||
        `<tr><td colspan="${4 + data.hosts.length}" class="muted" style="text-align:center; padding:24px;">No speed data.</td></tr>`;
    }
    document.getElementById('device-search-input').addEventListener('input', renderMatrixRows);

    // ---------- Run history ----------
    document.getElementById('runs-search-input').addEventListener('input', e => {
      const query = e.target.value.toLowerCase();
      document.querySelectorAll('#runs-table tbody tr').forEach(r => {
        r.style.display = r.innerText.toLowerCase().includes(query) ? '' : 'none';
      });
    });
    makeSortable(document.getElementById('runs-table'));

    // ---------- Model deep-dive ----------
    const select = document.getElementById('model-select');
    const modelKeys = Object.keys(data.models);
    modelKeys.forEach(m => {
      const opt = document.createElement('option');
      opt.value = m;
      opt.textContent = m;
      select.appendChild(opt);
    });

    function selectModel(modelKey) {
      select.value = modelKey;
      switchTab('model-view');
      renderModelCards(modelKey);
    }
    select.addEventListener('change', () => renderModelCards(select.value));

    function statusTag(r) {
      if (r.status === 'truncated') return '<span class="tag-trunc">✂️ truncated · scored 0%</span>';
      if (r.status === 'failed') return '<span class="tag-trunc">⚠️ generation failed · scored 0%</span>';
      if (r.status === 'infra') return '<span class="tag-trunc">⚠️ infra failure · excluded</span>';
      return `<span><strong>${r.passed}/${r.total}</strong> (${r.percent}%)</span>`;
    }
    function resultOrigin(r) {
      return `${hostLabel(r.host_id)} · ${r.backend} · ${r.quantization} · ${(r.tested_at || '').slice(0, 10)}`;
    }

    function renderModelCards(modelKey) {
      const mData = data.models[modelKey];
      const grid = document.getElementById('benchmarks-grid');
      grid.innerHTML = '';
      const summaryDiv = document.getElementById('model-summary-badges');

      if (!mData) {
        summaryDiv.innerHTML = '';
        grid.innerHTML = '<p style="color:var(--text-muted);">No data available</p>';
        return;
      }

      summaryDiv.innerHTML = `
        <span class="score-pill ${pillClass(mData.avg_pct)}">${mData.avg_pct}% average score</span>
        <span style="font-size:13px; color:var(--text-muted); margin-left:8px;">${mData.tests_count}/${data.total_tasks} tasks${mData.ranked ? '' : ' (partial)'}</span>
        ${(mData.truncated + mData.failed) ? `<span class="tag-trunc" style="margin-left:8px;">✂ ${mData.truncated + mData.failed} truncated/failed</span>` : ''}
        ${mData.avg_speed ? `<span style="font-size:13px; color:var(--text-muted); margin-left:8px;">• ${mData.avg_speed} tok/s</span>` : ''}
      `;

      data.benchmarks.forEach(b => {
        const card = document.createElement('div');
        card.className = 'card';

        let levelsHtml = '';
        const pcts = [];
        let hasAny = false;

        b.levels.forEach(l => {
          const key = b.id + '/' + l.id;
          const r = mData.results[key];
          if (!r) {
            levelsHtml += `
              <div class="level-row" style="opacity: 0.5;">
                <div class="level-meta"><span>${esc(l.name)}</span><span style="color:var(--text-muted);">not tested</span></div>
              </div>`;
            return;
          }
          hasAny = true;
          const excluded = r.status === 'infra';
          if (!excluded) pcts.push(r.percent);
          const fillCls = excluded ? 'fill-yellow' : fillClass(r.percent);

          const failuresHtml = (r.failures && r.failures.length)
            ? '<ul class="failures-list">' + r.failures.map(f => '<li>' + esc(f) + '</li>').join('') + '</ul>' : '';

          let reasoningHtml = '';
          if (r.has_reasoning) {
            reasoningHtml = `
              <details class="code-box" data-lazy="reasoning" data-model="${esc(modelKey)}" data-key="${esc(key)}" style="border-color: rgba(137, 87, 229, 0.4); margin-top: 6px;">
                <summary style="color:#d2a8ff; font-weight:600;">🧠 Reasoning trace${r.reasoning_tokens ? ' • ' + r.reasoning_tokens + ' tokens' : ''}</summary>
                <pre style="color:#e1d9f5; font-size:12px;"><code></code></pre>
              </details>`;
          } else if (r.reasoning_tokens) {
            reasoningHtml = `<div style="font-size:12px; color:#d2a8ff; margin-top:4px;">🧠 ${r.reasoning_tokens} reasoning tokens</div>`;
          }
          const codeHtml = r.has_code ? `
              <details class="code-box" data-lazy="code" data-model="${esc(modelKey)}" data-key="${esc(key)}">
                <summary>📄 Code (${r.lines} lines)${r.tok_per_sec ? ' • ' + r.tok_per_sec + ' tok/s' : ''}</summary>
                <pre><code></code></pre>
              </details>` : '';

          levelsHtml += `
            <div class="level-row">
              <div class="level-meta"><span style="font-weight:500;">${esc(l.name)}</span>${statusTag(r)}</div>
              <div class="progress-bar"><div class="progress-fill ${fillCls}" style="width: ${excluded ? 0 : r.percent}%;"></div></div>
              <div class="muted small" style="margin-bottom:4px;">${esc(resultOrigin(r))}</div>
              ${failuresHtml}${reasoningHtml}${codeHtml}
            </div>`;
        });

        const bPct = pcts.length ? Math.round(pcts.reduce((a, c) => a + c, 0) / pcts.length) : null;
        card.innerHTML = `
          <div class="card-header">
            <div>
              <div class="card-title">${esc(b.name)}</div>
              <span class="badge lang-${esc(b.lang)}">${esc(b.lang)}</span>
            </div>
            ${bPct !== null ? `<span class="score-pill ${pillClass(bPct)}">${bPct}%</span>` : '<span style="font-size:12px; color:var(--text-muted);">—</span>'}
          </div>
          <div>${levelsHtml}</div>`;
        grid.appendChild(card);
      });
    }
    // <details> "toggle" does not bubble, so listen in the capture phase and fill content on first open.
    document.getElementById('benchmarks-grid').addEventListener('toggle', ev => {
      const d = ev.target;
      if (!d.open || !d.dataset.lazy) return;
      const code = d.querySelector('code');
      if (code.textContent) return;
      code.textContent = getBlob(d.dataset.model, d.dataset.key)[d.dataset.lazy === 'code' ? 'code' : 'reasoning_text'] || '';
    }, true);

    // ---------- Diff ----------
    const diffModelA = document.getElementById('diff-model-a');
    const diffModelB = document.getElementById('diff-model-b');
    const diffTask = document.getElementById('diff-task');

    modelKeys.forEach(m => {
      [diffModelA, diffModelB].forEach(sel => {
        const o = document.createElement('option');
        o.value = m; o.textContent = m; sel.appendChild(o);
      });
    });
    if (modelKeys.length > 0) diffModelA.value = modelKeys[0];
    diffModelB.value = modelKeys.length > 1 ? modelKeys[1] : (modelKeys[0] || '');

    data.benchmarks.forEach(b => {
      const grp = document.createElement('optgroup');
      grp.label = b.short + ' (' + b.lang + ')';
      b.levels.forEach(l => {
        const opt = document.createElement('option');
        opt.value = b.id + '/' + l.id;
        opt.textContent = b.short + ' / ' + l.name;
        grp.appendChild(opt);
      });
      diffTask.appendChild(grp);
    });
    [diffModelA, diffModelB, diffTask].forEach(sel => sel.addEventListener('change', renderDiff));

    // Longest-common-subsequence line diff; skipped for very large inputs.
    function lineDiff(aText, bText) {
      const a = aText.split('\n'), b = bText.split('\n');
      const n = a.length, m = b.length;
      if (n * m > 4000000) return null;
      const dp = Array.from({ length: n + 1 }, () => new Uint32Array(m + 1));
      for (let i = n - 1; i >= 0; i--) {
        for (let j = m - 1; j >= 0; j--) {
          dp[i][j] = a[i] === b[j] ? dp[i + 1][j + 1] + 1 : Math.max(dp[i + 1][j], dp[i][j + 1]);
        }
      }
      const ops = [];
      let i = 0, j = 0;
      while (i < n && j < m) {
        if (a[i] === b[j]) { ops.push([' ', a[i]]); i++; j++; }
        else if (dp[i + 1][j] >= dp[i][j + 1]) { ops.push(['-', a[i]]); i++; }
        else { ops.push(['+', b[j]]); j++; }
      }
      while (i < n) ops.push(['-', a[i++]]);
      while (j < m) ops.push(['+', b[j++]]);
      return ops;
    }

    function renderLineDiff(modelA, modelB, taskKey) {
      const box = document.getElementById('diff-lines');
      const a = getBlob(modelA, taskKey).code, b = getBlob(modelB, taskKey).code;
      if (!a || !b) { box.innerHTML = ''; return; }
      const ops = lineDiff(a, b);
      if (ops === null) {
        box.innerHTML = '<p class="muted small">Line diff skipped: the sources are too large.</p>';
        return;
      }
      const changed = ops.filter(o => o[0] !== ' ').length;
      const cls = { '+': 'diff-add', '-': 'diff-del', ' ': '' };
      box.innerHTML = `
        <details class="code-box" ${changed ? 'open' : ''}>
          <summary>🔀 Line diff — A (−) vs B (+): ${changed} changed lines</summary>
          <pre class="diff">${ops.map(o => `<span class="${cls[o[0]]}">${esc(o[0] + ' ' + o[1])}</span>`).join('')}</pre>
        </details>`;
    }

    function renderDiff() {
      const modelA = diffModelA.value, modelB = diffModelB.value, taskKey = diffTask.value;
      const container = document.getElementById('diff-container');

      if (!modelA || !modelB || !taskKey) {
        container.innerHTML = '<p style="color:var(--text-muted); padding:20px;">Select models and task to compare.</p>';
        document.getElementById('diff-lines').innerHTML = '';
        return;
      }

      function renderSide(modelKey, res, label) {
        if (!res) {
          return `
            <div class="card" style="border-top:3px solid #30363d;">
              <div class="card-header">
                <div>
                  <span class="badge" style="background:#21262d; color:#8b949e; margin-bottom:4px; display:inline-block;">${label}</span>
                  <div class="card-title">${esc(modelKey)}</div>
                </div>
                <span class="score-pill" style="background:#21262d; color:#8b949e;">not tested</span>
              </div>
              <p style="color:var(--text-muted); font-size:13px; margin:30px 0; text-align:center;">
                This level was not run for model ${esc(modelKey)}.
              </p>
            </div>`;
        }

        const harness = res.status !== 'ok';
        const excluded = res.status === 'infra';
        const pct = res.percent;
        let pillHtml;
        if (harness) {
          pillHtml = `<span class="score-pill" style="background:rgba(210,153,34,0.2); color:#e3b341; border:1px solid rgba(210,153,34,0.4);">${res.status === 'truncated' ? '✂️ truncated · 0%' : res.status === 'failed' ? '⚠️ failed · 0%' : '⚠️ infra · excluded'}</span>`;
        } else {
          pillHtml = `<span class="score-pill ${pillClass(pct)}">${res.passed}/${res.total} (${pct}%)</span>`;
        }
        const fillCls = excluded ? 'fill-yellow' : fillClass(pct);
        const borderColor = excluded ? 'var(--yellow)' : (pct >= 80 ? 'var(--green)' : pct >= 40 ? 'var(--yellow)' : 'var(--red)');

        let speedBadge = '';
        if (res.tok_per_sec) speedBadge += `<span class="speed-tag">${res.tok_per_sec} tok/s</span>`;
        if (res.ttft) speedBadge += `<span style="font-size:12px; color:var(--text-muted); margin-left:6px;">TTFT: ${res.ttft}s</span>`;
        if (res.reasoning_tokens) speedBadge += `<span style="font-size:12px; color:#d2a8ff; margin-left:8px;">🧠 ${res.reasoning_tokens} think tok</span>`;

        let failuresHtml = '';
        if (res.failures && res.failures.length > 0) {
          const failTitle = harness ? '⚠️ Harness error / Truncated:' : `❌ Failed tests (${res.failures.length}):`;
          failuresHtml = `
            <div style="background:rgba(248,81,73,0.08); border:1px solid rgba(248,81,73,0.3); border-radius:6px; padding:10px 14px; margin: 12px 0;">
              <strong style="color:var(--red); font-size:13px;">${failTitle}</strong>
              <ul class="failures-list" style="margin-top:6px;">${res.failures.map(f => '<li>' + esc(f) + '</li>').join('')}</ul>
            </div>`;
        }

        const blob = getBlob(modelKey, taskKey);
        let reasoningHtml = '';
        if (blob.reasoning_text) {
          reasoningHtml = `
            <details class="code-box" style="border-color: rgba(137,87,229,0.4); margin-bottom:12px;">
              <summary style="color:#d2a8ff; font-weight:600;">🧠 Reasoning trace${res.reasoning_tokens ? ' • ' + res.reasoning_tokens + ' tokens' : ''}</summary>
              <pre style="color:#e1d9f5; font-size:12px; max-height:260px;"><code>${esc(blob.reasoning_text)}</code></pre>
            </details>`;
        }

        const codeHtml = blob.code ? `
            <div style="margin-top:10px;">
              <div style="display:flex; justify-content:space-between; font-size:12px; color:var(--text-muted); margin-bottom:6px;">
                <span>📄 Generated code (${res.lines} lines)</span>
                <span>Language: ${esc(res.ext)}</span>
              </div>
              <pre style="background:#090d12; border:1px solid var(--card-border); border-radius:6px; padding:12px; max-height:480px; overflow-y:auto; color:#e6edf3; font-family:Consolas, monospace; font-size:12px; white-space:pre-wrap;"><code>${esc(blob.code)}</code></pre>
            </div>` : '<p style="color:var(--text-muted); font-size:13px; margin:16px 0;">Code not saved.</p>';

        return `
          <div class="card" style="border-top: 3px solid ${borderColor};">
            <div class="card-header">
              <div>
                <span class="badge" style="background:#1f242c; color:var(--text-muted); margin-bottom:4px; display:inline-block;">${label}</span>
                <div class="card-title">${esc(modelKey)}</div>
                <div style="margin-top:4px;">${speedBadge}</div>
                <div class="muted small" style="margin-top:2px;">${esc(resultOrigin(res))}</div>
              </div>
              <div style="text-align:right;">${pillHtml}</div>
            </div>
            <div class="progress-bar" style="margin-bottom:12px;">
              <div class="progress-fill ${fillCls}" style="width: ${excluded ? 0 : pct}%;"></div>
            </div>
            ${failuresHtml}${reasoningHtml}${codeHtml}
          </div>`;
      }

      const resA = data.models[modelA] ? data.models[modelA].results[taskKey] : null;
      const resB = data.models[modelB] ? data.models[modelB].results[taskKey] : null;
      container.innerHTML = renderSide(modelA, resA, 'MODEL A') + renderSide(modelB, resB, 'MODEL B');
      renderLineDiff(modelA, modelB, taskKey);
    }

    // ---------- Init ----------
    renderLeaderboard();
    renderDevices();
    if (modelKeys.length > 0) renderModelCards(modelKeys[0]);
    const initialTab = location.hash.slice(1);
    if (TABS.includes(initialTab)) switchTab(initialTab);
  </script>
</body>
</html>"""


if __name__ == "__main__":
    db = Database(ROOT / "bench.db")
    path = generate_html_report(db)
    print(f"Report generated: {path}")
    open_report_in_browser(path)
