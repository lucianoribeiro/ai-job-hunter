"""Generate a safe, read-only offline HTML dashboard from public listing metadata."""
from __future__ import annotations

import html
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

from src.hunter import DATA

OUTPUT = DATA / "dashboard.html"
ALLOWED = {"pending_review", "approved", "dismissed", "applied", "interview", "rejected", "offer"}


def escape(value: object) -> str:
    return html.escape(str(value if value is not None else ""), quote=True)


def safe_url(value: object) -> str:
    url = str(value or "")
    parts = urlsplit(url)
    return url if parts.scheme in ("http", "https") and parts.netloc else "#"


def render(queue: dict, generated: str = "") -> str:
    entries = [j for j in queue.values() if isinstance(j, dict)]
    counts = Counter(str(j.get("status", "")) for j in entries)
    total = len(entries)
    freelance = sum(j.get("category") == "freelance" for j in entries)
    approved = counts["approved"]
    active = sum(counts[s] for s in ("applied", "interview", "offer"))
    cards = [
        ("Vagas registradas", total),
        ("Freelance / contratos", freelance),
        ("Pendentes de revisão", counts["pending_review"]),
        ("Aprovadas", approved),
        ("Candidaturas / entrevistas / ofertas", active),
    ]
    stats = "".join(f'<article class="stat"><span>{escape(label)}</span><strong>{number}</strong></article>' for label, number in cards)
    companies = sorted({str(j.get("company") or "").strip() for j in entries if str(j.get("company") or "").strip()}, key=str.casefold)
    rows = []
    for job in sorted(entries, key=lambda j: -int(j.get("score") or 0)):
        status = str(job.get("status", "pending_review"))
        if status not in ALLOWED:
            continue
        url = safe_url(job.get("url"))
        title = escape(job.get("title", "Untitled"))
        link = f'<a href="{escape(url)}" target="_blank" rel="noopener noreferrer">{title}</a>'
        checks = job.get("assessment") if isinstance(job.get("assessment"), dict) else {}
        reputation = checks.get("company_reputation") if isinstance(checks.get("company_reputation"), dict) else {}
        row = [link, escape(job.get("company")), escape(job.get("category")),
               escape(job.get("score")), escape(status),
               escape(checks.get("salary_currency", "unspecified")),
               escape(checks.get("two_hours_per_day", "unverified")),
               escape(reputation.get("status", "unverified"))]
        rows.append('<tr data-status="' + escape(status) + '" data-type="' + escape(job.get("category")) + '">' +
                    "".join(f"<td>{cell}</td>" for cell in row) + "</tr>")
    timestamp = escape(generated or datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"))
    return """<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow"><title>AI Job Hunter | Dashboard</title>
<style>
:root{font-family:system-ui,-apple-system,sans-serif;color:#edf1fc;background:#111827}
body{max-width:1250px;margin:auto;padding:30px 18px}h1{margin:0}p{color:#aab7cf}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(175px,1fr));gap:12px;margin:25px 0}
.stat{padding:18px;border-radius:12px;background:#1f2937;border:1px solid #364152}
.stat span{display:block;font-size:13px;color:#bec8d8}.stat strong{font-size:30px;display:block;margin-top:5px}
.controls{display:flex;flex-wrap:wrap;gap:10px;margin:18px 0}
input,select{padding:10px;color:#fff;background:#1f2937;border:1px solid #546179;border-radius:8px}
input{flex:1;min-width:180px}.table{overflow-x:auto;border:1px solid #374151;border-radius:12px}
table{border-collapse:collapse;width:100%;min-width:860px}th,td{padding:12px;text-align:left;border-bottom:1px solid #303c4b;font-size:14px}
th{color:#cbd5e1;background:#1f2937}a{color:#8bc2ff}footer{margin-top:20px;font-size:13px;color:#b8c3d4}
</style></head><body><header><h1>AI Job Hunter</h1>
<p>Painel somente leitura · gerado em """ + timestamp + """ · Sem candidaturas automáticas</p></header>
<section class="stats">""" + stats + """</section>
<div class="controls"><input id="query" aria-label="Pesquisar vagas" placeholder="Pesquisar empresa ou vaga">
<select id="status" aria-label="Filtrar status"><option value="">Todos os status</option>""" + "".join(
        f'<option value="{escape(s)}">{escape(s.replace("_", " ").title())}</option>' for s in sorted(ALLOWED)) + """</select>
<select id="type" aria-label="Filtrar tipo"><option value="">Todos os tipos</option><option value="freelance">Freelance</option>
<option value="full-time/unspecified">Integral / não especificado</option></select></div>
<div class="table"><table id="jobs"><thead><tr><th>Vaga</th><th>Empresa</th><th>Categoria</th><th>Score</th>
<th>Status</th><th>Moeda</th><th>2h/dia</th><th>Reputação</th></tr></thead><tbody>""" + "".join(rows) + """</tbody></table></div>
<footer>Empresas, elegibilidade no Brasil, disponibilidade de 2h/dia e pagamento devem ser verificados diretamente.
O status do painel não envia candidatura. Não armazene CV ou informações pessoais neste repositório público.</footer>
<script>
const q=document.querySelector('#query'),s=document.querySelector('#status'),t=document.querySelector('#type'),company=document.querySelector('#company');
function filter(){const search=q.value.toLocaleLowerCase();for(const row of document.querySelectorAll('#jobs tbody tr')){
row.hidden=!(row.textContent.toLocaleLowerCase().includes(search)&&(!s.value||row.dataset.status===s.value)&&(!t.value||row.dataset.type===t.value)&&(!company.value||row.dataset.company===company.value));}}
[q,s,t,company].forEach(x=>x.addEventListener('input',filter));
</script></body></html>"""


def run() -> None:
    source = DATA / "applications.json"
    queue = json.loads(source.read_text(encoding="utf-8")) if source.exists() else {}
    if not isinstance(queue, dict):
        raise ValueError("applications.json must be an object")
    DATA.mkdir(exist_ok=True)
    OUTPUT.write_text(render(queue), encoding="utf-8")
    print(f"Dashboard written to {OUTPUT}")


if __name__ == "__main__":
    run()
