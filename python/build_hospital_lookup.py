"""Build a dependency-free searchable hospital comparison page."""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "results" / "hospital_peer_comparison.csv"
OUTPUT = ROOT / "site" / "hospital_lookup.html"
FIELDS = ["facility_id", "facility_name_op18", "state", "psych_gap_minutes", "sample_min_op18bc", "peer_group", "median_gap_minutes", "gap_vs_peer_median_minutes"]


def main() -> None:
    with SOURCE.open(newline="", encoding="utf-8-sig") as f:
        rows = [{key: row.get(key, "") for key in FIELDS} for row in csv.DictReader(f)]
    payload = json.dumps(rows, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    html = r'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Hospital psychiatric ED time lookup</title><style>
:root{font:16px/1.5 system-ui,-apple-system,Segoe UI,sans-serif;color:#172234;background:#f4f7fb}body{margin:0}main{max-width:1100px;margin:36px auto;padding:0 20px}h1{font-size:2rem;line-height:1.2}.lead{max-width:850px;color:#42536b}.note{background:#fff8df;border-left:4px solid #db9a12;padding:12px 16px;margin:20px 0}.filters{display:grid;grid-template-columns:2fr 1fr 1fr;gap:12px;margin:20px 0}.filters label{font-size:.9rem;font-weight:650}input,select{display:block;width:100%;box-sizing:border-box;margin-top:5px;padding:10px;border:1px solid #cbd5e1;border-radius:7px;font:inherit;background:white}.meta{color:#526176;margin:10px 0}table{width:100%;border-collapse:collapse;background:white}th,td{text-align:left;padding:10px 12px;border-bottom:1px solid #e5eaf1}th{background:#eaf0f7;font-size:.88rem;position:sticky;top:0}td.num{text-align:right;font-variant-numeric:tabular-nums}tbody tr:hover{background:#f4f8fc}.tablewrap{overflow:auto;max-height:70vh}small{color:#5c6b7e}.footer{margin:18px 0;color:#58677a}@media(max-width:700px){.filters{grid-template-columns:1fr}table{font-size:.9rem}th,td{padding:8px}}
</style></head><body><main><h1>Hospital psychiatric ED time lookup</h1><p class="lead">Explore the latest CMS OP-18 comparison for hospitals with reportable results. The displayed gap is the hospital's reported psychiatric/mental-health median minus its reported non-psychiatric, non-transfer median, for discharged ED visits.</p><div class="note"><strong>How to read this:</strong> The gap is a difference between separately reported hospital medians, not the average extra time for an individual patient. It does not measure admitted-patient boarding. Peer comparisons are descriptive; they are not quality ratings or adjusted rankings. Data period: October 1, 2024–September 30, 2025.</div><div class="filters"><label>Find a hospital<input id="q" type="search" placeholder="Name or CMS facility ID"></label><label>State<select id="state"><option value="">All states</option></select></label><label>Peer group<select id="peer"><option value="">All peer groups</option></select></label></div><p id="meta" class="meta" aria-live="polite"></p><div class="tablewrap"><table><thead><tr><th>Hospital</th><th>State</th><th>Peer group</th><th>Psychiatric ED median gap</th><th>Peer median</th><th>Difference from peer median</th><th>Minimum component sample</th></tr></thead><tbody id="rows"></tbody></table></div><p class="footer"><small>Source: CMS Timely and Effective Care—Hospital OP-18, CMS Hospital General Information, and USDA 2023 RUCC. Hospital characteristics and rurality are latest linked values and may not match the reporting-period date exactly. Missing or suppressed OP-18 results are not shown.</small></p></main><script>
const DATA=__DATA__;const state=document.getElementById('state'),peer=document.getElementById('peer'),query=document.getElementById('q');const uniq=k=>[...new Set(DATA.map(x=>x[k]).filter(Boolean))].sort();uniq('state').forEach(x=>{const o=document.createElement('option');o.value=x;o.textContent=x;state.append(o)});uniq('peer_group').forEach(x=>{const o=document.createElement('option');o.value=x;o.textContent=x;peer.append(o)});const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));const n=x=>x===''||x==null?'—':`${Math.round(Number(x))} min`;function render(){const q=query.value.trim().toLowerCase(),s=state.value,p=peer.value;const list=DATA.filter(x=>(!s||x.state===s)&&(!p||x.peer_group===p)&&(!q||`${x.facility_name_op18} ${x.facility_id}`.toLowerCase().includes(q))).sort((a,b)=>a.facility_name_op18.localeCompare(b.facility_name_op18)||a.state.localeCompare(b.state));document.getElementById('meta').textContent=`${list.length.toLocaleString()} hospitals shown`;document.getElementById('rows').innerHTML=list.slice(0,500).map(x=>`<tr><td>${esc(x.facility_name_op18)}<br><small>CMS ID ${esc(x.facility_id)}</small></td><td>${esc(x.state)}</td><td>${esc(x.peer_group||'Unknown')}</td><td class="num">${n(x.psych_gap_minutes)}</td><td class="num">${n(x.median_gap_minutes)}</td><td class="num">${n(x.gap_vs_peer_median_minutes)}</td><td class="num">${esc(x.sample_min_op18bc)}</td></tr>`).join('')||'<tr><td colspan="7">No hospitals match those filters.</td></tr>';if(list.length>500)document.getElementById('meta').textContent+=' (showing first 500; narrow the search to see more)'}[query,state,peer].forEach(x=>x.addEventListener('input',render));render();
</script></body></html>'''.replace("__DATA__", payload)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(html, encoding="utf-8")
    print(f"Wrote {OUTPUT} with {len(rows)} hospitals ({OUTPUT.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()

