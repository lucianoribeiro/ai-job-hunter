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
    'site:linkedin.com/posts/ ("hiring" OR "vaga") ("project manager" OR "gerente de projetos")',
    'site:linkedin.com/posts/ ("recruiter" OR "recrutador") ("remote" OR "remoto")',
    'site:linkedin.com/posts/ ("coordenador de manufatura" OR "coordenador de produção" OR "manufacturing coordinator") hiring',
    'site:linkedin.com/posts/ ("manufacturing manager" OR "production supervisor" OR "industrial operations manager") (remote OR hybrid)',
    'site:linkedin.com/posts/ ("manufatura" OR "produção industrial") ("híbrido" OR "remoto" OR "vaga")',
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
    'site:linkedin.com/posts/ "project manager" "we are hiring"',
    'site:linkedin.com/posts/ "gerente de projetos" "vaga"',
    'site:linkedin.com/posts/ "coordenador de projetos" "contratando"',
]

# Discovery of publicly indexed LinkedIn posts; queries do not prove authorship.
COMPANY_POST_SEARCHES = [
    'site:linkedin.com/posts/ "we are hiring" "QA Engineer"',
    'site:linkedin.com/posts/ "join our team" "Quality Assurance"',
    'site:linkedin.com/posts/ "estamos contratando" "QA"',
    'site:linkedin.com/posts/ "QA Manager" "careers"',
    'site:linkedin.com/posts/ "manufacturing manager" "we are hiring"',
    'site:linkedin.com/posts/ "coordenador de produção" "estamos contratando"',
    'site:linkedin.com/posts/ "gerente industrial" "oportunidade"',
    'site:linkedin.com/posts/ "gerente de projetos" "estamos contratando"',
    'site:linkedin.com/company/ "vagas" "QA"',
    'site:linkedin.com/company/ "vagas" "manufatura"',
]

MANUFACTURING_SEARCHES = [
    'site:linkedin.com/posts/ "gerente de produção" vaga',
    'site:linkedin.com/posts/ "coordenador de produção" contratação',
    'site:linkedin.com/posts/ "supervisor de produção" oportunidade',
    'site:linkedin.com/posts/ "gerente industrial" vaga',
    'site:linkedin.com/posts/ "coordenador de manufatura"',
    'site:linkedin.com/posts/ "gestor de operações industriais"',
    'site:linkedin.com/posts/ "manufacturing manager" hiring',
    'site:linkedin.com/posts/ "production manager" hiring',
    'site:linkedin.com/posts/ "production supervisor" hiring',
    'site:linkedin.com/posts/ "plant manager" hiring',
    'site:linkedin.com/posts/ "industrial operations manager" hiring',
    'site:linkedin.com/posts/ ("manufatura" OR "produção") ("Sumaré" OR "Campinas" OR "Paulínia" OR "Americana")',
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


def classify(title: str) -> dict:
    """Conservative title-only tags; never infer remote/hybrid eligibility."""
    import re
    t = title.casefold()
    manufacturing = bool(re.search(r"manufatur|manufactur|produ[cç][aã]o|production|industrial|lean manufacturing|plant manager|gerente de planta|gestor de f[aá]brica", t))
    qa = bool(re.search(r"\bqa\b|quality engineer|quality assurance|sdet|test engineer|software test", t))
    projects = bool(re.search(r"project manager|gerente de projetos|coordenador de projetos|project coordinator|pmo", t))
    remote = bool(re.search(r"\bremote\b|\bremoto\b|home.office", t))
    hybrid = bool(re.search(r"\bhybrid\b|\bh[ií]brid[oa]\b", t))
    explicit_hiring = bool(re.search(r"hiring|contratando|estamos contratando|we.re hiring|vaga|opportunit|oportunidade|open position|job opening", t))
    area = "Manufatura" if manufacturing else "QA" if qa else "Projetos" if projects else "Outros"
    modality = "Remoto (citado)" if remote else "Híbrido (citado)" if hybrid else "Não informada"
    return {"area": area, "modality": modality, "review_priority": "high" if area != "Outros" and explicit_hiring else "normal"}


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
        hiring = bool(re.search(r"\bhiring\b|\bcontratando\b|\bvaga(?:s)?\b|\bjob opening\b|\bapply\b|\bopportunit(?:y|ies)\b|\boportunidade\b|\brecruiting\b|\bwe.re hiring\b|\bselection process\b|\bseletivo\b", title, re.I))
        if labels["area"] in ("QA", "Projetos") and not hiring:
            continue
        if manufacturing_only:
            if labels["area"] != "Manufatura":
                continue
            import re
            leadership = r"gerente|coordenador|supervisor|diretor|gestor|lideran[cç]a|l[ií]der|manager|supervisor|director|lead|plant manager"
            if not re.search(leadership, title.casefold()):
                continue
            # Require the advertised role, not just incidental text, to be industrial leadership.
            role = title.casefold().split(" - linkedin")[0]
            if not re.search(r"(?:gerente|coordenador|supervisor|diretor|gestor|manager|director|lead|l[ií]der).{0,65}(?:produ[cç][aã]o|production|manufatur|manufactur|industrial|f[aá]brica|plant)|(?:produ[cç][aã]o|production|manufatur|manufactur|industrial|plant).{0,65}(?:gerente|coordenador|supervisor|manager|director|lead)", role):
                continue
            # Manufacturing listings should not be broad engineering/QA job advertisements.
            if re.search(r"\b(?:qa|sdet|software quality|quality engineer)\b", title.casefold()):
                continue
        found[url] = {
            "title": title[:500], "salary_usd": advertised_usd_salary(title), "url": url, "published_at": date.isoformat(),
            "source": "Public web news index", "status": "needs_review", "post_origin": post_origin(url, source_url), **labels,
        }
    return list(found.values())


def run() -> dict:
    day = datetime.now(timezone.utc).date().isoformat()
    jobs: dict[str, dict] = {}
    failures = []
    if os.environ.get("RECRUITER_MONITOR_DISABLED") == "1":
        state = "disabled"
    else:
        for query in SEARCHES + QA_SEARCHES + LINKEDIN_EXTRA_SEARCHES + COMPANY_POST_SEARCHES + MANUFACTURING_SEARCHES:
            manufacturing_query = query in MANUFACTURING_SEARCHES or query in SEARCHES[3:]
            qa_query = query == SEARCHES[0] or query in QA_SEARCHES or query in LINKEDIN_EXTRA_SEARCHES or query in COMPANY_POST_SEARCHES
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
                    jobs[result["url"]] = result
            except Exception as exc:
                failures.append(type(exc).__name__)
        state = "partial" if failures else "ok"
    data = {
        "date_utc": day, "checked_at": datetime.now(timezone.utc).isoformat(),
        "status": state, "query_count": len(SEARCHES) + len(QA_SEARCHES) + len(LINKEDIN_EXTRA_SEARCHES) + len(COMPANY_POST_SEARCHES) + len(MANUFACTURING_SEARCHES),
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
