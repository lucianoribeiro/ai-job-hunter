"""Unified read-only dashboard for REAL QA and project job results (no sample data)."""
from __future__ import annotations
import argparse
import csv
import html
import json
import re
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import urlsplit


def e(value):
    return html.escape(str(value if value is not None else ""), quote=True)


def safe_url(value):
    parsed = urlsplit(str(value or ""))
    return str(value) if parsed.scheme == "https" and parsed.netloc else "#"


QA_TITLE = re.compile(r"\b(qa|quality assurance|quality engineer|quality engineering|software tester|test engineer|sdet|test automation|test lead|automation tester)\b", re.I)


def published_date(value):
    if value in (None, ""):
        return "Não informada"
    try:
        if isinstance(value, (int, float)) or str(value).isdigit():
            timestamp = float(value)
            if timestamp > 1e12:
                timestamp /= 1000
            return datetime.fromtimestamp(timestamp, timezone.utc).strftime("%d/%m/%Y")
        if re.match(r"^\d{4}-\d{2}-\d{2}", str(value)):
            return datetime.fromisoformat(str(value).replace("Z", "+00:00")).strftime("%d/%m/%Y")
    except (OverflowError, ValueError, OSError):
        pass
    return "Não informada"


def published_iso(value):
    """Return only a source-supplied publication date, never an update or first-seen date."""
    if value in (None, ""):
        return ""
    try:
        if isinstance(value, (int, float)) or str(value).isdigit():
            timestamp = float(value)
            if timestamp > 1e12:
                timestamp /= 1000
            return datetime.fromtimestamp(timestamp, timezone.utc).date().isoformat()
        raw = str(value)
        if re.match(r"^\d{4}-\d{2}-\d{2}", raw):
            return datetime.fromisoformat(raw.replace("Z", "+00:00")).date().isoformat()
    except (OverflowError, ValueError, OSError):
        pass
    return ""


REGIONAL_CITIES = ("Nova Odessa", "Americana", "Sumaré", "Santa Bárbara d'Oeste", "Hortolândia", "Campinas")


def region_city(location):
    """Matches only named cities; a generic Brazil posting is not a local vacancy."""
    normalized = str(location or "").casefold()
    normalized = normalized.replace("sumare", "sumaré").replace("hortolandia", "hortolândia").replace("santa barbara", "santa bárbara")
    for city in REGIONAL_CITIES:
        if city.casefold() in normalized:
            return city
    return ""


def normalize(project_report, qa_jobs, linkedin_jobs=None, remote_jobs=None):
    rows, seen = [], set()
    for area, jobs in (("Projetos", project_report.get("jobs", [])), ("QA", qa_jobs)):
        for job in jobs:
            if area == "QA" and not QA_TITLE.search(str(job.get("title", ""))):
                continue
            url = safe_url(job.get("url"))
            if url == "#":
                continue
            key = urlsplit(url)._replace(query="", fragment="").geturl().rstrip("/").lower()
            if key in seen:
                continue
            seen.add(key)
            loc = str(job.get("location") or "")
            evidence = str(job.get("remote_evidence") or "")
            if area == "QA":
                evidence = "description_only" if str(job.get("remote", "")).lower() == "true" else "unknown"
            modality = {"explicit": "Remoto informado", "description_only": "Remoto citado — confirmar",
                        "unknown": "Não informado"}.get(evidence, "Não informado")
            # Absence of an explicit signal is NOT proof of on-site or hybrid.
            rows.append({
                "area": area, "title": job.get("title", ""), "company": job.get("company", ""),
                "location": loc, "regional_city": region_city(loc), "source": job.get("source", ""), "url": url,
                "modality": modality, "mode_key": "remote" if evidence == "explicit" else (
                    "verify" if evidence == "description_only" else "unknown"),
                "published": published_date(job.get("published")),
                "published_iso": published_iso(job.get("published")),
                "brazil": job.get("brazil_eligible") or "Não verificado"
            })
    for job in (remote_jobs or []):
        if job.get("area") not in ("QA", "Projetos"):
            continue
        url = safe_url(job.get("url"))
        if url == "#":
            continue
        key = urlsplit(url)._replace(query="", fragment="").geturl().rstrip("/").lower()
        if key in seen:
            continue
        seen.add(key)
        loc = str(job.get("location") or "")
        rows.append({"area": job["area"], "title": job.get("title", ""), "company": job.get("company", ""),
                     "location": loc, "regional_city": region_city(loc), "source": job.get("source") or "Himalayas",
                     "url": url, "modality": "Remoto informado — elegibilidade a confirmar" if job.get("remote_evidence") == "explicit" else "Não informado",
                     "mode_key": "remote" if job.get("remote_evidence") == "explicit" else "unknown", "published": published_date(job.get("published")),
                     "published_iso": published_iso(job.get("published")), "brazil": "Não verificado"})
    return rows


