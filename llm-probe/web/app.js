/* llm-probe frontend — vanilla JS, no build step */

// ── API helpers ─────────────────────────────────────────────────

async function api(path, opts = {}) {
  const res = await fetch('/api' + path, {
    headers: { 'Content-Type': 'application/json' },
    ...opts,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`${res.status}: ${text}`);
  }
  return res.json();
}

// ── Navigation ──────────────────────────────────────────────────

const navItems = document.querySelectorAll('.nav-item');
const pages = document.querySelectorAll('.page');

function showPage(name) {
  navItems.forEach(n => n.classList.toggle('active', n.dataset.page === name));
  pages.forEach(p => p.classList.toggle('active', p.id === `page-${name}`));
  if (name === 'dashboard') loadDashboard();
  if (name === 'results')   loadResults();
}

navItems.forEach(n => n.addEventListener('click', () => showPage(n.dataset.page)));

// ── LM Studio status ─────────────────────────────────────────────

const dot = document.getElementById('lm-dot');
const statusText = document.getElementById('lm-status-text');

async function checkLMStatus() {
  try {
    const models = await api('/models');
    dot.className = 'status-dot online';
    statusText.textContent = `${models.length} model${models.length !== 1 ? 's' : ''}`;
  } catch {
    dot.className = 'status-dot offline';
    statusText.textContent = 'LM Studio offline';
  }
}

setInterval(checkLMStatus, 10000);

// ── Dashboard ────────────────────────────────────────────────────

async function loadDashboard() {
  try {
    const [rows, results] = await Promise.all([
      api('/leaderboard'),
      api('/results?limit=1000'),
    ]);

    // Stats
    const models = [...new Set(rows.map(r => r.model_id))];
    document.getElementById('stat-models').textContent = models.length || '—';
    document.getElementById('stat-runs').textContent = results.length || '—';

    if (rows.length > 0) {
      // Best model by avg accuracy
      const byModel = {};
      rows.forEach(r => {
        if (!byModel[r.model_id]) byModel[r.model_id] = [];
        byModel[r.model_id].push(r.avg_accuracy ?? 0);
      });
      let bestModel = '—', bestAcc = -1;
      for (const [model, accs] of Object.entries(byModel)) {
        const avg = accs.reduce((a, b) => a + b, 0) / accs.length;
        if (avg > bestAcc) { bestAcc = avg; bestModel = model; }
      }
      document.getElementById('stat-best-model').textContent =
        bestModel.length > 18 ? bestModel.slice(0, 16) + '…' : bestModel;
      document.getElementById('stat-best-acc').textContent =
        bestAcc >= 0 ? (bestAcc * 100).toFixed(0) + '%' : '—';
    }

    renderLeaderboard(rows);
  } catch (e) {
    document.getElementById('leaderboard-content').innerHTML =
      `<div class="empty"><div class="empty-title">Error loading data</div><div class="empty-sub">${e.message}</div></div>`;
  }
}

