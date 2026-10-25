"""Unified read-only dashboard for REAL QA and project job results (no sample data)."""
from __future__ import annotations
import argparse
import csv
import html
import json
import os
import re
from src.finance_advisor import render_advisor
from pathlib import Path
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from urllib.parse import urlencode, urlsplit


def e(value):
    return html.escape(str(value if value is not None else ""), quote=True)


def safe_url(value):
    parsed = urlsplit(str(value or ""))
    return str(value) if parsed.scheme == "https" and parsed.netloc else "#"



def recruiter_index_date(value):
    """Accessible Brazilian date for an index timestamp, never a post publication claim."""
    try:
        dt = datetime.fromisoformat(str(value or "").replace("Z", "+00:00"))
        if dt.tzinfo is None:
            return "Data do índice não informada", ""
        local = dt.astimezone(ZoneInfo("America/Sao_Paulo"))
        display = local.strftime("%d/%m/%Y às %Hh%M")
        accessible = local.strftime("%d de %B de %Y às %H horas e %M minutos")
        return display, accessible
    except (TypeError, ValueError, OverflowError):
        return "Data do índice não informada", ""


def recruiter_email(value):
    """Return only an explicitly published email address from public post text."""
    match = re.search(r"(?<![\w.+-])([A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,})(?![\w.-])", str(value or ""), re.I)
    return match.group(1).lower() if match else ""


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


def manufacturing_leadership_alert(title):
    """Match leadership roles whose advertised title is explicitly manufacturing-related."""
    value = re.sub(r"\s+", " ", str(title or "")).strip()
    leadership = r"(?:coordenador(?:a)?|gerente|manager|coordinator)"
    manufacturing = r"(?:manufatura|manufacturing|produ[cç][aã]o|production|opera[cç][oõ]es industriais|industrial operations|industrial|planta|plant)"
    return bool(re.search(
        rf"\b(?:{leadership}\b.{{0,70}}\b{manufacturing}|{manufacturing}\b.{{0,70}}\b{leadership})\b",
        value, re.I,
    ))



def usd_monthly_floor(job):
    """Only explicitly USD-denominated advertised salaries; no inferred amounts."""
    raw = str(job.get("salary") or job.get("salary_range") or "").strip()
    currency = str(job.get("salary_currency") or "").upper()
    if not raw or not (currency == "USD" or re.search(r"USD|US\\$|\\$", raw, re.I)):
        return None
    numbers = [float(x.replace(",", "")) for x in re.findall(r"(?<![\\w])(?:USD\\s*|US\\$\\s*|\\$\\s*)?(\\d{1,3}(?:,\\d{3})+(?:\\.\\d+)?|\\d{4,7}(?:\\.\\d+)?)", raw, re.I)]
    if not numbers:
        return None
    floor = min(numbers)
    if re.search(r"\\b(?:year|yearly|annual|annually|ano|anual|/yr|/year)\\b", raw, re.I):
        floor /= 12
    elif re.search(r"\\b(?:hour|hourly|hora|/hr|/hour)\\b", raw, re.I):
        floor *= 160
    elif not re.search(r"\\b(?:month|monthly|mensal|mês|/mo|/month)\\b", raw, re.I):
        return None
    return round(floor, 2)

def normalize(project_report, qa_jobs, linkedin_jobs=None, remote_jobs=None):
    rows, seen = [], set()
    for default_area, jobs in (("Projetos", project_report.get("jobs", [])), ("QA", qa_jobs)):
        for job in jobs:
            area = job.get("area") if job.get("area") in ("QA", "Projetos") else default_area
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
                "published_iso": published_iso(job.get("published")), "usd_monthly": usd_monthly_floor(job),
                "brazil": job.get("brazil_eligible") or "Não verificado", "description": str(job.get("description") or job.get("job_description") or job.get("requirements") or "")[:12000]
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
                     "published_iso": published_iso(job.get("published")), "usd_monthly": usd_monthly_floor(job), "brazil": "Não verificado", "description": str(job.get("description") or job.get("job_description") or job.get("requirements") or "")[:12000]})
    return rows


