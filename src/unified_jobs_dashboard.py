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


CJK = re.compile(r"[\u3040-\u30ff\u3400-\u9fff]")
LANGUAGE_REQUIREMENT = re.compile(r"\b(?:japanese|mandarin|korean|chinese)[ -]speaking\b", re.I)
OVERSEAS_LOCATION = re.compile(r"\b(?:Japan|Tokyo|Osaka|Vietnam|Hanoi|Malaysia|India|Indonesia|Germany|France|Poland|China|Thailand|Philippines)\b", re.I)
ROLE_TERMS = re.compile(r"\b(?:project|program|portfolio|pmo|coordinator|manager|quality|qa|test|projetos?|gerente|coordenador)\b", re.I)


def studio_job_label(title):
    """Preserve a meaningful Latin-script job title; never alter source record."""
    value = str(title or "").strip()
    if CJK.search(value):
        parts = re.split(r"\s*[/|–—]\s*", value)
        latin = [p.strip(" -|/") for p in parts if not CJK.search(p) and ROLE_TERMS.search(p)]
        if latin:
            return max(latin, key=len)
        value = CJK.sub("", value).strip(" -|/[]")
    return re.sub(r"\s+", " ", value).strip()


def studio_job_eligible(job):
    """Conservative selector ranking: avoid known foreign/on-site or language-mismatch roles."""
    title = str(job.get("title") or "")
    cleaned = studio_job_label(title)
    if not cleaned or not ROLE_TERMS.search(cleaned) or LANGUAGE_REQUIREMENT.search(title):
        return False
    location = str(job.get("location") or "")
    # Explicit overseas location must not be presented as a local/default eligible role.
    if OVERSEAS_LOCATION.search(location) and job.get("mode_key") != "remote":
        return False
    return True


def studio_seniority(title):
    title = str(title or "")
    if re.search(r"\b(intern|internship|estagi[aá]ri[oa]|trainee)\b", title, re.I):
        return "Estágio"
    if re.search(r"\b(junior|jr\.?|júnior)\b", title, re.I):
        return "Júnior"
    if re.search(r"\b(senior|sr\.?|sênior|lead|head|director|diretor)\b", title, re.I):
        return "Sênior/Liderança"
    if re.search(r"\b(mid.level|pleno)\b", title, re.I):
        return "Pleno"
    return "Não informada"


