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


def normalize(project_report, qa_jobs, linkedin_jobs=None):
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
                "location": loc, "source": job.get("source", ""), "url": url,
                "modality": modality, "mode_key": "remote" if evidence == "explicit" else (
                    "verify" if evidence == "description_only" else "unknown"),
                "published": published_date(job.get("published")),
                "published_iso": published_iso(job.get("published")),
                "brazil": job.get("brazil_eligible") or "Não verificado"
            })
    return rows


def render(project_report, qa_jobs, linkedin_jobs=None, regional_sources=None):
    jobs = normalize(project_report, qa_jobs, linkedin_jobs)
    qa_count = sum(x["area"] == "QA" for x in jobs)
    projects_count = sum(x["area"] == "Projetos" for x in jobs)
    body = "".join(
        '<tr data-area="' + e(j["area"]) + '" data-mode="' + e(j["mode_key"]) + '" data-source="' + e(j["source"]) + '" data-location="' + e(j["location"]) + '" data-published="' + e(j["published_iso"]) + '">' +
        '<td><a href="' + e(j["url"]) + '" target="_blank" rel="noopener noreferrer">' + e(j["title"]) + '</a></td>' +
        "<td>" + e(j["company"]) + "</td><td>" + e(j["area"]) + "</td><td>" + e(j["location"]) +
        "</td><td>" + e(j["modality"]) + "</td><td>" + e(j["source"]) + "</td><td>" +
        e(j["published"]) + "</td></tr>" for j in jobs
    )
    source_options = "".join('<option value="' + e(s) + '">' + e(s) + '</option>' for s in sorted({j["source"] for j in jobs}))
    return """<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow"><title>AI Job Hunter | Vagas reais</title>
<style>
:root{font-family:system-ui,sans-serif;color:#182744;background:#f3f6fb}
body{max-width:1180px;margin:30px auto;padding:0 16px}header{background:#192b4a;color:white;padding:26px;border-radius:16px}
h1{margin:0 0 5px}.summary{display:flex;gap:12px;flex-wrap:wrap;margin:16px 0}
.summary article{background:white;border-radius:12px;padding:16px;min-width:135px;flex:1}
.summary strong{display:block;font-size:26px}section{background:white;border-radius:14px;padding:20px}
.filters{display:flex;gap:12px;flex-wrap:wrap;margin:15px 0}
input,select{font:inherit;padding:11px;border:1px solid #a5b2c8;border-radius:9px;flex:1;min-width:155px}
.table{overflow-x:auto}table{width:100%;border-collapse:collapse;min-width:870px}
td,th{text-align:left;padding:12px;border-bottom:1px solid #e2e7f0;font-size:14px}
th{background:#edf2fa}a{color:#1456aa}p,footer{color:#53627b}footer{margin-top:18px}
</style></head><body>
<header><h1>AI Job Hunter</h1>Vagas reais de QA e Gerência / Coordenação de Projetos</header>
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
<select id="source" aria-label="Fonte das vagas"><option value="">Todas as fontes integradas</option>""" + source_options + """</select><select id="region" aria-label="Região"><option value="">Todas as localidades</option><option value="local">Nova Odessa e região</option><option value="remote">Remoto informado</option></select>
<select id="age" aria-label="Data da publicação"><option value="">Todas as datas</option><option value="1">Último dia</option><option value="7">Últimos 7 dias</option><option value="15">Últimos 15 dias</option><option value="30">Últimos 30 dias</option><option value="unknown">Data não informada</option></select></div>
<p id="count" aria-live="polite"></p>
<div class="table"><table><thead><tr><th>Cargo</th><th>Empresa</th><th>Área</th><th>Local</th>
<th>Modalidade</th><th>Fonte</th><th>Publicação</th></tr></thead><tbody>""" + body + """</tbody></table></div>
<p id="empty" hidden>Nenhuma vaga corresponde aos filtros.</p>
</section><footer>Dados obtidos de anúncios públicos. Remoto e elegibilidade brasileira exigem confirmação
na página oficial. Apenas datas de publicação fornecidas pelas fontes são exibidas; datas ausentes não são estimadas. Candidaturas não são enviadas automaticamente.</footer>
<script>
const q=document.getElementById('q'),a=document.getElementById('area'),m=document.getElementById('mode'),source=document.getElementById('source'),region=document.getElementById('region'),age=document.getElementById('age');
const rows=[...document.querySelectorAll('tbody tr')],count=document.getElementById('count');
function apply(){let visible=0;for(const r of rows){
const local=/nova odessa|americana|sumaré|sumare|santa bárbara|santa barbara|hortolândia|hortolandia|campinas/i.test(r.dataset.location||'');
const locOK=!region.value||(region.value==='local'?local:r.dataset.mode==='remote');
const published=r.dataset.published;
let dateOK=!age.value||(age.value==='unknown'?!published:false);
if(age.value&&age.value!=='unknown'&&published){const date=Date.parse(published+'T00:00:00Z');const now=Date.now();const elapsed=(now-date)/86400000;dateOK=elapsed>=0&&elapsed<=Number(age.value);}
const show=dateOK&&locOK&&(!a.value||r.dataset.area===a.value)&&(!m.value||r.dataset.mode===m.value)&&(!source.value||r.dataset.source===source.value)&&
r.textContent.toLocaleLowerCase().includes(q.value.trim().toLocaleLowerCase());
r.hidden=!show;if(show)visible++;
}count.textContent=visible+' vaga(s) exibida(s)';document.getElementById('empty').hidden=visible!==0;}
[q,a,m,source,region,age].forEach(el=>el.addEventListener('input',apply));apply();
</script></body></html>"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--projects", type=Path, default=Path("data/project_jobs_poc.json"))
    parser.add_argument("--qa", type=Path, default=Path("data/jobs.csv"))
    parser.add_argument("--output", type=Path, default=Path("data/unified_jobs.html"))
    parser.add_argument("--regional-qa", type=Path, default=Path("data/regional_qa_jobs.json"))
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
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render(project, qa), encoding="utf-8")
    print(f"Unified dashboard: {len(normalize(project, qa))} unique real listings")


if __name__ == "__main__":
    main()
