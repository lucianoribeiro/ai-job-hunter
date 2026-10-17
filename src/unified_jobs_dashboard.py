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
                "brazil": job.get("brazil_eligible") or "Não verificado"
            })
    for entry in (linkedin_jobs or []):
        url = safe_url(entry.get("url"))
        if url == "#" or not urlsplit(url).hostname in ("linkedin.com", "www.linkedin.com"):
            continue
        key = urlsplit(url)._replace(query="", fragment="").geturl().rstrip("/").lower()
        if key in seen:
            continue
        seen.add(key)
        rows.append({"area": "LinkedIn · Revisar", "title": "Publicação compartilhada — verificar vaga",
                     "company": "Não verificada", "location": "Não informada",
                     "source": "LinkedIn (compartilhado)", "url": url,
                     "modality": "Não informado", "mode_key": "unknown",
                     "published": "Não informada", "brazil": "Não verificado"})
    return rows


def render(project_report, qa_jobs, linkedin_jobs=None):
    jobs = normalize(project_report, qa_jobs, linkedin_jobs)
    qa_count = sum(x["area"] == "QA" for x in jobs)
    projects_count = sum(x["area"] == "Projetos" for x in jobs)
    linkedin_count = len(jobs) - qa_count - projects_count
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
<article>Projetos<strong>""" + str(projects_count) + """</strong></article>
<article>LinkedIn · revisar<strong>""" + str(linkedin_count) + """</strong></article></div>
<section><h2>Pesquisar oportunidades</h2><div class="filters">
<input id="q" aria-label="Pesquisar vaga ou empresa" placeholder="Cargo, empresa, local...">
<select id="area" aria-label="Área"><option value="">Todas as áreas</option><option>QA</option><option>Projetos</option><option>LinkedIn · Revisar</option></select>
<select id="mode" aria-label="Modalidade"><option value="">Todas as modalidades</option>
<option value="remote">Remoto informado</option><option value="verify">Remoto citado — confirmar</option>
<option value="unknown">Não informado</option></select></div>
<div class="filters"><input id="linkedinInput" aria-label="Link LinkedIn" placeholder="Cole um link de vaga ou publicação do LinkedIn">
<button id="linkedinAdd" type="button">Adicionar para revisão</button></div>
<p id="linkedinMessage" aria-live="polite">Importação manual: não consulta o LinkedIn nem confirma disponibilidade de vagas. O link é incluído apenas nesta sessão do navegador.</p>
<p id="count" aria-live="polite"></p>
<div class="table"><table><thead><tr><th>Cargo</th><th>Empresa</th><th>Área</th><th>Local</th>
<th>Modalidade</th><th>Fonte</th><th>Publicação</th></tr></thead><tbody>""" + body + """</tbody></table></div>
<p id="empty" hidden>Nenhuma vaga corresponde aos filtros.</p>
</section><footer>Dados obtidos de anúncios públicos. Remoto e elegibilidade brasileira exigem confirmação
na página oficial. Datas ausentes não são estimadas. Candidaturas não são enviadas automaticamente.</footer>
<script>
const linked=document.getElementById('linkedinInput'), add=document.getElementById('linkedinAdd'), notice=document.getElementById('linkedinMessage');
add.addEventListener('click',()=>{
try {
 const u=new URL(linked.value.trim());
 const path=u.pathname, job=/^\\/jobs\\/view\\/(?:[^/?#]*\\/)?\d{6,}\\/?$/.test(path),
 post=/^\\/posts\\/[A-Za-z0-9_-]{6,}\\/?$/.test(path)||/^\\/feed\\/update\\/urn:li:activity:\d+\\/?$/.test(path);
 if(u.protocol!=='https:'||!['linkedin.com','www.linkedin.com'].includes(u.hostname)||u.username||u.password||!(job||post)) throw Error('URL inválida');
 const clean='https://www.linkedin.com'+path.replace(/\\/$/,'');
 if([...document.querySelectorAll('tbody a')].some(x=>x.href.replace(/\\/$/,'')===clean)){notice.textContent='Este link já está na lista.';return;}
 const tr=document.createElement('tr');tr.dataset.area='LinkedIn · Revisar';tr.dataset.mode='unknown';
 const td=document.createElement('td'),aLink=document.createElement('a');aLink.href=clean;aLink.target='_blank';aLink.rel='noopener noreferrer';aLink.textContent='Publicação compartilhada — verificar vaga';td.append(aLink);tr.append(td);
 for(const value of ['Não verificada','LinkedIn · Revisar','Não informada','Não informado','LinkedIn (compartilhado)','Não informada']){const cell=document.createElement('td');cell.textContent=value;tr.append(cell);}
 document.querySelector('tbody').append(tr);rows.push(tr);linked.value='';notice.textContent='Link adicionado para revisão nesta sessão. Não foi salva nenhuma candidatura.';apply();
}catch(e){notice.textContent='Cole um link https válido de vaga ou post do LinkedIn.';}
});
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
    parser.add_argument("--linkedin", type=Path, default=Path("data/linkedin_shared_jobs.json"))
    args = parser.parse_args()
    project = json.loads(args.projects.read_text(encoding="utf-8"))
    if not args.qa.exists():
        raise FileNotFoundError(f"QA source file missing: {args.qa}")
    with args.qa.open(encoding="utf-8", newline="") as stream:
        qa = list(csv.DictReader(stream))
    linkedin_jobs = json.loads(args.linkedin.read_text(encoding="utf-8")) if args.linkedin.exists() else []
    if not isinstance(linkedin_jobs, list):
        raise ValueError("LinkedIn import must be an array")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render(project, qa, linkedin_jobs), encoding="utf-8")
    print(f"Unified dashboard: {len(normalize(project, qa, linkedin_jobs))} unique real listings")


if __name__ == "__main__":
    main()
