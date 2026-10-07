#!/usr/bin/env python3
"""Build demo/index.html with REAL TabPFN predictions precomputed at build time.

Runs the same predict() pipeline used by the live Flask app for a set of
sample cities, then bakes the results into a static page for GitHub Pages.
Every number on the page is a genuine TabPFN inference — labeled as precomputed.
"""
import datetime
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from frostwise.predict import predict  # noqa: E402

CITIES = [
    ("Chicago, USA", 41.8781, -87.6298),
    ("Berlin, Germany", 52.52, 13.405),
    ("Bengaluru, India", 12.9719, 77.5937),
    ("Sydney, Australia", -33.8688, 151.2093),
    ("Tokyo, Japan", 35.6762, 139.6503),
    ("Toronto, Canada", 43.6532, -79.3832),
]

BUILD_DATE = datetime.date.today().isoformat()


def main():
    results = []
    for name, lat, lon in CITIES:
        print(f"predicting {name} ...", flush=True)
        try:
            r = predict(lat, lon)
            r["city"] = name
            results.append(r)
        except Exception as e:  # noqa: BLE001
            print(f"  FAILED: {e}")
    payload = json.dumps(results)
    html = PAGE_TEMPLATE.replace("__RESULTS__", payload).replace("__BUILD_DATE__", BUILD_DATE)
    os.makedirs("demo", exist_ok=True)
    with open("demo/index.html", "w") as f:
        f.write(html)
    print(f"Wrote demo/index.html with {len(results)} cities")


PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Frostwise — live demo (precomputed TabPFN predictions)</title>
<style>
  :root { --bg:#0e1a12; --card:#16241b; --accent:#7ddf9a; --accent2:#ffd166; --text:#eef5ee; --muted:#9db3a4; }
  * { box-sizing:border-box; }
  body { margin:0; font-family: ui-sans-serif, system-ui, "Segoe UI", Roboto, sans-serif; background:var(--bg); color:var(--text); }
  header { padding:48px 24px 24px; text-align:center; background: radial-gradient(60% 90% at 50% 0%, #1d3a26 0%, var(--bg) 70%); }
  header h1 { font-size: clamp(2rem, 5vw, 3.2rem); margin:0 0 8px; } header h1 span { color:var(--accent); }
  header p { color:var(--muted); max-width:660px; margin:0 auto; line-height:1.6; }
  .badge { display:inline-block; font-size:.75rem; letter-spacing:.08em; text-transform:uppercase; color:#0e1a12; background:var(--accent2); border-radius:999px; padding:4px 12px; margin-bottom:14px; font-weight:700; }
  main { max-width:960px; margin:0 auto; padding:0 20px 48px; }
  .tabs { display:flex; flex-wrap:wrap; gap:8px; justify-content:center; margin:20px 0; }
  .tabs button { padding:10px 18px; border-radius:999px; border:1px solid #2c4634; background:#16241b; color:var(--text); cursor:pointer; font-size:.95rem; }
  .tabs button.active { background:var(--accent); color:#0e1a12; font-weight:700; border-color:var(--accent); }
  .card { background:var(--card); border:1px solid #243b2d; border-radius:16px; padding:24px; margin:16px 0; }
  .frost-grid { display:grid; grid-template-columns:1fr 1fr; gap:16px; margin:16px 0; }
  .frost-box { background:#101d14; border-radius:12px; padding:20px; text-align:center; border:1px solid #243b2d; }
  .frost-box .label { font-size:.8rem; text-transform:uppercase; letter-spacing:.08em; color:var(--muted); }
  .frost-box .date { font-size:1.6rem; font-weight:800; margin:8px 0 4px; color:var(--accent2); }
  .frost-box .sub { font-size:.85rem; color:var(--muted); }
  table { width:100%; border-collapse:collapse; font-size:.9rem; }
  th, td { text-align:left; padding:9px 8px; border-bottom:1px solid #243b2d; vertical-align:top; }
  th { color:var(--muted); font-size:.75rem; text-transform:uppercase; letter-spacing:.06em; }
  .pill { display:inline-block; font-size:.7rem; padding:2px 10px; border-radius:999px; font-weight:700; }
  .tender { background:#4a2b2b; color:#ffb3a7; } .hardy { background:#234a2e; color:#9fe8b4; } .half-hardy { background:#4a3f22; color:#ffd166; }
  .fine { font-size:.8rem; color:var(--muted); line-height:1.6; }
  footer { text-align:center; color:var(--muted); font-size:.82rem; padding:28px 20px; border-top:1px solid #1c2f23; }
  footer a { color:var(--accent); }
</style>
</head>
<body>
<header>
  <div class="badge">Static demo · predictions precomputed __BUILD_DATE__</div>
  <h1>Frost<span>wise</span> demo</h1>
  <p>Every frost date below is a <strong>real TabPFN inference</strong> — the open-source tabular
  foundation model run on live ERA5 climate data for each city, precomputed at build time so this
  page works without a backend. The full app runs the same inference on demand for any location.</p>
</header>
<main>
  <div class="tabs" id="tabs"></div>
  <div id="out"></div>
  <div class="card"><h3 style="margin-top:0">How it works</h3>
    <p class="fine">20 years of daily minimum temperatures (Open-Meteo archive / ERA5) for 80 global
    locations → median first/last frost day-of-year per location → <strong>TabPFN</strong>
    (<a href="https://github.com/PriorLabs/TabPFN">PriorLabs/TabPFN</a>, open-source) learns the
    climate→frost mapping in-context and predicts for any new location. Predictions are statistical
    estimates from historical climate, not weather forecasts.</p></div>
</main>
<footer>Frostwise · DEV Hacktoberfest Week 1 · <a href="https://github.com/arindewangan/frostwise">GitHub</a></footer>
<script>
const DATA = __RESULTS__;
const tabs = document.getElementById('tabs'), out = document.getElementById('out');
function show(i) {
  document.querySelectorAll('.tabs button').forEach((b,j)=>b.classList.toggle('active', j===i));
  const d = DATA[i];
  let frostHtml = d.has_frost
    ? `<div class="frost-grid">
        <div class="frost-box"><div class="label">Last spring frost</div><div class="date">${d.last_frost.date}</div><div class="sub">day ${d.last_frost.doy}</div></div>
        <div class="frost-box"><div class="label">First autumn frost</div><div class="date">${d.first_frost.date}</div><div class="sub">day ${d.first_frost.doy}</div></div>
      </div>`
    : `<div class="frost-box"><div class="label">Frost outlook</div><div class="date">No frost expected</div><div class="sub">frost probability ${(d.frost_probability*100).toFixed(0)}%</div></div>`;
  const rows = d.planting_calendar.map(c =>
    `<tr><td><strong>${c.crop}</strong></td><td><span class="pill ${c.hardiness}">${c.hardiness}</span></td><td>${c.sow_window}</td></tr>`).join('');
  out.innerHTML = `<div class="card"><h2 style="margin-top:0">${d.city}</h2>
    <p class="fine">TabPFN frost probability <strong>${(d.frost_probability*100).toFixed(1)}%</strong> · in-context on ${d.training_locations} locations · ${d.data_source}</p>
    ${frostHtml}<h3>Planting calendar</h3>
    <table><tr><th>Crop</th><th>Type</th><th>Sow window</th></tr>${rows}</table></div>`;
}
DATA.forEach((d,i)=>{ const b=document.createElement('button'); b.textContent=d.city; b.onclick=()=>show(i); tabs.appendChild(b); });
if (DATA.length) show(0); else out.innerHTML = '<div class="card">No precomputed results.</div>';
</script>
</body>
</html>
"""

if __name__ == "__main__":
    main()