function renderLeaderboard(rows) {
  const el = document.getElementById('leaderboard-content');
  if (!rows.length) {
    el.innerHTML = `<div class="empty">
      <div class="empty-icon">📊</div>
      <div class="empty-title">No results yet</div>
      <div class="empty-sub">Run some benchmarks to see rankings here</div>
    </div>`;
    return;
  }

  // Group by model for summary rows
  const byModel = {};
  rows.forEach(r => {
    if (!byModel[r.model_id]) byModel[r.model_id] = { pass1: 0, total: 0, acc: [], toks: [] };
    const m = byModel[r.model_id];
    m.pass1 += r.pass_at_1 ? 1 : 0;
    m.total++;
    if (r.avg_accuracy != null) m.acc.push(r.avg_accuracy);
    if (r.avg_tok_per_sec != null) m.toks.push(r.avg_tok_per_sec);
  });

  const modelRows = Object.entries(byModel)
    .map(([model_id, d]) => ({
      model_id,
      pass1_rate: d.pass1 / d.total,
      avg_acc: d.acc.length ? d.acc.reduce((a, b) => a + b) / d.acc.length : null,
      avg_toks: d.toks.length ? d.toks.reduce((a, b) => a + b) / d.toks.length : null,
      tasks: d.total,
    }))
    .sort((a, b) => (b.avg_acc ?? 0) - (a.avg_acc ?? 0));

  let html = `
    <div class="table-wrap">
    <table>
      <thead>
        <tr>
          <th>#</th>
          <th>Model</th>
          <th>Tasks</th>
          <th>pass@1</th>
          <th>Avg Accuracy</th>
          <th>Avg tok/s</th>
        </tr>
      </thead>
      <tbody>`;

  modelRows.forEach((r, i) => {
    const acc = r.avg_acc != null ? (r.avg_acc * 100).toFixed(1) + '%' : '—';
    const toks = r.avg_toks != null ? r.avg_toks.toFixed(1) : '—';
    const pass1Pct = (r.pass1_rate * 100).toFixed(0) + '%';
    const rankColor = i === 0 ? 'color:var(--yellow);font-weight:700' : '';
    html += `
      <tr>
        <td style="${rankColor}">${i + 1}</td>
        <td class="mono">${escHtml(r.model_id)}</td>
        <td><span class="tag">${r.tasks}</span></td>
        <td><span class="badge ${r.pass1_rate > 0.5 ? 'badge-green' : 'badge-yellow'}">${pass1Pct}</span></td>
        <td>
          <div class="accuracy-bar">
            <div class="accuracy-track">
              <div class="accuracy-fill" style="width:${(r.avg_acc ?? 0) * 100}%"></div>
            </div>
            <span style="font-size:12px;min-width:38px;text-align:right">${acc}</span>
          </div>
        </td>
        <td class="mono" style="color:var(--text-dim)">${toks}</td>
      </tr>`;
  });

  html += '</tbody></table></div>';

  // Detail rows
  html += `
    <details style="margin-top:16px">
      <summary style="cursor:pointer;color:var(--text-dim);font-size:12px;padding:4px 0">
        Show all ${rows.length} bench/level rows
      </summary>
      <div class="table-wrap" style="margin-top:12px">
      <table>
        <thead>
          <tr>
            <th>Model</th><th>Bench</th><th>Level</th>
            <th>Attempts</th><th>pass@1</th><th>Avg Acc</th><th>tok/s</th>
          </tr>
        </thead>
        <tbody>`;
  rows.forEach(r => {
    const acc = r.avg_accuracy != null ? (r.avg_accuracy * 100).toFixed(1) + '%' : '—';
    const toks = r.avg_tok_per_sec != null ? r.avg_tok_per_sec.toFixed(1) : '—';
    html += `<tr>
      <td class="mono" style="font-size:11px">${escHtml(r.model_id)}</td>
      <td><span class="badge badge-blue">${r.bench_id}</span></td>
      <td><span class="tag">${r.level_id.toUpperCase()}</span></td>
      <td>${r.attempts}</td>
      <td><span class="badge ${r.pass_at_1 ? 'badge-green' : 'badge-red'}">${r.pass_at_1 ? 'YES' : 'NO'}</span></td>
      <td>${acc}</td>
      <td class="mono" style="color:var(--text-dim)">${toks}</td>
    </tr>`;
  });
  html += '</tbody></table></div></details>';

  el.innerHTML = html;
}

// ── Run page ─────────────────────────────────────────────────────

async function loadRunPage() {
  await Promise.all([loadModels(), loadBenchmarks()]);
}

async function loadModels() {
  const sel = document.getElementById('model-select');
  try {
    const models = await api('/models');
    if (!models.length) {
      sel.innerHTML = '<option value="">No models loaded in LM Studio</option>';
      return;
    }
    sel.innerHTML = models.map(m =>
      `<option value="${escHtml(m.id)}">${escHtml(m.id)}</option>`
    ).join('');
  } catch {
    sel.innerHTML = '<option value="">LM Studio offline</option>';
  }
}