def render(project_report, qa_jobs, linkedin_jobs=None, regional_sources=None, remote_jobs=None, strategic=None):
    jobs = normalize(project_report, qa_jobs, linkedin_jobs, remote_jobs)
    qa_count = sum(x["area"] == "QA" for x in jobs)
    projects_count = sum(x["area"] == "Projetos" for x in jobs)
    body = "".join(
        '<tr data-area="' + e(j["area"]) + '" data-mode="' + e(j["mode_key"]) + '" data-source="' + e(j["source"]) + '" data-location="' + e(j["location"]) + '" data-city="' + e(j["regional_city"]) + '" data-published="' + e(j["published_iso"]) + '">' +
        '<td><a href="' + e(j["url"]) + '" target="_blank" rel="noopener noreferrer">' + e(j["title"]) + '</a></td>' +
        "<td>" + e(j["company"]) + "</td><td>" + e(j["area"]) + "</td><td>" + e(j["location"]) +
        "</td><td>" + e(j["modality"]) + "</td><td>" + e(j["source"]) + "</td><td>" +
        e(j["published"]) + "</td></tr>" for j in jobs
    )
    source_options = "".join('<option value="' + e(s) + '">' + e(s) + '</option>' for s in sorted({j["source"] for j in jobs}))
    studio_html = "<section id=\"ai-career-studio\" aria-labelledby=\"aiTitle\">\n<h2 id=\"aiTitle\">✦ AI Career Studio</h2>\n<p>Quatro ferramentas para sua carreira. <strong>Prévia da interface:</strong> a análise por IA requer uma conexão privada com o servidor; este arquivo estático não envia dados ou currículos.</p>\n<div class=\"ai-tabs\" role=\"tablist\" aria-label=\"Ferramentas de inteligência artificial\">\n<button type=\"button\" class=\"ai-tab\" data-task=\"fit\" aria-pressed=\"true\">Compatibilidade</button>\n<button type=\"button\" class=\"ai-tab\" data-task=\"cv\" aria-pressed=\"false\">CV Premium</button>\n<button type=\"button\" class=\"ai-tab\" data-task=\"application\" aria-pressed=\"false\">Candidatura</button>\n<button type=\"button\" class=\"ai-tab\" data-task=\"career\" aria-pressed=\"false\">Carreira</button>\n</div>\n<div class=\"ai-workspace\">\n<h3 id=\"aiTaskTitle\">AI Job Match</h3>\n<p id=\"aiTaskHelp\">Compare seu perfil com uma vaga e identifique aderência, evidências e lacunas.</p>\n<label for=\"aiJob\">Vaga real para análise</label>\n<select id=\"aiJob\"><option value=\"\">Selecionar uma vaga do catálogo...</option>\"\"\" + \"\".join('<option value=\"' + e(j[\"url\"]) + '\">' + e(j[\"title\"] + \" · \" + j[\"company\"]) + '</option>' for j in jobs) + \"\"\"</select>\n<p class=\"muted\">Não faça upload de CV neste arquivo offline. Nenhuma informação pessoal é armazenada ou enviada.</p>\n<div class=\"ai-actions\"><button type=\"button\" id=\"aiCopy\">Copiar link da vaga</button><span id=\"aiStatus\" role=\"status\"></span></div>\n<p class=\"muted\"><strong>Análise por IA ainda indisponível neste HTML.</strong> O processamento real dependerá de autenticação e API privada antes de ativarmos upload de currículo ou geração de conteúdo.</p>\n</div>\n</section>"
    strategic = strategic or {}
    source_status = strategic.get("sources", [])
    seen_jobs = strategic.get("jobs", [])

    city_scope = ("Sumaré", "Paulínia", "Americana")
    regional_jobs = [j for j in jobs if j["regional_city"] in city_scope]
    strategic_jobs = [j for j in seen_jobs if isinstance(j, dict) and j.get("url") and j.get("title")]
    entries = []
    seen_links = set()
    for j in regional_jobs:
        url = safe_url(j["url"])
        if url != "#" and url not in seen_links:
            entries.append({"title": j["title"], "company": j["company"], "city": j["regional_city"],
                            "area": j["area"], "url": url, "source": j["source"],
                            "details": "Modalidade: " + j["modality"] + ". Publicação: " + j["published"] +
                                       ". Requisitos completos: consulte o anúncio oficial."})
            seen_links.add(url)
    for j in strategic_jobs:
        url = safe_url(j["url"])
        if url != "#" and url not in seen_links:
            company = str(j.get("company", ""))
            company_city = next((str(x.get("city", "")) for x in source_status if isinstance(x, dict) and x.get("company") == company), "")
            city = next((x for x in city_scope if x.casefold() in str(j.get("location", "")).casefold()), "")
            entries.append({"title": str(j["title"]), "company": company, "city": city,
                            "area": "A confirmar", "url": url, "source": str(j.get("source", "Portal oficial")),
                            "details": "Cidade da vaga não verificada" + ("; empresa cadastrada em " + company_city if company_city else "") +
                                       ". Cargo, requisitos e local devem ser confirmados no anúncio."})
            seen_links.add(url)
    regional_cards = "".join(
        '<article class="regional-card" data-company="' + e(item["company"]) + '" data-city="' + e(item["city"]) +
        '" data-area="' + e(item["area"]) + '"><div class="regional-heading"><strong>' + e(item["title"]) +
        '</strong><span class="regional-pill">' + e(item["area"]) + '</span></div><p>' +
        e(item["company"]) + ' · ' + e(item["city"] or "Cidade não verificada") +
        ' · ' + e(item["source"]) + '</p><details><summary>Ver informações da vaga</summary><p>' +
        e(item["details"]) + '</p><a href="' + e(item["url"]) +
        '" target="_blank" rel="noopener noreferrer">Ver anúncio original / candidatar-se ↗</a></details></article>'
        for item in entries
    )
    companies = sorted({str(x.get("company", "")) for x in source_status if isinstance(x, dict) and x.get("company")} |
                       {x["company"] for x in entries})
    company_options = "".join('<option value="' + e(name) + '">' + e(name) + '</option>' for name in companies)
    company_cards = "".join(
        '<li><strong>' + e(item.get("company", "")) + '</strong> · ' + e(item.get("city", "")) +
        ' · ' + e({"manual": "Fonte ainda não integrada", "needs_connector": "Coleta incompleta (needs_connector)",
                   "ok": "Links públicos identificados", "error": "Consulta indisponível"}.get(item.get("state"), "A verificar")) +
        (' · <a href="' + e(safe_url(item.get("url"))) + '" target="_blank" rel="noopener noreferrer">Portal</a>'
         if safe_url(item.get("url")) != "#" else '') + '</li>'
        for item in source_status if isinstance(item, dict)
    )
    strategic_html = (
        '<section id="empresas-estrategicas" aria-labelledby="regionalTitle"><h2 id="regionalTitle">Vagas regionais · Sumaré, Paulínia e Americana</h2>'
        '<p>Explore oportunidades em um só lugar. Apenas anúncios efetivamente obtidos das fontes aparecem como vagas; '
        'a presença de uma empresa na lista não garante vagas abertas.</p>'
        '<div class="regional-filters"><label>Empresa<select id="regionalCompany"><option value="">Todas as empresas</option>' +
        company_options + '</select></label><label>Cidade<select id="regionalCity"><option value="">Todas as cidades</option>'
        '<option value="Sumaré">Sumaré</option><option value="Paulínia">Paulínia</option>'
        '<option value="Americana">Americana</option></select></label>'
        '<label>Área<select id="regionalArea"><option value="">Todas as áreas</option>'
        '<option value="QA">QA</option><option value="Projetos">Projetos</option>'
        '<option value="A confirmar">A confirmar</option></select></label>'
        '<label>Pesquisar<input id="regionalQuery" placeholder="Cargo, empresa..." aria-label="Pesquisar vagas regionais"></label></div>'
        '<p id="regionalCount" role="status"></p><div id="regionalCards" class="regional-cards">' +
        (regional_cards or '<p>Nenhum anúncio regional foi obtido nas fontes atuais. Consulte os portais das empresas abaixo.</p>') +
        '</div><details class="regional-sources"><summary>Empresas monitoradas e cobertura das fontes</summary><ul>' +
        company_cards + '</ul></details></section>'
    )

    return """<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow"><title>AI Job Hunter | Vagas reais</title>
<style>
:root{font-family:Inter,system-ui,-apple-system,sans-serif;color:#f3f4f6;background:#101216;color-scheme:dark}
*{box-sizing:border-box}body{background:radial-gradient(ellipse at 80% 0%,#222a32 0%,transparent 42%),#101216;max-width:1280px;margin:0 auto;padding:28px 20px;min-height:100vh}
header{background:linear-gradient(135deg,#20242b,#171a20);border:1px solid #393f49;padding:28px;border-radius:22px;box-shadow:0 18px 40px #02061742}
header h1{font-size:clamp(26px,4vw,42px);letter-spacing:-1.1px;margin:0 0 10px;color:white}
header:before{content:'✦ CAREER AI · DASHBOARD PREMIUM';display:block;color:#c3a574;font-size:12px;letter-spacing:2px;font-weight:750;margin-bottom:14px}
.summary{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px;margin:20px 0}
.summary article{background:#242930;border:1px solid #414650;border-radius:18px;padding:22px;color:#bdc2cb;box-shadow:0 8px 20px #0206171f}
.summary strong{display:block;font-size:34px;color:white;margin-top:7px}.summary article:nth-child(2) strong{color:#81b9a0}.summary article:nth-child(3) strong{color:#e8bd78}
section{background:linear-gradient(135deg,#20242bed,#171a20f5);border:1px solid #393f49;border-radius:22px;padding:24px;box-shadow:0 18px 40px #02061742;margin-bottom:20px}
h2{margin-top:0;font-size:22px;color:#f5f5f4}.filters{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;margin:18px 0}
input,select{font:inherit;width:100%;min-width:0;padding:13px 14px;background:#1b1f25;color:#f5f5f4;border:1px solid #454b56;border-radius:11px}
input:focus-visible,select:focus-visible,a:focus-visible{outline:3px solid #c3a574;outline-offset:2px}
.table{overflow-x:auto;border:1px solid #393f49;border-radius:15px}
table{width:100%;border-collapse:collapse;min-width:850px}td,th{text-align:left;padding:15px 13px;border-bottom:1px solid #393f49;font-size:14px}
th{background:#2d323a;color:#d6d9df;font-size:12px;letter-spacing:.4px;text-transform:uppercase}
tbody tr:nth-child(2n){background:#21252b}tbody tr:hover{background:#333a41}
a{color:#93c5b7;font-weight:650;text-decoration:none}a:hover{text-decoration:underline}
p,footer{color:#aeb4bd;line-height:1.6}footer{padding:4px 6px 24px;font-size:13px}
#count{color:#e7e9ea;font-weight:700}#empty{padding:20px;color:#ffd493}
@media(max-width:650px){body{padding:12px}header,section{padding:19px;border-radius:18px}.summary{gap:8px}.summary article{padding:13px;border-radius:12px}.summary strong{font-size:27px}.filters{grid-template-columns:1fr}td,th{padding:11px}}
.ai-tabs{display:flex;flex-wrap:wrap;gap:10px;margin:16px 0}.ai-tab,.ai-actions button{cursor:pointer;border-radius:12px;background:#2b3038;color:#e4e5e7;border:1px solid #515960;padding:12px 16px;font-weight:700}.ai-tab[aria-pressed=true]{background:#477f71;border-color:#78af9f;color:white}.ai-workspace{background:#1b2026;border:1px solid #404750;border-radius:18px;padding:20px}.ai-workspace h3{color:white}.ai-workspace label{display:block;margin-bottom:8px;color:#d6d9df}.ai-actions{display:flex;gap:10px;align-items:center;margin-top:14px;flex-wrap:wrap}#aiStatus{color:#d3d7da;font-size:13px}.muted{color:#aeb4bd}
.regional-filters{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin:18px 0}.regional-filters label{font-size:13px;display:grid;gap:7px;color:#d6d9df}.regional-cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:13px}.regional-card{padding:17px;border:1px solid #46505a;border-radius:15px;background:#252a31}.regional-heading{display:flex;justify-content:space-between;align-items:start;gap:12px}.regional-pill{font-size:11px;border:1px solid #638e82;border-radius:20px;padding:4px 7px;white-space:nowrap}.regional-card p{color:#bbc3cc;font-size:13px;line-height:1.5}.regional-card summary,.regional-sources summary{cursor:pointer;color:#9bd4c6;font-weight:650}.regional-card details a{display:inline-block;margin-top:12px}.regional-sources{margin-top:20px}.regional-card[hidden]{display:none}
</style></head><body>
<header><h1>AI Job Hunter</h1><p>Oportunidades reais, de QA e Gerência / Coordenação de Projetos, em um só lugar.</p></header>
""" + studio_html + strategic_html + """
<div class="summary"><article>Total de vagas<strong>""" + str(len(jobs)) + """</strong></article>
<article>QA<strong>""" + str(qa_count) + """</strong></article>
<article>Projetos<strong>""" + str(projects_count) + """</strong></article>
</div>
<section><h2>Pesquisar oportunidades</h2><div class="filters">
<input id="q" aria-label="Pesquisar vaga ou empresa" placeholder="Cargo, empresa, local...">
<select id="area" aria-label="Área"><option value="">Todas as áreas</option><option>QA</option><option>Projetos</option></select>
<select id="mode" aria-label="Modalidade"><option value="">Todas as modalidades</option>
<option value="remote">Remoto informado</option><option value="verify">Remoto citado — confirmar</option>
<option value="unknown">Não informado</option></select>
<select id="source" aria-label="Fonte das vagas"><option value="">Todas as fontes integradas</option>""" + source_options + """</select><select id="region" aria-label="Filtro regional"><option value="">Todas as localidades</option><option value="local">Vagas nas cidades da região</option><option value="remote">Remoto informado — conferir elegibilidade</option><option value="brazil">Brasil (localização genérica)</option><option value="unknown">Localização sem cidade regional identificada</option></select>
<select id="city" aria-label="Cidade regional"><option value="">Todas as cidades</option><option>Nova Odessa</option><option>Americana</option><option>Sumaré</option><option>Santa Bárbara d'Oeste</option><option>Hortolândia</option><option>Campinas</option></select>
<select id="age" aria-label="Data da publicação"><option value="">Todas as datas</option><option value="1">Último dia</option><option value="7">Últimos 7 dias</option><option value="15">Últimos 15 dias</option><option value="30">Últimos 30 dias</option><option value="unknown">Data não informada</option></select></div>
<p>Filtro regional baseado na cidade informada no anúncio; não calcula distância ou comprova elegibilidade para trabalho remoto.</p><p id="count" aria-live="polite"></p>
<div class="table"><table><thead><tr><th>Cargo</th><th>Empresa</th><th>Área</th><th>Local</th>
<th>Modalidade</th><th>Fonte</th><th>Publicação</th></tr></thead><tbody>""" + body + """</tbody></table></div>
<p id="empty" hidden>Nenhuma vaga corresponde aos filtros.</p>
</section>
<footer>Dados obtidos de anúncios públicos. Remoto e elegibilidade brasileira exigem confirmação
na página oficial. Fonte Himalayas: <a href="https://himalayas.app">himalayas.app</a>. Apenas datas de publicação fornecidas pelas fontes são exibidas; datas ausentes não são estimadas. Candidaturas não são enviadas automaticamente.</footer>
<script>
const q=document.getElementById('q'),a=document.getElementById('area'),m=document.getElementById('mode'),source=document.getElementById('source'),region=document.getElementById('region'),city=document.getElementById('city'),age=document.getElementById('age');
const rows=[...document.querySelectorAll('tbody tr')],count=document.getElementById('count');
function apply(){let visible=0;for(const r of rows){
const local=Boolean(r.dataset.city),location=(r.dataset.location||'').toLocaleLowerCase();
const locOK=!region.value||(region.value==='local'?local:region.value==='remote'?r.dataset.mode==='remote':region.value==='brazil'?(!local&&/brasil|brazil/.test(location)):!local);
const cityOK=!city.value||r.dataset.city===city.value;
const published=r.dataset.published;
let dateOK=!age.value||(age.value==='unknown'?!published:false);
if(age.value&&age.value!=='unknown'&&published){const date=Date.parse(published+'T00:00:00Z');const now=Date.now();const elapsed=(now-date)/86400000;dateOK=elapsed>=0&&elapsed<=Number(age.value);}
const show=dateOK&&locOK&&cityOK&&(!a.value||r.dataset.area===a.value)&&(!m.value||r.dataset.mode===m.value)&&(!source.value||r.dataset.source===source.value)&&
r.textContent.toLocaleLowerCase().includes(q.value.trim().toLocaleLowerCase());
r.hidden=!show;if(show)visible++;
}count.textContent=visible+' vaga(s) exibida(s)';document.getElementById('empty').hidden=visible!==0;}
[q,a,m,source,region,city,age].forEach(el=>el.addEventListener('input',apply));apply();

const rc=document.getElementById('regionalCompany'),rCity=document.getElementById('regionalCity'),rArea=document.getElementById('regionalArea'),rq=document.getElementById('regionalQuery');
if(rc&&rCity&&rArea&&rq){const cards=[...document.querySelectorAll('.regional-card')];const updateRegional=()=>{let count=0;for(const c of cards){const match=(!rc.value||c.dataset.company===rc.value)&&(!rCity.value||c.dataset.city===rCity.value)&&(!rArea.value||c.dataset.area===rArea.value)&&c.textContent.toLocaleLowerCase().includes(rq.value.trim().toLocaleLowerCase());c.hidden=!match;if(match)count++;}document.getElementById('regionalCount').textContent=count+' vaga(s) regional(is) encontrada(s)';};[rc,rCity,rArea,rq].forEach(x=>x.addEventListener('input',updateRegional));updateRegional();}
const taskInfo={
fit:['AI Job Match','Compare seu perfil com uma vaga e identifique aderência, evidências e lacunas.'],
cv:['AI CV Studio','Produza uma versão ATS-friendly do seu currículo, sem inventar informações.'],
application:['AI Application Assistant','Prepare rascunhos de candidatura para revisão humana, sem envio automático.'],
career:['AI Career Advisor','Planeje competências, entrevistas e oportunidades de desenvolvimento.']};
for(const btn of document.querySelectorAll('.ai-tab'))btn.addEventListener('click',()=>{
for(const other of document.querySelectorAll('.ai-tab'))other.setAttribute('aria-pressed',String(other===btn));
document.getElementById('aiTaskTitle').textContent=taskInfo[btn.dataset.task][0];
document.getElementById('aiTaskHelp').textContent=taskInfo[btn.dataset.task][1];
});
document.getElementById('aiCopy').addEventListener('click',async()=>{
const value=document.getElementById('aiJob').value,status=document.getElementById('aiStatus');
if(!value){status.textContent='Selecione uma vaga primeiro.';return;}
try{await navigator.clipboard.writeText(value);status.textContent='Link copiado. A análise de IA ainda requer backend privado.';}
catch(_){status.textContent='Abra a vaga diretamente na lista acima para copiar o link.';}
});
</script></body></html>"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--projects", type=Path, default=Path("data/project_jobs_poc.json"))
    parser.add_argument("--qa", type=Path, default=Path("data/jobs.csv"))
    parser.add_argument("--output", type=Path, default=Path("data/unified_jobs.html"))
    parser.add_argument("--regional-qa", type=Path, default=Path("data/regional_qa_jobs.json"))
    parser.add_argument("--remote-jobs", type=Path, default=Path("data/himalayas_jobs.json"))
    parser.add_argument("--extra-jobs", type=Path, default=Path("data/extra_jobs.json"))
    args = parser.parse_args()
    project = json.loads(args.projects.read_text(encoding="utf-8"))
    if not args.qa.exists():
        raise FileNotFoundError(f"QA source file missing: {args.qa}")
    with args.qa.open(encoding="utf-8", newline="") as stream:
        qa = list(csv.DictReader(stream))
    if args.regional_qa.exists():
        regional_qa = json.loads(args.regional_qa.read_text(encoding="utf-8"))
        if not isinstance(regional_qa, list):
            raise ValueError("Regional QA payload must be a list")
        qa.extend(regional_qa)
    remote_report = json.loads(args.remote_jobs.read_text(encoding="utf-8")) if args.remote_jobs.exists() else {"jobs": []}
    if args.extra_jobs.exists():
        extra_report = json.loads(args.extra_jobs.read_text(encoding="utf-8"))
        remote_report["jobs"].extend(extra_report.get("jobs", []))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    strategic_path = Path("data/strategic_jobs.json")
    strategic = json.loads(strategic_path.read_text(encoding="utf-8")) if strategic_path.exists() else {}
    args.output.write_text(render(project, qa, remote_jobs=remote_report["jobs"], strategic=strategic), encoding="utf-8")
    print(f"Unified dashboard: {len(normalize(project, qa, remote_jobs=remote_report['jobs']))} unique real listings")


if __name__ == "__main__":
    main()
