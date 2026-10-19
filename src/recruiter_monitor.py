"""Discover same-day public mentions of LinkedIn recruiter posts via Google News RSS.

This is best-effort discovery, NOT LinkedIn API access. No LinkedIn login,
scraping, recruiter email extraction, or automatic sending.
Only public titles/links are persisted in this PUBLIC repository.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from xml.etree import ElementTree

from src.hunter import DATA

OUTPUT = DATA / "recruiter_monitor.json"
SEARCHES = [
    'site:linkedin.com/posts/ ("hiring" OR "we are hiring") ("QA" OR "quality engineer")',
    'site:linkedin.com/posts/ ("hiring" OR "vaga") ("IT project manager" OR "gerente de projetos de TI")',
    'site:linkedin.com/posts/ ("recruiter" OR "recrutador") ("remote" OR "remoto")',
    'site:linkedin.com/posts/ ("coordenador de projetos industriais" OR "industrial project coordinator") hiring',
    'site:linkedin.com/posts/ ("industrial project specialist" OR "industrial project analyst") hiring',
    'site:linkedin.com/posts/ ("especialista de projetos" OR "analista de projetos") ("manufatura" OR "industrial")',
]


QA_SEARCHES = [
    'site:linkedin.com/posts/ "engenheiro de QA" "remoto"',
    'site:linkedin.com/posts/ "QA Engineer" "remote" "hiring"',
    'site:linkedin.com/posts/ "QA Manager" hiring',
    'site:linkedin.com/posts/ "QA Lead" remote',
    'site:linkedin.com/posts/ "SDET" "hiring"',
    'site:linkedin.com/posts/ "Quality Assurance Engineer" vacancy',
    'site:linkedin.com/posts/ ("QA Engineer" OR "Test Engineer") ("USD" OR "US$" OR "dollar")',
]

# Additional discovery remains restricted to publicly indexed LinkedIn posts.
LINKEDIN_EXTRA_SEARCHES = [
    'site:linkedin.com/posts/ "QA Engineer" "we are hiring"',
    'site:linkedin.com/posts/ "Senior QA Engineer" "apply"',
    'site:linkedin.com/posts/ "QA Lead" "opportunity"',
    'site:linkedin.com/posts/ "QA Manager" "job opening"',
    'site:linkedin.com/posts/ "Tech Lead QA" "vaga"',
    'site:linkedin.com/posts/ "SDET" "remote" "apply"',
    'site:linkedin.com/posts/ "Automation Test Engineer" "hiring"',
    'site:linkedin.com/posts/ "engenheiro de qualidade de software" "vaga"',
    'site:linkedin.com/posts/ "analista de testes" "contratando"',
    'site:linkedin.com/posts/ "gerente de qualidade" "software" "vaga"',
    'site:linkedin.com/posts/ "IT Project Manager" "we are hiring"',
    'site:linkedin.com/posts/ "gerente de projetos de TI" "vaga"',
    'site:linkedin.com/posts/ "technical project manager" "hiring"',
]

# Discovery of publicly indexed LinkedIn posts; queries do not prove authorship.
COMPANY_POST_SEARCHES = [
    'site:linkedin.com/posts/ "we are hiring" "QA Engineer"',
    'site:linkedin.com/posts/ "join our team" "Quality Assurance"',
    'site:linkedin.com/posts/ "estamos contratando" "QA"',
    'site:linkedin.com/posts/ "QA Manager" "careers"',
    'site:linkedin.com/posts/ "industrial project coordinator" "we are hiring"',
    'site:linkedin.com/posts/ "coordenador de projetos industriais" "estamos contratando"',
    'site:linkedin.com/posts/ "especialista de projetos industriais" "oportunidade"',
    'site:linkedin.com/posts/ "gerente de projetos de software" "estamos contratando"',
    'site:linkedin.com/company/ "vagas" "QA"',
    'site:linkedin.com/company/ "vagas" "manufatura"',
]

QA_LEADERSHIP_SEARCHES = [
    'site:linkedin.com/posts/ "Head of QA" "hiring"',
    'site:linkedin.com/posts/ "Test Manager" "opportunity"',
    'site:linkedin.com/posts/ "Quality Engineering Lead" "hiring"',
    'site:linkedin.com/posts/ "QA Tech Lead" "vaga"',
    'site:linkedin.com/posts/ "Software Test Manager" "remote"',
    'site:linkedin.com/posts/ "Gerente de QA" "vaga"',
    'site:linkedin.com/posts/ "Líder de Testes" "contratando"',
    'site:linkedin.com/posts/ "Quality Assurance Manager" "Brazil"',
    'site:linkedin.com/posts/ "QA Lead" "LATAM"',
    'site:linkedin.com/posts/ "SDET Lead" "hiring"',
]

FREELANCE_QA_SEARCHES = [
    'site:linkedin.com/posts/ "QA Engineer" "freelance" "remote"',
    'site:linkedin.com/posts/ "software tester" "freelance" "remote"',
    'site:linkedin.com/posts/ "QA automation" "contractor" "remote"',
    'site:linkedin.com/posts/ "SDET" "independent contractor"',
    'site:linkedin.com/posts/ "QA tester" "part-time" "remote"',
    'site:linkedin.com/posts/ "quality assurance" "project based" "remote"',
    'site:linkedin.com/posts/ "QA Engineer" "hourly" "remote"',
    'site:linkedin.com/posts/ "QA" "freelancer" "USD"',
    'site:linkedin.com/posts/ "test automation" "contract" "LATAM"',
]

MANUFACTURING_SEARCHES = [
    'site:linkedin.com/posts/ "coordenador de projetos industriais" vaga',
    'site:linkedin.com/posts/ "especialista de projetos industriais" vaga',
    'site:linkedin.com/posts/ "analista de projetos industriais" vaga',
    'site:linkedin.com/posts/ "coordenador de projetos" ("indústria" OR "manufatura" OR "automotivo")',
    'site:linkedin.com/posts/ "especialista de projetos" ("indústria" OR "manufatura" OR "automotivo")',
    'site:linkedin.com/posts/ "analista de projetos" ("indústria" OR "manufatura" OR "automotivo")',
    'site:linkedin.com/posts/ "industrial project coordinator" hiring',
    'site:linkedin.com/posts/ "industrial project specialist" hiring',
    'site:linkedin.com/posts/ "industrial project analyst" hiring',
    'site:linkedin.com/posts/ "project coordinator" ("manufacturing" OR "industrial")',
    'site:linkedin.com/posts/ "project specialist" ("manufacturing" OR "industrial")',
    'site:linkedin.com/posts/ "project analyst" ("manufacturing" OR "industrial")',
]



def advertised_usd_salary(text: str) -> str | None:
    """Extract explicitly published USD amounts, never convert or infer."""
    import re
    value = str(text or "")
    patterns = [
        r"(?:US\$|USD|U\$)\s*(\d[\d,.]*)\s*(?:a|to|[-–])\s*(?:US\$|USD|U\$)?\s*(\d[\d,.]*)\s*(?:por hora|/h|/hr|per hour|hourly)",
        r"(?:US\$|USD|U\$)\s*(\d[\d,.]*)\s*(?:por hora|/h|/hr|per hour|hourly)",
        r"(?:US\$|USD|U\$)\s*(\d[\d,.]*)\s*(?:por mês|/month|monthly|/mo|per month)",
        r"(?:US\$|USD|U\$)\s*(\d[\d,.]*)\s*(?:por ano|/year|annually|yearly)",
    ]
    for idx, pattern in enumerate(patterns):
        found = re.search(pattern, value, re.I)
        if found:
            numbers = [g for g in found.groups() if g]
            suffix = "/hora" if idx <= 1 else "/mês" if idx == 2 else "/ano"
            return "US$ " + "–".join(numbers) + " " + suffix
    return None


def freelance_qa_facts(title: str, excerpt: str = "", area: str = "") -> dict:
    """Require explicit freelance/contract signals in a QA listing."""
    import re
    if area != "QA":
        return {"freelance_qa": "no", "freelance_evidence": "", "part_time_evidence": ""}
    value = str(title or "") + " " + str(excerpt or "")
    contract = re.search(
        r"\bfreelanc(?:e|er|ing)\b|\bindependent contractor\b|\bcontractor\b|"
        r"\bcontract(?:\s+role|\s+position|\s+job|\s+work|\s+opportunity)\b|"
        r"\bproject[ -]based\b|\bfreela\b|\baut[oô]nom[oa]\b", value, re.I
    )
    part_time = re.search(
        r"\bpart[ -]time\b|\bflexible hours\b|\b(?:2|two)\s+hours?\s+(?:per|a|/)\s+day\b|"
        r"\b(?:up to|max(?:imum)?)\s+10\s+hours?\s+(?:per|a|/)\s+week\b",
        value, re.I
    )
    return {
        "freelance_qa": "yes" if contract else "no",
        "freelance_evidence": contract.group(0) if contract else "",
        "part_time_evidence": part_time.group(0) if part_time else "",
    }


def extract_job_facts(text: str) -> dict:
    """Extract only explicitly indexed facts; retain short source evidence."""
    import re
    value = str(text or "")
    signals = (
        ("Híbrido confirmado", r"\bhybrid\b|\bh[ií]brid[oa]\b"),
        ("Remoto confirmado", r"\bremote\b|\bremot[oa]\b|\bhome[\s-]?office\b|\bwork from home\b"),
        ("Presencial confirmado", r"\bonsite\b|\bon[\s-]?site\b|\bpresencial\b|\bno escrit[oó]rio\b"),
    )
    hits = [(label, re.search(pattern, value, re.I)) for label, pattern in signals]
    hits = [(label, match) for label, match in hits if match]
    modality = hits[0][0] if len(hits) == 1 else "Não informada"
    modality_evidence = hits[0][1].group(0) if len(hits) == 1 else ""
    contract = "Não informado"
    contract_evidence = ""
    for label, pattern in (
        ("B2B", r"\bB2B\b"),
        ("PJ", r"\bPJ\b|\bpessoa jur[ií]dica\b"),
        ("CLT", r"\bCLT\b"),
        ("Cooperativa", r"\bcooperativ[ao]\b"),
    ):
        match = re.search(pattern, value, re.I)
        if match:
            contract, contract_evidence = label, match.group(0)
            break
    salary = advertised_usd_salary(value)
    salary_evidence = ""
    if salary:
        match = re.search(r"(?:US\$|USD|U\$)\s*[\d,.]+(?:\s*(?:a|to|[-–])\s*(?:US\$|USD|U\$)?\s*[\d,.]+)?\s*(?:por hora|/h|/hr|per hour|hourly|por mês|/month|monthly|/mo|per month|por ano|/year|annually|yearly)", value, re.I)
        salary_evidence = match.group(0)[:140] if match else ""
    return {"modality": modality, "modality_evidence": modality_evidence,
            "contract_type": contract, "contract_evidence": contract_evidence,
            "salary_usd": salary, "salary_evidence": salary_evidence}


def extract_application_contract(html_text: str, application_url: str) -> dict:
    """Only explicit contract information from a public Vagas.com application."""
    from html.parser import HTMLParser
    from urllib.parse import urlsplit
    import re
    if (urlsplit(application_url).hostname or "").lower() not in ("vagas.com.br", "www.vagas.com.br"):
        return {}
    class VisibleText(HTMLParser):
        def __init__(self):
            super().__init__()
            self.parts = []
        def handle_data(self, data):
            self.parts.append(data)
    parser = VisibleText()
    parser.feed(html_text[:500000])
    content = re.sub(r"\s+", " ", " ".join(parser.parts))
    match = re.search(r"\bRegime\s+(CLT|PJ|B2B)\b", content, re.I)
    return {"contract_type": match.group(1).upper(), "contract_evidence": match.group(0),
            "contract_source": "Anúncio de candidatura", "application_url": application_url} if match else {}


def enrich_application(item: dict) -> dict:
    """Follow an explicitly indexed lnkd.in application link to allowlisted Vagas.com only."""
    import re
    from urllib.parse import urlsplit
    from urllib.request import build_opener, HTTPRedirectHandler
    link = re.search(r"https://lnkd\.in/[a-zA-Z0-9]+", str(item.get("title", "")) + " " + str(item.get("indexed_excerpt", "")))
    if not link:
        return item
    class SafeRedirect(HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            if (urlsplit(newurl).hostname or "").lower() not in ("vagas.com.br", "www.vagas.com.br"):
                raise ValueError("Unsupported redirect destination")
            return super().redirect_request(req, fp, code, msg, headers, newurl)
    try:
        opener = build_opener(SafeRedirect())
        with opener.open(Request(link.group(0), headers={"User-Agent": "AIJobHunter/1.0"}), timeout=6) as response:
            final_url = response.geturl()
            if (urlsplit(final_url).hostname or "").lower() not in ("vagas.com.br", "www.vagas.com.br"):
                return item
            raw = response.read(500001)
        if len(raw) > 500000:
            return item
        return {**item, **extract_application_contract(raw.decode("utf-8", "replace"), final_url)}
    except (OSError, ValueError):
        return item


def industrial_project_role(title: str, excerpt: str = "") -> str:
    """Accept generic project job titles only with explicit industrial context."""
    import re
    t = title.casefold().split(" - linkedin")[0]
    context = (t + " " + excerpt.casefold())
    if re.search(r"marketing|advertising|publicidade|software|\bti\b|\bit\b|construction|constru[cç][aã]o civil|events?|eventos", t):
        return ""
    if not re.search(r"manufatur|manufactur|industrial|ind[uú]stria|automotiv|f[aá]brica|factory|plant|produ[cç][aã]o|production", context):
        return ""
    for label, pattern in (
        ("Coordenador", r"coordenador(?:a)? de projetos|project coordinator"),
        ("Especialista", r"especialista de projetos?|project specialist"),
        ("Analista", r"analista de projetos?|project analyst"),
    ):
        if re.search(pattern, t):
            return label
    return ""


def classify(title: str) -> dict:
    """Classify advertised roles conservatively; generic project managers are not IT."""
    import re
    t = title.casefold().split(" - linkedin")[0]
    industrial = r"manufatur|manufactur|produ[cç][aã]o|production|industrial|f[aá]brica|factory|plant|automotiv"
    project = r"project manager|gerente de projetos|coordenador de projetos|project coordinator|pmo|especialista de projetos|analista de projetos|project specialist|project analyst"
    tech = r"\b(?:it|ti|software|technology|technical|tecnologia|sistemas|cloud|devops|digital transformation|transforma[cç][aã]o digital|infraestrutura de ti)\b"
    excluded = r"marketing|advertising|publicidade|construction|constru[cç][aã]o civil|real estate|imobili[aá]ri|events?|eventos|architecture|arquitetura"
    manufacturing_role = industrial_project_role(title)
    manufacturing = bool(manufacturing_role)
    software_qa = bool(re.search(r"\bqa\b|sdet|software (?:quality|test)|quality (?:assurance|engineering|engineer)|test (?:engineer|manager|lead|automation)|head of qa|l[ií]der de testes|gerente de qa|autom[aá]c[aã]o de testes", t))
    industrial_quality = bool(re.search(r"qualidade industrial|quality control|quality inspector|qualidade de produ[cç][aã]o|quality manufacturing|supplier quality", t))
    software_qa = software_qa or bool(re.search(r"\bqa\s+(?:tech\s+)?lead\b|\bqa\s+manager\b", t))
    qa = software_qa and not (industrial_quality and not re.search(r"software|\bqa\b|sdet|test automation", t))
    projects = bool(re.search(project, t) and re.search(tech, t) and not re.search(excluded, t))
    remote = bool(re.search(r"\bremote\b|\bremoto\b|home.office", t))
    hybrid = bool(re.search(r"\bhybrid\b|\bh[ií]brid[oa]\b", t))
    explicit_hiring = bool(re.search(r"hiring|contratando|estamos contratando|we.re hiring|vaga|opportunit|oportunidade|open position|job opening", t))
    area = "Manufatura" if manufacturing else "QA" if qa else "Projetos" if projects else "Outros"
    if area == "Manufatura":
        role = manufacturing_role
    elif area == "Projetos":
        role = "Gerente de Projetos de TI"
    else:
        role = ""
    modality = "Remoto (citado)" if remote else "Híbrido (citado)" if hybrid else "Não informada"
    return {"area": area, "role": role, "modality": modality, "review_priority": "high" if area != "Outros" and explicit_hiring else "normal"}


def explicit_city(text: str) -> str:
    """Use only an explicitly mentioned municipality; never infer from query geography."""
    import re
    cities = ("Sumaré", "Campinas", "Paulínia", "Americana", "Nova Odessa",
              "Hortolândia", "Indaiatuba", "Valinhos", "Vinhedo", "Jaguariúna",
              "Piracicaba", "São Paulo", "Mogi Guaçu")
    for city in cities:
        if re.search(r"(?<!\w)" + re.escape(city) + r"(?!\w)", text, re.I):
            return city
    return ""


def post_origin(url: str, source_url: str = "") -> str:
    """Only attest LinkedIn company/member origins from explicit URL structure.

    Search phrases, company names in headlines and Google News's generic LinkedIn
    attribution do NOT establish who authored the post.
    """
    from urllib.parse import urlsplit
    for candidate in (source_url, url):
        parsed = urlsplit(candidate)
        host = (parsed.hostname or "").lower()
        if host != "linkedin.com" and not host.endswith(".linkedin.com"):
            continue
        path = parsed.path.lower()
        if path.startswith("/company/"):
            return "Empresa"
        if path.startswith("/in/"):
            return "Recrutador" if source_url else "Não verificada"
    return "Não verificada"


def parse_feed(xml_text: str, day: str, max_age_days: int = 1, manufacturing_only: bool = False) -> list[dict]:
    """Keep verifiably recent public indexed posts; do not infer actual vacancy dates."""
    from urllib.parse import urlsplit
    import re
    root = ElementTree.fromstring(xml_text)
    cutoff = datetime.fromisoformat(day).replace(tzinfo=timezone.utc) - timedelta(days=max_age_days - 1)
    found: dict[str, dict] = {}
    for item in root.findall(".//item"):
        title = (item.findtext("title") or "").strip()
        indexed_excerpt = (item.findtext("description") or "").strip()
        url = (item.findtext("link") or "").strip()
        published = (item.findtext("pubDate") or "").strip()
        source_node = item.find("source")
        source_url = source_node.get("url", "") if source_node is not None else ""
        try:
            date = parsedate_to_datetime(published).astimezone(timezone.utc)
        except (TypeError, ValueError, OverflowError):
            continue
        if not (cutoff <= date < cutoff + timedelta(days=max_age_days)) or not url.startswith("https://"):
            continue
        # Google News may provide a google.com RSS redirect URL for a LinkedIn-indexed
        # post. Accept those only when the result is explicitly attributed to LinkedIn.
        host = (urlsplit(url).hostname or "").lower()
        linkedin_url = host == "linkedin.com" or host.endswith(".linkedin.com")
        news_redirect = host in ("news.google.com", "news.googleusercontent.com")
        if not (linkedin_url or (news_redirect and re.search(r"\bLinkedIn\b", title, re.I))):
            continue
        labels = classify(title)
        industrial_role = industrial_project_role(title, indexed_excerpt)
        if industrial_role:
            labels["area"], labels["role"] = "Manufatura", industrial_role
        facts = extract_job_facts(title + " " + indexed_excerpt)
        freelance = freelance_qa_facts(title, indexed_excerpt, labels["area"])
        labels["modality"] = facts["modality"]
        hiring = bool(re.search(r"\bhiring\b|\bcontratando\b|\bvaga(?:s)?\b|\bjob opening\b|\bapply\b|\bopportunit(?:y|ies)\b|\boportunidade\b|\brecruiting\b|\bwe.re hiring\b|\bselection process\b|\bseletivo\b", title, re.I))
        if labels["area"] in ("QA", "Projetos", "Outros") and not (hiring or freelance["freelance_qa"] == "yes"):
            continue
        if manufacturing_only and not industrial_role:
            continue
        if labels["area"] == "Manufatura" and not industrial_role:
            continue
        city = explicit_city(title + " " + indexed_excerpt) if labels["area"] == "Manufatura" else ""
        found[url] = {
            "title": title[:500], "indexed_excerpt": indexed_excerpt[:1500], **facts, **freelance, "url": url, "published_at": date.isoformat(),
            "source": "Public web news index", "status": "needs_review", "city": city, "post_origin": post_origin(url, source_url), **labels,
        }
    return list(found.values())


def run() -> dict:
    day = datetime.now(timezone.utc).date().isoformat()
    jobs: dict[str, dict] = {}
    failures = []
    if os.environ.get("RECRUITER_MONITOR_DISABLED") == "1":
        state = "disabled"
    else:
        for query in SEARCHES + QA_SEARCHES + QA_LEADERSHIP_SEARCHES + LINKEDIN_EXTRA_SEARCHES + COMPANY_POST_SEARCHES + FREELANCE_QA_SEARCHES + MANUFACTURING_SEARCHES:
            manufacturing_query = query in MANUFACTURING_SEARCHES or query in SEARCHES[3:]
            qa_query = query == SEARCHES[0] or query in QA_SEARCHES or query in QA_LEADERSHIP_SEARCHES or query in LINKEDIN_EXTRA_SEARCHES or query in COMPANY_POST_SEARCHES or query in FREELANCE_QA_SEARCHES
            days = 30 if manufacturing_query or qa_query else 1
            endpoint = "https://news.google.com/rss/search?" + urlencode({
                "q": query + f" when:{days}d", "hl": "pt-BR" if manufacturing_query else "en-US", "gl": "BR" if manufacturing_query else "US", "ceid": "BR:pt-419" if manufacturing_query else "US:en"
            })
            try:
                req = Request(endpoint, headers={"User-Agent": "AIJobHunter/1.0 (public RSS reader)"})
                with urlopen(req, timeout=12) as response:
                    xml = response.read(1_000_001)
                if len(xml) > 1_000_000:
                    raise ValueError("Feed too large")
                for result in parse_feed(xml.decode("utf-8"), day, max_age_days=days, manufacturing_only=manufacturing_query):
                    jobs[result["url"]] = enrich_application(result)
            except Exception as exc:
                failures.append(type(exc).__name__)
        state = "partial" if failures else "ok"
    data = {
        "date_utc": day, "checked_at": datetime.now(timezone.utc).isoformat(),
        "status": state, "query_count": len(SEARCHES) + len(QA_SEARCHES) + len(QA_LEADERSHIP_SEARCHES) + len(LINKEDIN_EXTRA_SEARCHES) + len(COMPANY_POST_SEARCHES) + len(FREELANCE_QA_SEARCHES) + len(MANUFACTURING_SEARCHES),
        "items": sorted(jobs.values(), key=lambda x: x["published_at"], reverse=True)[:100],
        "limitations": "Incomplete web-index coverage; RSS publication date is not guaranteed to match original LinkedIn post date. Review each link. No automatic applications.",
        "failed_queries": len(failures),
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Recruiter monitor: {len(data['items'])} index results; status={state}")
    return data


if __name__ == "__main__":
    run()