def studio_region(location, mode_key):
    location = str(location or "")
    if region_city(location):
        return "Região de Campinas"
    if re.search(r"\b(brasil|brazil|\bBR\b)\b", location, re.I):
        return "Brasil"
    if mode_key == "remote":
        return "Remoto (elegibilidade a verificar)"
    return "Outra ou não informada"


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
        '<td><a href="' + e(j["url"]) + '" target="_blank" rel="noopener noreferrer">' + e(studio_job_label(j["title"])) + '</a></td>' +
        "<td>" + e(j["company"]) + "</td><td>" + e(j["area"]) + "</td><td>" + e(j["location"]) +
        "</td><td>" + e(j["modality"]) + "</td><td>" + e(j["source"]) + "</td><td>" +
        e(j["published"]) + "</td></tr>" for j in jobs
    )
    source_options = "".join('<option value="' + e(s) + '">' + e(s) + '</option>' for s in sorted({j["source"] for j in jobs}))
    studio_jobs = [j for j in jobs if studio_job_eligible(j)]
    job_options = "".join(
        '<option data-category="' + e(j["area"]) +
        '" data-seniority="' + e(studio_seniority(j["title"])) +
        '" data-region="' + e(studio_region(j["location"], j["mode_key"])) +
        '" value="' + e(j["url"]) + '">' + e(studio_job_label(j["title"]) + " · " + j["company"] +
        (" · " + j["location"] if j["location"] else "")) + '</option>'
        for j in studio_jobs
    )
    studio_html = "<section id=\"ai-career-studio\" aria-labelledby=\"aiTitle\">\n<h2 id=\"aiTitle\">✦ AI Career Studio</h2>\n<p>Quatro ferramentas para sua carreira. <strong>Prévia da interface:</strong> a análise por IA requer uma conexão privada com o servidor; este arquivo estático não envia dados ou currículos.</p>\n<div class=\"ai-tabs\" role=\"tablist\" aria-label=\"Ferramentas de inteligência artificial\">\n<button type=\"button\" class=\"ai-tab\" data-task=\"fit\" aria-pressed=\"true\">Compatibilidade</button>\n<button type=\"button\" class=\"ai-tab\" data-task=\"cv\" aria-pressed=\"false\">CV Premium</button>\n<button type=\"button\" class=\"ai-tab\" data-task=\"application\" aria-pressed=\"false\">Candidatura</button>\n<button type=\"button\" class=\"ai-tab\" data-task=\"career\" aria-pressed=\"false\">Carreira</button>\n</div>\n<div class=\"ai-workspace\">\n<h3 id=\"aiTaskTitle\">AI Job Match</h3>\n<p id=\"aiTaskHelp\">Compare seu perfil com uma vaga e identifique aderência, evidências e lacunas.</p>\n<div id=\"studioFitPanel\" class=\"studio-panel\">\n<div class=\"studio-filters\"><label for=\"studioCategory\">Categoria profissional<select id=\"studioCategory\"><option value=\"Projetos\">Gestão de Projetos</option><option value=\"QA\">QA / Quality Engineering</option></select></label><label for=\"studioSeniority\">Senioridade<select id=\"studioSeniority\"><option value=\"\">Todas</option><option>Estágio</option><option>Júnior</option><option>Pleno</option><option>Sênior/Liderança</option><option>Não informada</option></select></label><label for=\"studioRegion\">Localização<select id=\"studioRegion\"><option value=\"\">Todas</option><option>Região de Campinas</option><option>Brasil</option><option>Remoto (elegibilidade a verificar)</option><option>Outra ou não informada</option></select></label></div>\n<p id=\"studioCount\" role=\"status\" aria-live=\"polite\" class=\"studio-results\"></p>\n<label for=\"aiJob\">Vaga real para análise</label>\n<select id=\"aiJob\"><option value=\"\">Selecionar uma vaga do catálogo...</option>__AI_JOB_OPTIONS__</select>\n<div class=\"match-profile\">\n<h3>Seu perfil profissional</h3>\n<p>Envie um CV ou PDF exportado do LinkedIn, ou cole o texto. Todo o processamento acontece no seu navegador. Bibliotecas de leitura de documentos serão carregadas sob demanda.</p>\n<label for=\"matchFile\">Arquivo do perfil (PDF, DOCX, TXT)</label>\n<input type=\"file\" id=\"matchFile\" accept=\".pdf,.docx,.txt,.md,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,text/plain\">\n<p id=\"matchFileStatus\" role=\"status\" aria-live=\"polite\" class=\"muted\">Aguardando arquivo. Selecione PDF, DOCX ou TXT.</p>\n<details id=\"matchReviewDetails\"><summary>Revisar perfil extraído ou colar texto manualmente</summary><label for=\"matchProfile\">Experiência e competências do perfil</label><textarea id=\"matchProfile\" rows=\"7\" placeholder=\"Texto extraído do currículo; edite se necessário.\"></textarea></details>\n<details id=\"matchDescriptionDetails\"><summary>Adicionar descrição e requisitos da vaga (para melhorar o match)</summary><label for=\"matchDescription\">Descrição original da vaga</label><textarea id=\"matchDescription\" rows=\"5\" placeholder=\"Cole os requisitos completos do anúncio.\"></textarea></details>\n<button type=\"button\" id=\"matchAnalyze\">Calcular compatibilidade local</button>\n<div id=\"matchResult\" role=\"status\" aria-live=\"polite\"></div>\n<p class=\"muted\">Pontuação exploratória baseada em evidências textuais, não probabilidade de contratação. Sem envio externo, sem armazenamento persistente. Bibliotecas de leitura carregadas via CDN somente ao escolher PDF/DOCX.</p>\n</div>\n<div class=\"ai-actions\"><button type=\"button\" id=\"aiCopy\">Copiar link da vaga</button><span id=\"aiStatus\" role=\"status\"></span></div>\n<p class=\"muted\"><strong>Análise por IA ainda indisponível neste HTML.</strong> O processamento real dependerá de autenticação e API privada antes de ativarmos upload de currículo ou geração de conteúdo.</p>\n</div>\n<div id=\"studioCvPanel\" class=\"studio-panel\" hidden>\n<h3>CV Premium — preparação ATS</h3><p>Organize informações reais do seu perfil. O texto fica somente neste navegador e não é enviado.</p>\n<label for=\"studioCvText\">Resumo e experiências profissionais</label><textarea id=\"studioCvText\" rows=\"6\" placeholder=\"Cole aqui seu resumo, experiências, competências e resultados comprovados.\"></textarea>\n<button type=\"button\" id=\"studioCvPrepare\">Preparar estrutura do CV</button>\n<pre id=\"studioCvOutput\" class=\"studio-output\" aria-live=\"polite\"></pre>\n<p class=\"muted\">Estrutura local, sem IA generativa; revise o texto antes de usar. Não insira dados sensíveis.</p>\n</div>\n<div id=\"studioApplicationPanel\" class=\"studio-panel\" hidden>\n<h3>Assistente de Candidatura</h3><p>Prepare uma mensagem inicial usando suas informações reais, sem envio automático.</p>\n<label for=\"studioAppRole\">Cargo e empresa</label><input id=\"studioAppRole\" placeholder=\"Ex.: Gerente de Projetos — Empresa\">\n<label for=\"studioAppExperience\">Experiência relevante comprovada</label><textarea id=\"studioAppExperience\" rows=\"4\" placeholder=\"Descreva competências e resultados reais.\"></textarea>\n<button type=\"button\" id=\"studioAppPrepare\">Preparar rascunho</button>\n<pre id=\"studioAppOutput\" class=\"studio-output\" aria-live=\"polite\"></pre>\n</div>\n<div id=\"studioCareerPanel\" class=\"studio-panel\" hidden>\n<h3>Planejamento de Carreira</h3><p>Monte um roteiro inicial de desenvolvimento profissional, sem análise automática de perfil.</p>\n<label for=\"studioCareerGoal\">Objetivo profissional</label><input id=\"studioCareerGoal\" placeholder=\"Ex.: Gerência de Projetos\">\n<label for=\"studioCareerGap\">Competências que deseja desenvolver</label><textarea id=\"studioCareerGap\" rows=\"3\" placeholder=\"Ex.: gestão de orçamento, inglês, liderança\"></textarea>\n<button type=\"button\" id=\"studioCareerPrepare\">Criar plano de ação</button>\n<pre id=\"studioCareerOutput\" class=\"studio-output\" aria-live=\"polite\"></pre>\n</div>\n</div>\n</section>"
    studio_html = studio_html.replace("__AI_JOB_OPTIONS__", job_options)
    strategic = strategic or {}
    source_status = strategic.get("sources", [])
    seen_jobs = strategic.get("jobs", [])

    city_scope = ("Sumaré", "Paulínia", "Americana")
    regional_jobs = [j for j in jobs if j["regional_city"] in city_scope]
    strategic_jobs = [j for j in seen_jobs if isinstance(j, dict) and j.get("url") and j.get("title")]
    entries = []
    seen_links = set()
    strategic_invalid = len(seen_jobs) - len(strategic_jobs)
    strategic_duplicates = 0
    strategic_outside = 0
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
            # Do not misclassify a known external-city posting as regional.
            title_location = str(j.get("title", "")).casefold()
            known_external = ("são paulo", "sao paulo", "manaus", "brasília", "brasilia", "rio de janeiro")
            if not city and any(other in title_location for other in known_external):
                strategic_outside += 1
                continue
            entries.append({"title": str(j["title"]), "company": company, "city": city,
                            "area": "A confirmar", "url": url, "source": str(j.get("source", "Portal oficial")),
                            "details": "Cidade da vaga não verificada" + ("; empresa cadastrada em " + company_city if company_city else "") +
                                       ". Cargo, requisitos e local devem ser confirmados no anúncio."})
            seen_links.add(url)
        else:
            strategic_duplicates += 1
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
    companies = sorted({x["company"] for x in entries if x.get("company")})
    company_options = "".join('<option value="' + e(name) + '">' + e(name) + '</option>' for name in companies)
    company_cards = "".join(
        '<li><strong>' + e(item.get("company", "")) + '</strong> · ' + e(item.get("city", "")) +
        ' · ' + e({"manual": "Fonte ainda não integrada", "needs_connector": "Coleta incompleta (needs_connector)",
                   "ok": "Links públicos identificados", "error": "Consulta indisponível"}.get(item.get("state"), "A verificar")) +
        (' · <a href="' + e(safe_url(item.get("url"))) + '" target="_blank" rel="noopener noreferrer">Portal</a>'
         if safe_url(item.get("url")) != "#" else '') + '</li>'
        for item in source_status if isinstance(item, dict)
    )
    monitored_count = len([x for x in source_status if isinstance(x, dict)])
    strategic_displayed = len(strategic_jobs) - strategic_duplicates - strategic_outside
    assert len(seen_jobs) == strategic_displayed + strategic_duplicates + strategic_outside + strategic_invalid
    audit_html = (
        '<details class="regional-sources" id="regionalAudit"><summary>Conferência: fonte e interface</summary><p>'
        'Retornados pelo coletor de empresas: ' + str(len(seen_jobs)) +
        ' · Exibidos: ' + str(strategic_displayed) +
        ' · Duplicados: ' + str(strategic_duplicates) +
        ' · Localidade fora da região: ' + str(strategic_outside) +
        ' · Registros inválidos: ' + str(strategic_invalid) +
        '. A soma dos resultados deve coincidir com os registros coletados.</p>'
        '<p>O total geral também inclui outras fontes de QA e Projetos. Empresas sem coleta integrada não retornam vagas.</p></details>'
    )
    live_count = len(entries)
    city_counts = {city: sum(j["city"] == city for j in entries) for city in city_scope}
    city_counts["unverified"] = sum(not j["city"] for j in entries)
    strategic_html = (
        '<section id="empresas-estrategicas" aria-labelledby="regionalTitle"><h2 id="regionalTitle">Vagas regionais · Sumaré, Paulínia e Americana</h2>'
        '<p>Vagas coletadas: ' + str(live_count) + '. Empresas acompanhadas: ' + str(monitored_count) +
        '. Cidades são as informadas nos anúncios, nunca deduzidas pela sede da empresa.</p>'
        '<div class="regional-filters"><label>Empresa<select id="regionalCompany"><option value="">Todas as empresas com vagas</option>' +
        company_options + '</select></label><label>Cidade<select id="regionalCity"><option value="">Todas as cidades</option>'
        '<option value="Sumaré">Sumaré (' + str(city_counts["Sumaré"]) + ')</option>'
        '<option value="Paulínia">Paulínia (' + str(city_counts["Paulínia"]) + ')</option>'
        '<option value="Americana">Americana (' + str(city_counts["Americana"]) + ')</option>'
        '<option value="unverified">Local não confirmado (' + str(city_counts["unverified"]) + ')</option></select></label>'
        '<label>Área<select id="regionalArea"><option value="">Todas as áreas</option>'
        '<option value="QA">QA</option><option value="Projetos">Projetos</option>'
        '<option value="A confirmar">A confirmar</option></select></label>'
        '<label>Pesquisar<input id="regionalQuery" placeholder="Cargo, empresa..." aria-label="Pesquisar vagas regionais"></label></div>'
        '<p id="regionalCount" role="status"></p><div id="regionalCards" class="regional-cards">' +
        (regional_cards or '<p>Nenhum anúncio regional foi obtido nas fontes atuais. Consulte os portais das empresas abaixo.</p>') +
        '</div>' + "<div class=\"page-controls\" aria-label=\"Paginação de resultados\"><label>Mostrar<select class=\"page-size\"><option value=\"10\">10 por página</option><option value=\"all\">Todos</option></select></label><span class=\"page-summary\" role=\"status\"></span><button type=\"button\" class=\"page-prev\">Anterior</button><span class=\"page-index\"></span><button type=\"button\" class=\"page-next\">Próxima</button></div>" + audit_html + '<details class="regional-sources"><summary>Empresas acompanhadas (inclusive sem integração)</summary>'
        '<p>Essas empresas não necessariamente possuem vagas coletadas. Consulte as fontes oficiais para cobertura adicional.</p><ul>' +
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
.match-profile{margin-top:18px;padding:16px;border:1px solid #4b5760;border-radius:13px}.match-profile details{margin:12px 0;border:1px solid #46535b;border-radius:9px;padding:12px}.match-profile summary{cursor:pointer;font-weight:650}.match-profile label{display:block;margin:15px 0 6px}.match-profile textarea{font:inherit;width:100%;background:#1b1f25;border:1px solid #626b78;border-radius:9px;padding:12px;color:#eee;resize:vertical}.match-profile input[type=file]{font:inherit}.match-profile button{cursor:pointer;background:#356e5e;color:white;border:1px solid #9ad2ba;padding:12px 16px;border-radius:10px;font-weight:700}#matchResult{margin-top:18px;line-height:1.6}#matchResult ul{padding-left:22px}.studio-panel[hidden]{display:none}.studio-panel label{display:block;margin:14px 0 6px}.studio-panel textarea{font:inherit;width:100%;background:#1b1f25;color:#f5f5f4;border:1px solid #626b78;border-radius:11px;padding:13px;resize:vertical}.studio-panel button{cursor:pointer;background:#356e5e;color:#fff;border:1px solid #8dc3ad;border-radius:10px;padding:12px 16px;margin-top:14px;font-weight:700}.studio-output{white-space:pre-wrap;overflow-wrap:anywhere;font:inherit;font-size:14px;line-height:1.6;color:#e9edf0}.studio-results{font-size:16px!important;color:#e7f4ef!important;font-weight:750;margin:12px 0 8px}#studioQuery{margin:10px 0 4px;font-size:16px;min-height:48px}#aiJob{font-size:16px;min-height:48px}.studio-filters{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin:14px 0}.studio-filters label{display:grid;gap:6px;color:#d6d9df;font-size:13px}#studioCount{color:#9bd4c6;font-size:12px}.ai-tabs{display:flex;flex-wrap:wrap;gap:10px;margin:16px 0}.ai-tab,.ai-actions button{cursor:pointer;border-radius:12px;background:#2b3038;color:#e4e5e7;border:1px solid #515960;padding:12px 16px;font-weight:700}.ai-tab[aria-pressed=true]{background:#477f71;border-color:#78af9f;color:white}.ai-workspace{background:#1b2026;border:1px solid #404750;border-radius:18px;padding:20px}.ai-workspace h3{color:white}.ai-workspace label{display:block;margin-bottom:8px;color:#d6d9df}.ai-actions{display:flex;gap:10px;align-items:center;margin-top:14px;flex-wrap:wrap}#aiStatus{color:#d3d7da;font-size:13px}.muted{color:#aeb4bd}
.regional-filters{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin:18px 0}.regional-filters label{font-size:13px;display:grid;gap:7px;color:#d6d9df}.regional-cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:13px}.regional-card{padding:17px;border:1px solid #46505a;border-radius:15px;background:#252a31}.regional-heading{display:flex;justify-content:space-between;align-items:start;gap:12px}.regional-pill{font-size:11px;border:1px solid #638e82;border-radius:20px;padding:4px 7px;white-space:nowrap}.regional-card p{color:#bbc3cc;font-size:13px;line-height:1.5}.regional-card summary,.regional-sources summary{cursor:pointer;color:#9bd4c6;font-weight:650}.regional-card details a{display:inline-block;margin-top:12px}.regional-sources{margin-top:20px}.regional-card[hidden]{display:none}
.primary-tabs{position:sticky;top:0;z-index:20;background:#171b21;border:1px solid #46505a;border-radius:16px;display:flex;gap:8px;padding:9px;margin:14px 0}.primary-tab{flex:1;min-height:48px;padding:12px;border:1px solid #515960;border-radius:10px;background:#292f37;color:#f5f5f4;font:inherit;font-weight:700;cursor:pointer}.primary-tab[aria-selected="true"]{background:#477f71;border-color:#9bd4c6;color:white}.primary-panel[hidden]{display:none!important}.primary-tab:focus-visible{outline:3px solid #e8bd78;outline-offset:2px}@media(max-width:650px){.primary-tabs{gap:5px}.primary-tab{font-size:12px;padding:10px 6px}}.page-controls{display:flex;flex-wrap:wrap;align-items:center;gap:12px;margin-top:18px;padding:12px;border:1px solid #414b55;border-radius:12px;background:#222830}.page-controls label{display:flex;gap:8px;align-items:center;font-size:14px}.page-controls select{width:auto;min-width:130px}.page-controls button{background:#323a43;color:#fff;border:1px solid #5b6976;border-radius:9px;padding:10px 14px;cursor:pointer;min-height:42px}.page-controls button:disabled{opacity:.45;cursor:not-allowed}.page-summary,.page-index{font-size:14px;color:#e6eeec}.page-controls button:focus-visible{outline:3px solid #e8bd78}@media(max-width:650px){.page-controls{gap:8px}.page-controls label,.page-summary{width:100%}}.sort-column{background:transparent;border:0;color:inherit;font:inherit;font-weight:700;text-transform:uppercase;cursor:pointer;display:inline-flex;align-items:center;gap:5px;padding:8px 3px;min-height:40px}.sort-column:hover{text-decoration:underline}.sort-column:focus-visible{outline:3px solid #e8bd78;outline-offset:2px}</style></head><body>
<header><h1>AI Job Hunter</h1><p>Oportunidades reais, de QA e Gerência / Coordenação de Projetos, em um só lugar.</p></header>
<nav class="primary-tabs" aria-label="Navegação principal" role="tablist"><button type="button" class="primary-tab" id="mainTabGeneral" role="tab" aria-controls="mainPanelGeneral" aria-selected="true" tabindex="0">Oportunidades Gerais</button><button type="button" class="primary-tab" id="mainTabRegional" role="tab" aria-controls="mainPanelRegional" aria-selected="false" tabindex="-1">Oportunidades Regionais</button><button type="button" class="primary-tab" id="mainTabAI" role="tab" aria-controls="mainPanelAI" aria-selected="false" tabindex="-1">AI Career Studio</button></nav>
<div id="mainPanelGeneral" class="primary-panel" role="tabpanel" aria-labelledby="mainTabGeneral">
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
<div class="table"><table><thead><tr><th scope="col" aria-sort="none"><button type="button" class="sort-column" data-column="0" aria-label="Ordenar por Cargo">Cargo <span aria-hidden="true">↕</span></button></th><th scope="col" aria-sort="none"><button type="button" class="sort-column" data-column="1" aria-label="Ordenar por Empresa">Empresa <span aria-hidden="true">↕</span></button></th><th scope="col" aria-sort="none"><button type="button" class="sort-column" data-column="2" aria-label="Ordenar por Área">Área <span aria-hidden="true">↕</span></button></th><th scope="col" aria-sort="none"><button type="button" class="sort-column" data-column="3" aria-label="Ordenar por Local">Local <span aria-hidden="true">↕</span></button></th><th scope="col" aria-sort="none"><button type="button" class="sort-column" data-column="4" aria-label="Ordenar por Modalidade">Modalidade <span aria-hidden="true">↕</span></button></th><th scope="col" aria-sort="none"><button type="button" class="sort-column" data-column="5" aria-label="Ordenar por Fonte">Fonte <span aria-hidden="true">↕</span></button></th><th scope="col" aria-sort="none"><button type="button" class="sort-column" data-column="6" aria-label="Ordenar por Publicação">Publicação <span aria-hidden="true">↕</span></button></th></tr></thead><tbody>""" + body + """</tbody></table></div>
<div class="page-controls" aria-label="Paginação de resultados"><label>Mostrar<select class="page-size"><option value="10">10 por página</option><option value="all">Todos</option></select></label><span class="page-summary" role="status"></span><button type="button" class="page-prev">Anterior</button><span class="page-index"></span><button type="button" class="page-next">Próxima</button></div><p id="empty" hidden>Nenhuma vaga corresponde aos filtros.</p>
</section>
</div>
<div id="mainPanelRegional" class="primary-panel" role="tabpanel" aria-labelledby="mainTabRegional" hidden>""" + strategic_html + """</div>
<div id="mainPanelAI" class="primary-panel" role="tabpanel" aria-labelledby="mainTabAI" hidden>""" + studio_html + """</div>
<footer>Dados obtidos de anúncios públicos. Remoto e elegibilidade brasileira exigem confirmação
na página oficial. Fonte Himalayas: <a href="https://himalayas.app">himalayas.app</a>. Apenas datas de publicação fornecidas pelas fontes são exibidas; datas ausentes não são estimadas. Candidaturas não são enviadas automaticamente.</footer>
<script>
const mainTabPairs=[['mainTabGeneral','mainPanelGeneral'],['mainTabRegional','mainPanelRegional'],['mainTabAI','mainPanelAI']];
function activateMainTab(index,focus=false){mainTabPairs.forEach(([tid,pid],i)=>{const active=i===index,tab=document.getElementById(tid),panel=document.getElementById(pid);tab.setAttribute('aria-selected',String(active));tab.tabIndex=active?0:-1;panel.hidden=!active;});if(focus)document.getElementById(mainTabPairs[index][0]).focus();}
mainTabPairs.forEach(([tid],i)=>{const tab=document.getElementById(tid);tab.addEventListener('click',()=>activateMainTab(i));tab.addEventListener('keydown',evt=>{if(!['ArrowRight','ArrowLeft','Home','End'].includes(evt.key))return;evt.preventDefault();const next=evt.key==='Home'?0:evt.key==='End'?mainTabPairs.length-1:(i+(evt.key==='ArrowRight'?1:-1)+mainTabPairs.length)%mainTabPairs.length;activateMainTab(next,true);});});
activateMainTab(0);
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
r.hidden=!show;r.dataset.filterPass=String(show);if(show)visible++;
}count.textContent=visible+' vaga(s) exibida(s)';document.getElementById('empty').hidden=visible!==0;}
[q,a,m,source,region,city,age].forEach(el=>el.addEventListener('input',apply));apply();

const rc=document.getElementById('regionalCompany'),rCity=document.getElementById('regionalCity'),rArea=document.getElementById('regionalArea'),rq=document.getElementById('regionalQuery');
if(rc&&rCity&&rArea&&rq){const cards=[...document.querySelectorAll('.regional-card')];const updateRegional=()=>{let count=0;for(const c of cards){const match=(!rc.value||c.dataset.company===rc.value)&&(!rCity.value||(rCity.value==='unverified'?!c.dataset.city:c.dataset.city===rCity.value))&&(!rArea.value||c.dataset.area===rArea.value)&&c.textContent.toLocaleLowerCase().includes(rq.value.trim().toLocaleLowerCase());c.hidden=!match;c.dataset.filterPass=String(match);if(match)count++;}document.getElementById('regionalCount').textContent=count+' vaga(s) encontrada(s)'+(count===0?' para os filtros selecionados. Isso não significa que não existam vagas nos portais; a coleta é parcial.':'');};[rc,rCity,rArea,rq].forEach(x=>x.addEventListener('input',updateRegional));updateRegional();}
const studioCategory=document.getElementById('studioCategory'),studioSeniority=document.getElementById('studioSeniority'),studioRegion=document.getElementById('studioRegion'),aiJob=document.getElementById('aiJob'),studioCount=document.getElementById('studioCount');
if(studioCategory&&studioSeniority&&studioRegion&&aiJob&&studioCount){
 const opts=[...aiJob.options].filter(o=>o.value);
 const refreshStudio=()=>{
  let matched=0;
  for(const o of opts){
   const show=o.dataset.category===studioCategory.value&&(!studioSeniority.value||o.dataset.seniority===studioSeniority.value)&&(!studioRegion.value||o.dataset.region===studioRegion.value);
   o.hidden=!show;o.disabled=!show;if(show)matched++;
  }
  if(aiJob.selectedOptions[0]&&aiJob.selectedOptions[0].disabled)aiJob.value='';
  studioCount.textContent=matched+' '+(matched===1?'vaga encontrada':'vagas encontradas')+' nos filtros selecionados';
  if(matched===0)aiJob.value='';
 };
 [studioCategory,studioSeniority,studioRegion].forEach(el=>el.addEventListener('change',refreshStudio));
 refreshStudio();
}

const taskInfo={
fit:['AI Job Match','Compare seu perfil com uma vaga e identifique aderência, evidências e lacunas.'],
cv:['AI CV Studio','Produza uma versão ATS-friendly do seu currículo, sem inventar informações.'],
application:['AI Application Assistant','Prepare rascunhos de candidatura para revisão humana, sem envio automático.'],
career:['AI Career Advisor','Planeje competências, entrevistas e oportunidades de desenvolvimento.']};
for(const btn of document.querySelectorAll('.ai-tab'))btn.addEventListener('click',()=>{
for(const other of document.querySelectorAll('.ai-tab'))other.setAttribute('aria-pressed',String(other===btn));
document.getElementById('aiTaskTitle').textContent=taskInfo[btn.dataset.task][0];
document.getElementById('aiTaskHelp').textContent=taskInfo[btn.dataset.task][1];
for(const [key,id] of Object.entries({fit:'studioFitPanel',cv:'studioCvPanel',application:'studioApplicationPanel',career:'studioCareerPanel'})){
 const panel=document.getElementById(id);
 panel.hidden=key!==btn.dataset.task;
}

});

function studioText(id){return document.getElementById(id).value.trim();}
function studioOutput(id,value){document.getElementById(id).textContent=value;}
document.getElementById('studioCvPrepare').addEventListener('click',()=>{
 const experience=studioText('studioCvText');
 studioOutput('studioCvOutput',experience?'PERFIL PROFISSIONAL\\n'+experience+'\\n\\nEXPERIÊNCIAS E RESULTADOS\\nOrganize as experiências acima por empresa, período, responsabilidades e resultados mensuráveis.\\n\\nCOMPETÊNCIAS\\nListe apenas habilidades que possa comprovar.':'Insira seu histórico profissional para preparar a estrutura.');
});
document.getElementById('studioAppPrepare').addEventListener('click',()=>{
 const role=studioText('studioAppRole'),exp=studioText('studioAppExperience');
 studioOutput('studioAppOutput',role&&exp?'Olá, tenho interesse na oportunidade de '+role+'.\\n\\nMinha experiência relevante inclui: '+exp+'\\n\\nGostaria de conversar sobre como posso contribuir.\\n\\nAtenciosamente,\\n[Seu nome]':'Informe o cargo e sua experiência comprovada.');
});
document.getElementById('studioCareerPrepare').addEventListener('click',()=>{
 const goal=studioText('studioCareerGoal'),gaps=studioText('studioCareerGap');
 studioOutput('studioCareerOutput',goal?'OBJETIVO: '+goal+'\\n1. Mapear requisitos de vagas reais relacionadas ao objetivo.\\n2. Avaliar evidências das competências: '+(gaps||'definir competências a desenvolver')+'.\\n3. Planejar atividades e entregas para os próximos 30 dias.\\n4. Revisar progresso e candidaturas a cada semana.':'Informe seu objetivo profissional.');
});

document.getElementById('aiCopy').addEventListener('click',async()=>{
const value=document.getElementById('aiJob').value,status=document.getElementById('aiStatus');
if(!value){status.textContent='Selecione uma vaga primeiro.';return;}
try{await navigator.clipboard.writeText(value);status.textContent='Link copiado. A análise de IA ainda requer backend privado.';}
catch(_){status.textContent='Abra a vaga diretamente na lista acima para copiar o link.';}
});
</script><script>
(()=>{'use strict';
const tabs=[['mainTabGeneral','mainPanelGeneral'],['mainTabRegional','mainPanelRegional'],['mainTabAI','mainPanelAI']];
function selectTab(index,focus){tabs.forEach(([tabId,panelId],i)=>{const tab=document.getElementById(tabId),panel=document.getElementById(panelId),active=i===index;if(!tab||!panel)return;tab.setAttribute('aria-selected',String(active));tab.tabIndex=active?0:-1;panel.hidden=!active;panel.style.display=active?'':'none';});if(focus)document.getElementById(tabs[index][0]).focus();}
tabs.forEach(([tabId],i)=>{const tab=document.getElementById(tabId);if(!tab)return;tab.addEventListener('click',()=>selectTab(i,false));tab.addEventListener('keydown',e=>{if(!['ArrowLeft','ArrowRight','Home','End'].includes(e.key))return;e.preventDefault();const next=e.key==='Home'?0:e.key==='End'?tabs.length-1:(i+(e.key==='ArrowRight'?1:-1)+tabs.length)%tabs.length;selectTab(next,true);});});
selectTab(0,false);
function setupTableSort(panelId){const panel=document.getElementById(panelId);if(!panel)return;const table=panel.querySelector('table'),tbody=table?.tBodies[0];if(!tbody)return;const buttons=[...table.querySelectorAll('.sort-column')];const collator=new Intl.Collator('pt-BR',{numeric:true,sensitivity:'base'});let col=-1,asc=true;
buttons.forEach(btn=>btn.addEventListener('click',()=>{const selected=Number(btn.dataset.column);asc=col===selected?!asc:true;col=selected;const rows=[...tbody.rows];rows.sort((a,b)=>{const av=col===6?a.dataset.published||'':a.cells[col].textContent.trim(),bv=col===6?b.dataset.published||'':b.cells[col].textContent.trim();if(!av&&!bv)return 0;if(!av)return 1;if(!bv)return -1;const cmp=collator.compare(av,bv);return asc?cmp:-cmp;});tbody.replaceChildren(...rows);buttons.forEach(b=>{const active=b===btn;b.closest('th').setAttribute('aria-sort',active?(asc?'ascending':'descending'):'none');b.querySelector('span').textContent=active?(asc?'↑':'↓'):'↕';});panel.dispatchEvent(new Event('table-sorted'));}));}
setupTableSort('mainPanelGeneral');
function setupPager(panelId,selector){const panel=document.getElementById(panelId);if(!panel)return;const ctl=panel.querySelector('.page-controls');if(!ctl)return;let items=[...panel.querySelectorAll(selector)],size=ctl.querySelector('.page-size'),prev=ctl.querySelector('.page-prev'),next=ctl.querySelector('.page-next'),summary=ctl.querySelector('.page-summary'),index=ctl.querySelector('.page-index');let page=1;
function render(){items=[...panel.querySelectorAll(selector)];const matching=items.filter(el=>el.dataset.filterPass!=='false');const limit=size.value==='all'?Math.max(1,matching.length):10;const pages=Math.max(1,Math.ceil(matching.length/limit));page=Math.min(page,pages);const from=(page-1)*limit;const slice=new Set(matching.slice(from,from+limit));for(const el of items)el.hidden=!slice.has(el);summary.textContent=matching.length+' resultado(s) correspondem aos filtros';index.textContent=size.value==='all'?'Todos':('Página '+page+' de '+pages);prev.disabled=page<=1||size.value==='all';next.disabled=page>=pages||size.value==='all';}
panel.addEventListener('table-sorted',()=>{page=1;render();});size.addEventListener('change',()=>{page=1;render();});prev.addEventListener('click',()=>{page=Math.max(1,page-1);render();});next.addEventListener('click',()=>{page++;render();});
const filterIds=panelId==='mainPanelGeneral'?['q','area','mode','source','region','city','age']:['regionalCompany','regionalCity','regionalArea','regionalQuery'];for(const id of filterIds){const el=document.getElementById(id);if(el)el.addEventListener('input',()=>{page=1;render();});}
render();
}
setupPager('mainPanelGeneral','tbody tr');
setupPager('mainPanelRegional','.regional-card');
})();
</script><script>
(()=>{
'use strict';
try{
const matchId=id=>document.getElementById(id);
const matchTerms={
 Projetos:['projetos','project','pmo','scrum','agile','stakeholder','gestão','management','cronograma','planning','orçamento','budget','risco','risk','liderança','leadership'],
 QA:['qa','qualidade','quality','testes','testing','automation','automação','selenium','playwright','cypress','api','regressão','regression','ci/cd','defeitos','bugs']
};
const matchNormalize=s=>String(s||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLocaleLowerCase('pt-BR');
const matchWords=s=>new Set(matchNormalize(s).match(/[a-z0-9+#./-]{3,}/g)||[]);
function matchScore(profile,description,job){
 const category=job.dataset.category||'Projetos';
 const dictionary=matchTerms[category]||[];
 const prof=matchNormalize(profile),vac=matchNormalize(description);
 const evidence=dictionary.filter(x=>prof.includes(matchNormalize(x))&&vac.includes(matchNormalize(x)));
 const required=dictionary.filter(x=>vac.includes(matchNormalize(x)));
 const missing=required.filter(x=>!prof.includes(matchNormalize(x)));
 const lexical=matchWords(description).size;
 const overlap=[...matchWords(description)].filter(x=>matchWords(profile).has(x)).length;
 const technical=required.length?Math.round(100*evidence.length/required.length):null;
 const lexicalScore=lexical?Math.min(100,Math.round(100*overlap/lexical)):null;
 const seniority=job.dataset.seniority||'Não informada';
 const seniorMarkers={'Sênior/Liderança':['senior','sênior','lead','lider','liderança','manager','gerente','coordenador'],'Júnior':['junior','júnior'],'Estágio':['estágio','estagiário','intern'],'Pleno':['pleno','mid-level']};
 const seniorKnown=!!seniorMarkers[seniority],seniorMatch=seniorKnown?seniorMarkers[seniority].some(t=>prof.includes(matchNormalize(t))):false;
 const metrics=[{name:'Competências mencionadas',weight:45,score:technical},{name:'Termos do anúncio',weight:35,score:lexicalScore},{name:'Evidência de senioridade',weight:20,score:seniorKnown?(seniorMatch?100:0):null}];
 const usable=metrics.filter(m=>m.score!==null),weight=usable.reduce((a,m)=>a+m.weight,0);
 const total=weight?Math.round(usable.reduce((a,m)=>a+m.weight*m.score,0)/weight):null;
 return {total,metrics,evidence,missing,confidence:weight===100?'Moderada':'Baixa',coverage:weight};
}
function showMatchResult(data){
 const el=matchId('matchResult');el.replaceChildren();
 const title=document.createElement('h3');title.textContent=data.total===null?'Dados insuficientes para estimar compatibilidade':'Match preliminar: '+data.total+'%';el.append(title);
 const info=document.createElement('p');info.textContent='Cobertura dos critérios: '+data.coverage+'% · Confiança: '+data.confidence+'. Este número NÃO prevê contratação. Requisitos não publicados não são avaliados.';el.append(info);
 const ul=document.createElement('ul');for(const metric of data.metrics){const li=document.createElement('li');li.textContent=metric.name+': '+(metric.score===null?'Sem dados':' '+metric.score+'%');ul.append(li);}el.append(ul);
 const evidence=document.createElement('p');evidence.textContent='Termos com evidência no perfil e anúncio: '+(data.evidence.join(', ')||'nenhum identificado')+'. Lacunas a verificar: '+(data.missing.join(', ')||'nenhuma nos termos identificados')+'.';el.append(evidence);
}
function matchLoadScript(url){
 return new Promise((resolve,reject)=>{const script=document.createElement('script');script.src=url;script.onload=resolve;script.onerror=()=>reject(new Error('Não foi possível carregar biblioteca de leitura de documentos.'));document.head.append(script);});
}
matchId('matchFile').addEventListener('change',async()=>{
 const file=matchId('matchFile').files[0],status=matchId('matchFileStatus');if(!file){status.textContent='Nenhum arquivo escolhido. Selecione novamente.';return;}status.textContent='Arquivo selecionado: '+file.name+' ('+Math.round(file.size/1024)+' KB). Iniciando leitura...';
 if(file.size>8*1024*1024){status.textContent='Arquivo maior que 8 MB. Escolha um arquivo menor.';return;}
 status.textContent='Lendo arquivo localmente...';
 try{
  const name=file.name.toLowerCase();let content='';
  if(name.endsWith('.txt')||name.endsWith('.md'))content=await file.text();
  else if(name.endsWith('.docx')){
   if(!window.mammoth)await matchLoadScript('https://cdn.jsdelivr.net/npm/mammoth@1.9.1/mammoth.browser.min.js');
   const result=await window.mammoth.extractRawText({arrayBuffer:await file.arrayBuffer()});content=result.value;
  }else if(name.endsWith('.pdf')){
   if(!window.pdfjsLib){await matchLoadScript('https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js');}
   window.pdfjsLib.GlobalWorkerOptions.workerSrc='https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
   const doc=await window.pdfjsLib.getDocument({data:new Uint8Array(await file.arrayBuffer())}).promise;
   if(doc.numPages>40)throw new Error('O PDF possui mais de 40 páginas.');
   const parts=[];for(let p=1;p<=doc.numPages;p++){const page=await doc.getPage(p);const c=await page.getTextContent();parts.push(c.items.map(x=>x.str||'').join(' '));}content=parts.join('\n');
  }else throw new Error('Formato inválido: utilize PDF, DOCX ou TXT.');
  if(!content.trim())throw new Error('Nenhum texto extraído. PDFs digitalizados precisam de OCR, que não está disponível nesta versão.');
  matchId('matchProfile').value=content.slice(0,40000);status.textContent='Arquivo carregado: '+file.name+' — '+content.length+' caracteres extraídos. Pronto para análise.';
 }catch(err){status.textContent='Não foi possível ler: '+err.message+' Cole o texto manualmente.';}
});
matchId('matchAnalyze').addEventListener('click',()=>{
 const job=matchId('aiJob'),opt=job.selectedOptions[0],profile=matchId('matchProfile').value.trim(),description=matchId('matchDescription').value.trim();
 if(!job.value){matchId('matchResult').textContent='Selecione uma vaga real para calcular a compatibilidade.';job.focus();return;}if(!profile){matchId('matchReviewDetails').open=true;matchId('matchResult').textContent='Carregue o currículo e aguarde a confirmação da extração, ou cole as experiências no perfil.';return;}
 if(!description){matchId('matchDescriptionDetails').open=true;matchId('matchResult').textContent='Perfil carregado. Para calcular um match confiável, abra “Adicionar descrição e requisitos da vaga” e cole os requisitos; a API pode fornecer somente o título.';return;}
 showMatchResult(matchScore(profile,description,opt));
});


}catch(error){const result=document.getElementById('matchResult'),status=document.getElementById('matchFileStatus');if(result)result.textContent='Não foi possível iniciar a análise local: '+error.message;if(status)status.textContent='Falha ao inicializar a leitura. Atualize a página.';}
})();
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
