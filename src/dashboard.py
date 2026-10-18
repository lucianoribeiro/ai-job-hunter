"""Generate a safe, read-only offline HTML dashboard from public listing metadata."""
from __future__ import annotations

import html
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

from src.hunter import DATA
from src.finance_advisor import render_advisor

OUTPUT = DATA / "dashboard.html"
ALLOWED = {"pending_review", "approved", "dismissed", "applied", "interview", "rejected", "offer"}


def escape(value: object) -> str:
    return html.escape(str(value if value is not None else ""), quote=True)


def safe_url(value: object) -> str:
    url = str(value or "")
    parts = urlsplit(url)
    return url if parts.scheme in ("http", "https") and parts.netloc else "#"


def monthly_usd_salary(job: dict) -> float | None:
    """Return a conservative monthly USD floor; unknown salary is excluded."""
    salary = str(job.get("salary") or "").strip()
    checks = job.get("assessment") if isinstance(job.get("assessment"), dict) else {}
    currency = str(checks.get("salary_currency") or "").upper()
    if not salary or not (re.search(r"\bUSD\b|US\$|\$", salary, re.I) or currency == "USD"):
        return None
    numbers = re.findall(r"(?<![\w])(?:USD\s*|US\$\s*|\$\s*)?(\d{1,3}(?:,\d{3})+|\d{4,6}|\d{1,3})(?:\.\d+)?\s*([kK]?)", salary)
    if not numbers:
        return None
    values = [float(n.replace(",", "")) * (1000 if k else 1) for n, k in numbers]
    amount = min(values)
    unit = salary.lower()
    if re.search(r"/\s*(?:year|yr|annum)|per\s+(?:year|annum)|annual|yearly", unit):
        return amount / 12
    if re.search(r"/\s*(?:month|mo)\b|per\s+month|monthly", unit):
        return amount
    if re.search(r"/\s*(?:hour|hr|h)\b|per\s+hour|hourly", unit):
        return amount * 40 * 52 / 12
    if re.search(r"/\s*(?:week|wk)\b|per\s+week|weekly", unit):
        return amount * 52 / 12
    return None



