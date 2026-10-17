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


def render(queue: dict, generated: str = "", insights: dict | None = None, strategic: dict | None = None) -> str:
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
    insights = insights or {}
    advisor = ('<section style="background:white;border:1px solid #dbe5fb;border-radius:18px;padding:24px;margin-bottom:20px">'
               '<strong>✦ AI Job Hunter · Assistente de oportunidades</strong>'
               '<h2>' + escape(insights.get("headline", "Seu radar inteligente de oportunidades")) + '</h2>'
               '<p>' + escape(insights.get("summary", "Análise ainda não executada.")) + '</p>'
               '<ol>' + ''.join('<li><strong>' + escape(j.get("title", "")) + '</strong> — ' + escape(j.get("company", "")) +
               '<p>' + escape(j.get("reason", "")) + '</p></li>' for j in insights.get("recommendations", [])[:3]) + '</ol>'
               '<small>Modo: ' + ("IA" if insights.get("mode") == "ai" else "Regras explicáveis") + '</small></section>')
    strategic = strategic or {}
    strategic_jobs = strategic.get("jobs") or []
    watch_sources = strategic.get("sources") or []
    strategic_cards = "".join(
        '<li><a href="' + escape(safe_url(item.get("url"))) + '" target="_blank" rel="noopener noreferrer">' +
        escape(item.get("title", "Título indisponível")) + "</a> · " + escape(item.get("company", "")) +
        ' <small>— Localidade e aderência a confirmar</small></li>'
        for item in strategic_jobs[:20] if isinstance(item, dict)
    ) or "<li>Nenhuma vaga extraída do HTML público; consulte o portal oficial.</li>"
    statuses = "; ".join(
        str(item.get("company", "")) + ": " + str(item.get("state", "unknown"))
        for item in watch_sources if isinstance(item, dict)
    )
    strategic_html = (
        '<section class="advisor" id="empresas"><h2>Empresas estratégicas da região</h2>'
        '<p>Monitoramento do portal público da Honda e fontes autorizadas. '
        'Quando o portal não disponibiliza links acessíveis, o resultado fica não verificado.</p>'
        '<p><a href="https://honda.gupy.io/" target="_blank" rel="noopener noreferrer">Ver vagas oficiais da Honda</a></p>'
        '<p><small>' + escape(statuses or "Coleta ainda não executada") + '</small></p>'
        '<ul>' + strategic_cards + '</ul></section>'
    )
    apinfo_html = (
        '<section class="advisor" id="apinfo" style="background:#fff;border:1px solid #dfe5ed;'
        'border-radius:18px;padding:24px;margin:20px 0">'
        '<h2>APinfo · fonte externa</h2>'
        '<p>Consulte vagas de tecnologia diretamente no portal APinfo. '
        'Não há API pública oficial confirmada: esta fonte exige consulta manual, '
        'não alimenta automaticamente os resultados nem os indicadores do painel.</p>'
        '<p><a href="https://www.apinfo.com/apinfo/" target="_blank" '
        'rel="noopener noreferrer">Abrir portal de vagas APinfo ↗</a></p>'
        '<small>Status: consulta externa · integração automática não habilitada</small>'
        '</section>'
    )
    return """<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow"><title>AI Job Hunter | Dashboard</title>
<style>
:root{font-family:Inter,ui-sans-serif,system-ui,-apple-system,sans-serif;color:#17233d;background:#f5f7fc}
*{box-sizing:border-box}body{margin:0;min-height:100vh}a{color:#225ce7;text-decoration:none}a:hover{text-decoration:underline}
.shell{display:grid;grid-template-columns:238px minmax(0,1fr);min-height:100vh}
.sidebar{background:white;border-right:1px solid #e5eaf3;padding:28px 17px;position:sticky;top:0;height:100vh}
.brand{font-weight:800;font-size:19px;letter-spacing:-.6px;color:#12234a;margin:0 0 34px 8px}
.brand:before{content:"✦";background:#2865ed;color:white;border-radius:10px;padding:8px;margin-right:10px}
.nav{display:grid;gap:7px}.nav a{padding:13px 15px;border-radius:10px;color:#5b6780;font-size:14px;font-weight:600}
.nav a.active{background:#eaf1ff;color:#215be1}.sidebar-note{font-size:12px;color:#7a879b;margin:35px 10px;line-height:1.7}
.main{min-width:0;padding:24px clamp(18px,3vw,48px) 40px;max-width:1700px;width:100%;margin:auto}
.topbar{display:flex;justify-content:space-between;align-items:center;gap:12px;margin-bottom:22px}
.eyebrow{font-size:12px;color:#64748b;text-transform:uppercase;letter-spacing:1.5px;font-weight:700}
.topbar strong{font-size:14px;color:#334155}.hero{background:linear-gradient(110deg,#0b1b3b,#1d4ca4 72%,#4679e9);border-radius:20px;padding:32px 35px;color:white;position:relative;overflow:hidden}
.hero:after{content:"✦";position:absolute;right:8%;top:-65px;font-size:280px;color:#ffffff10;pointer-events:none}
.hero h1{font-size:clamp(25px,3vw,38px);letter-spacing:-1.3px;line-height:1.15;max-width:650px;margin:10px 0}
.hero p{color:#dce7ff;max-width:690px;line-height:1.6;font-size:14px}
.pills{display:flex;flex-wrap:wrap;gap:9px;margin-top:20px}.pill{border:1px solid #ffffff55;border-radius:100px;padding:9px 14px;font-size:12px;background:#ffffff1b}
.stats{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:13px;margin:20px 0 30px}
.stat{background:#fff;border:1px solid #e5eaf3;border-radius:15px;padding:19px;box-shadow:0 4px 18px #192f5910}
.stat span{display:block;font-size:12px;color:#64748b;min-height:32px}.stat strong{display:block;font-size:29px;color:#162e61;margin-top:7px;letter-spacing:-1px}
.section-title{font-size:20px;letter-spacing:-.5px;margin:0 0 4px}.section-sub{color:#7b879a;font-size:13px;margin:0 0 20px}
.workspace{display:grid;grid-template-columns:245px minmax(0,1fr);gap:20px;align-items:start}
.filters,.results{background:#fff;border:1px solid #e5eaf3;border-radius:16px;padding:20px;min-width:0}
.filters h2,.results h2{font-size:16px;margin:0 0 18px}.controls{display:grid;gap:14px}
label{display:block;font-size:12px;color:#52627d;font-weight:700;margin-bottom:6px}
input,select{width:100%;padding:11px 12px;background:#fff;border:1px solid #dce3ef;border-radius:9px;color:#273754;font:inherit;font-size:13px}
input:focus,select:focus{outline:2px solid #95b6ff;outline-offset:1px}
.results-head{display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap;margin-bottom:16px}
.results-head p{font-size:12px;color:#738096;margin:0}
.table{overflow:auto}table{border-collapse:collapse;width:100%;min-width:780px}
th,td{padding:15px 10px;text-align:left;border-bottom:1px solid #edf1f7;font-size:12px;vertical-align:middle}
th{color:#74829b;font-size:11px;text-transform:uppercase;letter-spacing:.4px}
td:first-child{font-weight:700;max-width:240px}td:nth-child(4){font-weight:800;color:#2563eb}
tr:hover td{background:#f8faff}tr[hidden]{display:none}
footer{margin-top:25px;color:#7b879b;font-size:12px;line-height:1.8}
@media(max-width:1100px){.stats{grid-template-columns:repeat(3,1fr)}.workspace{grid-template-columns:210px minmax(0,1fr)}}
@media(max-width:760px){.shell{display:block}.sidebar{height:auto;position:static;padding:16px;border-right:0;border-bottom:1px solid #e5eaf3}.brand{margin:0}.nav,.sidebar-note{display:none}.main{padding:18px 14px}.hero{padding:24px}.stats{grid-template-columns:repeat(2,minmax(0,1fr))}.workspace{grid-template-columns:1fr}.filters{padding:16px}.controls{grid-template-columns:repeat(2,minmax(0,1fr))}.results{padding:16px}.topbar{margin-bottom:14px}}
@media(max-width:420px){.controls{grid-template-columns:1fr}.stats{gap:8px}.stat{padding:13px}.stat strong{font-size:23px}}
</style></head><body><div class="shell"><aside class="sidebar"><div class="brand">AI Job Hunter</div>
<nav class="nav" aria-label="Navegação principal"><a class="active" href="#inicio">⌂ &nbsp; Visão geral</a><a href="#vagas">▤ &nbsp; Explorar vagas</a><a href="#vagas">◷ &nbsp; Candidaturas</a><a href="#filtros">⚙ &nbsp; Filtros</a></nav>
<p class="sidebar-note">Painel de descoberta e revisão de vagas. Nenhuma candidatura é enviada automaticamente.</p></aside>
<main class="main" id="inicio"><div class="topbar"><span class="eyebrow">Seu painel de oportunidades</span><strong>AI Job Hunter · Dashboard</strong></div>
<header class="hero"><span class="pill">✦ Busca inteligente de oportunidades</span><h1>Encontre sua próxima grande oportunidade.</h1>
<p>Explore vagas de QA, liderança e contratos remotos. Compare oportunidades e revise os anúncios antes de se candidatar.</p>
<div class="pills"><span class="pill">✓ Remoto e internacional</span><span class="pill">✓ Freelance e contratos</span><span class="pill">✓ Busca por empresa e vaga</span></div></header>
""" + advisor + strategic_html + apinfo_html + """<section class="stats">""" + stats + """</section>
<h2 class="section-title" id="vagas">Explore oportunidades</h2><p class="section-sub">Dados do último processamento · gerado em """ + timestamp + """</p>
<div class="workspace"><aside class="filters" id="filtros"><h2>Filtros de busca</h2><div class="controls">
<div><label for="query">Cargo ou empresa</label><input id="query" aria-label="Pesquisar vagas" placeholder="Ex.: QA Manager, Bosch"></div>
<div><label for="status">Etapa da candidatura</label><select id="status" aria-label="Filtrar status"><option value="">Todos os status</option>""" + "".join(
        f'<option value="{escape(s)}">{escape(s.replace("_", " ").title())}</option>' for s in sorted(ALLOWED)) + """</select></div>
<div><label for="type">Modalidade</label><select id="type" aria-label="Filtrar tipo"><option value="">Todas as modalidades</option><option value="freelance">Freelance</option><option value="full-time/unspecified">Integral / não especificado</option></select></div>
</div></aside><section class="results"><div class="results-head"><h2>Vagas encontradas</h2><p>Resultados disponíveis no arquivo gerado</p></div>
<div class="table"><table id="jobs"><thead><tr><th>Vaga</th><th>Empresa</th><th>Categoria</th><th>Score</th>
<th>Status</th><th>Moeda</th><th>2h/dia</th><th>Reputação</th></tr></thead><tbody>""" + "".join(rows) + """</tbody></table></div></section></div>
<footer>Empresas, elegibilidade no Brasil, disponibilidade de 2h/dia e pagamento devem ser verificados diretamente.
O status do painel não envia candidatura. Não armazene CV ou informações pessoais neste repositório público.</footer></main></div>
<script>
const q=document.querySelector('#query'),s=document.querySelector('#status'),t=document.querySelector('#type');
function filter(){const search=q.value.toLocaleLowerCase();for(const row of document.querySelectorAll('#jobs tbody tr')){
row.hidden=!(row.textContent.toLocaleLowerCase().includes(search)&&(!s.value||row.dataset.status===s.value)&&(!t.value||row.dataset.type===t.value));}}
[q,s,t].forEach(x=>x.addEventListener('input',filter));
</script></body></html>"""


def run() -> None:
    source = DATA / "applications.json"
    queue = json.loads(source.read_text(encoding="utf-8")) if source.exists() else {}
    if not isinstance(queue, dict):
        raise ValueError("applications.json must be an object")
    DATA.mkdir(exist_ok=True)
    path = DATA / "ai_insights.json"
    insights = json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
    strategic_path = DATA / "strategic_jobs.json"
    strategic = json.loads(strategic_path.read_text(encoding="utf-8")) if strategic_path.exists() else None
    OUTPUT.write_text(render(queue, insights=insights, strategic=strategic), encoding="utf-8")
    print(f"Dashboard written to {OUTPUT}")


if __name__ == "__main__":
    run()