async function loadBenchmarks() {
  const container = document.getElementById('bench-checks');
  const filterSel = document.getElementById('filter-bench');
  try {
    const benches = await api('/benchmarks');
    container.innerHTML = benches.map(b => `
      <label class="checkbox-item">
        <input type="checkbox" name="bench" value="${b.id}" checked />
        <span>${b.name} <span class="tag">${b.levels}</span></span>
      </label>`).join('');

    filterSel.innerHTML = '<option value="">All benchmarks</option>' +
      benches.map(b => `<option value="${b.id}">${b.name}</option>`).join('');
  } catch {
    container.innerHTML = '<div class="log-err">Could not load benchmarks</div>';
  }
}

document.getElementById('refresh-models-btn').addEventListener('click', loadModels);

// ── SSE Run ──────────────────────────────────────────────────────

let activeSSE = null;

document.getElementById('start-btn').addEventListener('click', startRun);
document.getElementById('stop-btn').addEventListener('click', stopRun);

async function startRun() {
  const modelId = document.getElementById('model-select').value;
  if (!modelId) { alert('Select a model first'); return; }

  const benchIds = [...document.querySelectorAll('[name=bench]:checked')].map(el => el.value);
  if (!benchIds.length) { alert('Select at least one benchmark'); return; }

  const levels = [...document.querySelectorAll('[name=level]:checked')].map(el => el.value);
  if (!levels.length) { alert('Select at least one level'); return; }

  const k = parseInt(document.getElementById('k-input').value) || 3;
  const evalTimeout = parseFloat(document.getElementById('timeout-input').value) || 5;

  // Reset UI
  const log = document.getElementById('progress-log');
  log.innerHTML = '';
  document.getElementById('progress-bar').style.width = '0%';
  document.getElementById('progress-section').style.display = 'block';
  document.getElementById('start-btn').disabled = true;
  document.getElementById('stop-btn').style.display = 'inline-flex';
  document.getElementById('run-status').textContent = 'Starting…';

  // Build SSE URL with params
  const params = new URLSearchParams({
    model_id: modelId,
    k: k,
    eval_timeout: evalTimeout,
  });
  benchIds.forEach(b => params.append('bench_ids', b));
  levels.forEach(l => params.append('levels', l));

  // Kick off POST first to get chain_id (for background tracking)
  let totalJobs = '?';
  try {
    const resp = await api('/run', {
      method: 'POST',
      body: JSON.stringify({
        model_id: modelId,
        bench_ids: benchIds,
        levels: levels,
        k: k,
        eval_timeout: evalTimeout,
      }),
    });
    totalJobs = resp.total_jobs;
    logLine(log, `Started chain: ${totalJobs} jobs`, 'info');
    document.getElementById('progress-count').textContent = `0 / ${totalJobs}`;
  } catch (e) {
    logLine(log, `Failed to start: ${e.message}`, 'err');
    resetRunUI();
    return;
  }

  // Stream via SSE
  const sseUrl = `/api/run/stream?${params}`;
  activeSSE = new EventSource(sseUrl);
  let done = 0;

  activeSSE.onmessage = (e) => {
    const data = JSON.parse(e.data);
    if (data.done) {
      logLine(log, `\nChain complete! ${done} jobs processed.`, 'ok');
      stopRun();
      loadDashboard();
      return;
    }

    done++;
    const pct = totalJobs !== '?' ? (done / totalJobs * 100).toFixed(0) : 0;
    document.getElementById('progress-bar').style.width = pct + '%';
    document.getElementById('progress-count').textContent = `${done} / ${totalJobs}`;
    document.getElementById('progress-label').textContent = data.label || '';

    const icon = data.status === 'ok' ? '✓' : '✗';
    const cls = data.status === 'ok' ? 'ok' : (data.status === 'llm_error' ? 'err' : 'warn');
    const pct_str = data.total_tests ? `${data.passed}/${data.total_tests}` : '';
    const speed = data.tok_per_sec ? ` · ${data.tok_per_sec.toFixed(1)} tok/s` : '';
    const err = data.error ? ` · ${data.error}` : '';
    logLine(log, `[${done}/${totalJobs}] ${icon} ${data.label}  ${pct_str}${speed}${err}`, cls);
  };

  activeSSE.onerror = () => {
    if (activeSSE?.readyState === EventSource.CLOSED) return; // normal close
    logLine(log, 'Connection lost — server may have finished', 'warn');
    stopRun();
  };
}