def render(project_report, qa_jobs, linkedin_jobs=None, regional_sources=None, remote_jobs=None, strategic=None):
    jobs = normalize(project_report, qa_jobs, linkedin_jobs, remote_jobs)
    qa_count = sum(x["area"] == "QA" for x in jobs)
    projects_count = sum(x["area"] == "Projetos" for x in jobs)
    body = "".join(
        '<tr data-usd-monthly="' + e(j.get("usd_monthly") or "") + '" data-area="' + e(j["area"]) + '" data-mode="' + e(j["mode_key"]) + '" data-source="' + e(j["source"]) + '" data-location="' + e(j["location"]) + '" data-city="' + e(j["regional_city"]) + '" data-published="' + e(j["published_iso"]) + '">' +
        '<td><a href="' + e(j["url"]) + '" target="_blank" rel="noopener noreferrer">' + e(studio_job_label(j["title"])) + '</a></td>' +
        "<td>" + e(j["company"]) + (" 🇺🇸" if j.get("usd_monthly") else "") + "</td><td>" + e(j["area"]) + "</td><td>" + e(j["location"]) +
        "</td><td>" + e(j["modality"]) + "</td><td>" + e(j["source"]) + "</td><td>" +
        e(j["published"]) + "</td></tr>" for j in jobs
    )
    source_options = "".join('<option value="' + e(s) + '">' + e(s) + '</option>' for s in sorted({j["source"] for j in jobs}))
    studio_jobs = [j for j in jobs if studio_job_eligible(j)]
    job_options = "".join(
        '<option data-category="' + e(j["area"]) +
        '" data-seniority="' + e(studio_seniority(j["title"])) +
        '" data-region="' + e(studio_region(j["location"], j["mode_key"])) +
        '" data-description="' + e(j.get("description", "")) + '" value="' + e(j["url"]) + '">' + e(studio_job_label(j["title"]) + " · " + j["company"] +
        (" · " + j["location"] if j["location"] else "")) + '</option>'
        for j in studio_jobs
    )
    studio_html = "<section id=\"ai-career-studio\" aria-labelledby=\"aiTitle\">\n<h2 id=\"aiTitle\">✦ Meu CV e Candidaturas · AI Career Studio</h2>\n<p>Importe seu perfil do LinkedIn em PDF e gere uma versão profissional do currículo com inteligência artificial.</p>\n<p><a class=\"recruiter-outreach\" href=\"https://ai-job-hunter-lucianoribeiro.vercel.app/dashboard\" target=\"_blank\" rel=\"noopener noreferrer\">Abrir minha área autenticada: perfis, CVs e candidaturas ↗</a> · <a href=\"https://ai-job-hunter-lucianoribeiro.vercel.app/applications/outreach\" target=\"_blank\" rel=\"noopener noreferrer\">Histórico de e-mails enviados ↗</a></p>\n<div class=\"ai-tabs\" role=\"tablist\" aria-label=\"Ferramentas de inteligência artificial\">\n<button type=\"button\" class=\"ai-tab\" data-task=\"fit\" aria-pressed=\"true\">Compatibilidade</button>\n<button type=\"button\" class=\"ai-tab\" data-task=\"cv\" aria-pressed=\"false\">CV Premium</button>\n<button type=\"button\" class=\"ai-tab\" data-task=\"application\" aria-pressed=\"false\">Candidatura</button>\n<button type=\"button\" class=\"ai-tab\" data-task=\"career\" aria-pressed=\"false\">Carreira</button>\n</div>\n<div class=\"ai-workspace\">\n<h3 id=\"aiTaskTitle\">AI Job Match</h3>\n<p id=\"aiTaskHelp\">Compare seu perfil com uma vaga e identifique aderência, evidências e lacunas.</p>\n<p class=\"muted\">Análise por IA ainda indisponível: a compatibilidade preliminar utiliza regras locais e exige os requisitos da vaga; não há avaliação por um modelo de IA conectado.</p>\n<div id=\"studioFitPanel\" class=\"studio-panel\">\n<details class=\"studio-advanced\" id=\"matchFilters\"><summary>Filtros de vagas</summary>\n<div class=\"studio-filters\"><label for=\"studioCategory\">Categoria profissional<select id=\"studioCategory\"><option value=\"Projetos\">Gestão de Projetos</option><option value=\"QA\">QA / Quality Engineering</option></select></label><label for=\"studioSeniority\">Senioridade<select id=\"studioSeniority\"><option value=\"\">Todas</option><option>Estágio</option><option>Júnior</option><option>Pleno</option><option>Sênior/Liderança</option><option>Não informada</option></select></label><label for=\"studioRegion\">Localização<select id=\"studioRegion\"><option value=\"\">Todas</option><option>Região de Campinas</option><option>Brasil</option><option>Remoto (elegibilidade a verificar)</option><option>Outra ou não informada</option></select></label></div>\n<p id=\"studioCount\" role=\"status\" aria-live=\"polite\"></p>\n</details>\n<label for=\"aiJob\">1. Selecione uma vaga para análise</label>\n<select id=\"aiJob\"><option value=\"\">Selecionar uma vaga do catálogo...</option>__AI_JOB_OPTIONS__</select>\n<div class=\"match-profile\">\n<h3>2. Envie seu currículo</h3>\n<p class=\"muted\">PDF do LinkedIn, CV em PDF, DOCX ou TXT. A leitura é feita no navegador.</p>\n<label for=\"matchFile\">Arquivo do perfil (PDF, DOCX, TXT)</label>\n<input type=\"file\" id=\"matchFile\" accept=\".pdf,.docx,.txt,.md,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,text/plain\">\n<p id=\"matchFileStatus\" role=\"status\" aria-live=\"polite\" class=\"muted\">Aguardando arquivo. Selecione PDF, DOCX ou TXT.</p>\n<details id=\"matchReviewDetails\"><summary>Editar perfil ou informar experiências manualmente</summary><label for=\"matchProfile\">Experiência e competências do perfil</label><textarea id=\"matchProfile\" rows=\"7\" placeholder=\"Texto extraído do currículo; edite se necessário.\"></textarea></details>\n<p id=\"matchRequirementsStatus\" class=\"muted\" role=\"status\" aria-live=\"polite\"></p>\n<details id=\"matchDescriptionDetails\"><summary>Requisitos da vaga — necessários para um score confiável</summary><label for=\"matchDescription\">Descrição original da vaga</label><textarea id=\"matchDescription\" rows=\"5\" placeholder=\"Cole os requisitos completos do anúncio.\"></textarea></details>\n<button type=\"button\" id=\"matchAnalyze\">3. Analisar compatibilidade</button>\n<div id=\"matchResult\" role=\"status\" aria-live=\"polite\"></div>\n<details class=\"match-method\"><summary>Como o resultado é calculado e privacidade</summary><p class=\"muted\">A pontuação compara evidências textuais do perfil com os requisitos da vaga. Não representa chance de contratação. Nenhum currículo é enviado ao servidor ou armazenado permanentemente. Bibliotecas públicas de leitura de PDF/DOCX são carregadas quando necessário.</p></details>\n</div>\n<div class=\"ai-actions\"><button type=\"button\" id=\"aiCopy\">Copiar link da vaga</button><span id=\"aiStatus\" role=\"status\"></span></div>\n<p class=\"muted\">Match local baseado em regras. Análise semântica por IA ainda não está disponível nesta versão.</p>\n</div>\n<div id=\"studioCvPanel\" class=\"studio-panel\" hidden>\n<h3>Seu novo currículo com IA</h3>\n<p>Exporte seu perfil no LinkedIn em PDF, selecione o arquivo e clique em Gerar meu CV com IA.</p>\n<label for=\"cvSourceFile\">Perfil do LinkedIn em PDF (ou currículo DOCX/TXT)</label>\n<input type=\"file\" id=\"cvSourceFile\" accept=\".pdf,.docx,.txt,.md\">\n<p id=\"cvFileStatus\" class=\"muted\" role=\"status\" aria-live=\"polite\">Ou cole o texto abaixo.</p>\n<label for=\"cvTargetRole\">Cargo-alvo (opcional)</label>\n<select id=\"cvTargetRole\"><option value=\"QA Lead / Quality Engineering Manager\">QA Lead / Quality Engineering Manager</option><option value=\"Senior QA Engineer\">Senior QA Engineer</option><option value=\"Gerente de Projetos\">Gerente de Projetos</option><option value=\"Coordenador de Manufatura\">Coordenador de Manufatura</option><option value=\"\">Outro / Sem cargo definido</option></select>\n<label for=\"cvLanguage\">Idioma do currículo</label>\n<select id=\"cvLanguage\"><option value=\"en\">Inglês (internacional)</option><option value=\"pt\">Português (Brasil)</option></select>\n<details><summary>Revisar texto extraído do arquivo</summary><label for=\"studioCvText\">Experiências, competências e conquistas reais</label><textarea id=\"studioCvText\" rows=\"10\" placeholder=\"Importe um arquivo ou cole aqui o texto integral do seu currículo ou LinkedIn.\"></textarea></details>\n<div style=\"display:flex;gap:10px;flex-wrap:wrap;margin:16px 0\"><button type=\"button\" id=\"studioCvPrepare\">Organizar CV localmente</button><button type=\"button\" id=\"studioCvAI\">Gerar meu CV com IA</button><button type=\"button\" id=\"studioCvDownload\">Baixar versão TXT</button></div>\n<label style=\"display:flex;gap:8px;align-items:flex-start\"><input type=\"checkbox\" id=\"cvAIConsent\" style=\"width:auto\"> Autorizo o envio do conteúdo deste CV ao serviço de IA configurado. Revise e retire informações sensíveis antes de enviar.</label>\n<p id=\"cvAIStatus\" class=\"muted\" role=\"status\" aria-live=\"polite\">A geração usa um serviço privado de IA. O sistema avisará se a conexão ainda não estiver disponível.</p>\n<pre id=\"studioCvOutput\" class=\"studio-output\" style=\"white-space:pre-wrap;overflow-wrap:anywhere\" aria-live=\"polite\"></pre>\n<p class=\"muted\">Nenhuma experiência, certificação, resultado ou métrica deve ser inventada. Revise o CV antes de enviá-lo a um recrutador. O arquivo não é salvo neste repositório público.</p>\n</div>\n<div id=\"studioApplicationPanel\" class=\"studio-panel\" hidden>\n<h3>Assistente de Candidatura</h3><p>Prepare uma mensagem inicial usando suas informações reais, sem envio automático.</p>\n<label for=\"studioAppRole\">Cargo e empresa</label><input id=\"studioAppRole\" placeholder=\"Ex.: Gerente de Projetos — Empresa\">\n<label for=\"studioAppExperience\">Experiência relevante comprovada</label><textarea id=\"studioAppExperience\" rows=\"4\" placeholder=\"Descreva competências e resultados reais.\"></textarea>\n<button type=\"button\" id=\"studioAppPrepare\">Preparar rascunho</button>\n<pre id=\"studioAppOutput\" class=\"studio-output\" aria-live=\"polite\"></pre>\n</div>\n<div id=\"studioCareerPanel\" class=\"studio-panel\" hidden>\n<h3>Planejamento de Carreira</h3><p>Monte um roteiro inicial de desenvolvimento profissional, sem análise automática de perfil.</p>\n<label for=\"studioCareerGoal\">Objetivo profissional</label><input id=\"studioCareerGoal\" placeholder=\"Ex.: Gerência de Projetos\">\n<label for=\"studioCareerGap\">Competências que deseja desenvolver</label><textarea id=\"studioCareerGap\" rows=\"3\" placeholder=\"Ex.: gestão de orçamento, inglês, liderança\"></textarea>\n<button type=\"button\" id=\"studioCareerPrepare\">Criar plano de ação</button>\n<pre id=\"studioCareerOutput\" class=\"studio-output\" aria-live=\"polite\"></pre>\n</div>\n</div>\n</section>"
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
    monitored_companies = {str(x.get("company", "")) for x in source_status if isinstance(x, dict)}
    manufacturing_alerts = [
        item for item in entries
        if item.get("company") in monitored_companies and manufacturing_leadership_alert(item.get("title"))
    ]
    alert_cards = "".join(
        '<li><a href="' + e(item["url"]) + '" target="_blank" rel="noopener noreferrer">' +
        e(item["title"]) + '</a><span>' + e(item["company"]) + ' · ' +
        e(item["city"] or "Cidade não verificada") + '</span></li>'
        for item in manufacturing_alerts
    )
    alert_html = (
        '<aside id="manufacturingLeadershipAlert" class="job-alert" aria-labelledby="manufacturingAlertTitle">'
        '<div><p class="alert-kicker">ALERTA AUTOMÁTICO</p><h3 id="manufacturingAlertTitle">'
        'Coordenação e Gerência de Manufatura</h3><p>Monitoramento diário nas empresas estratégicas para '
        'liderança em manufatura, produção e operações industriais.</p></div>'
        '<strong class="alert-count">' + str(len(manufacturing_alerts)) + ' alerta(s) ativo(s)</strong>' +
        ('<ul>' + alert_cards + '</ul>' if alert_cards else
         '<p class="alert-empty">Nenhuma vaga correspondente foi encontrada na coleta atual.</p>') +
        '<small>A cobertura depende dos portais integrados; fontes manuais não são tratadas como ausência de vagas.</small>'
        '</aside>'
    )
    company_cards = "".join(
        '<li><strong>' + e(item.get("company", "")) + '</strong> · ' + e(item.get("city", "")) +
        ' · ' + e({"manual": "Fonte ainda não integrada", "needs_connector": "Coleta incompleta (needs_connector)",
                   "ok": "Vagas identificadas", "portal_only": "Portal oficial monitorado · vagas ainda não coletadas", "no_open_registration": "Sem inscrições abertas no concurso consultado", "error": "Consulta indisponível"}.get(item.get("state"), "A verificar")) +
        (' · <a href="' + e(safe_url(item.get("url"))) + '" target="_blank" rel="noopener noreferrer">Portal</a>'
         if safe_url(item.get("url")) != "#" else '') + '</li>'
        for item in source_status if isinstance(item, dict)
    )
    monitored_count = len([x for x in source_status if isinstance(x, dict)])
    strategic_displayed = len(strategic_jobs) - strategic_duplicates - strategic_outside
    assert len(seen_jobs) == strategic_displayed + strategic_duplicates + strategic_outside + strategic_invalid
    live_count = len(entries)
    city_counts = {city: sum(j["city"] == city for j in entries) for city in city_scope}
    city_counts["unverified"] = sum(not j["city"] for j in entries)
    strategic_html = (
        '<section id="empresas-estrategicas" aria-labelledby="regionalTitle"><h2 id="regionalTitle">Vagas regionais · Sumaré, Paulínia e Americana</h2>'
        '<p>Vagas coletadas: ' + str(live_count) + '. Empresas acompanhadas: ' + str(monitored_count) +
        '. Empresas com vagas coletadas: ' + str(len(companies)) +
        '. Cidades são as informadas nos anúncios, nunca deduzidas pela sede da empresa.</p>'
        '<p class="regional-filter-note">O filtro Empresa mostra somente empresas com vagas encontradas na coleta atual. '
        'A lista Empresas acompanhadas inclui também empresas sem resultados ou com fontes ainda não integradas.</p>'
        + '<!-- MONICA_OPPORTUNITIES_SLOT -->' +
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
        '</div>' + "<div class=\"page-controls\" aria-label=\"Paginação de resultados\"><label>Mostrar<select class=\"page-size\"><option value=\"10\">10 por página</option><option value=\"all\">Todos</option></select></label><span class=\"page-summary\" role=\"status\"></span><button type=\"button\" class=\"page-prev\">Anterior</button><span class=\"page-index\"></span><button type=\"button\" class=\"page-next\">Próxima</button></div>" + '<details class="regional-sources" open><summary>Empresas acompanhadas (' + str(monitored_count) + ') · inclusive sem vagas coletadas</summary>'
        '<p>Esta é uma lista de empresas monitoradas, não de vagas abertas. A ausência de registros não significa ausência de contratações. Consulte os portais oficiais para cobertura adicional.</p><ul>' +
        company_cards + '</ul></details></section>'
    )

    # Manufacturing-only extraction from public post titles; all labels are tentative.
    import re as _re
    def manufacturing_details(title):
        text = str(title or "")
        roles = [
            ("Gerente industrial", r"gerente industrial|industrial manager|plant manager"),
            ("Gerente de produção", r"gerente de produ[cç][aã]o|production manager"),
            ("Coordenador de produção", r"coordenador(?:a)? de produ[cç][aã]o|production coordinator"),
            ("Supervisor de produção", r"supervisor(?:a)? de produ[cç][aã]o|production supervisor"),
            ("Coordenador de manufatura", r"coordenador(?:a)? de manufatura|manufacturing coordinator"),
            ("Gerente de operações", r"gerente de opera[cç][oõ]es|operations manager"),
        ]
        role = next((name for name, pattern in roles if _re.search(pattern, text, _re.I)), "Liderança industrial")
        location_match = _re.search(r"(?:Local:|Localidade:|em|–|-)\s*([A-Za-zÀ-ÿ ]{3,35})(?:/|\s*-\s*)SP\b", text, _re.I)
        location = (location_match.group(1).strip() + "/SP") if location_match else ""
        cities = ["Sumaré", "Campinas", "Paulínia", "Americana", "Nova Odessa", "Hortolândia", "Santa Bárbara", "Jundiaí", "Monte Mor", "Valinhos", "Vinhedo"]
        priority = any(city.casefold() in text.casefold() for city in cities)
        employer_match = _re.search(r"\bEmpresa:\s*([^|:]{2,65}?)(?=\s+Local:|\s+Prazo|\s+Cadastre|$)", text, _re.I)
        employer = employer_match.group(1).strip() if employer_match else ""
        deadline = _re.search(r"prazo de candidatura:\s*(\d{1,2}) de ([a-zç]+) de (\d{4})", text, _re.I)
        expired = False
        if deadline:
            months = {"janeiro": 1, "fevereiro": 2, "março": 3, "abril": 4, "maio": 5, "junho": 6, "julho": 7, "agosto": 8, "setembro": 9, "outubro": 10, "novembro": 11, "dezembro": 12}
            try:
                from datetime import date as _date
                expired = _date(int(deadline.group(3)), months[deadline.group(2).casefold()], int(deadline.group(1))) < _date.today()
            except (ValueError, KeyError):
                pass
        return {"role": role, "location": location, "employer": employer, "priority": priority, "expired": expired}

    monitor_file = Path("data/recruiter_monitor.json")
    monitor = json.loads(monitor_file.read_text(encoding="utf-8")) if monitor_file.exists() else {}
    monitor_items = list(monitor.get("items", []))
    # Merge actual public ATS vacancies already gathered by the project workflow.
    # Do not infer posting dates or represent ATS jobs as LinkedIn posts.
    ats_path = Path("data/project_jobs_poc.json")
    ats = json.loads(ats_path.read_text(encoding="utf-8")) if ats_path.exists() else {}
    from src.recruiter_monitor import industrial_project_role, explicit_city
    existing_links = {safe_url(item.get("url")) for item in monitor_items if isinstance(item, dict)}
    curated_path = Path("data/curated_industrial_projects.json")
    curated = json.loads(curated_path.read_text(encoding="utf-8")) if curated_path.exists() else {}
    for job in list(ats.get("jobs", [])) + list(curated.get("jobs", [])):
        if not isinstance(job, dict):
            continue
        role = (job.get("role") if job.get("curated") and job.get("role") in ("Gerente de Projetos", "Coordenador de Projetos", "Analista de Projetos") else industrial_project_role(str(job.get("title") or ""), str(job.get("description") or "")))
        url = safe_url(job.get("url"))
        if not role or url == "#" or url in existing_links:
            continue
        existing_links.add(url)
        location = str(job.get("location") or "")
        # Manufacturing results are scoped to explicitly located São Paulo vacancies.
        if not (re.search(r"(?:,|/|\\s)\\s*SP\\b|São Paulo|Sao Paulo", location, re.I) or (job.get("curated") and job.get("city") and str(job.get("location") or "").endswith(", SP"))):
            continue
        monitor_items.append({
            "area": "Manufatura", "role": role, "title": str(job.get("title") or ""),
            "indexed_excerpt": str(job.get("description") or "")[:1500],
            "city": str(job.get("city") or "").strip() or (location.split(",")[0].strip() if location.endswith(", SP") else "") or explicit_city(location) or explicit_city(str(job.get("title") or "")),
            "url": url, "published_at": "", "source": str(job.get("source") or "Public ATS"),
            "company": str(job.get("company") or ""), "modality": "Não informada",
            "post_origin": "Empresa", "contract_type": "Não informado",
            "salary_usd": None, "freelance_qa": "no", "source_kind": "curated" if job.get("curated") else "ats",
        })
    app_base = (os.environ.get("CAREER_APP_URL") or "https://ai-job-hunter-lucianoribeiro.vercel.app").strip().rstrip("/")
    if app_base and safe_url(app_base) == "#":
        app_base = ""
    monitor_cards = []
    # Deduplicate manufacturing posts with the same inferred role, company and city.
    seen_manufacturing = set()
    # Publication index timestamp is the primary sort key: newest first, across all areas.
    # Use the original ISO timestamp (UTC-aware) to avoid sorting localized display strings.
    ordered_items = sorted(
        [item for item in monitor_items if isinstance(item, dict)],
        key=lambda item: str(item.get("published_at") or ""),
        reverse=True,
    )
    for item in ordered_items:
        if not isinstance(item, dict):
            continue
        # Revalidate cached results so old production leadership cards do not reappear.
        if item.get("area") == "Manufatura":
            # Exclude non-SP and unknown-location cached ATS posts, including Bosch Portugal.
            item_city = str(item.get("city") or "")
            item_url = str(item.get("url") or "")
            if ("api.smartrecruiters.com/" in item_url or item.get("source_kind") == "ats") and not item_city:
                continue
            from src.recruiter_monitor import industrial_project_role
            verified_role = (item.get("role") if item.get("source_kind") == "curated" and item.get("role") in ("Gerente de Projetos", "Coordenador de Projetos", "Analista de Projetos") else industrial_project_role(str(item.get("title") or ""), str(item.get("indexed_excerpt") or "")))
            if not verified_role:
                continue
            item = {**item, "role": verified_role}
        category = e(item.get("area", "Não classificado"))
        modality = e(item.get("modality", "Não informada"))
        published, published_accessible = recruiter_index_date(item.get("published_at"))
        raw_title = item.get("title", "Publicação")
        title = e(raw_title)
        url = e(safe_url(item.get("url")))
        extra = ""
        origin = item.get("post_origin", "Não verificada")
        if origin not in ("Empresa", "Recrutador"):
            origin = "Não verificada"
        freelance = "yes" if item.get("area") == "QA" and item.get("freelance_qa") == "yes" else "no"
        salary = item.get('salary_usd')
        contract = item.get("contract_type", "Não informado")
        if contract not in ("CLT", "PJ", "B2B", "Cooperativa"):
            contract = "Não informado"
        if isinstance(salary, str) and salary.startswith('US$ '):
            extra += '<p class="recruiter-salary"><strong>Remuneração em USD:</strong> ' + e(salary) + '</p>'
        if freelance == "yes":
            extra += '<p class="recruiter-evidence"><strong>Freelancer QA identificado:</strong> ' + e(item.get("freelance_evidence", "")) + ' · confirmar condições no anúncio.</p>'
        if item.get("part_time_evidence"):
            extra += '<p class="recruiter-evidence">Flexibilidade mencionada: ' + e(item["part_time_evidence"]) + ' · carga horária a confirmar.</p>'
        if item.get("salary_evidence"):
            extra += '<p class="recruiter-evidence">Trecho da remuneração: ' + e(item["salary_evidence"]) + '</p>'
        if item.get("modality_evidence"):
            extra += '<p class="recruiter-evidence">Trecho da modalidade: ' + e(item["modality_evidence"]) + '</p>'
        if item.get("contract_evidence"):
            extra += '<p class="recruiter-evidence">Trecho da contratação: ' + e(item["contract_evidence"]) + '</p>'
        if item.get("contract_source") and contract != "Não informado":
            extra += '<p class="recruiter-evidence">Contrato confirmado em: ' + e(item["contract_source"]) + '</p>'
        application_url = safe_url(item.get("application_url"))
        if application_url != "#":
            extra += '<p><a href="' + e(application_url) + '" target="_blank" rel="noopener noreferrer">Ver anúncio de candidatura ↗</a></p>'
        # Extract only contacts explicitly present in public indexed text.
        indexed_text = re.sub(r"<[^>]+>", " ", str(item.get("indexed_excerpt") or ""))
        contact = recruiter_email(" ".join([str(raw_title), html.unescape(indexed_text), str(item.get("description") or "")]))
        if not contact and "SDET" in str(raw_title) and "Manual & Web/Mobile Automation with AI" in str(raw_title) and "Hyderabad" in str(raw_title):
            # Email verified against the original LinkedIn posting provided by the user.
            contact = "haridharani.s@bct-consulting.com"
        if not contact and "SDET / QA" in str(raw_title) and "IoT & AI" in str(raw_title) and "Crystal Ball" in str(raw_title):
            # Address visibly published in the original LinkedIn post provided by the user.
            contact = "payal@digital-twin-solution.com"
        if category == "Manufatura":
            details = manufacturing_details(raw_title)
            fingerprint = _re.sub(r"[^a-z0-9]+", " ", raw_title.casefold().replace("linkedin", "")).strip()
            key = (item["role"].casefold(), (item.get("company") or details["employer"]).casefold(), (item.get("city") or details["location"]).casefold()) if (item.get("company") or details["employer"]) and (item.get("city") or details["location"]) else (fingerprint,)
            if key in seen_manufacturing:
                continue
            seen_manufacturing.add(key)
            # The matching project role was verified above; never relabel it as production leadership.
            title = e(item["role"] + (" · " + (item.get("company") or details["employer"]) if (item.get("company") or details["employer"]) else "") + (" · " + details["location"] if details["location"] else ""))
            city = item.get("city") or details["location"] or ""
            extra += '<p class="recruiter-location">📍 Cidade: ' + e(city or "Não informada") + '</p>'
            if details["priority"]:
                extra += '<span class="recruiter-tag">Região prioritária</span>'
            if details["expired"]:
                extra += '<span class="recruiter-tag">Prazo informado vencido — verificar</span>'
            extra += '<details class="recruiter-original"><summary>Ver publicação original</summary><p>' + e(raw_title) + '</p></details>'
        # Keep the card compact: all actions appear in a dedicated footer.
        # The original publication remains the first, prominent action.
        # Indexed titles can contain full post excerpts; do not fabricate an employer or summary.
        link_label = "Ver vaga na fonte original" if item.get("source_kind") in ("ats", "curated") else "Ver publicação no LinkedIn"
        accessible_date = e("Data do índice público: " + published_accessible + ", horário de Brasília") if published_accessible else e(published)
        # Stable card action: rendered outside the optional excerpt/extra area.
        email_status = ('<p class="recruiter-email-status recruiter-email-found" role="status">✅ E-mail identificado: <strong>' + e(contact) + '</strong></p>') if contact else '<p class="recruiter-email-status recruiter-email-missing" role="status">⚠️ E-mail não identificado no índice público — confira a publicação original</p>'
        card_action = ""
        if app_base:
            handoff = app_base + "/applications/outreach?" + urlencode({
                "recipient": contact, "title": str(raw_title)[:160],
                "source": str(item.get("url") or ""),
                "description": str(item.get("description") or item.get("indexed_excerpt") or raw_title)[:2400],
            })
            label = "✉ Preparar candidatura com CV" if contact else "✉ Preparar CV · informar e-mail"
            card_action = ('<a class="recruiter-cta recruiter-cta-secondary" target="_blank" rel="noopener noreferrer" '
                           'href="' + e(handoff) + '">' + label + '</a>')
        monitor_cards.append(
            '<article class="recruiter-card" data-area="' + category + '" data-mode="' + modality + '" '
            'data-role="' + e(item.get("role") or ("Gerente de Projetos de TI" if category == "Projetos" else "")) + '" data-city="' + e(item.get("city") or (details["location"] if category == "Manufatura" else "") or "") + '" data-origin="' + e(origin) + '" data-contract="' + e(contract) + '" data-freelance="' + freelance + '" data-usd="' + ('yes' if isinstance(salary, str) and salary.startswith('US$ ') else 'no') + '">'
            '<div class="recruiter-badges">'
            '<span class="recruiter-pill recruiter-pill-area">' + category + '</span>'
            '<span class="recruiter-pill">' + modality + '</span>'
            '<span class="recruiter-pill recruiter-pill-origin">Origem: ' + e(origin) + '</span>'
            '<span class="recruiter-pill">Contrato: ' + e(contract) + '</span>' + ('<span class="recruiter-pill">Freelancer QA</span>' if freelance == "yes" else '') + '</div>'
            '<h3 class="recruiter-title">' + title + '</h3>'
            '<p class="recruiter-employer">Empresa: ' + e(item.get("company") or "não identificada no índice") + '</p>'
            + email_status +
            '<div class="recruiter-extra">' + extra + '</div>'
            '<div class="recruiter-index-date"><span aria-hidden="true">◷</span> '
            '<time aria-label="' + accessible_date + '" datetime="' + e(item.get("published_at", "")) + '">'
            + e(published) + '</time><span class="recruiter-index-note">' + ("Data não informada pela fonte" if item.get("source_kind") == "ats" else "Data do índice público · horário de Brasília") + '</span></div>'
            '<div class="recruiter-card-actions">'
            '<a class="recruiter-cta recruiter-cta-primary" target="_blank" rel="noopener noreferrer" href="' + url + '">'
            + link_label + ' ↗</a>' + card_action + '</div></article>'
        )
    checked_display, checked_accessible = recruiter_index_date(monitor.get("checked_at"))
    collection_state = {
        "ok": "Coleta concluída sem erros reportados",
        "partial": "Coleta parcial · algumas consultas falharam",
        "disabled": "Coleta desativada",
        "error": "Falha na coleta",
    }.get(monitor.get("status"), "Status da coleta não disponível")
    total_posts = len(monitor_cards)
    monitor_html = (
        '<section id="recruiter-results" style="padding:20px 0"><h2>Recruiter Monitor · Vagas e publicações</h2>'
        '<p>O monitor apresenta todas as publicações descobertas no índice público. '
        'Áreas e modalidades são classificadas com base no título e precisam ser verificadas no anúncio original.</p>'
        '<p><a class="recruiter-outreach" href="' + e(app_base + '/applications/outreach') + '" target="_blank" rel="noopener noreferrer">Abrir minhas candidaturas e consultar o status dos CVs ↗</a></p>'
        '<div class="recruiter-stats" aria-label="Resumo da coleta">'
        '<div class="recruiter-stat"><span>Última coleta</span><strong>' + e(checked_display) + '</strong>'
        '<small>Horário de Brasília</small></div>'
        '<div class="recruiter-stat"><span>Publicações coletadas</span><strong id="recruiter-total">' + str(total_posts) + '</strong>'
        '<small>Publicações pertinentes exibidas após validação</small></div>'
        '<div class="recruiter-stat"><span>Resultados exibidos</span><strong id="recruiter-count" role="status" aria-live="polite" aria-atomic="true">' + str(total_posts) + '</strong>'
        '<small>Após aplicar os filtros</small></div></div>'
        '<p class="recruiter-collection-status" role="status">' + e(collection_state) + '</p>'
        + ('<p id="recruiter-empty-note">Nenhuma publicação compatível com os critérios da coleta. Isso não significa ausência de vagas no mercado.</p>' if not total_posts else '')
        + '<div class="recruiter-controls" role="group" aria-label="Filtros do Recruiter Monitor">'
        '<label>Área <select id="recruiter-area"><option value="">Todas as áreas</option>'
        '<option>Manufatura</option><option>QA</option><option value="Projetos">Projetos de TI</option><option>Outros</option></select></label>'
        '<label>Cargo <select id="recruiter-role"><option value="">Todos os cargos</option></select></label>'
        '<label>Cidade <select id="recruiter-city"><option value="">Todas as cidades</option></select></label>'
        '<label>Modalidade <select id="recruiter-mode"><option value="">Todas</option>'
        '<option value="Remoto">Remoto mencionado</option><option value="Híbrido">Híbrido mencionado</option>'
        '<option value="Não informada">Não informada</option></select></label>'
        '<label>Salário <select id="recruiter-usd"><option value="">Todos os salários</option><option value="yes">Somente vagas com salário em USD</option></select></label>'
        '<label>Contrato <select id="recruiter-contract"><option value="">Todos</option><option>CLT</option><option>PJ</option><option>B2B</option><option>Cooperativa</option><option value="Não informado">Não informado</option></select></label>'
        '<button type="button" id="recruiter-clear" class="recruiter-clear">Limpar Filtros</button></div>'
        '<style>.career-hub-tabs{display:flex;gap:10px;flex-wrap:wrap;margin:0 0 20px}.career-hub-tabs button{flex:1;min-width:180px;padding:13px;background:#283848;color:white;border:1px solid #68768c;border-radius:12px;cursor:pointer;font-weight:700}.career-hub-tabs button[aria-selected=true]{background:#397d70;border-color:#9fe6cd}.career-hub-note{color:#a8bdd0;line-height:1.6}.career-hub-form{display:grid;gap:12px;max-width:800px;padding:20px;border:1px solid #4a5b6c;border-radius:14px}.career-hub-form input,.career-hub-form textarea,.career-hub-form select{width:100%;padding:12px;border:1px solid #657489;border-radius:8px;background:#19242e;color:white}.career-hub-form button{padding:12px;background:#397d70;color:white;border:1px solid #92dfc7;border-radius:9px;cursor:pointer}.career-hub-form button:disabled{opacity:.5}.recruiter-controls{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:16px;padding:20px;margin:20px 0 18px;border:1px solid #3b4754;border-radius:16px;background:#1b222b}.recruiter-controls label{display:flex;min-width:0;flex-direction:column;gap:8px;font-size:13px;font-weight:650;color:#dbe4ee;margin:0}.recruiter-controls select{width:100%;min-width:0;min-height:46px;padding:10px 36px 10px 12px;border:1px solid #596473;border-radius:10px;background-color:#202a35;color:#f5f7fa}.recruiter-controls select:hover{border-color:#8ba99f}.recruiter-controls select:focus-visible,.recruiter-clear:focus-visible{outline:3px solid #9fe1ca;outline-offset:2px}.recruiter-clear{align-self:end;min-height:46px;padding:11px 18px;border:1px solid #86c9b3;border-radius:10px;background:#316f61;color:#fff;font:inherit;font-weight:750;cursor:pointer;transition:background .15s,border-color .15s}.recruiter-clear:hover{background:#408b77;border-color:#b1ebd6}.recruiter-clear:active{background:#285d52}@media(max-width:950px){.recruiter-controls{grid-template-columns:repeat(2,minmax(0,1fr))}}@media(max-width:520px){.recruiter-controls{grid-template-columns:minmax(0,1fr);padding:16px;gap:14px}.recruiter-clear{width:100%}}.recruiter-stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin:18px 0}.recruiter-stat{border:1px solid #465363;border-radius:12px;background:#202c39;padding:15px;display:flex;flex-direction:column;gap:5px}.recruiter-stat span,.recruiter-stat small{color:#c1d0de;font-size:13px}.recruiter-stat strong{font-size:22px;color:#f4f7fa}.recruiter-collection-status{border-left:3px solid #5ec9b3;padding:8px 12px;color:#dae8ee;font-size:14px}.recruiter-card[hidden]{display:none!important}.recruiter-card{background:#202832;border:1px solid #465363;border-radius:16px;padding:18px;min-width:0;display:flex;flex-direction:column;gap:12px;color:#e8eef5}.recruiter-badges{display:flex;gap:7px;flex-wrap:wrap}.recruiter-pill{background:#363d49;color:#e0e9f3;border-radius:99px;padding:5px 10px;font-size:12px;font-weight:600}.recruiter-pill-area{background:#314f4a;color:#bcffe9}.recruiter-pill-origin{background:#39374d;color:#eee2ff}.recruiter-title{font-size:18px;line-height:1.4;color:#f1f5f9;margin:0;overflow-wrap:anywhere}.recruiter-employer{font-size:13px;color:#d0dae5;margin:0}.recruiter-index-date{border-top:1px solid #465363;padding-top:12px;color:#e3edf7;font-size:14px}.recruiter-index-note{display:block;color:#b2c5d7;font-size:12px;margin-top:4px}.recruiter-open{display:block;margin-top:auto;text-align:center;padding:12px 14px;border-radius:10px;background:#347d6d;color:white!important;font-weight:700;text-decoration:none;min-height:44px}.recruiter-open:hover,.recruiter-open:focus-visible{background:#409582;outline-offset:3px}.recruiter-extra{overflow-wrap:anywhere}.recruiter-email-status{font-size:13px;line-height:1.45;padding:9px 10px;border-radius:9px;margin:0;overflow-wrap:anywhere}.recruiter-email-found{color:#b9ffdc;background:#183f36;border:1px solid #4eac86}.recruiter-email-missing{color:#f3debb;background:#3a3125;border:1px solid #886b42}.recruiter-card-actions{display:grid;gap:8px;margin-top:auto}.recruiter-cta{display:block;text-align:center;padding:12px 10px;border-radius:10px;font-size:14px;line-height:1.3;font-weight:750;text-decoration:none;min-height:46px}.recruiter-cta-primary{background:#347d6d;color:#fff!important}.recruiter-cta-secondary{background:#1a2931;border:1px solid #61bbaa;color:#c4fff0!important}.recruiter-cta:hover,.recruiter-cta:focus-visible{filter:brightness(1.17);outline:2px solid #9de3d3;outline-offset:2px}</style>'
        '<p id="recruiter-filter-empty" hidden role="status">Nenhuma publicação corresponde aos filtros selecionados. Tente outro cargo, cidade ou modalidade.</p>'
        '<div id="recruiter-list" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,300px),1fr));gap:12px">'
        + "".join(monitor_cards) + '</div>'
        '<p style="font-size:12px;opacity:.7">A data do índice pode diferir da data do post. '
        'Nenhuma candidatura é enviada automaticamente.</p></section>'
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
.match-profile{margin-top:18px;padding:16px;border:1px solid #4b5760;border-radius:13px}.studio-advanced{border:1px solid #43515b;border-radius:10px;padding:10px 14px;margin-bottom:16px}.studio-advanced summary{cursor:pointer;font-weight:650}.studio-advanced .studio-filters{margin-top:12px}.studio-advanced #studioCount{font-weight:500;font-size:12px;color:#a2d4c5;margin-left:8px}.match-method{margin-top:14px}.match-profile details{margin:12px 0;border:1px solid #46535b;border-radius:9px;padding:12px}.match-profile summary{cursor:pointer;font-weight:650}.match-profile label{display:block;margin:15px 0 6px}.match-profile textarea{font:inherit;width:100%;background:#1b1f25;border:1px solid #626b78;border-radius:9px;padding:12px;color:#eee;resize:vertical}.match-profile input[type=file]{font:inherit}.match-profile button{cursor:pointer;background:#356e5e;color:white;border:1px solid #9ad2ba;padding:12px 16px;border-radius:10px;font-weight:700}#matchResult{margin-top:18px;line-height:1.6}#matchResult ul{padding-left:22px}.studio-panel[hidden]{display:none}.studio-panel label{display:block;margin:14px 0 6px}.studio-panel textarea{font:inherit;width:100%;background:#1b1f25;color:#f5f5f4;border:1px solid #626b78;border-radius:11px;padding:13px;resize:vertical}.studio-panel button{cursor:pointer;background:#356e5e;color:#fff;border:1px solid #8dc3ad;border-radius:10px;padding:12px 16px;margin-top:14px;font-weight:700}.studio-output{white-space:pre-wrap;overflow-wrap:anywhere;font:inherit;font-size:14px;line-height:1.6;color:#e9edf0}.studio-results{font-size:16px!important;color:#e7f4ef!important;font-weight:750;margin:12px 0 8px}#studioQuery{margin:10px 0 4px;font-size:16px;min-height:48px}#aiJob{font-size:16px;min-height:48px}.studio-filters{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin:14px 0}.studio-filters label{display:grid;gap:6px;color:#d6d9df;font-size:13px}#studioCount{color:#9bd4c6;font-size:12px}.ai-tabs{display:flex;flex-wrap:wrap;gap:10px;margin:16px 0}.ai-tab,.ai-actions button{cursor:pointer;border-radius:12px;background:#2b3038;color:#e4e5e7;border:1px solid #515960;padding:12px 16px;font-weight:700}.ai-tab[aria-pressed=true]{background:#477f71;border-color:#78af9f;color:white}.ai-workspace{background:#1b2026;border:1px solid #404750;border-radius:18px;padding:20px}.ai-workspace h3{color:white}.ai-workspace label{display:block;margin-bottom:8px;color:#d6d9df}.ai-actions{display:flex;gap:10px;align-items:center;margin-top:14px;flex-wrap:wrap}#aiStatus{color:#d3d7da;font-size:13px}.muted{color:#aeb4bd}
.regional-filters{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin:18px 0}.regional-filters label{font-size:13px;display:grid;gap:7px;color:#d6d9df}.regional-cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:13px}.regional-card{padding:17px;border:1px solid #46505a;border-radius:15px;background:#252a31}.regional-heading{display:flex;justify-content:space-between;align-items:start;gap:12px}.regional-pill{font-size:11px;border:1px solid #638e82;border-radius:20px;padding:4px 7px;white-space:nowrap}.regional-card p{color:#bbc3cc;font-size:13px;line-height:1.5}.regional-card summary,.regional-sources summary{cursor:pointer;color:#9bd4c6;font-weight:650}.regional-card details a{display:inline-block;margin-top:12px}.regional-sources{margin-top:20px}.regional-card[hidden]{display:none}
.job-alert{margin:18px 0;padding:18px;border:1px solid #b9914f;border-left:5px solid #e8bd78;border-radius:14px;background:#2a261f}.job-alert h3{margin:2px 0 5px;color:#fff}.job-alert p{margin:4px 0}.alert-kicker{color:#e8bd78!important;font-size:11px;font-weight:800;letter-spacing:1.5px}.alert-count{display:inline-block;margin:12px 0;color:#ffe1a8}.job-alert ul{display:grid;gap:9px;padding-left:20px}.job-alert li span{display:block;color:#bbc3cc;font-size:12px;margin-top:3px}.job-alert small{display:block;color:#aeb4bd;margin-top:12px}.alert-empty{color:#d7dbe0!important}
.primary-tabs{position:sticky;top:0;z-index:20;background:#171b21;border:1px solid #46505a;border-radius:16px;display:flex;gap:8px;padding:9px;margin:14px 0}.primary-tab{flex:1;min-height:48px;padding:12px;border:1px solid #515960;border-radius:10px;background:#292f37;color:#f5f5f4;font:inherit;font-weight:700;cursor:pointer}.primary-tab[aria-selected="true"]{background:#477f71;border-color:#9bd4c6;color:white}.primary-panel[hidden]{display:none!important}.primary-tab:focus-visible{outline:3px solid #e8bd78;outline-offset:2px}@media(max-width:650px){.primary-tabs{gap:5px}.primary-tab{font-size:12px;padding:10px 6px}}.page-controls{display:flex;flex-wrap:wrap;align-items:center;gap:12px;margin-top:18px;padding:12px;border:1px solid #414b55;border-radius:12px;background:#222830}.page-controls label{display:flex;gap:8px;align-items:center;font-size:14px}.page-controls select{width:auto;min-width:130px}.page-controls button{background:#323a43;color:#fff;border:1px solid #5b6976;border-radius:9px;padding:10px 14px;cursor:pointer;min-height:42px}.page-controls button:disabled{opacity:.45;cursor:not-allowed}.page-summary,.page-index{font-size:14px;color:#e6eeec}.page-controls button:focus-visible{outline:3px solid #e8bd78}@media(max-width:650px){.page-controls{gap:8px}.page-controls label,.page-summary{width:100%}}.sort-column{background:transparent;border:0;color:inherit;font:inherit;font-weight:700;text-transform:uppercase;cursor:pointer;display:inline-flex;align-items:center;gap:5px;padding:8px 3px;min-height:40px}.sort-column span[aria-hidden]{font-size:21px;line-height:1;min-width:22px;text-align:center;font-weight:900;color:#e8bd78}.brand-lockup{display:flex;align-items:center;gap:15px}.brand-symbol{display:inline-flex;flex:0 0 auto}.sort-column:hover{text-decoration:underline}.sort-column:focus-visible{outline:3px solid #e8bd78;outline-offset:2px}#ai-career-studio .ai-tabs,#ai-career-studio #studioFitPanel,#ai-career-studio #studioApplicationPanel,#ai-career-studio #studioCareerPanel{display:none!important}
#ai-career-studio #studioCvPanel{display:block!important}
#ai-career-studio #studioCvPrepare,#ai-career-studio #studioCvDownload{display:none!important}
#ai-career-studio #cvTargetRole,#ai-career-studio #cvLanguage{max-width:460px}
#ai-career-studio #studioCvAI{font-weight:750;padding:13px 23px;font-size:14px}
</style></head><body>
<header><div class="brand-lockup"><span class="brand-symbol" aria-hidden="true"><svg viewBox="0 0 64 64" width="48" height="48"><rect x="2" y="2" width="60" height="60" rx="16" fill="#c3a574"/><path d="M16 45V19h7v10h18V19h7v26h-7V36H23v9z" fill="#171a20"/><path d="M49 12l2.5 5.5L57 20l-5.5 2.5L49 28l-2.5-5.5L41 20l5.5-2.5z" fill="#fff5df"/></svg></span><h1>AI Job Hunter</h1></div><p>Oportunidades reais, de QA e Gerência / Coordenação de Projetos, em um só lugar.</p></header>
<aside id="account-bar" style="display:flex;justify-content:space-between;gap:12px;align-items:center;flex-wrap:wrap;padding:13px 16px;border:1px solid #415574;border-radius:12px;background:#162338;margin:12px 0" aria-label="Conta do AI Job Hunter"><span id="account-name" role="status">Entre pela Vercel para identificar sua conta.</span><span style="display:flex;gap:10px;flex-wrap:wrap"><a href="https://ai-job-hunter-lucianoribeiro.vercel.app/resumes">Entrar / Meu CV</a><a href="https://ai-job-hunter-lucianoribeiro.vercel.app/logout" id="account-logout">Encerrar sessão</a></span></aside>
<nav class="primary-tabs" aria-label="Navegação principal" role="tablist"><button type="button" class="primary-tab" id="mainTabGeneral" role="tab" aria-controls="mainPanelGeneral" aria-selected="true" tabindex="0">Oportunidades Gerais</button><button type="button" class="primary-tab" id="mainTabRegional" role="tab" aria-controls="mainPanelRegional" aria-selected="false" tabindex="-1">Oportunidades Regionais</button><button type="button" class="primary-tab" id="mainTabAI" role="tab" aria-controls="mainPanelAI" aria-selected="false" tabindex="-1">Meu CV e Candidaturas</button><button type="button" class="primary-tab" id="mainTabFinance" role="tab" aria-controls="mainPanelFinance" aria-selected="false" tabindex="-1">Consultor Salarial</button><button type="button" class="primary-tab" id="mainTabRecruiter" role="tab" aria-controls="mainPanelRecruiter" aria-selected="false" tabindex="-1">Recruiter Monitor</button></nav>
<div id="mainPanelGeneral" class="primary-panel" role="tabpanel" aria-labelledby="mainTabGeneral">
<section class="market-intelligence" aria-labelledby="market-heading" style="margin:20px 0;padding:22px;border:1px solid #415574;border-radius:18px;background:#152540"><h2 id="market-heading">Inteligência do Mercado · Histórico de oportunidades</h2><p style="color:#b7c7e0">Evolução mensal de vagas coletadas e posts públicos indexados. Os números representam a amostra encontrada, não todo o mercado.</p>""" + market_chart_html(len(monitor_cards)) + """</section>
<div class="summary" aria-label="Resumo das vagas filtradas"><article>Total de vagas<strong id="summary-total" aria-live="polite">""" + str(len(jobs)) + """</strong></article>
<article>QA<strong id="summary-qa" aria-live="polite">""" + str(qa_count) + """</strong></article>
<article>Projetos<strong id="summary-projects" aria-live="polite">""" + str(projects_count) + """</strong></article>
</div>
<section><h2>Pesquisar oportunidades</h2><div class="filters">
<input id="q" aria-label="Pesquisar vaga ou empresa" placeholder="Cargo, empresa, local...">
<select id="area" aria-label="Área"><option value="">Todas as áreas</option><option>QA</option><option>Projetos</option></select>
<select id="mode" aria-label="Modalidade"><option value="">Todas as modalidades</option>
<option value="remote">Remoto informado</option><option value="verify">Remoto citado — confirmar</option>
<option value="unknown">Não informado</option></select>
<select id="usdFilter" aria-label="Salário em dólar"><option value="">Todas as moedas</option><option value="usd">🇺🇸 Salário USD divulgado</option><option value="5000">🇺🇸 USD 5.000+/mês (salário divulgado)</option></select><select id="source" aria-label="Fonte das vagas"><option value="">Todas as fontes integradas</option>""" + source_options + """</select><select id="region" aria-label="Filtro regional"><option value="">Todas as localidades</option><option value="local">Vagas nas cidades da região</option><option value="remote">Remoto informado — conferir elegibilidade</option><option value="brazil">Brasil (localização genérica)</option><option value="unknown">Localização sem cidade regional identificada</option></select>
<select id="city" aria-label="Cidade regional"><option value="">Todas as cidades</option><option>Nova Odessa</option><option>Americana</option><option>Sumaré</option><option>Santa Bárbara d'Oeste</option><option>Hortolândia</option><option>Campinas</option></select>
<select id="age" aria-label="Data da publicação"><option value="">Todas as datas</option><option value="1">Último dia</option><option value="7">Últimos 7 dias</option><option value="15">Últimos 15 dias</option><option value="30">Últimos 30 dias</option><option value="unknown">Data não informada</option></select></div>
<p>Filtro regional baseado na cidade informada no anúncio; não calcula distância ou comprova elegibilidade para trabalho remoto.</p><p id="count" aria-live="polite"></p>
<div class="table"><table id="jobs-table"><thead><tr><th scope="col" aria-sort="none"><button type="button" class="sort-column" data-column="0" aria-label="Ordenar por Cargo">Cargo <span aria-hidden="true">↕</span></button></th><th scope="col" aria-sort="none"><button type="button" class="sort-column" data-column="1" aria-label="Ordenar por Empresa">Empresa <span aria-hidden="true">↕</span></button></th><th scope="col" aria-sort="none"><button type="button" class="sort-column" data-column="2" aria-label="Ordenar por Área">Área <span aria-hidden="true">↕</span></button></th><th scope="col" aria-sort="none"><button type="button" class="sort-column" data-column="3" aria-label="Ordenar por Local">Local <span aria-hidden="true">↕</span></button></th><th scope="col" aria-sort="none"><button type="button" class="sort-column" data-column="4" aria-label="Ordenar por Modalidade">Modalidade <span aria-hidden="true">↕</span></button></th><th scope="col" aria-sort="none"><button type="button" class="sort-column" data-column="5" aria-label="Ordenar por Fonte">Fonte <span aria-hidden="true">↕</span></button></th><th scope="col" aria-sort="none"><button type="button" class="sort-column" data-column="6" aria-label="Ordenar por Publicação">Publicação <span aria-hidden="true">↕</span></button></th></tr></thead><tbody>""" + body + """</tbody></table></div>
<div class="page-controls" aria-label="Paginação de resultados"><label>Mostrar<select class="page-size"><option value="10">10 por página</option><option value="all">Todos</option></select></label><span class="page-summary" role="status"></span><button type="button" class="page-prev">Anterior</button><span class="page-index"></span><button type="button" class="page-next">Próxima</button></div><p id="empty" hidden>Nenhuma vaga corresponde aos filtros.</p>
</section>
</div>
<div id="mainPanelRegional" class="primary-panel" role="tabpanel" aria-labelledby="mainTabRegional" hidden>""" + strategic_html + """</div>
<div id="mainPanelAI" class="primary-panel" role="tabpanel" aria-labelledby="mainTabAI" hidden>
<div class="career-hub">
<nav class="career-hub-tabs" role="tablist" aria-label="Currículos e candidaturas" style="display:flex!important;flex-wrap:wrap;gap:12px;padding:12px;margin:0 0 18px;border:1px solid #55677b;border-radius:14px;background:#202a34"><button type="button" id="careerHubCV" role="tab" aria-controls="careerHubCVPanel" aria-selected="true" style="flex:1;min-width:180px;min-height:50px;background:#397d70;color:#fff;border:1px solid #8acdbb;border-radius:9px;font-weight:750;cursor:pointer">Meu CV</button><button type="button" id="careerHubApplications" role="tab" aria-controls="careerHubApplicationsPanel" aria-selected="false" style="flex:1;min-width:180px;min-height:50px;background:#283848;color:#fff;border:1px solid #66778c;border-radius:9px;font-weight:750;cursor:pointer">Minhas Candidaturas</button></nav>
<section id="careerHubCVPanel" role="tabpanel" aria-labelledby="careerHubCV"><p class="career-hub-note">Importe e prepare seu CV. O upload privado ainda requer integração à aplicação autenticada.</p>""" + studio_html + """</section>
<section id="careerHubApplicationsPanel" role="tabpanel" aria-labelledby="careerHubApplications" hidden><h2>Minhas Candidaturas</h2><p>Prepare uma mensagem para um recrutador. Esta página pública não armazena CVs ou histórico pessoal e não envia e-mails.</p>
<div class="career-hub-form"><label for="careerJobRole">Cargo e empresa</label><input id="careerJobRole" maxlength="180" placeholder="Ex.: QA Lead — Empresa">
<label for="careerRecruiter">E-mail divulgado no anúncio</label><input id="careerRecruiter" type="email" maxlength="254" placeholder="recrutamento@empresa.com">
<label for="careerLanguage">Idioma da mensagem</label><select id="careerLanguage"><option value="en">Inglês</option><option value="pt">Português</option></select>
<label for="careerExperience">Experiência comprovada</label><textarea id="careerExperience" rows="4" maxlength="1800"></textarea>
<button id="careerPrepare" type="button">Preparar mensagem</button><p id="careerDraftStatus" role="status" aria-live="polite"></p>
<label for="careerDraftBody">Mensagem para revisão</label><textarea id="careerDraftBody" rows="10" readonly></textarea><button id="careerCopy" type="button" disabled>Copiar mensagem</button></div>
<p class="career-hub-note">Para anexar o PDF privado e confirmar um envio real, será necessário login e backend autenticado. Criar uma mensagem não significa enviar a candidatura.</p></section></div></div>
<div id="mainPanelFinance" class="primary-panel" role="tabpanel" aria-labelledby="mainTabFinance" hidden>""" + render_advisor() + """</div><div id="mainPanelRecruiter" class="primary-panel" role="tabpanel" aria-labelledby="mainTabRecruiter" hidden>""" + monitor_html + """</div>
<footer>Dados obtidos de anúncios públicos. Remoto e elegibilidade brasileira exigem confirmação
na página oficial. Fonte Himalayas: <a href="https://himalayas.app">himalayas.app</a>. Apenas datas de publicação fornecidas pelas fontes são exibidas; datas ausentes não são estimadas. Candidaturas não são enviadas automaticamente.</footer>
<script>
const recruiterArea=document.getElementById('recruiter-area'),recruiterRole=document.getElementById('recruiter-role'),recruiterCity=document.getElementById('recruiter-city'),recruiterMode=document.getElementById('recruiter-mode'),recruiterUsd=document.getElementById('recruiter-usd'),recruiterContract=document.getElementById('recruiter-contract');
function filterRecruiter(){
 if(!recruiterArea||!recruiterMode||!recruiterUsd||!recruiterContract)return;
 let visible=0;
 document.querySelectorAll('.recruiter-card').forEach(card=>{
  const area=!recruiterArea.value||card.dataset.area===recruiterArea.value;
  const role=!recruiterRole||!recruiterRole.value||card.dataset.role===recruiterRole.value;
  const city=!recruiterCity||!recruiterCity.value||card.dataset.city===recruiterCity.value;
  const mode=!recruiterMode.value||card.dataset.mode.startsWith(recruiterMode.value);
  const usd=!recruiterUsd.value||card.dataset.usd===recruiterUsd.value;
  const contract=!recruiterContract.value||card.dataset.contract===recruiterContract.value;
  card.hidden=!(area&&role&&city&&mode&&usd&&contract);
  if(!card.hidden)visible++;
 });
 const count=document.getElementById('recruiter-count');
 if(count)count.textContent=String(visible);
 const empty=document.getElementById('recruiter-filter-empty');
 if(empty)empty.hidden=visible!==0;
}
if(recruiterArea&&recruiterMode&&recruiterUsd&&recruiterContract){
 const available=[...document.querySelectorAll('.recruiter-card')];
 function fillRecruiterSelect(select,values,placeholder){const previous=select.value;select.replaceChildren(new Option(placeholder,''),...values.map(v=>new Option(v,v)));if(values.includes(previous))select.value=previous;}
 function refreshRecruiterOptions(){
  if(!recruiterRole||!recruiterCity)return filterRecruiter();
  const cards=available.filter(c=>!recruiterArea.value||c.dataset.area===recruiterArea.value);
  const industrialRoles=['Gerente de Projetos','Coordenador de Projetos','Analista de Projetos'];
  const roles=recruiterArea.value==='Manufatura'?industrialRoles:recruiterArea.value===''
   ?[...new Set([...industrialRoles,...cards.map(c=>c.dataset.role).filter(Boolean)])]
   :[...new Set(cards.map(c=>c.dataset.role).filter(Boolean))].sort();
  fillRecruiterSelect(recruiterRole,roles,'Todos os cargos');
  fillRecruiterSelect(recruiterCity,[...new Set(cards.map(c=>c.dataset.city).filter(Boolean))].sort(),'Todas as cidades');
  filterRecruiter();
 }
 recruiterArea.addEventListener('change',refreshRecruiterOptions);
 for(const select of [...(recruiterRole?[recruiterRole]:[]),...(recruiterCity?[recruiterCity]:[]),recruiterMode,recruiterUsd,recruiterContract])select.addEventListener('change',filterRecruiter);
 document.getElementById('recruiter-clear')?.addEventListener('click',()=>{
  for(const select of [recruiterArea,recruiterRole,recruiterCity,recruiterMode,recruiterUsd,recruiterContract])if(select)select.value='';
  refreshRecruiterOptions();
 });
 refreshRecruiterOptions();
}
document.querySelector('.ai-tab[data-task="cv"]')?.click();
const cvStudio=document.getElementById('studioCvPanel');
if(cvStudio){const workspace=cvStudio.parentElement;for(const child of [...workspace.children]){if(child!==cvStudio && child.id!=='studioFitPanel' && child.id!=='studioApplicationPanel' && child.id!=='studioCareerPanel' && child.id!=='aiTaskTitle' && child.id!=='aiTaskHelp' && child.matches('p.muted'))child.hidden=true;}const title=document.getElementById('aiTaskTitle');if(title)title.hidden=true;const hint=document.getElementById('aiTaskHelp');if(hint)hint.hidden=true;}

const mainTabPairs=[['mainTabGeneral','mainPanelGeneral'],['mainTabRegional','mainPanelRegional'],['mainTabAI','mainPanelAI'],['mainTabFinance','mainPanelFinance'],['mainTabRecruiter','mainPanelRecruiter']];
function activateMainTab(index,focus=false){mainTabPairs.forEach(([tid,pid],i)=>{const active=i===index,tab=document.getElementById(tid),panel=document.getElementById(pid);tab.setAttribute('aria-selected',String(active));tab.tabIndex=active?0:-1;panel.hidden=!active;});if(focus)document.getElementById(mainTabPairs[index][0]).focus();}
mainTabPairs.forEach(([tid],i)=>{const tab=document.getElementById(tid);tab.addEventListener('click',()=>activateMainTab(i));tab.addEventListener('keydown',evt=>{if(!['ArrowRight','ArrowLeft','Home','End'].includes(evt.key))return;evt.preventDefault();const next=evt.key==='Home'?0:evt.key==='End'?mainTabPairs.length-1:(i+(evt.key==='ArrowRight'?1:-1)+mainTabPairs.length)%mainTabPairs.length;activateMainTab(next,true);});});
activateMainTab(0);
const q=document.getElementById('q'),a=document.getElementById('area'),m=document.getElementById('mode'),source=document.getElementById('source'),region=document.getElementById('region'),city=document.getElementById('city'),age=document.getElementById('age'),usdFilter=document.getElementById('usdFilter');
const rows=[...document.querySelectorAll('#jobs-table tbody tr')],count=document.getElementById('count');
function apply(){let visible=0,qaVisible=0,projectsVisible=0;for(const r of rows){
const local=Boolean(r.dataset.city),location=(r.dataset.location||'').toLocaleLowerCase();
const locOK=!region.value||(region.value==='local'?local:region.value==='remote'?r.dataset.mode==='remote':region.value==='brazil'?(!local&&/brasil|brazil/.test(location)):!local);
const cityOK=!city.value||r.dataset.city===city.value;
const published=r.dataset.published;
let dateOK=!age.value||(age.value==='unknown'?!published:false);
if(age.value&&age.value!=='unknown'&&published){const date=Date.parse(published+'T00:00:00Z');const now=Date.now();const elapsed=(now-date)/86400000;dateOK=elapsed>=0&&elapsed<=Number(age.value);}
const usd=Number(r.dataset.usdMonthly||0),usdOK=!usdFilter.value||(usdFilter.value==='usd'?usd>0:usd>=5000);const show=usdOK&&dateOK&&locOK&&cityOK&&(!a.value||r.dataset.area===a.value)&&(!m.value||r.dataset.mode===m.value)&&(!source.value||r.dataset.source===source.value)&&
r.textContent.toLocaleLowerCase().includes(q.value.trim().toLocaleLowerCase());
r.hidden=!show;r.dataset.filterPass=String(show);if(show){visible++;if(r.dataset.area==='QA')qaVisible++;else if(r.dataset.area==='Projetos')projectsVisible++;}
}document.getElementById('summary-total').textContent=String(visible);
document.getElementById('summary-qa').textContent=String(qaVisible);
document.getElementById('summary-projects').textContent=String(projectsVisible);
count.textContent=visible+' vaga(s) exibida(s)';document.getElementById('empty').hidden=visible!==0;}
[q,a,m,source,region,city,age,usdFilter].forEach(el=>el.addEventListener('input',apply));apply();

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
function cvLoadScript(url){
 return new Promise((resolve,reject)=>{const script=document.createElement('script');script.src=url;script.onload=resolve;script.onerror=()=>reject(new Error('Não foi possível carregar o leitor de documentos.'));document.head.append(script);});
}
const cvFile=document.getElementById('cvSourceFile'),cvSource=document.getElementById('studioCvText'),cvStatus=document.getElementById('cvFileStatus');
cvFile.addEventListener('change',async()=>{
 const file=cvFile.files[0];if(!file)return;
 if(file.size>8*1024*1024){cvStatus.textContent='Arquivo acima de 8 MB.';return;}
 cvStatus.textContent='Lendo arquivo localmente...';
 try{
  let content='';const name=file.name.toLowerCase();
  if(name.endsWith('.txt')||name.endsWith('.md'))content=await file.text();
  else if(name.endsWith('.docx')){
   if(!window.mammoth)await cvLoadScript('https://cdn.jsdelivr.net/npm/mammoth@1.9.1/mammoth.browser.min.js');
   content=(await window.mammoth.extractRawText({arrayBuffer:await file.arrayBuffer()})).value;
  }else if(name.endsWith('.pdf')){
   if(!window.pdfjsLib)await cvLoadScript('https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js');
   window.pdfjsLib.GlobalWorkerOptions.workerSrc='https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
   const pdf=await window.pdfjsLib.getDocument({data:new Uint8Array(await file.arrayBuffer())}).promise;
   if(pdf.numPages>40)throw new Error('Limite de 40 páginas');
   const pages=[];for(let i=1;i<=pdf.numPages;i++){const page=await pdf.getPage(i);const result=await page.getTextContent();pages.push(result.items.map(t=>t.str||'').join(' '));}
   content=pages.join('\\n');
  }else throw new Error('Formato não suportado.');
  if(content.trim().length<30)throw new Error('Texto insuficiente; tente DOCX ou cole o texto.');
  cvSource.value=content.slice(0,40000);document.querySelector('#studioCvText').closest('details').open=true;
  cvStatus.textContent='Arquivo lido localmente: '+file.name+'. Confira o texto antes de prosseguir.';
 }catch(error){cvStatus.textContent='Erro: '+error.message+' Você pode colar o texto manualmente.';}
});
function cvContent(){return cvSource.value.trim();}
function cvResult(value){document.getElementById('studioCvOutput').textContent=value;}
document.getElementById('studioCvPrepare').addEventListener('click',()=>{
 const input=cvContent();if(input.length<30){cvStatus.textContent='Envie um arquivo ou cole seu perfil profissional primeiro.';return;}
 const role=document.getElementById('cvTargetRole').value||'Cargo desejado';
 const lang=document.getElementById('cvLanguage').value;
 cvResult((lang==='pt'?'CURRÍCULO PROFISSIONAL':'PROFESSIONAL RESUME')+'\\n'+role+'\\n\\n'+(lang==='pt'?'HISTÓRICO E EVIDÊNCIAS ORIGINAIS':'ORIGINAL EXPERIENCE AND EVIDENCE')+'\\n'+input+'\\n\\n'+(lang==='pt'?'REVISAR ANTES DE ENVIAR: resumo, resultados mensuráveis comprovados, ordem das experiências e habilidades técnicas.':'REVIEW BEFORE SENDING: summary, verified measurable results, work chronology and technical skills.'));
 document.getElementById('cvAIStatus').textContent='Versão organizada localmente. Para reescrita profissional, use Aprimorar com IA.';
});
document.getElementById('studioCvAI').addEventListener('click',async()=>{
 const btn=document.getElementById('studioCvAI'),status=document.getElementById('cvAIStatus');
 const profile=cvContent(),endpoint=window.AI_MATCH_API_URL||'';
 if(profile.length<50){status.textContent='Carregue seu currículo (mínimo 50 caracteres).';return;}
 if(!document.getElementById('cvAIConsent').checked){status.textContent='Autorize explicitamente o envio do currículo para a IA.';return;}
 if(!endpoint){status.textContent='O serviço de IA ainda não foi configurado.';return;}
 btn.disabled=true;status.textContent='Solicitando revisão profissional à IA...';
 try{
  const controller=new AbortController(),timeout=setTimeout(()=>controller.abort(),25000);let response;
  try{response=await fetch(endpoint+'/cv',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({profile:profile.slice(0,30000),role:document.getElementById('cvTargetRole').value,language:document.getElementById('cvLanguage').value,consent:true}),signal:controller.signal});}finally{clearTimeout(timeout);}
  let data=await response.json();if(!response.ok)throw new Error(data.error||'Endpoint de geração indisponível');
  const output=String(data.cv||data.resume||'').trim();if(output.length<80)throw new Error('O serviço não retornou um currículo válido');
  cvResult(output);status.textContent='Rascunho gerado por IA. Revise cada afirmação antes de enviar.';
 }catch(error){status.textContent='Não foi possível gerar por IA: '+error.message+'. A versão local continua disponível.';}finally{btn.disabled=false;}
});
document.getElementById('studioCvDownload').addEventListener('click',()=>{
 const content=document.getElementById('studioCvOutput').textContent;
 if(!content.trim()){document.getElementById('cvAIStatus').textContent='Gere uma versão do CV antes de baixar.';return;}
 const url=URL.createObjectURL(new Blob([content],{type:'text/plain;charset=utf-8'}));
 const link=document.createElement('a');link.href=url;link.download='cv-premium.txt';document.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
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
(()=>{
const cv=document.getElementById('careerHubCV'),apps=document.getElementById('careerHubApplications'),cvPanel=document.getElementById('careerHubCVPanel'),appsPanel=document.getElementById('careerHubApplicationsPanel');
function show(app){cv.setAttribute('aria-selected',String(!app));apps.setAttribute('aria-selected',String(app));cv.style.background=app?'#283848':'#397d70';apps.style.background=app?'#397d70':'#283848';cvPanel.hidden=app;appsPanel.hidden=!app;cvPanel.style.display=app?'none':'block';appsPanel.style.display=app?'block':'none';}
cv.addEventListener('click',()=>show(false));apps.addEventListener('click',()=>show(true));
const button=document.getElementById('careerPrepare'),copy=document.getElementById('careerCopy'),result=document.getElementById('careerDraftBody'),status=document.getElementById('careerDraftStatus');
button.addEventListener('click',()=>{const role=document.getElementById('careerJobRole').value.trim(),email=document.getElementById('careerRecruiter'),exp=document.getElementById('careerExperience').value.trim(),en=document.getElementById('careerLanguage').value==='en';
if(!role||!exp||!email.value.trim()||!email.checkValidity()){status.textContent='Preencha o cargo, o e-mail válido e a experiência.';return;}
result.value=en?['Hello,','I would like to apply for '+role+'.',exp,'I would be happy to share my resume for your consideration.','Best regards,'].join(String.fromCharCode(10,10)):['Olá,','Tenho interesse na oportunidade de '+role+'.',exp,'Posso encaminhar meu currículo para sua avaliação.','Atenciosamente,'].join(String.fromCharCode(10,10));
copy.disabled=false;status.textContent='Rascunho preparado localmente. Nenhum e-mail foi enviado.';});
copy.addEventListener('click',async()=>{try{await navigator.clipboard.writeText(result.value);status.textContent='Texto copiado. Nenhum e-mail foi enviado.';}catch(e){result.select();status.textContent='Copie a mensagem selecionada manualmente.';}});
})();
const tabs=[['mainTabGeneral','mainPanelGeneral'],['mainTabRegional','mainPanelRegional'],['mainTabAI','mainPanelAI'],['mainTabFinance','mainPanelFinance'],['mainTabRecruiter','mainPanelRecruiter']];
function selectTab(index,focus){tabs.forEach(([tabId,panelId],i)=>{const tab=document.getElementById(tabId),panel=document.getElementById(panelId),active=i===index;if(!tab||!panel)return;tab.setAttribute('aria-selected',String(active));tab.tabIndex=active?0:-1;panel.hidden=!active;panel.style.display=active?'':'none';});if(focus)document.getElementById(tabs[index][0]).focus();}
tabs.forEach(([tabId],i)=>{const tab=document.getElementById(tabId);if(!tab)return;tab.addEventListener('click',()=>selectTab(i,false));tab.addEventListener('keydown',e=>{if(!['ArrowLeft','ArrowRight','Home','End'].includes(e.key))return;e.preventDefault();const next=e.key==='Home'?0:e.key==='End'?tabs.length-1:(i+(e.key==='ArrowRight'?1:-1)+tabs.length)%tabs.length;selectTab(next,true);});});
selectTab(0,false);
function setupTableSort(panelId,tableSelector){const panel=document.getElementById(panelId);if(!panel)return;const table=panel.querySelector(tableSelector),tbody=table?.tBodies[0];if(!tbody)return;const buttons=[...table.querySelectorAll('.sort-column')];const collator=new Intl.Collator('pt-BR',{numeric:true,sensitivity:'base'});let col=-1,asc=true;
buttons.forEach(btn=>btn.addEventListener('click',()=>{const selected=Number(btn.dataset.column);asc=col===selected?!asc:selected!==6;col=selected;const rows=[...tbody.rows];rows.sort((a,b)=>{const av=col===6?a.dataset.published||'':a.cells[col].textContent.trim(),bv=col===6?b.dataset.published||'':b.cells[col].textContent.trim();if(!av&&!bv)return 0;if(!av)return 1;if(!bv)return -1;const cmp=collator.compare(av,bv);return asc?cmp:-cmp;});tbody.replaceChildren(...rows);buttons.forEach(b=>{const active=b===btn;b.closest('th').setAttribute('aria-sort',active?(asc?'ascending':'descending'):'none');b.querySelector('span').textContent=active?(asc?'↑':'↓'):'↕';});panel.dispatchEvent(new Event('table-sorted'));}));}
setupTableSort('mainPanelGeneral','#jobs-table');
// Initial view is always newest published first; undated rows remain last.
const newestButton=document.querySelector('#mainPanelGeneral .sort-column[data-column="6"]');if(newestButton)newestButton.click();
function setupPager(panelId,selector){const panel=document.getElementById(panelId);if(!panel)return;const ctl=panel.querySelector('.page-controls');if(!ctl)return;let items=[...panel.querySelectorAll(selector)],size=ctl.querySelector('.page-size'),prev=ctl.querySelector('.page-prev'),next=ctl.querySelector('.page-next'),summary=ctl.querySelector('.page-summary'),index=ctl.querySelector('.page-index');let page=1;
function render(){items=[...panel.querySelectorAll(selector)];const matching=items.filter(el=>el.dataset.filterPass!=='false');const limit=size.value==='all'?Math.max(1,matching.length):10;const pages=Math.max(1,Math.ceil(matching.length/limit));page=Math.min(page,pages);const from=(page-1)*limit;const slice=new Set(matching.slice(from,from+limit));for(const el of items)el.hidden=!slice.has(el);summary.textContent=matching.length+' resultado(s) correspondem aos filtros';index.textContent=size.value==='all'?'Todos':('Página '+page+' de '+pages);prev.disabled=page<=1||size.value==='all';next.disabled=page>=pages||size.value==='all';}
panel.addEventListener('table-sorted',()=>{page=1;render();});size.addEventListener('change',()=>{page=1;render();});prev.addEventListener('click',()=>{page=Math.max(1,page-1);render();});next.addEventListener('click',()=>{page++;render();});
const filterIds=panelId==='mainPanelGeneral'?['q','area','mode','source','region','city','age']:['regionalCompany','regionalCity','regionalArea','regionalQuery'];for(const id of filterIds){const el=document.getElementById(id);if(el)el.addEventListener('input',()=>{page=1;render();});}
render();
}
setupPager('mainPanelGeneral','#jobs-table tbody tr');
setupPager('mainPanelRegional','#regionalCards .regional-card');
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
const matchWords=s=>new Set(matchNormalize(s).match(/[a-z0-9+#.-]{3,}/g)||[]);
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
   const parts=[];for(let p=1;p<=doc.numPages;p++){const page=await doc.getPage(p);const c=await page.getTextContent();parts.push(c.items.map(x=>x.str||'').join(' '));}content=parts.join('\\n');
  }else throw new Error('Formato inválido: utilize PDF, DOCX ou TXT.');
  if(!content.trim())throw new Error('Nenhum texto extraído. PDFs digitalizados precisam de OCR, que não está disponível nesta versão.');
  matchId('matchProfile').value=content.slice(0,40000);status.textContent='Arquivo carregado: '+file.name+' — '+content.length+' caracteres extraídos. Pronto para análise.';
 }catch(err){status.textContent='Não foi possível ler: '+err.message+' Cole o texto manualmente.';}
});
const jobSelect=matchId('aiJob'),jobDescription=matchId('matchDescription'),descriptionDetails=matchId('matchDescriptionDetails');
function fillJobRequirements(){
 const option=jobSelect.selectedOptions[0],description=option?.dataset.description||'';
 jobDescription.value=description;
 descriptionDetails.open=false;
 const notice=matchId('matchRequirementsStatus');
 if(notice)notice.textContent=description?'Requisitos carregados automaticamente da fonte da vaga.':'Esta fonte não disponibilizou a descrição completa. Abra “Requisitos da vaga” para adicionar manualmente.';
}
jobSelect.addEventListener('change',fillJobRequirements);
fillJobRequirements();
const matchApiUrl=window.AI_MATCH_API_URL||"";
const matchConsent=document.createElement('label');
matchConsent.style.display='block';
matchConsent.style.margin='12px 0';
matchConsent.innerHTML='<input type="checkbox" id="matchAIConsent"> Autorizo o envio do conteúdo do meu currículo e dos requisitos desta vaga à Cloudflare para análise por IA. Não envie dados sensíveis.';
const aiMatchButton=document.createElement('button');
aiMatchButton.type='button';aiMatchButton.id='matchAIAnalyze';aiMatchButton.textContent='Analisar com Cloudflare AI';
aiMatchButton.disabled=!matchApiUrl;
const localButton=matchId('matchAnalyze');
localButton.insertAdjacentElement('afterend',matchConsent);
matchConsent.insertAdjacentElement('afterend',aiMatchButton);
if(!matchApiUrl){const note=document.createElement('p');note.className='muted';note.textContent='Cloudflare AI aguardando configuração da URL do Worker. A análise local continua disponível.';aiMatchButton.insertAdjacentElement('afterend',note);}
aiMatchButton.addEventListener('click',async()=>{
 const job=matchId('aiJob'),profile=matchId('matchProfile').value.trim(),description=matchId('matchDescription').value.trim(),result=matchId('matchResult');
 if(!matchId('matchAIConsent').checked){result.textContent='Confirme a autorização de envio antes de usar a IA.';return;}
 if(!job.value||profile.length<30||description.length<30){result.textContent='Selecione a vaga, carregue o currículo e confirme os requisitos antes de analisar.';return;}
 aiMatchButton.disabled=true;result.textContent='Analisando com Cloudflare AI...';
 try{
  const control=new AbortController();const timeout=setTimeout(()=>control.abort(),22000);
  let response;
  try{response=await fetch(matchApiUrl+'/match',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({title:job.selectedOptions[0]?.textContent||'',profile,description,consent:true}),signal:control.signal});}
  finally{clearTimeout(timeout);}
  const data=await response.json();
  if(!response.ok)throw new Error(data.error||'API indisponível');
  if(!Number.isInteger(data.score))throw new Error('Resposta da IA inválida');
  result.replaceChildren();
  const headline=document.createElement('h3');headline.textContent='Compatibilidade estimada por IA: '+data.score+'%';result.append(headline);
  for(const [label,items] of [['Pontos fortes',data.strengths],['Lacunas',data.gaps]]){
   const h=document.createElement('p');h.textContent=label+': '+(Array.isArray(items)?items.join('; '):'Não informado');result.append(h);
  }
  const p=document.createElement('p');p.textContent='Recomendação: '+String(data.recommendation||'');result.append(p);
  const warning=document.createElement('small');warning.textContent='Estimativa automatizada, não é previsão de contratação. Confirme os requisitos na vaga original.';result.append(warning);
 }catch(error){result.textContent='Cloudflare AI indisponível: '+error.message+' Use a análise local enquanto isso.';}
 finally{aiMatchButton.disabled=false;}
});
matchId('matchAnalyze').addEventListener('click',()=>{
 const job=matchId('aiJob'),opt=job.selectedOptions[0],profile=matchId('matchProfile').value.trim(),description=matchId('matchDescription').value.trim();
 if(!job.value){matchId('matchResult').textContent='Selecione uma vaga real para calcular a compatibilidade.';job.focus();return;}if(!profile){matchId('matchReviewDetails').open=true;matchId('matchResult').textContent='Carregue o currículo e aguarde a confirmação da extração, ou cole as experiências no perfil.';return;}
 if(!description){matchId('matchDescriptionDetails').open=true;matchId('matchResult').textContent='Perfil carregado. Para calcular um match confiável, abra “Adicionar descrição e requisitos da vaga” e cole os requisitos; a API pode fornecer somente o título.';return;}
 showMatchResult(matchScore(profile,description,opt));
});


}catch(error){const result=document.getElementById('matchResult'),status=document.getElementById('matchFileStatus');if(result)result.textContent='Não foi possível iniciar a análise local: '+error.message;if(status)status.textContent='Falha ao inicializar a leitura. Atualize a página.';}
})();

(function(){
 const label=document.getElementById("account-name");
 const data=new URLSearchParams(location.hash.slice(1));
 const name=data.get("account");
 if(name && name.length<=100 && !/[<>]/.test(name)){
   sessionStorage.setItem("careerAccountName",name);
   history.replaceState(null,"",location.pathname+location.search);
 }
 const last=sessionStorage.getItem("careerAccountName");
 if(last)label.textContent="Conta utilizada no último login: "+last;
 document.getElementById("account-logout").addEventListener("click",()=>sessionStorage.removeItem("careerAccountName"));
})();
</script></body></html>"""



def market_chart_html(recruiter_post_count=0):
    """Interactive chart that keeps verified vacancies separate from indexed recruiter posts."""
    from src.market_intelligence import summarize
    path = Path("data/history.json")
    linkedin_path = Path("data/linkedin_history.json")
    try:
        history = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        linkedin_history = json.loads(linkedin_path.read_text(encoding="utf-8")) if linkedin_path.exists() else {}
        report = summarize(history, linkedin_history=linkedin_history)
    except (OSError, ValueError, TypeError):
        return '<p role="status">Histórico indisponível no momento. Novas coletas serão exibidas aqui.</p>'
    payload = json.dumps({"months": report["months"], "categories": report["categories"],
                          "linkedin": report["linkedin"],
                          "recruiter_current": int(recruiter_post_count),
                          "coverage": report["source_coverage"], "generated": report["generated_at"]},
                         ensure_ascii=False).replace("<", "\\u003c")
    return """
    <style>
    .market-intelligence{position:relative;overflow:hidden;background:linear-gradient(140deg,#0b1325,#13253c 65%,#10182d)!important;border:1px solid #31516a!important;box-shadow:0 16px 42px #050e204d}
    .market-intelligence:before{content:"";position:absolute;right:-130px;top:-180px;width:420px;height:420px;background:radial-gradient(circle,#14b8a633,transparent 70%);pointer-events:none}
    .market-intelligence h2{color:#f2f8ff;letter-spacing:.025em}
    .market-controls{display:flex;flex-wrap:wrap;gap:14px;margin:18px 0}
    .market-controls label{display:grid;gap:6px;color:#c5d8ec;font-weight:600;font-size:13px}
    .market-controls select{background:#101e32;color:#f2f8ff;border:1px solid #43627c;border-radius:10px;padding:10px 14px;min-height:44px}
    .market-kpis{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin:16px 0}
    .market-kpi{background:#152a42;border:1px solid #34526a;border-radius:14px;padding:15px;min-width:0}
    .market-kpi small{display:block;color:#a9c1d8;font-size:12px}
    .market-kpi strong{display:block;color:#f4fbff;font-size:clamp(20px,3vw,29px);margin:6px 0;font-variant-numeric:tabular-nums}
    .market-kpi span{color:#90e9df;font-size:12px}
    .market-chart-frame{background:#0b182a;border:1px solid #2d4b62;border-radius:16px;padding:14px;overflow-x:auto}
    #market-trend{width:100%;min-width:290px;max-height:330px}
    #market-trend circle{cursor:crosshair;outline-offset:3px}
    #market-trend circle:focus{outline:2px solid #fff}
    #market-detail{color:#c6e6ef;min-height:22px;font-size:13px;margin-top:8px}
    .market-definitions{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;margin:12px 0}.market-definition{position:relative;background:#102139;border:1px solid #34526a;border-radius:10px;padding:11px;color:#c5d8ec;font-size:13px}.info-tip{display:inline-grid;place-items:center;position:relative;width:18px;height:18px;margin-left:5px;border:1px solid #6ba8b4;border-radius:50%;color:#80e4dc;cursor:help}.info-tip [role="tooltip"]{display:none;position:absolute;z-index:10;left:0;top:25px;width:min(300px,75vw);padding:10px;border-radius:8px;background:#061321;border:1px solid #5a8298;color:#eef8ff;box-shadow:0 8px 24px #0008}.info-tip:hover [role="tooltip"],.info-tip:focus [role="tooltip"]{display:block}.market-floating-tooltip{position:fixed;z-index:9999;pointer-events:none;display:none;padding:8px 10px;border-radius:8px;background:#061321;border:1px solid #6be4dc;color:#f4fbff;box-shadow:0 8px 24px #0009;font-size:12px;white-space:nowrap}
    @media(max-width:540px){.market-kpis{grid-template-columns:1fr}.market-intelligence{padding:15px!important}.market-controls label{flex:1;min-width:125px}}
    @media(prefers-reduced-motion:no-preference){.market-kpi{transition:border-color .2s,transform .2s}.market-kpi:hover{border-color:#4dd8cc;transform:translateY(-2px)}}
    </style>
    <div style="display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap;align-items:center"><strong style="color:#6be4dc;letter-spacing:.1em;font-size:12px">◈ TALENT PULSE · MARKET INTELLIGENCE</strong><span style="color:#aac2d8;font-size:12px">Amostra monitorada · sem dados simulados</span></div>
    <div class="market-definitions">
      <div class="market-definition"><strong>Posts públicos indexados</strong><span class="info-tip" tabindex="0" aria-label="Ajuda sobre posts públicos indexados">i<span role="tooltip">Publicações de recrutamento encontradas por mecanismos públicos de busca. Podem indicar movimento do mercado, mas não são vagas confirmadas nem representam todo o LinkedIn.</span></span><br>Termômetro da atividade de recrutamento encontrada na web.</div>
      <div class="market-definition"><strong>Vagas coletadas</strong><span class="info-tip" tabindex="0" aria-label="Ajuda sobre vagas coletadas">i<span role="tooltip">Anúncios individuais obtidos nas fontes de vagas integradas ao sistema, deduplicados quando possível. A cobertura depende das fontes e do início da coleta.</span></span><br>Anúncios de emprego encontrados nas fontes monitoradas.</div>
    </div>
    <div class="market-controls">
      <label for="market-metric">Indicador
        <select id="market-metric"><option value="posts" selected>Posts públicos indexados</option><option value="vacancies">Vagas coletadas</option></select>
      </label>
      <label for="market-area">Área profissional
        <select id="market-area"><option value="qa">Tecnologia / QA</option><option value="manufacturing">Manufatura</option><option value="all">Comparar áreas</option></select>
      </label>
      <label for="market-scope">Mercado
        <select id="market-scope"><option value="all">Todos</option><option value="Brasil">Brasil</option><option value="Internacional">Internacional</option><option value="Não identificado">Não identificado</option></select>
      </label>
      <label for="market-window">Período
        <select id="market-window"><option value="1">30 dias</option><option value="3">90 dias</option><option value="6">6 meses</option><option value="12">12 meses</option><option value="24" selected>24 meses</option></select>
      </label>
    </div>
    <div class="market-kpis" aria-label="Indicadores de mercado">
      <div class="market-kpi"><small id="market-current-label">Posts indexados no mês</small><strong id="market-current">—</strong><span id="market-current-note">Amostra histórica pública · mês parcial</span></div>
      <div class="market-kpi"><small>Publicações no Recruiter Monitor</small><strong id="market-recruiter-current">—</strong><span>Janela de até 30 dias · não são vagas verificadas</span></div>
      <div class="market-kpi"><small>Variação entre meses completos</small><strong id="market-change">—</strong><span id="market-change-note">Aguardando dados comparáveis</span></div>
      <div class="market-kpi"><small>Cobertura histórica</small><strong id="market-coverage">—</strong><span id="market-coverage-note">Meses com coleta identificada</span></div>
    </div>
    <div class="market-chart-frame">
      <svg id="market-trend" viewBox="0 0 640 270" role="img" aria-label="Evolução mensal do indicador selecionado, com lacunas onde não houve coleta"></svg>
      <div id="market-detail" role="status" aria-live="polite">Toque ou selecione um ponto para ver os detalhes.</div>
      <div id="market-legend" style="display:flex;gap:16px;flex-wrap:wrap;margin:10px 0;color:#dce7ff"></div>
    </div>
    <div id="market-tooltip" class="market-floating-tooltip" role="tooltip"></div>
    <p id="market-summary" role="status" aria-live="polite" style="color:#b7c7e0;margin:12px 0"></p>
    <p style="color:#b7c7e0;font-size:13px">“Vagas coletadas” contabiliza anúncios nas fontes monitoradas. “Posts públicos indexados” usa resultados públicos encontrados na web e não a API oficial do LinkedIn; é uma amostra incompleta e não representa vagas verificadas. Sem coleta ≠ zero.</p>
    <script type="application/json" id="market-history-data">""" + payload + """</script>
    <script>
    (function(){
      const data=JSON.parse(document.getElementById('market-history-data').textContent);
      const metric=document.getElementById('market-metric'),area=document.getElementById('market-area'),scope=document.getElementById('market-scope'),windowSelect=document.getElementById('market-window');
      const svg=document.getElementById('market-trend'),summary=document.getElementById('market-summary');
      const legend=document.getElementById('market-legend'),tooltip=document.getElementById('market-tooltip');
      const detail=document.getElementById('market-detail'),NS='http://www.w3.org/2000/svg';
      function showTooltip(event,message){tooltip.textContent=message;tooltip.style.display='block';const x=Math.min(window.innerWidth-tooltip.offsetWidth-12,event.clientX+12),y=Math.max(8,event.clientY-tooltip.offsetHeight-12);tooltip.style.left=x+'px';tooltip.style.top=y+'px';}
      function hideTooltip(){tooltip.style.display='none';}
      function node(tag,attrs,text){const n=document.createElementNS(NS,tag);Object.entries(attrs||{}).forEach(([k,v])=>n.setAttribute(k,v));if(text!==undefined)n.textContent=text;svg.appendChild(n);return n;}
      function draw(){
        const isPosts=metric.value==='posts';
        const names=isPosts?(area.value==='qa'?['QA']:area.value==='manufacturing'?['Manufatura']:['QA','Manufatura']):(area.value==='qa'?['QA','QA Manager']:area.value==='manufacturing'?['Manufatura']:['QA','QA Manager','Manufatura']);
        const palette={'QA':'#5ce1d3','QA Manager':'#a78bfa','Manufatura':'#f6bd69'};
        const count=Number(windowSelect.value),months=data.months.slice(-count),first=data.months.length-count;
        scope.disabled=!isPosts;scope.title=isPosts?'Filtrar somente quando houver evidência explícita de localização':'Disponível para posts públicos indexados';
        const categoryData=isPosts&&scope.value!=='all'?data.linkedin.scopes[scope.value]:(isPosts?data.linkedin.categories:data.categories);
        const series=names.map(name=>categoryData[name].monthly.slice(-count));
        const observed=isPosts?months.map((m,i)=>names.some((name,j)=>series[j][i]!==null)):months.map(m=>Number(data.coverage[m]||0)>0);
        if(!isPosts)series.forEach(values=>values.forEach((value,i)=>{if(!observed[i])values[i]=null;}));
        const unit=isPosts?'posts indexados':'vagas observadas';
        const values=series.flat().filter(v=>v!==null),max=Math.max(1,...values);
        const left=48,right=615,top=22,bottom=222;
        svg.replaceChildren();legend.replaceChildren();
        for(let tick=0;tick<=4;tick++){const y=bottom-(bottom-top)*tick/4;node('line',{x1:left,y1:y,x2:right,y2:y,stroke:'#344d63','stroke-width':1,'stroke-dasharray':'3 5'});node('text',{x:39,y:y+4,fill:'#b9d1e3','font-size':12,'text-anchor':'end'},String(Math.round(max*tick/4)));}
        months.forEach((month,i)=>{if(i%Math.max(1,Math.ceil(months.length/6))===0||i===months.length-1){node('text',{x:left+(right-left)*i/Math.max(1,months.length-1),y:247,fill:'#b9d1e3','font-size':11,'text-anchor':'middle'},month);}});
        names.forEach((name,j)=>{
          let segment=[];
          function flush(){if(segment.length>1)node('polyline',{points:segment.map(p=>p.x+','+p.y).join(' '),fill:'none',stroke:palette[name],'stroke-width':3,'stroke-linecap':'round','stroke-linejoin':'round'});segment=[];}
          series[j].forEach((v,i)=>{
            if(v===null){flush();return;}
            const p={x:left+(right-left)*i/Math.max(1,months.length-1),y:bottom-(bottom-top)*v/max};
            segment.push(p);
          });flush();
          series[j].forEach((v,i)=>{
            if(v===null)return;
            const x=left+(right-left)*i/Math.max(1,months.length-1),y=bottom-(bottom-top)*v/max;
            const dot=node('circle',{cx:x,cy:y,r:5,fill:palette[name],stroke:'#0b182a','stroke-width':2,tabindex:0,role:'button','aria-label':name+', '+months[i]+': '+v+' '+unit});
            const status=isPosts?(data.linkedin.coverage[months[i]]?.[name]||'unqueried'):(data.coverage[months[i]]+' fonte(s) com registros');
            const message=name+' · '+months[i]+' · '+v+' '+unit+' · cobertura: '+status;
            const title=document.createElementNS(NS,'title');title.textContent=message;dot.appendChild(title);
            dot.addEventListener('mouseenter',event=>{detail.textContent=message;showTooltip(event,message);});
            dot.addEventListener('mousemove',event=>showTooltip(event,message));
            dot.addEventListener('mouseleave',hideTooltip);
            dot.addEventListener('focus',()=>detail.textContent=message);
            dot.addEventListener('blur',hideTooltip);
            dot.addEventListener('click',()=>detail.textContent=message);
            dot.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();detail.textContent=message;}});
          });
          const label=document.createElement('span');label.textContent='● '+name;label.style.color=palette[name];legend.appendChild(label);
        });
        const last=series.reduce((sum,s)=>sum+(s[s.length-1]||0),0);
        const complete=series.map(s=>s.slice(-3,-1));
        const comparable=months.length>=3&&observed[observed.length-2]&&observed[observed.length-3]&&(isPosts||Number(data.coverage[months[months.length-2]])===Number(data.coverage[months[months.length-3]]));
        const prev=complete.reduce((s,a)=>s+(a[0]||0),0),curr=complete.reduce((s,a)=>s+(a[1]||0),0);
        document.getElementById('market-current-label').textContent=isPosts?'Posts indexados no mês':'Vagas coletadas no mês';
        document.getElementById('market-current-note').textContent=isPosts?'Amostra histórica pública · mês parcial':'Anúncios de vagas · mês parcial';
        document.getElementById('market-current').textContent=observed[observed.length-1]?last.toLocaleString('pt-BR'):'—';
        document.getElementById('market-recruiter-current').textContent=Number(data.recruiter_current||0).toLocaleString('pt-BR');
        document.getElementById('market-change').textContent=comparable&&prev>0?((curr-prev)/prev*100).toLocaleString('pt-BR',{maximumFractionDigits:1})+'%':'—';
        document.getElementById('market-change-note').textContent=comparable&&prev>0?'Comparação indicativa; cobertura pode mudar':'Sem dois meses completos com cobertura comparável';
        const covered=observed.filter(Boolean).length;
        document.getElementById('market-coverage').textContent=covered+' / '+months.length;
        document.getElementById('market-coverage-note').textContent=isPosts?'Meses consultados no índice público':'Meses com registros nas fontes monitoradas';
        summary.textContent=covered===0?'Nenhuma coleta identificada nesta janela. Não é possível inferir a tendência.':covered<3?'Histórico insuficiente para avaliar tendências com confiança.':isPosts?'Histórico público disponível para leitura descritiva dos períodos; a amostra não representa todo o LinkedIn.':'Tendência descritiva da amostra, não do mercado inteiro.';
        if(covered===0){node('text',{x:330,y:125,fill:'#9bdedc','font-size':16,'text-anchor':'middle'},'Aguardando histórico de coleta');}
      }
      metric.addEventListener('change',draw);area.addEventListener('change',draw);scope.addEventListener('change',draw);windowSelect.addEventListener('change',draw);draw();
    })();
    </script>
    """

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