def market_intelligence(entries: list[dict]) -> str:
    """Count unique, dated listings in the local dataset, never invent market totals."""
    from collections import defaultdict
    from datetime import timedelta
    from urllib.parse import urlsplit
    now = datetime.now(timezone.utc)
    months = [(now.year * 12 + now.month - 1 - i) for i in range(23, -1, -1)]
    counts = defaultdict(lambda: defaultdict(int))
    seen = set()
    observed_months = set()
    for job in entries:
        title = str(job.get("title") or "").lower()
        description = str(job.get("description") or "").lower()
        if not title:
            continue
        if re.search(r"\b(?:qa manager|quality assurance manager|gerente de qa|gerente de qualidade de software|test manager)\b", title):
            category = "QA Manager"
        elif re.search(r"\b(?:qa|quality assurance|quality engineer|software test|test automation|sdet|quality lead|test lead)\b", title):
            category = "QA"
        elif re.search(r"\b(?:manufatura|manufacturing|production manager|production coordinator|gerente de produção|coordenador de produção)\b", title) or (
            re.search(r"\b(?:project manager|gerente de projetos|coordenador de projetos)\b", title)
            and re.search(r"\b(?:manufacturing|manufatura|industrial|fábrica|factory|produção)\b", description)
        ):
            category = "Manufatura"
        else:
            continue
        raw = str(job.get("published") or job.get("published_at") or job.get("publication_date") or job.get("first_seen") or "")
        try:
            if raw.isdigit():
                dt = datetime.fromtimestamp(int(raw), timezone.utc)
            else:
                dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
        except (ValueError, OverflowError, OSError):
            continue
        if dt > now + timedelta(days=1):
            continue
        month = dt.year * 12 + dt.month - 1
        if month not in months:
            continue
        url = str(job.get("url") or "")
        identity = urlsplit(url)._replace(query="", fragment="").geturl().rstrip("/") if url else str(job.get("id") or "")
        if not identity:
            identity = "|".join((title, str(job.get("company") or "").lower(), str(month)))
        key = (identity, category)
        if key in seen:
            continue
        seen.add(key)
        counts[month][category] += 1
        observed_months.add(month)
    labels = [f"{m % 12 + 1:02d}/{m // 12}" for m in months]
    series = {name: [counts[m][name] if m in observed_months else None for m in months] for name in ("QA", "QA Manager", "Manufatura")}
    payload = json.dumps({"labels": labels, "series": series, "coverage": [m in observed_months for m in months]}, ensure_ascii=False).replace("<", "\\u003c")
    return (
        '<section id="mercado" class="market" aria-labelledby="market-title">'
        '<div class="market-head"><div><h2 id="market-title">Inteligência de Mercado</h2>'
        '<p>Vagas publicadas identificadas pelas fontes integradas · amostra observada, não o mercado inteiro.</p></div>'
        '<label for="market-period">Período <select id="market-period"><option value="3">3 meses</option>'
        '<option value="6" selected>6 meses</option><option value="12">12 meses</option><option value="24">24 meses</option></select></label></div>'
        '<div class="market-cards" id="market-cards" aria-live="polite"></div>'
        '<div class="market-chart"><div id="market-tooltip" class="market-tooltip" role="status" hidden></div><svg id="market-chart" viewBox="0 0 700 230" role="img" '
        'aria-label="Gráfico de vagas mensais de QA, QA Manager e Manufatura"></svg>'
        '<div class="market-legend"><span>● QA</span><span>● QA Manager</span><span>● Manufatura</span></div></div>'
        '<p class="market-note">Contagens por data de publicação, com deduplicação por anúncio. '
        'Meses sem registros históricos são exibidos como sem coleta, nunca como zero vagas. O mês atual está em andamento.</p>'
        '</section><script type="application/json" id="market-data">' + payload + '</script>'
    )


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
        monthly = monthly_usd_salary(job)
        usd_confirmed = monthly is not None
        salary_display = (f"🇺🇸 US$ {monthly:,.0f}/mês" if usd_confirmed else escape(job.get("salary") or "Não divulgado"))
        row = [link, escape(job.get("company")), escape(job.get("category")),
               escape(job.get("score")), escape(status),
               ("🇺🇸 USD" if usd_confirmed else escape(checks.get("salary_currency", "não informada"))),
               escape(checks.get("two_hours_per_day", "unverified")),
               escape(reputation.get("status", "unverified")), salary_display]
        rows.append('<tr data-salary-usd-monthly="' + (str(monthly) if monthly is not None else '') +
                    '" data-usd-confirmed="' + ('true' if usd_confirmed else 'false') +
                    '" data-status="' + escape(status) + '" data-type="' + escape(job.get("category")) + '">' +
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
    market_path = DATA / "history.json"
    market_history = json.loads(market_path.read_text(encoding="utf-8")) if market_path.exists() else {}
    market_entries = list(market_history.values()) if isinstance(market_history, dict) else entries
    from src.market_intelligence import summarize
    market_report = summarize(market_history if isinstance(market_history, dict) else {})
    market_guidance = ('<p class="market-note"><strong>Leitura estratégica:</strong> ' +
        ('Histórico ainda insuficiente para identificar a melhor época do ano. ' if not market_report["seasonality_ready"] else 'Histórico plurianual disponível; avaliar sazonalidade e cobertura antes de concluir. ') +
        'Meses observados: ' + str(market_report["observed_months"]) +
        '. Comparações devem considerar mudanças nas fontes consultadas.</p>')
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
    monitor_path = DATA / "recruiter_monitor.json"
    monitor = json.loads(monitor_path.read_text(encoding="utf-8")) if monitor_path.exists() else {}
    monitor_items = monitor.get("items", [])
    def br_date(value: object) -> str:
        raw = str(value or "").strip()
        if not raw:
            return "Data não informada"
        match = re.match(r"^(\\d{4})-(\\d{2})-(\\d{2})(?:[T\\s].*)?$", raw)
        if match:
            return f"{match.group(3)}/{match.group(2)}/{match.group(1)}"
        match = re.match(r"^(\\d{1,2})/(\\d{1,2})/(\\d{4})$", raw)
        if match:
            return f"{int(match.group(2)):02d}/{int(match.group(1)):02d}/{match.group(3)}"
        return raw

    monitor_rows = "".join(
        '<li><a href="' + escape(safe_url(item.get("url"))) + '" target="_blank" rel="noopener noreferrer">' +
        escape(item.get("title", "Publicação")) + '</a> <span style="display:inline-block;margin:6px 0;padding:6px 10px;border-radius:8px;background:#eef2f8;color:#17233d;font-size:1rem;font-weight:700;line-height:1.5" aria-label="Publicado em ' + escape(br_date(item.get("published_at"))) + '">Publicado em: ' + escape(br_date(item.get("published_at"))) + '</span></li>'
        for item in monitor_items[:50] if isinstance(item, dict)
    ) or "<li>Nenhuma publicação localizada no índice consultado hoje. Isso não significa ausência de vagas.</li>"
    monitor_html = (
        '<section class="advisor" id="recruiter-monitor" style="background:white;border:1px solid #dfe5ed;border-radius:18px;padding:24px;margin:20px 0">'
        '<h2>Recruiter Monitor · Publicações recentes</h2>'
        '<p>Descoberta experimental por índice público de notícias, sem login nem coleta automatizada no LinkedIn. '
        'Não cobre todos os posts. A data do índice pode diferir da data original do post. '
        'Nenhum e-mail ou currículo é enviado automaticamente.</p>'
        '<p><strong>Data da consulta (UTC):</strong> ' + escape(br_date(monitor.get("date_utc"))) +
        ' · <strong>Estado:</strong> ' + escape(monitor.get("status", "não executado")) +
        ' · <strong>Resultados:</strong> ' + str(len(monitor_items)) + '</p>'
        '<ul>' + monitor_rows + '</ul></section>'
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
.market{background:linear-gradient(145deg,#0b1830,#101f3a 65%,#142b43);color:#f1f7ff;border:1px solid #294363;border-radius:22px;padding:clamp(16px,2.5vw,28px);margin:22px 0;box-shadow:0 18px 45px #08172d30;position:relative;overflow:hidden}.market:before{content:"";position:absolute;inset:0;background:radial-gradient(circle at 85% 0%,#27d6d018,transparent 42%);pointer-events:none}.market>*{position:relative}.market-head{display:flex;justify-content:space-between;align-items:center;gap:14px;flex-wrap:wrap}.market-head h2{margin:0 0 6px;color:#f4faff;letter-spacing:-.6px}.market-head p,.market-note{font-size:12px;color:#b6c9df;line-height:1.7}.market-head label{color:#c9dcf1}.market-head select{min-width:125px;background:#162a46;color:#fff;border:1px solid #44617e}.market-cards{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin:18px 0}.market-card{background:linear-gradient(140deg,#182e4d,#12233c);border:1px solid #365271;border-radius:15px;padding:16px;box-shadow:inset 0 1px #ffffff10}.market-card strong{display:block;font-size:clamp(20px,2.5vw,30px);margin-top:7px;color:#f6fbff;font-variant-numeric:tabular-nums}.market-card span{font-size:12px;color:#b9cbe1}.market-card:nth-child(1){border-top:3px solid #3de1d2}.market-card:nth-child(2){border-top:3px solid #ad94ff}.market-card:nth-child(3){border-top:3px solid #ffc477}.market-chart{position:relative;overflow-x:auto;background:#0a172c99;border:1px solid #294461;border-radius:16px;padding:10px 8px 0}.market-chart svg{width:100%;min-width:310px;height:auto;display:block}.market-legend{display:flex;gap:16px;flex-wrap:wrap;font-size:12px;margin:12px 2px 14px}.market-legend span:nth-child(1){color:#3de1d2}.market-legend span:nth-child(2){color:#ad94ff}.market-legend span:nth-child(3){color:#ffc477}.market-tooltip{position:absolute;z-index:2;pointer-events:none;background:#1a3152;color:#fff;border:1px solid #567493;border-radius:10px;padding:9px 12px;font-size:12px;box-shadow:0 10px 30px #0008;max-width:220px}.market-tooltip[hidden]{display:none}.market-note strong{color:#e0f3ff}@media(max-width:500px){.market{padding:16px}.market-cards{gap:7px}.market-card{padding:11px}.market-card strong{font-size:22px}.market-legend{gap:10px}}.salary-tab{display:none}.salary-tab.active{display:block}.nav a{cursor:pointer}.nav a.active{font-weight:800}
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
<nav class="nav" aria-label="Navegação principal"><a class="active" href="#inicio">⌂ &nbsp; Visão geral</a><a href="#vagas">▤ &nbsp; Explorar vagas</a><a href="#vagas">◷ &nbsp; Candidaturas</a><a href="#filtros">⚙ &nbsp; Filtros</a><a href="#mercado">↗ &nbsp; Mercado</a><a href="#recruiter-monitor">◎ &nbsp; Recruiter Monitor</a><a href="#consultor" id="nav-consultor">＄ &nbsp; Consultor Salarial</a></nav>
<p class="sidebar-note">Painel de descoberta e revisão de vagas. Nenhuma candidatura é enviada automaticamente.</p></aside>
<main class="main" id="inicio"><div class="topbar"><span class="eyebrow">Seu painel de oportunidades</span><strong>AI Job Hunter · Dashboard</strong></div>
<header class="hero"><span class="pill">✦ Busca inteligente de oportunidades</span><h1>Encontre sua próxima grande oportunidade.</h1>
<p>Explore vagas de QA, liderança e contratos remotos. Compare oportunidades e revise os anúncios antes de se candidatar.</p>
<div class="pills"><span class="pill">✓ Remoto e internacional</span><span class="pill">✓ Freelance e contratos</span><span class="pill">✓ Busca por empresa e vaga</span></div></header>
""" + market_intelligence(market_entries).replace('</section><script type="application/json" id="market-data">', market_guidance + '</section><script type="application/json" id="market-data">') + advisor + '<div class="salary-tab" id="salary-tab">' + render_advisor() + '</div>' + strategic_html + monitor_html + apinfo_html + """<section class="stats">""" + stats + """</section>
<h2 class="section-title" id="vagas">Explore oportunidades</h2><p class="section-sub">Dados do último processamento · gerado em """ + timestamp + """</p>
<div class="workspace"><aside class="filters" id="filtros"><h2>Filtros de busca</h2><div class="controls">
<div><label for="query">Cargo ou empresa</label><input id="query" aria-label="Pesquisar vagas" placeholder="Ex.: QA Manager, Bosch"></div>
<div><label for="status">Etapa da candidatura</label><select id="status" aria-label="Filtrar status"><option value="">Todos os status</option>""" + "".join(
        f'<option value="{escape(s)}">{escape(s.replace("_", " ").title())}</option>' for s in sorted(ALLOWED)) + """</select></div>
<div><label for="type">Modalidade</label><select id="type" aria-label="Filtrar tipo"><option value="">Todas as modalidades</option><option value="freelance">Freelance</option><option value="full-time/unspecified">Integral / não especificado</option></select></div>
<div><label for="salary-min">🇺🇸 Salário mínimo (USD/mês)</label><input id="salary-min" type="number" min="0" step="100" value="5000" aria-label="Salário mínimo em dólar por mês"></div>
<div><label><input id="usd-only" type="checkbox" style="width:auto;margin-right:8px">🇺🇸 Somente vagas remuneradas em USD</label></div>\n<div><label><input id="salary-unknown" type="checkbox" checked style="width:auto;margin-right:8px">Incluir salários não divulgados</label></div>
</div></aside><section class="results"><div class="results-head"><h2>Vagas encontradas</h2><p>Resultados disponíveis no arquivo gerado</p></div>
<div class="table"><table id="jobs"><thead><tr><th>Vaga</th><th>Empresa</th><th>Categoria</th><th>Score</th>
<th>Status</th><th>Moeda</th><th>2h/dia</th><th>Reputação</th><th>Salário divulgado</th></tr></thead><tbody>""" + "".join(rows) + """</tbody></table></div></section></div>
<footer>Empresas, elegibilidade no Brasil, disponibilidade de 2h/dia e pagamento devem ser verificados diretamente.
O status do painel não envia candidatura. Não armazene CV ou informações pessoais neste repositório público.</footer></main></div>
<script>
const market=JSON.parse(document.querySelector('#market-data').textContent);
function drawMarket(){
 const n=Number(document.querySelector('#market-period').value),labels=market.labels.slice(-n);
 const names=['QA','QA Manager','Manufatura'],colors=['#3de1d2','#ad94ff','#ffc477'];
 const values=names.map(name=>market.series[name].slice(-n));
 const all=values.flat().filter(v=>Number.isFinite(v)),max=Math.max(1,...all);
 const cards=document.querySelector('#market-cards');
 cards.replaceChildren();
 names.forEach((name,i)=>{const card=document.createElement('div');card.className='market-card';
 const label=document.createElement('span');label.textContent=name;const count=document.createElement('strong');
 const observed=values[i].filter(v=>Number.isFinite(v));count.textContent=observed.length?observed.reduce((a,b)=>a+b,0).toLocaleString('pt-BR'):'—';
 const foot=document.createElement('span');foot.textContent=observed.length?'Registros identificados · '+observed.length+' meses com dados':'Sem coleta no período';
 card.append(label,count,foot);cards.appendChild(card)});
 const svg=document.querySelector('#market-chart'),tip=document.querySelector('#market-tooltip'),ns='http://www.w3.org/2000/svg';svg.replaceChildren();tip.hidden=true;
 const add=(tag,attrs,txt)=>{const e=document.createElementNS(ns,tag);Object.entries(attrs).forEach(([k,v])=>e.setAttribute(k,v));if(txt!==undefined)e.textContent=txt;svg.appendChild(e);return e};
 const defs=add('defs',{});colors.forEach((c,i)=>{const g=document.createElementNS(ns,'linearGradient');g.setAttribute('id','market-glow-'+i);g.setAttribute('x1','0');g.setAttribute('y1','0');g.setAttribute('x2','0');g.setAttribute('y2','1');const a=document.createElementNS(ns,'stop');a.setAttribute('offset','0%');a.setAttribute('stop-color',c);a.setAttribute('stop-opacity','.23');const b=document.createElementNS(ns,'stop');b.setAttribute('offset','100%');b.setAttribute('stop-color',c);b.setAttribute('stop-opacity','0');g.append(a,b);defs.appendChild(g)});
 for(let j=0;j<4;j++){const y=185-j*48;add('line',{x1:45,y1:y,x2:675,y2:y,stroke:'#36516d','stroke-dasharray':'3 6'});add('text',{x:37,y:y+4,'text-anchor':'end',fill:'#adc5de','font-size':11},String(Math.round(max*j/3)))}
 const x=j=>48+j*622/Math.max(1,n-1),y=v=>185-v/max*144;
 labels.forEach((m,i)=>{if(n>12&&i%Math.ceil(n/8)!==0&&i!==n-1)return;add('text',{x:x(i),y:216,'text-anchor':'middle',fill:'#c1d2e7','font-size':11},m)});
 values.forEach((series,i)=>{let segment=[];const flush=()=>{if(!segment.length)return;const coords=segment.map(p=>x(p[0])+','+y(p[1])).join(' ');if(segment.length>1){const first=segment[0],last=segment[segment.length-1];add('polygon',{points:x(first[0])+',185 '+coords+' '+x(last[0])+',185',fill:'url(#market-glow-'+i+')'});add('polyline',{points:coords,fill:'none',stroke:colors[i],'stroke-width':3,'stroke-linejoin':'round','stroke-linecap':'round'})}segment=[]};
 series.forEach((v,j)=>{if(!Number.isFinite(v)){flush();return}segment.push([j,v])});flush();
 series.forEach((v,j)=>{if(!Number.isFinite(v))return;const dot=add('circle',{cx:x(j),cy:y(v),r:4,fill:colors[i],stroke:'#0b1830','stroke-width':2,tabindex:0,role:'img','aria-label':nameLabel(i,j,v)});const show=()=>{tip.textContent=nameLabel(i,j,v);tip.hidden=false;tip.style.left=Math.min(75,Math.max(3,x(j)/7))+'%';tip.style.top='12px'};dot.addEventListener('mouseenter',show);dot.addEventListener('focus',show);dot.addEventListener('mouseleave',()=>tip.hidden=true);dot.addEventListener('blur',()=>tip.hidden=true)})
 });
 function nameLabel(i,j,v){return names[i]+' · '+labels[j]+' · '+v.toLocaleString('pt-BR')+' registros da amostra'}
}
document.querySelector('#market-period').addEventListener('change',drawMarket);drawMarket();
const navConsultor=document.querySelector('#nav-consultor');
function showTab(){const active=location.hash==='#consultor';document.querySelector('#salary-tab').classList.toggle('active',active);document.querySelectorAll('.main > :not(.salary-tab)').forEach(el=>{if(el.classList.contains('topbar'))return;el.style.display=active?'none':''});document.querySelectorAll('.nav a').forEach(el=>el.classList.toggle('active',active?el===navConsultor:el!==navConsultor&&el.getAttribute('href')==='#inicio'));}
window.addEventListener('hashchange',showTab);showTab();
const q=document.querySelector('#query'),s=document.querySelector('#status'),t=document.querySelector('#type'),min=document.querySelector('#salary-min'),unknown=document.querySelector('#salary-unknown'),usdOnly=document.querySelector('#usd-only');
function filter(){const search=q.value.toLocaleLowerCase();for(const row of document.querySelectorAll('#jobs tbody tr')){
const salary=row.dataset.salaryUsdMonthly;const threshold=Number(min.value||0);const salaryMatch=salary===''?unknown.checked&&!usdOnly.checked:Number(salary)>=threshold;const currencyMatch=!usdOnly.checked||row.dataset.usdConfirmed==='true';
row.hidden=!(salaryMatch&&currencyMatch&&row.textContent.toLocaleLowerCase().includes(search)&&(!s.value||row.dataset.status===s.value)&&(!t.value||row.dataset.type===t.value));}}
[q,s,t,min,unknown,usdOnly].forEach(x=>x.addEventListener('input',filter));filter();
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
