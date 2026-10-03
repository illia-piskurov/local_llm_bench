"""Unified interactive HTML dashboard for local LLM benchmark.

Combines:
1. 🏆 General quality leaderboard (accuracy, average score, tests).
2. ⚡ Speed comparison across devices (Hardware Matrix: M4 vs ThinkPad vs i5).
3. 🔍 Model deep-dive (cards for 8 benchmarks, generated code, errors).

Works fully offline in any browser, without external CDN or npm.
"""

import html
import webbrowser
from datetime import datetime
from pathlib import Path

from database import Database
from report_data import load_report_data

ROOT = Path(__file__).parent


def generate_html_report(db: Database, output_path: Path = ROOT / "report.html", sync_records: bool = True) -> Path:
    if sync_records:
        try:
            from sync import sync_db_and_records

            sync_db_and_records(db)
        except Exception:
            pass

    data = load_report_data(db)
    leaderboard = data.leaderboard
    runs_data = data.runs_data
    active_hosts = data.active_hosts
    device_stats = data.device_stats
    model_host_matrix = data.model_host_matrix
    client_json = data.client_json
    runs_table_rows = data.runs_table_rows
    total_tests_count = data.total_tests_count
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Build HTML
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Local LLM Benchmark Unified Dashboard</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    :root {{
      --bg: #0d1117;
      --card-bg: #161b22;
      --card-border: #30363d;
      --text: #c9d1d9;
      --text-muted: #8b949e;
      --accent: #58a6ff;
      --green: #3fb950;
      --yellow: #d29922;
      --red: #f85149;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background-color: var(--bg);
      color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      line-height: 1.5;
      padding: 24px;
    }}
    .container {{ max-width: 1350px; margin: 0 auto; }}
    header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-bottom: 20px;
      border-bottom: 1px solid var(--card-border);
      margin-bottom: 24px;
    }}
    h1 {{ font-size: 24px; font-weight: 600; color: #f0f6fc; }}
    .subtitle {{ color: var(--text-muted); font-size: 14px; margin-top: 4px; }}
    .badge {{
      display: inline-block;
      padding: 2px 8px;
      font-size: 12px;
      font-weight: 500;
      border-radius: 12px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }}
    .lang-python {{ background: #2b5b84; color: #fff; }}
    .lang-c {{ background: #444; color: #fff; }}
    .lang-javascript {{ background: #b89b14; color: #fff; }}
    .lang-lua {{ background: #0000aa; color: #fff; }}

    .score-pill {{
      display: inline-block;
      padding: 3px 10px;
      border-radius: 12px;
      font-weight: 600;
      font-size: 13px;
    }}
    .score-green {{ background: rgba(63, 185, 80, 0.2); color: var(--green); border: 1px solid var(--green); }}
    .score-yellow {{ background: rgba(210, 153, 34, 0.2); color: var(--yellow); border: 1px solid var(--yellow); }}
    .score-red {{ background: rgba(248, 81, 73, 0.2); color: var(--red); border: 1px solid var(--red); }}

    .tabs {{ display: flex; gap: 12px; margin-bottom: 20px; }}
    .tab-btn {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      color: var(--text);
      padding: 10px 18px;
      border-radius: 6px;
      cursor: pointer;
      font-weight: 600;
      font-size: 14px;
      transition: all 0.15s ease;
    }}
    .tab-btn:hover {{ border-color: var(--accent); }}
    .tab-btn.active {{
      background: var(--accent);
      color: #0d1117;
      border-color: var(--accent);
    }}

    .section {{ margin-bottom: 36px; }}
    .section-title {{
      font-size: 18px;
      color: #f0f6fc;
      margin-bottom: 14px;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }}

    /* Table */
    table {{ width: 100%; border-collapse: collapse; background: var(--card-bg); border-radius: 8px; overflow: hidden; border: 1px solid var(--card-border); }}
    th, td {{ padding: 11px 14px; text-align: left; font-size: 14px; border-bottom: 1px solid var(--card-border); }}
    th {{ background: #1f242c; color: var(--text-muted); font-weight: 600; }}
    tr:hover td {{ background: rgba(255, 255, 255, 0.02); }}

    /* Cards Grid */
    .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(380px, 1fr)); gap: 16px; }}
    .device-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px; margin-bottom: 24px; }}
    .card {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 8px;
      padding: 16px;
    }}
    .card-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;
      padding-bottom: 8px;
      border-bottom: 1px solid var(--card-border);
    }}
    .card-title {{ font-weight: 600; color: #f0f6fc; font-size: 15px; }}

    .level-row {{
      margin-bottom: 12px;
      padding-bottom: 8px;
      border-bottom: 1px dashed rgba(255,255,255,0.06);
    }}
    .level-row:last-child {{ border-bottom: none; margin-bottom: 0; padding-bottom: 0; }}
    .level-meta {{ display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 4px; }}

    .progress-bar {{
      height: 6px;
      background: rgba(255,255,255,0.1);
      border-radius: 3px;
      overflow: hidden;
      margin-bottom: 6px;
    }}
    .progress-fill {{ height: 100%; }}
    .fill-green {{ background: var(--green); }}
    .fill-yellow {{ background: var(--yellow); }}
    .fill-red {{ background: var(--red); }}

    .code-box {{
      margin-top: 8px;
      background: #090d12;
      border: 1px solid var(--card-border);
      border-radius: 6px;
      padding: 8px 12px;
      font-size: 12px;
    }}
    .code-box summary {{ cursor: pointer; color: var(--accent); outline: none; font-weight: 500; }}
    .code-box pre {{
      margin-top: 8px;
      max-height: 280px;
      overflow-y: auto;
      color: #e6edf3;
      font-family: Consolas, monospace;
      white-space: pre-wrap;
    }}

    .failures-list {{
      margin-top: 4px;
      padding-left: 18px;
      color: var(--red);
      font-size: 12px;
    }}

    select.model-picker {{
      background: var(--card-bg);
      border: 1px solid var(--accent);
      color: #f0f6fc;
      padding: 6px 12px;
      border-radius: 6px;
      font-size: 14px;
      font-weight: 500;
      cursor: pointer;
    }}

    .speed-tag {{
      font-weight: 600;
      color: #58a6ff;
    }}
    .speed-fastest {{
      color: #3fb950;
      font-weight: 700;
    }}
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div>
        <h1>🚀 Local LLM Unified Dashboard</h1>
        <div class="subtitle">Quality, speed, and hardware comparison | Updated: {now_str}</div>
      </div>
      <div>
        <span class="badge" style="background:#238636; color:#fff; padding:6px 12px; font-size:13px;">
          Models: {len(leaderboard)} | Devices: {len(active_hosts)} | Tests: {total_tests_count}
        </span>
      </div>
    </header>

    <div class="tabs">
      <button class="tab-btn active" onclick="switchTab('leaderboard')">🏆 1. Leaderboard</button>
      <button class="tab-btn" onclick="switchTab('devices')">⚡ 2. Hardware Matrix</button>
      <button class="tab-btn" onclick="switchTab('model-view')">🔍 3. Model Deep-Dive & Code</button>
      <button class="tab-btn" onclick="switchTab('diff-view')">🔀 4. Model Comparison (Diff)</button>
      <button class="tab-btn" onclick="switchTab('runs-view')">📜 5. Run History</button>
    </div>


    <!-- TAB 1: LEADERBOARD -->
    <div id="tab-leaderboard" class="section">
      <div class="section-title">
        <span>Model ranking by generation quality</span>
        <input type="text" id="search-input" placeholder="Search model..." oninput="filterTable('leaderboard-table', 1)" style="background:#161b22; border:1px solid #30363d; color:#fff; padding:6px 12px; border-radius:6px; font-size:13px; width: 240px;">
      </div>
      <table id="leaderboard-table">
        <thead>
          <tr>
            <th style="width: 45px;">#</th>
            <th>Model</th>
            <th>Average Score</th>
            <th>Checks Passed</th>
            <th>Tasks Completed</th>
            <th>Speed (avg)</th>
            <th>Details</th>
          </tr>
        </thead>
        <tbody>"""

    for i, entry in enumerate(leaderboard, start=1):
        m = entry["model"]
        avg_pct = entry["avg_pct"]
        pill_cls = "score-green" if avg_pct >= 80 else "score-yellow" if avg_pct >= 40 else "score-red"
        speed_str = f"{entry['avg_speed']:.1f} tok/s" if entry["avg_speed"] else "—"

        think_badge = ""
        if entry.get("total_reasoning_tokens") and entry["total_reasoning_tokens"] > 0:
            think_badge = f' <span class="badge" style="background:rgba(137,87,229,0.2); color:#d2a8ff; border:1px solid rgba(137,87,229,0.4);" title="{entry["total_reasoning_tokens"]} reasoning tokens">🧠 Thinker</span>'

        html_content += f"""
          <tr>
            <td style="font-weight:600; color:var(--text-muted);">{i}</td>
            <td style="font-weight:600; color:#f0f6fc;">{html.escape(m)}{think_badge}</td>
            <td><span class="score-pill {pill_cls}">{avg_pct:.1f}%</span></td>
            <td>{entry["passed"]} / {entry["total"]}</td>
            <td>{entry["tests_count"]} tasks</td>
            <td style="color:var(--text-muted); font-weight:500;">{speed_str}</td>
            <td><a href="#model-view" data-model="{html.escape(m)}" onclick="selectModel(this.dataset.model)" style="color:var(--accent); text-decoration:none; font-size:13px; font-weight:500;">Details →</a></td>
          </tr>"""

    html_content += """
        </tbody>
      </table>
    </div>

    <!-- TAB 2: HARDWARE SPEED MATRIX -->
    <div id="tab-devices" class="section" style="display:none;">
      <div class="section-title">
        <span>Device Performance Profile (Generation Speed tok/s)</span>
      </div>

      <div class="device-grid">"""

    # Device summary cards
    for h in active_hosts:
        d_info = device_stats[h["id"]]
        avg_dev_speed = (sum(d_info["tps_list"]) / len(d_info["tps_list"])) if d_info["tps_list"] else 0.0
        html_content += f"""
        <div class="card" style="border-top: 3px solid var(--accent);">
          <div style="font-weight:600; font-size:15px; color:#f0f6fc; margin-bottom:6px;">{html.escape(h["label"])}</div>
          <div style="display:flex; justify-content:space-between; align-items:flex-end;">
            <div>
              <div style="font-size:26px; font-weight:700; color:#58a6ff;">{avg_dev_speed:.1f} <span style="font-size:14px; font-weight:400; color:var(--text-muted);">tok/s</span></div>
              <div style="font-size:12px; color:var(--text-muted);">average speed</div>
            </div>
            <div style="font-size:12px; color:var(--text-muted); text-align:right;">
              <strong>{d_info["count"]}</strong> samples
            </div>
          </div>
        </div>"""

    html_content += """
      </div>

      <div class="section-title" style="margin-top:28px;">
        <span>Model comparison across laptops and PCs (Matrix: Model × Device)</span>
        <input type="text" id="device-search-input" placeholder="Filter models..." oninput="filterTable('devices-table', 0)" style="background:#161b22; border:1px solid #30363d; color:#fff; padding:6px 12px; border-radius:6px; font-size:13px; width: 240px;">
      </div>

      <table id="devices-table">
        <thead>
          <tr>
            <th>Model</th>"""

    for h in active_hosts:
        html_content += f"<th>{html.escape(h['label'])}</th>"

    html_content += """
          </tr>
        </thead>
        <tbody>"""

    for m in sorted(model_host_matrix.keys()):
        html_content += f"<tr><td style='font-weight:600; color:#f0f6fc;'>{html.escape(m)}</td>"

        # Find max speed for this model for highlighting
        max_tps = 0.0
        for h in active_hosts:
            v = model_host_matrix[m].get(h["id"])
            if v and v["tps"] and v["tps"] > max_tps:
                max_tps = v["tps"]

        for h in active_hosts:
            val = model_host_matrix[m].get(h["id"])
            if val and val["tps"]:
                tps = val["tps"]
                ttft = val["ttft"]
                is_fastest = (len(model_host_matrix[m]) > 1) and (abs(tps - max_tps) < 0.01)
                cls = "speed-fastest" if is_fastest else "speed-tag"
                badge_fast = " 🏆" if is_fastest else ""
                html_content += f"""
                  <td>
                    <span class="{cls}">{tps:.1f} tok/s{badge_fast}</span>
                    <span style="font-size:12px; color:var(--text-muted); display:block;">TTFT: {ttft:.2f}s ({val["count"]} runs)</span>
                  </td>"""
            else:
                html_content += "<td><span style='color:var(--text-muted);'>—</span></td>"

        html_content += "</tr>"

    html_content += f"""
        </tbody>
      </table>
    </div>

    <!-- TAB 3: MODEL DEEP-DIVE -->
    <div id="tab-model-view" class="section" style="display:none;">
      <div class="section-title">
        <div style="display:flex; align-items:center; gap:12px;">
          <span>Model Engineering Profile:</span>
          <select id="model-select" class="model-picker" onchange="onModelSelectChange()">
          </select>
        </div>
        <div id="model-summary-badges"></div>
      </div>

      <div id="benchmarks-grid" class="grid">
        <!-- Rendered via JS -->
      </div>
    </div>

    <!-- TAB 4: SIDE-BY-SIDE DIFF -->
    <div id="tab-diff-view" class="section" style="display:none;">
      <div class="card" style="margin-bottom:20px; border-left: 4px solid var(--accent);">
        <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap:16px; align-items:center;">
          <div>
            <label style="display:block; font-size:12px; color:var(--text-muted); margin-bottom:6px; font-weight:600;">MODEL A (Left):</label>
            <select id="diff-model-a" class="model-picker" style="width:100%;" onchange="renderDiff()">
            </select>
          </div>
          <div>
            <label style="display:block; font-size:12px; color:var(--text-muted); margin-bottom:6px; font-weight:600;">MODEL B (Right):</label>
            <select id="diff-model-b" class="model-picker" style="width:100%;" onchange="renderDiff()">
            </select>
          </div>
          <div>
            <label style="display:block; font-size:12px; color:var(--text-muted); margin-bottom:6px; font-weight:600;">TASK / LEVEL:</label>
            <select id="diff-task" class="model-picker" style="width:100%;" onchange="renderDiff()">
            </select>
          </div>
        </div>
      </div>

      <div id="diff-container" style="display:grid; grid-template-columns: repeat(auto-fit, minmax(420px, 1fr)); gap:16px;">
        <!-- Left: Model A | Right: Model B -->
      </div>
    </div>

    <!-- TAB 5: RUN HISTORY -->
    <div id="tab-runs-view" class="section" style="display:none;">
      <div class="section-title">
        <span>Execution Sessions & Benchmark Runs ({len(runs_data)} total runs)</span>
        <input type="text" id="runs-search-input" placeholder="Search by model, host, quant..." oninput="filterRunsTable()" style="background:#161b22; border:1px solid #30363d; color:#fff; padding:6px 12px; border-radius:6px; font-size:13px; width: 280px;">
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
            <th>Hyperparameters & Artifact</th>
            <th>Tests</th>
            <th>Avg Score</th>
            <th>Avg Speed</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {runs_table_rows}
        </tbody>
      </table>
    </div>
  </div>

  <script>
    const data = {client_json};

    function switchTab(tab) {{
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.getElementById('tab-leaderboard').style.display = 'none';
      document.getElementById('tab-devices').style.display = 'none';
      document.getElementById('tab-model-view').style.display = 'none';
      document.getElementById('tab-diff-view').style.display = 'none';
      document.getElementById('tab-runs-view').style.display = 'none';

      if (tab === 'leaderboard') {{
        document.querySelector("button[onclick*='leaderboard']").classList.add('active');
        document.getElementById('tab-leaderboard').style.display = 'block';
      }} else if (tab === 'devices') {{
        document.querySelector("button[onclick*='devices']").classList.add('active');
        document.getElementById('tab-devices').style.display = 'block';
      }} else if (tab === 'model-view') {{
        document.querySelector("button[onclick*='model-view']").classList.add('active');
        document.getElementById('tab-model-view').style.display = 'block';
      }} else if (tab === 'diff-view') {{
        document.querySelector("button[onclick*='diff-view']").classList.add('active');
        document.getElementById('tab-diff-view').style.display = 'block';
        renderDiff();
      }} else if (tab === 'runs-view') {{
        document.querySelector("button[onclick*='runs-view']").classList.add('active');
        document.getElementById('tab-runs-view').style.display = 'block';
      }}
    }}

    function filterRunsTable() {{
      const query = document.getElementById('runs-search-input').value.toLowerCase();
      const rows = document.querySelectorAll('#runs-table tbody tr');
      rows.forEach(r => {{
        const text = r.innerText.toLowerCase();
        r.style.display = text.includes(query) ? '' : 'none';
      }});
    }}


    function filterTable(tableId, colIdx) {{
      const inputId = tableId === 'leaderboard-table' ? 'search-input' : 'device-search-input';
      const query = document.getElementById(inputId).value.toLowerCase();
      const rows = document.querySelectorAll('#' + tableId + ' tbody tr');
      rows.forEach(r => {{
        const text = r.children[colIdx].innerText.toLowerCase();
        r.style.display = text.includes(query) ? '' : 'none';
      }});
    }}

    // Populate model select
    const select = document.getElementById('model-select');
    const modelKeys = Object.keys(data.models);
    modelKeys.forEach(m => {{
      const opt = document.createElement('option');
      opt.value = m;
      opt.textContent = m;
      select.appendChild(opt);
    }});

    function selectModel(modelKey) {{
      select.value = modelKey;
      switchTab('model-view');
      renderModelCards(modelKey);
    }}

    function onModelSelectChange() {{
      renderModelCards(select.value);
    }}

    function escapeHtml(str) {{
      if (!str) return '';
      return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    }}

    function renderModelCards(modelKey) {{
      const mData = data.models[modelKey];
      const grid = document.getElementById('benchmarks-grid');
      grid.innerHTML = '';

      if (!mData) {{
        grid.innerHTML = '<p style="color:var(--text-muted);">No data available</p>';
        return;
      }}

      // Summary
      const summaryDiv = document.getElementById('model-summary-badges');
      const pillCls = mData.avg_pct >= 80 ? 'score-green' : mData.avg_pct >= 40 ? 'score-yellow' : 'score-red';
      summaryDiv.innerHTML = `
        <span class="score-pill ${{pillCls}}">${{mData.avg_pct}}% average score</span>
        <span style="font-size:13px; color:var(--text-muted); margin-left:8px;">${{mData.passed}}/${{mData.total}} checks</span>
        ${{mData.avg_speed ? `<span style="font-size:13px; color:var(--text-muted); margin-left:8px;">• ${{mData.avg_speed}} tok/s</span>` : ''}}
      `;

      data.benchmarks.forEach(b => {{
        const card = document.createElement('div');
        card.className = 'card';

        let levelsHtml = '';
        let bPassed = 0;
        let bTotal = 0;
        let hasAny = false;

        b.levels.forEach(l => {{
          const key = b.id + '/' + l.id;
          const r = mData.results[key];

          if (r) {{
            hasAny = true;
            if (!r.is_infra) {{
              bPassed += r.passed;
              bTotal += r.total;
            }}
            const pct = r.percent;
            const fillCls = r.is_infra ? 'fill-yellow' : (pct >= 80 ? 'fill-green' : pct >= 40 ? 'fill-yellow' : 'fill-red');

            let failuresHtml = '';
            if (r.failures && r.failures.length > 0) {{
              failuresHtml = '<ul class="failures-list">' + r.failures.map(f => '<li>' + escapeHtml(f) + '</li>').join('') + '</ul>';
            }}

            let reasoningHtml = '';
            if (r.reasoning_text) {{
              reasoningHtml = `
                <details class="code-box" style="border-color: rgba(137, 87, 229, 0.4); margin-top: 6px;">
                  <summary style="color:#d2a8ff; font-weight:600;">🧠 Reasoning trace (Reasoning${{r.reasoning_tokens ? ' • ' + r.reasoning_tokens + ' tokens' : ''}})</summary>
                  <pre style="color:#e1d9f5; font-size:12px;"><code>${{escapeHtml(r.reasoning_text)}}</code></pre>
                </details>
              `;
            }} else if (r.reasoning_tokens) {{
              reasoningHtml = `<div style="font-size:12px; color:#d2a8ff; margin-top:4px;">🧠 ${{r.reasoning_tokens}} reasoning tokens</div>`;
            }}

            let codeHtml = '';
            if (r.code) {{
              codeHtml = `
                <details class="code-box">
                  <summary>📄 Code (${{r.lines}} lines) ${{r.tok_per_sec ? '• ' + r.tok_per_sec + ' tok/s' : ''}}</summary>
                  <pre><code>${{escapeHtml(r.code)}}</code></pre>
                </details>
              `;
            }}

            let scoreMeta = '';
            if (r.is_infra) {{
              const isTrunc = r.failures && r.failures[0] && r.failures[0].startsWith('[TRUNCATED]');
              const tagText = isTrunc ? '✂️ truncated' : '⚠️ infra failure';
              scoreMeta = `<span style="color:#e3b341; font-weight:600; font-size:12px;">${{tagText}}</span>`;
            }} else {{
              scoreMeta = `<span><strong>${{r.passed}}/${{r.total}}</strong> (${{pct}}%)</span>`;
            }}

            levelsHtml += `
              <div class="level-row">
                <div class="level-meta">
                  <span style="font-weight:500;">${{l.name}}</span>
                  ${{scoreMeta}}
                </div>
                <div class="progress-bar">
                  <div class="progress-fill ${{fillCls}}" style="width: ${{r.is_infra ? 0 : pct}}%;"></div>
                </div>
                ${{failuresHtml}}
                ${{reasoningHtml}}
                ${{codeHtml}}
              </div>
            `;

          }} else {{
            levelsHtml += `
              <div class="level-row" style="opacity: 0.5;">
                <div class="level-meta">
                  <span>${{l.name}}</span>
                  <span style="color:var(--text-muted);">not tested</span>
                </div>
              </div>
            `;
          }}
        }});

        const bPct = bTotal > 0 ? (bPassed / bTotal * 100).toFixed(0) : '—';
        const bPillCls = bTotal > 0 ? (bPct >= 80 ? 'score-green' : bPct >= 40 ? 'score-yellow' : 'score-red') : '';

        card.innerHTML = `
          <div class="card-header">
            <div>
              <div class="card-title">${{b.name}}</div>
              <span class="badge lang-${{b.lang}}">${{b.lang}}</span>
            </div>
            ${{hasAny ? `<span class="score-pill ${{bPillCls}}">${{bPct}}%</span>` : '<span style="font-size:12px; color:var(--text-muted);">—</span>'}}
          </div>
          <div>${{levelsHtml}}</div>
        `;

        grid.appendChild(card);
      }});
    }}

    // Default select first model
    if (modelKeys.length > 0) {{
      selectModel(modelKeys[0]);
    }}

    // Diff Dropdowns & Logic
    const diffModelA = document.getElementById('diff-model-a');
    const diffModelB = document.getElementById('diff-model-b');
    const diffTask = document.getElementById('diff-task');

    modelKeys.forEach((m, idx) => {{
      const optA = document.createElement('option');
      optA.value = m;
      optA.textContent = m;
      diffModelA.appendChild(optA);

      const optB = document.createElement('option');
      optB.value = m;
      optB.textContent = m;
      diffModelB.appendChild(optB);
    }});

    if (modelKeys.length > 0) diffModelA.value = modelKeys[0];
    if (modelKeys.length > 1) diffModelB.value = modelKeys[1];
    else if (modelKeys.length > 0) diffModelB.value = modelKeys[0];

    data.benchmarks.forEach(b => {{
      const grp = document.createElement('optgroup');
      grp.label = b.short + ' (' + b.lang + ')';
      b.levels.forEach(l => {{
        const opt = document.createElement('option');
        opt.value = b.id + '/' + l.id;
        opt.textContent = b.short + ' / ' + l.name;
        grp.appendChild(opt);
      }});
      diffTask.appendChild(grp);
    }});

    function openDiff(modelA, modelB, taskKey) {{
      if (modelA) diffModelA.value = modelA;
      if (modelB) diffModelB.value = modelB;
      if (taskKey) diffTask.value = taskKey;
      switchTab('diff-view');
      renderDiff();
    }}

    function renderDiff() {{
      const modelA = diffModelA.value;
      const modelB = diffModelB.value;
      const taskKey = diffTask.value;
      const container = document.getElementById('diff-container');

      if (!modelA || !modelB || !taskKey) {{
        container.innerHTML = '<p style="color:var(--text-muted); padding:20px;">Select models and task to compare.</p>';
        return;
      }}

      function renderSide(modelKey, res, label) {{
        if (!res) {{
          return `
            <div class="card" style="border-top:3px solid #30363d;">
              <div class="card-header">
                <div>
                  <span class="badge" style="background:#21262d; color:#8b949e; margin-bottom:4px; display:inline-block;">${{label}}</span>
                  <div class="card-title">${{escapeHtml(modelKey)}}</div>
                </div>
                <span class="score-pill" style="background:#21262d; color:#8b949e;">not tested</span>
              </div>
              <p style="color:var(--text-muted); font-size:13px; margin:30px 0; text-align:center;">
                This level was not run for model ${{escapeHtml(modelKey)}}.
              </p>
            </div>
          `;
        }}

        const pct = res.percent;
        let pillHtml = '';
        if (res.is_infra) {{
          const isTrunc = res.failures && res.failures[0] && res.failures[0].startsWith('[TRUNCATED]');
          const tagText = isTrunc ? '✂️ truncated' : '⚠️ infra failure';
          pillHtml = `<span class="score-pill" style="background:rgba(210,153,34,0.2); color:#e3b341; border:1px solid rgba(210,153,34,0.4);">${{tagText}}</span>`;
        }} else {{
          const pillCls = pct >= 80 ? 'score-green' : pct >= 40 ? 'score-yellow' : 'score-red';
          pillHtml = `<span class="score-pill ${{pillCls}}">${{res.passed}}/${{res.total}} (${{pct}}%)</span>`;
        }}
        const fillCls = res.is_infra ? 'fill-yellow' : (pct >= 80 ? 'fill-green' : pct >= 40 ? 'fill-yellow' : 'fill-red');
        const borderColor = res.is_infra ? 'var(--yellow)' : (pct >= 80 ? 'var(--green)' : pct >= 40 ? 'var(--yellow)' : 'var(--red)');

        let speedBadge = '';
        if (res.tok_per_sec) {{
          speedBadge += `<span class="speed-tag">${{res.tok_per_sec}} tok/s</span>`;
        }}
        if (res.ttft) {{
          speedBadge += `<span style="font-size:12px; color:var(--text-muted); margin-left:6px;">TTFT: ${{res.ttft}}s</span>`;
        }}
        if (res.reasoning_tokens) {{
          speedBadge += `<span style="font-size:12px; color:#d2a8ff; margin-left:8px;">🧠 ${{res.reasoning_tokens}} think tok</span>`;
        }}

        let failuresHtml = '';
        if (res.failures && res.failures.length > 0) {{
          const failTitle = res.is_infra ? '⚠️ Infrastructure error / Truncated:' : `❌ Failed tests (${{res.failures.length}}):`;
          failuresHtml = `
            <div style="background:rgba(248,81,73,0.08); border:1px solid rgba(248,81,73,0.3); border-radius:6px; padding:10px 14px; margin: 12px 0;">
              <strong style="color:var(--red); font-size:13px;">${{failTitle}}</strong>
              <ul class="failures-list" style="margin-top:6px;">
                ${{res.failures.map(f => '<li>' + escapeHtml(f) + '</li>').join('')}}
              </ul>
            </div>
          `;
        }}

        let reasoningHtml = '';
        if (res.reasoning_text) {{
          reasoningHtml = `
            <details class="code-box" style="border-color: rgba(137,87,229,0.4); margin-bottom:12px;" open>
              <summary style="color:#d2a8ff; font-weight:600;">🧠 Reasoning trace (Reasoning${{res.reasoning_tokens ? ' • ' + res.reasoning_tokens + ' tokens' : ''}})</summary>
              <pre style="color:#e1d9f5; font-size:12px; max-height:260px;"><code>${{escapeHtml(res.reasoning_text)}}</code></pre>
            </details>
          `;
        }}

        let codeHtml = '';
        if (res.code) {{
          codeHtml = `
            <div style="margin-top:10px;">
              <div style="display:flex; justify-content:space-between; font-size:12px; color:var(--text-muted); margin-bottom:6px;">
                <span>📄 Generated code (${{res.lines}} lines)</span>
                <span>Language: ${{res.ext}}</span>
              </div>
              <pre style="background:#090d12; border:1px solid var(--card-border); border-radius:6px; padding:12px; max-height:480px; overflow-y:auto; color:#e6edf3; font-family:Consolas, monospace; font-size:12px; white-space:pre-wrap;"><code>${{escapeHtml(res.code)}}</code></pre>
            </div>
          `;
        }} else {{
          codeHtml = `<p style="color:var(--text-muted); font-size:13px; margin:16px 0;">Code not saved.</p>`;
        }}

        return `
          <div class="card" style="border-top: 3px solid ${{borderColor}};">
            <div class="card-header">
              <div>
                <span class="badge" style="background:#1f242c; color:var(--text-muted); margin-bottom:4px; display:inline-block;">${{label}}</span>
                <div class="card-title">${{escapeHtml(modelKey)}}</div>
                <div style="margin-top:4px;">${{speedBadge}}</div>
              </div>
              <div style="text-align:right;">
                ${{pillHtml}}
              </div>
            </div>

            <div class="progress-bar" style="margin-bottom:12px;">
              <div class="progress-fill ${{fillCls}}" style="width: ${{res.is_infra ? 0 : pct}}%;"></div>
            </div>

            ${{failuresHtml}}
            ${{reasoningHtml}}
            ${{codeHtml}}
          </div>
        `;
      }}

      const resA = data.models[modelA] ? data.models[modelA].results[taskKey] : null;
      const resB = data.models[modelB] ? data.models[modelB].results[taskKey] : null;

      container.innerHTML = renderSide(modelA, resA, 'MODEL A') + renderSide(modelB, resB, 'MODEL B');
    }}
  </script>

</body>
</html>"""

    output_path.write_text(html_content, encoding="utf-8")
    return output_path


def open_report_in_browser(report_path: Path = ROOT / "report.html") -> None:
    webbrowser.open(report_path.resolve().as_uri())


if __name__ == "__main__":
    db = Database(ROOT / "bench.db")
    path = generate_html_report(db)
    print(f"Report generated: {path}")
    open_report_in_browser(path)
