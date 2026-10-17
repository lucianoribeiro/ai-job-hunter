"""Unified read-only dashboard for REAL QA and project job results (no sample data)."""
from __future__ import annotations
import argparse
import csv
import html
import json
import re
from pathlib import Path
from urllib.parse import urlsplit


def e(value):
    return html.escape(str(value if value is not None else ""), quote=True)


def safe_url(value):
    parsed = urlsplit(str(value or ""))
    return str(value) if parsed.scheme == "https" and parsed.netloc else "#"


def normalize(project_report, qa_jobs):
    rows, seen = [], set()
    for area, jobs in (("Projetos", project_report.get("jobs", [])), ("QA", qa_jobs)):
        for job in jobs:
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
                evidence = "description_only" if job.get("remote") else "unknown"
            modality = {"explicit": "Remoto informado", "description_only": "Remoto citado — confirmar",
                        "unknown": "Não informado"}.get(evidence, "Não informado")
            # Absence of an explicit signal is NOT proof of on-site or hybrid.
            rows.append({
                "area": area, "title": job.get("title", ""), "company": job.get("company", ""),
                "location": loc, "source": job.get("source", ""), "url": url,
                "modality": modality, "mode_key": "remote" if evidence == "explicit" else (
                    "verify" if evidence == "description_only" else "unknown"),
                "published": job.get("published") or "Não informada",
                "brazil": job.get("brazil_eligible") or "Não verificado"
            })
    return rows


def render(project_report, qa_jobs):
    jobs = normalize(project_report, qa_jobs)
    qa_count = sum(x["area"] == "QA" for x in jobs)
    projects_count = len(jobs) - qa_count
    body = "".join(
        '<tr data-area="' + e(j["area"]) + '" data-mode="' + e(j["mode_key"]) + '">' +
        '<td><a href="' + e(j["url"]) + '" target="_blank" rel="noopener noreferrer">' + e(j["title"]) + '</a></td>' +
        "<td>" + e(j["company"]) + "</td><td>" + e(j["area"]) + "</td><td>" + e(j["location"]) +
        "</td><td>" + e(j["modality"]) + "</td><td>" + e(j["source"]) + "</td><td>" +
        e(j["published"]) + "</td></tr>" for j in jobs
    )
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
<article>Projetos<strong>""" + str(projects_count) + """</strong></article></div>
<section><h2>Pesquisar oportunidades</h2><div class="filters">
<input id="q" aria-label="Pesquisar vaga ou empresa" placeholder="Cargo, empresa, local...">
<select id="area" aria-label="Área"><option value="">Todas as áreas</option><option>QA</option><option>Projetos</option></select>
<select id="mode" aria-label="Modalidade"><option value="">Todas as modalidades</option>
<option value="remote">Remoto informado</option><option value="verify">Remoto citado — confirmar</option>
<option value="unknown">Não informado</option></select></div>
<p id="count" aria-live="polite"></p>
<div class="table"><table><thead><tr><th>Cargo</th><th>Empresa</th><th>Área</th><th>Local</th>
<th>Modalidade</th><th>Fonte</th><th>Publicação</th></tr></thead><tbody>""" + body + """</tbody></table></div>
<p id="empty" hidden>Nenhuma vaga corresponde aos filtros.</p>
</section><footer>Dados obtidos de anúncios públicos. Remoto e elegibilidade brasileira exigem confirmação
na página oficial. Datas ausentes não são estimadas. Candidaturas não são enviadas automaticamente.</footer>
<script>
const q=document.getElementById('q'),a=document.getElementById('area'),m=document.getElementById('mode');
const rows=[...document.querySelectorAll('tbody tr')],count=document.getElementById('count');
function apply(){let visible=0;for(const r of rows){
const show=(!a.value||r.dataset.area===a.value)&&(!m.value||r.dataset.mode===m.value)&&
r.textContent.toLocaleLowerCase().includes(q.value.trim().toLocaleLowerCase());
r.hidden=!show;if(show)visible++;
}count.textContent=visible+' vaga(s) exibida(s)';document.getElementById('empty').hidden=visible!==0;}
[q,a,m].forEach(el=>el.addEventListener('input',apply));apply();
</script></body></html>"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--projects", type=Path, default=Path("data/project_jobs_poc.json"))
    parser.add_argument("--qa", type=Path, default=Path("data/jobs.csv"))
    parser.add_argument("--output", type=Path, default=Path("data/unified_jobs.html"))
    args = parser.parse_args()
    project = json.loads(args.projects.read_text(encoding="utf-8"))
    if not args.qa.exists():
        raise FileNotFoundError(f"QA source file missing: {args.qa}")
    with args.qa.open(encoding="utf-8", newline="") as stream:
        qa = list(csv.DictReader(stream))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render(project, qa), encoding="utf-8")
    print(f"Unified dashboard: {len(normalize(project, qa))} unique real listings")


if __name__ == "__main__":
    main()
