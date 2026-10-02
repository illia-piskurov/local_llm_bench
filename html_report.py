"""Единый интерактивный HTML-дашборд бенчмарка локальных LLM.

Объединяет:
1. 🏆 Общий лидерборд качества (точность, средний балл, тесты).
2. ⚡ Сравнение скорости на разных устройствах (Hardware Matrix: M4 vs ThinkPad vs i5).
3. 🔍 Детализацию по моделям (карточки 8 бенчмарков, сгенерированный код, ошибки).

Работает полностью автономно в любом браузере, без внешних CDN или npm.
"""

import html
import json
import webbrowser
from datetime import datetime
from pathlib import Path

from benchmarks import BY_ID, REGISTRY
from database import Database

ROOT = Path(__file__).parent


def generate_html_report(db: Database, output_path: Path = ROOT / "report.html") -> Path:
    try:
        from sync import sync_db_and_records

        sync_db_and_records(db)
    except Exception:
        pass

    conn = db.conn

    # 1. Загрузка данных результатов
    rows = conn.execute("""
        SELECT r.model, r.benchmark, r.level, r.tested_at, r.passed, r.total, r.failures,
               s.tokens_per_second, s.time_to_first_token_seconds, s.reasoning_output_tokens, s.host_id
        FROM results r
        LEFT JOIN speed_results s
          ON r.model = s.model AND r.benchmark = s.benchmark AND r.level = s.level
        ORDER BY r.model, r.benchmark, r.level
    """).fetchall()

    # 2. Агрегация лидерборда
    models_data: dict[str, dict] = {}
    for r in rows:
        m = r["model"]
        if m not in models_data:
            models_data[m] = {
                "results": {},
                "total_passed": 0,
                "total_tests": 0,
                "speeds": [],
                "total_reasoning_tokens": 0,
                "latest_test": r["tested_at"],
            }
        key = (r["benchmark"], r["level"])
        pct = (r["passed"] / r["total"] * 100) if r["total"] and r["total"] > 0 else 0.0
        failures = json.loads(r["failures"]) if r["failures"] else []

        models_data[m]["results"][key] = {
            "benchmark": r["benchmark"],
            "level": r["level"],
            "passed": r["passed"],
            "total": r["total"],
            "percent": pct,
            "failures": failures,
            "tok_per_sec": r["tokens_per_second"],
            "ttft": r["time_to_first_token_seconds"],
            "reasoning_tokens": r["reasoning_output_tokens"],
            "tested_at": r["tested_at"],
        }
        models_data[m]["total_passed"] += r["passed"]
        models_data[m]["total_tests"] += r["total"]
        if r["tokens_per_second"]:
            models_data[m]["speeds"].append(r["tokens_per_second"])
        if r["reasoning_output_tokens"]:
            models_data[m]["total_reasoning_tokens"] += r["reasoning_output_tokens"]

    leaderboard = []
    for m, d in models_data.items():
        avg_pct = (d["total_passed"] / d["total_tests"] * 100) if d["total_tests"] > 0 else 0.0
        avg_speed = (sum(d["speeds"]) / len(d["speeds"])) if d["speeds"] else None
        leaderboard.append(
            {
                "model": m,
                "avg_pct": avg_pct,
                "passed": d["total_passed"],
                "total": d["total_tests"],
                "tests_count": len(d["results"]),
                "avg_speed": avg_speed,
                "total_reasoning_tokens": d["total_reasoning_tokens"],
                "data": d,
            }
        )
    leaderboard.sort(key=lambda x: (x["avg_pct"], x["tests_count"]), reverse=True)

    # 3. Загрузка данных по хостам (устройствам)
    hosts_rows = conn.execute("SELECT id, label, created_at FROM hosts ORDER BY created_at").fetchall()

    # Матрица скорости: Модель x Хост
    speed_matrix_rows = conn.execute("""
        SELECT s.model, s.host_id,
               AVG(s.tokens_per_second) AS avg_tps,
               AVG(s.time_to_first_token_seconds) AS avg_ttft,
               COUNT(*) AS cnt
        FROM speed_results s
        GROUP BY s.model, s.host_id
    """).fetchall()

    device_stats = {}
    for h in hosts_rows:
        device_stats[h["id"]] = {"label": h["label"], "tps_list": [], "count": 0}

    model_host_matrix = {}
    for r in speed_matrix_rows:
        m = r["model"]
        hid = r["host_id"]
        if m not in model_host_matrix:
            model_host_matrix[m] = {}
        model_host_matrix[m][hid] = {
            "tps": r["avg_tps"],
            "ttft": r["avg_ttft"],
            "count": r["cnt"],
        }
        if hid in device_stats and r["avg_tps"]:
            device_stats[hid]["tps_list"].append(r["avg_tps"])
            device_stats[hid]["count"] += r["cnt"]

    # Активные хосты (где есть хотя бы 1 замер)
    active_hosts = [h for h in hosts_rows if h["id"] in device_stats and device_stats[h["id"]]["count"] > 0]

    # 4. Чтение сохранённых файлов решений и рассуждений
    def get_code_and_meta(model: str, bench_id: str, level_id: str) -> tuple[str | None, str, int, str | None]:
        b = BY_ID.get(bench_id)
        ext = b.file_ext if b else "txt"
        key_safe = model.replace("/", "_").replace(":", "_").replace("@", "_")
        filename = f"{key_safe}_{bench_id}_{level_id}.{ext}"
        p = ROOT / "models_answers" / filename
        code = None
        if p.exists():
            try:
                code = p.read_text(encoding="utf-8")
            except Exception:
                pass

        reasoning_path = ROOT / "raw_answers" / f"{key_safe}_{bench_id}_{level_id}.reasoning.txt"
        reasoning_text = None
        if reasoning_path.exists():
            try:
                reasoning_text = reasoning_path.read_text(encoding="utf-8")
            except Exception:
                pass

        return code, ext, len(code.splitlines()) if code else 0, reasoning_text

    # 5. Подготовка JSON для клиентской части
    client_models_payload = {}
    for entry in leaderboard:
        m = entry["model"]
        res_dict = {}
        for (b_id, l_id), res in entry["data"]["results"].items():
            code, ext, lines_count, reasoning_text = get_code_and_meta(m, b_id, l_id)
            res_dict[f"{b_id}/{l_id}"] = {
                "passed": res["passed"],
                "total": res["total"],
                "percent": round(res["percent"], 1),
                "failures": res["failures"],
                "tok_per_sec": round(res["tok_per_sec"], 1) if res["tok_per_sec"] else None,
                "ttft": round(res["ttft"], 2) if res["ttft"] else None,
                "reasoning_tokens": res.get("reasoning_tokens"),
                "reasoning_text": reasoning_text,
                "code": code,
                "ext": ext,
                "lines": lines_count,
            }
        client_models_payload[m] = {
            "avg_pct": round(entry["avg_pct"], 1),
            "passed": entry["passed"],
            "total": entry["total"],
            "tests_count": entry["tests_count"],
            "avg_speed": round(entry["avg_speed"], 1) if entry["avg_speed"] else None,
            "total_reasoning_tokens": entry.get("total_reasoning_tokens", 0),
            "results": res_dict,
        }

    benchmarks_metadata = []
    for b in REGISTRY:
        benchmarks_metadata.append(
            {
                "id": b.id,
                "short": b.short,
                "name": b.name,
                "lang": b.code_lang,
                "ext": b.file_ext,
                "levels": [{"id": level.id, "name": level.name} for level in b.levels],
            }
        )

    client_json = json.dumps(
        {
            "models": client_models_payload,
            "benchmarks": benchmarks_metadata,
        },
        ensure_ascii=False,
    )

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Формирование HTML
    html_content = f"""<!DOCTYPE html>
<html lang="ru">
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
        <div class="subtitle">Качество, скорость и сравнение устройств | Обновлено: {now_str}</div>
      </div>
      <div>
        <span class="badge" style="background:#238636; color:#fff; padding:6px 12px; font-size:13px;">
          Моделей: {len(leaderboard)} | Устройств: {len(active_hosts)} | Тестов: {len(rows)}
        </span>
      </div>
    </header>

    <div class="tabs">
      <button class="tab-btn active" onclick="switchTab('leaderboard')">🏆 1. Общий Лидерборд</button>
      <button class="tab-btn" onclick="switchTab('devices')">⚡ 2. Сравнение Устройств (Hardware Matrix)</button>
      <button class="tab-btn" onclick="switchTab('model-view')">🔍 3. Детализация Модели и Код</button>
      <button class="tab-btn" onclick="switchTab('diff-view')">🔀 4. Сравнение Моделей (Diff)</button>
    </div>


    <!-- TAB 1: LEADERBOARD -->
    <div id="tab-leaderboard" class="section">
      <div class="section-title">
        <span>Рейтинг моделей по качеству генерации</span>
        <input type="text" id="search-input" placeholder="Поиск модели..." oninput="filterTable('leaderboard-table', 1)" style="background:#161b22; border:1px solid #30363d; color:#fff; padding:6px 12px; border-radius:6px; font-size:13px; width: 240px;">
      </div>
      <table id="leaderboard-table">
        <thead>
          <tr>
            <th style="width: 45px;">#</th>
            <th>Модель</th>
            <th>Средний балл</th>
            <th>Пройдено проверок</th>
            <th>Пройдено тестов</th>
            <th>Скорость (avg)</th>
            <th>Детали</th>
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
            think_badge = f' <span class="badge" style="background:rgba(137,87,229,0.2); color:#d2a8ff; border:1px solid rgba(137,87,229,0.4);" title="{entry["total_reasoning_tokens"]} токенов рассуждений">🧠 Thinker</span>'

        html_content += f"""
          <tr>
            <td style="font-weight:600; color:var(--text-muted);">{i}</td>
            <td style="font-weight:600; color:#f0f6fc;">{html.escape(m)}{think_badge}</td>
            <td><span class="score-pill {pill_cls}">{avg_pct:.1f}%</span></td>
            <td>{entry["passed"]} / {entry["total"]}</td>
            <td>{entry["tests_count"]} заданий</td>
            <td style="color:var(--text-muted); font-weight:500;">{speed_str}</td>
            <td><a href="#model-view" onclick="selectModel('{html.escape(m)}')" style="color:var(--accent); text-decoration:none; font-size:13px; font-weight:500;">Подробнее →</a></td>
          </tr>"""

    html_content += """
        </tbody>
      </table>
    </div>

    <!-- TAB 2: HARDWARE SPEED MATRIX -->
    <div id="tab-devices" class="section" style="display:none;">
      <div class="section-title">
        <span>Профиль производительности устройств (Скорость генерации tok/s)</span>
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
              <div style="font-size:12px; color:var(--text-muted);">средняя скорость</div>
            </div>
            <div style="font-size:12px; color:var(--text-muted); text-align:right;">
              <strong>{d_info["count"]}</strong> замеров
            </div>
          </div>
        </div>"""

    html_content += """
      </div>

      <div class="section-title" style="margin-top:28px;">
        <span>Сравнение моделей по разным ноутбукам и ПК (Матрица: Модель × Устройство)</span>
        <input type="text" id="device-search-input" placeholder="Фильтр моделей..." oninput="filterTable('devices-table', 0)" style="background:#161b22; border:1px solid #30363d; color:#fff; padding:6px 12px; border-radius:6px; font-size:13px; width: 240px;">
      </div>

      <table id="devices-table">
        <thead>
          <tr>
            <th>Модель</th>"""

    for h in active_hosts:
        html_content += f"<th>{html.escape(h['label'])}</th>"

    html_content += """
          </tr>
        </thead>
        <tbody>"""

    for m in sorted(model_host_matrix.keys()):
        html_content += f"<tr><td style='font-weight:600; color:#f0f6fc;'>{html.escape(m)}</td>"

        # Найдём максимальную скорость для этой модели для подсветки
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
                    <span style="font-size:12px; color:var(--text-muted); display:block;">TTFT: {ttft:.2f}s ({val["count"]} зам.)</span>
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
          <span>Инженерный профиль модели:</span>
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
            <label style="display:block; font-size:12px; color:var(--text-muted); margin-bottom:6px; font-weight:600;">МОДЕЛЬ A (Слева):</label>
            <select id="diff-model-a" class="model-picker" style="width:100%;" onchange="renderDiff()">
            </select>
          </div>
          <div>
            <label style="display:block; font-size:12px; color:var(--text-muted); margin-bottom:6px; font-weight:600;">МОДЕЛЬ B (Справа):</label>
            <select id="diff-model-b" class="model-picker" style="width:100%;" onchange="renderDiff()">
            </select>
          </div>
          <div>
            <label style="display:block; font-size:12px; color:var(--text-muted); margin-bottom:6px; font-weight:600;">ЗАДАНИЕ / УРОВЕНЬ:</label>
            <select id="diff-task" class="model-picker" style="width:100%;" onchange="renderDiff()">
            </select>
          </div>
        </div>
      </div>

      <div id="diff-container" style="display:grid; grid-template-columns: repeat(auto-fit, minmax(420px, 1fr)); gap:16px;">
        <!-- Left: Model A | Right: Model B -->
      </div>
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
      }}
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
        grid.innerHTML = '<p style="color:var(--text-muted);">Данные отсутствуют</p>';
        return;
      }}

      // Summary
      const summaryDiv = document.getElementById('model-summary-badges');
      const pillCls = mData.avg_pct >= 80 ? 'score-green' : mData.avg_pct >= 40 ? 'score-yellow' : 'score-red';
      summaryDiv.innerHTML = `
        <span class="score-pill ${{pillCls}}">${{mData.avg_pct}}% средний балл</span>
        <span style="font-size:13px; color:var(--text-muted); margin-left:8px;">${{mData.passed}}/${{mData.total}} проверок</span>
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
            bPassed += r.passed;
            bTotal += r.total;
            const pct = r.percent;
            const fillCls = pct >= 80 ? 'fill-green' : pct >= 40 ? 'fill-yellow' : 'fill-red';

            let failuresHtml = '';
            if (r.failures && r.failures.length > 0) {{
              failuresHtml = '<ul class="failures-list">' + r.failures.map(f => '<li>' + escapeHtml(f) + '</li>').join('') + '</ul>';
            }}

            let reasoningHtml = '';
            if (r.reasoning_text) {{
              reasoningHtml = `
                <details class="code-box" style="border-color: rgba(137, 87, 229, 0.4); margin-top: 6px;">
                  <summary style="color:#d2a8ff; font-weight:600;">🧠 Ход рассуждений (Reasoning${{r.reasoning_tokens ? ' • ' + r.reasoning_tokens + ' токенов' : ''}})</summary>
                  <pre style="color:#e1d9f5; font-size:12px;"><code>${{escapeHtml(r.reasoning_text)}}</code></pre>
                </details>
              `;
            }} else if (r.reasoning_tokens) {{
              reasoningHtml = `<div style="font-size:12px; color:#d2a8ff; margin-top:4px;">🧠 ${{r.reasoning_tokens}} токенов размышлений</div>`;
            }}

            let codeHtml = '';
            if (r.code) {{
              codeHtml = `
                <details class="code-box">
                  <summary>📄 Код (${{r.lines}} строк) ${{r.tok_per_sec ? '• ' + r.tok_per_sec + ' tok/s' : ''}}</summary>
                  <pre><code>${{escapeHtml(r.code)}}</code></pre>
                </details>
              `;
            }}

            levelsHtml += `
              <div class="level-row">
                <div class="level-meta">
                  <span style="font-weight:500;">${{l.name}}</span>
                  <span><strong>${{r.passed}}/${{r.total}}</strong> (${{pct}}%)</span>
                </div>
                <div class="progress-bar">
                  <div class="progress-fill ${{fillCls}}" style="width: ${{pct}}%;"></div>
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
                  <span style="color:var(--text-muted);">не тестировался</span>
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
        container.innerHTML = '<p style="color:var(--text-muted); padding:20px;">Выберите модели и задание для сравнения.</p>';
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
                <span class="score-pill" style="background:#21262d; color:#8b949e;">не запускался</span>
              </div>
              <p style="color:var(--text-muted); font-size:13px; margin:30px 0; text-align:center;">
                Этот уровень не запускался для модели ${{escapeHtml(modelKey)}}.
              </p>
            </div>
          `;
        }}

        const pct = res.percent;
        const pillCls = pct >= 80 ? 'score-green' : pct >= 40 ? 'score-yellow' : 'score-red';
        const fillCls = pct >= 80 ? 'fill-green' : pct >= 40 ? 'fill-yellow' : 'fill-red';

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
          failuresHtml = `
            <div style="background:rgba(248,81,73,0.08); border:1px solid rgba(248,81,73,0.3); border-radius:6px; padding:10px 14px; margin: 12px 0;">
              <strong style="color:var(--red); font-size:13px;">❌ Провалено тестов (${{res.failures.length}}):</strong>
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
              <summary style="color:#d2a8ff; font-weight:600;">🧠 Ход рассуждений (Reasoning${{res.reasoning_tokens ? ' • ' + res.reasoning_tokens + ' токенов' : ''}})</summary>
              <pre style="color:#e1d9f5; font-size:12px; max-height:260px;"><code>${{escapeHtml(res.reasoning_text)}}</code></pre>
            </details>
          `;
        }}

        let codeHtml = '';
        if (res.code) {{
          codeHtml = `
            <div style="margin-top:10px;">
              <div style="display:flex; justify-content:space-between; font-size:12px; color:var(--text-muted); margin-bottom:6px;">
                <span>📄 Сгенерированный код (${{res.lines}} строк)</span>
                <span>Язык: ${{res.ext}}</span>
              </div>
              <pre style="background:#090d12; border:1px solid var(--card-border); border-radius:6px; padding:12px; max-height:480px; overflow-y:auto; color:#e6edf3; font-family:Consolas, monospace; font-size:12px; white-space:pre-wrap;"><code>${{escapeHtml(res.code)}}</code></pre>
            </div>
          `;
        }} else {{
          codeHtml = `<p style="color:var(--text-muted); font-size:13px; margin:16px 0;">Код не сохранён.</p>`;
        }}

        return `
          <div class="card" style="border-top: 3px solid ${{pct >= 80 ? 'var(--green)' : pct >= 40 ? 'var(--yellow)' : 'var(--red)'}};">
            <div class="card-header">
              <div>
                <span class="badge" style="background:#1f242c; color:var(--text-muted); margin-bottom:4px; display:inline-block;">${{label}}</span>
                <div class="card-title">${{escapeHtml(modelKey)}}</div>
                <div style="margin-top:4px;">${{speedBadge}}</div>
              </div>
              <div style="text-align:right;">
                <span class="score-pill ${{pillCls}}">${{res.passed}}/${{res.total}} (${{pct}}%)</span>
              </div>
            </div>

            <div class="progress-bar" style="margin-bottom:12px;">
              <div class="progress-fill ${{fillCls}}" style="width: ${{pct}}%;"></div>
            </div>

            ${{failuresHtml}}
            ${{reasoningHtml}}
            ${{codeHtml}}
          </div>
        `;
      }}

      const resA = data.models[modelA] ? data.models[modelA].results[taskKey] : null;
      const resB = data.models[modelB] ? data.models[modelB].results[taskKey] : null;

      container.innerHTML = renderSide(modelA, resA, 'МОДЕЛЬ A') + renderSide(modelB, resB, 'МОДЕЛЬ B');
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