function stopRun() {
  if (activeSSE) { activeSSE.close(); activeSSE = null; }
  resetRunUI();
}

function resetRunUI() {
  document.getElementById('start-btn').disabled = false;
  document.getElementById('stop-btn').style.display = 'none';
  document.getElementById('run-status').textContent = '';
}

function logLine(el, text, cls = 'dim') {
  const div = document.createElement('div');
  div.className = `log-${cls}`;
  div.textContent = text;
  el.appendChild(div);
  el.scrollTop = el.scrollHeight;
}

// ── Results page ─────────────────────────────────────────────────

document.getElementById('filter-btn').addEventListener('click', loadResults);

async function loadResults() {
  const modelFilter = document.getElementById('filter-model').value.trim();
  const benchFilter = document.getElementById('filter-bench').value;

  const params = new URLSearchParams({ limit: 200 });
  if (modelFilter) params.set('model_id', modelFilter);
  if (benchFilter) params.set('bench_id', benchFilter);

  const el = document.getElementById('results-content');
  el.innerHTML = '<div class="log-dim" style="padding:16px">Loading…</div>';

  try {
    const rows = await api('/results?' + params);
    renderResults(rows);
  } catch (e) {
    el.innerHTML = `<div class="log-err" style="padding:16px">Error: ${e.message}</div>`;
  }
}

function renderResults(rows) {
  const el = document.getElementById('results-content');
  if (!rows.length) {
    el.innerHTML = `<div class="empty">
      <div class="empty-icon">📋</div>
      <div class="empty-title">No results found</div>
    </div>`;
    return;
  }

  let html = `<div class="table-wrap"><table>
    <thead><tr>
      <th>Model</th><th>Bench</th><th>Level</th><th>Attempt</th>
      <th>Result</th><th>Status</th><th>tok/s</th><th>Date</th>
    </tr></thead><tbody>`;

  rows.forEach(r => {
    const pct = r.passed != null && r.total ? `${r.passed}/${r.total}` : '—';
    const acc = r.passed != null && r.total ? (r.passed / r.total * 100).toFixed(0) + '%' : '';
    const toks = r.tok_per_sec != null ? r.tok_per_sec.toFixed(1) : '—';
    const date = r.created_at ? new Date(r.created_at).toLocaleString() : '—';
    const statusBadge = {
      ok: '<span class="badge badge-green">ok</span>',
      llm_error: '<span class="badge badge-red">llm error</span>',
      eval_error: '<span class="badge badge-yellow">eval error</span>',
      save_error: '<span class="badge badge-red">save error</span>',
      no_code: '<span class="badge badge-yellow">no code</span>',
    }[r.status] ?? `<span class="badge">${r.status}</span>`;

    html += `<tr>
      <td class="mono" style="font-size:11px;max-width:160px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${escHtml(r.model_id)}</td>
      <td><span class="badge badge-blue">${r.bench_id}</span></td>
      <td><span class="tag">${r.level_id.toUpperCase()}</span></td>
      <td style="color:var(--text-dim)">${r.attempt}</td>
      <td>${pct} <span style="color:var(--text-dimmer);font-size:11px">${acc}</span></td>
      <td>${statusBadge}</td>
      <td class="mono" style="color:var(--text-dim)">${toks}</td>
      <td style="color:var(--text-dimmer);font-size:11px;white-space:nowrap">${date}</td>
    </tr>`;
  });

  html += '</tbody></table></div>';
  el.innerHTML = html;
}

// ── Utilities ────────────────────────────────────────────────────

function escHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

// ── Init ─────────────────────────────────────────────────────────

async function init() {
  await checkLMStatus();
  await loadRunPage();
  await loadDashboard();
}

init();
