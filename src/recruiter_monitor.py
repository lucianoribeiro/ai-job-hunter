"""Discover same-day public mentions of LinkedIn recruiter posts via Google News RSS.

This is best-effort discovery, NOT LinkedIn API access. No LinkedIn login,
scraping, recruiter email extraction, or automatic sending.
Only public titles/links are persisted in this PUBLIC repository.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
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


def classify(title: str) -> dict:
    """Conservative title-only tags; never infer remote/hybrid eligibility."""
    import re
    t = title.casefold()
    manufacturing = bool(re.search(r"manufatur|manufactur|produ[cç][aã]o|production|industrial|opera[cç][oõ]es|operations|supply chain|lean manufacturing", t))
    qa = bool(re.search(r"\bqa\b|quality engineer|quality assurance|sdet|test engineer|software test", t))
    projects = bool(re.search(r"project manager|gerente de projetos|coordenador de projetos|project coordinator|pmo", t))
    remote = bool(re.search(r"\bremote\b|\bremoto\b|home.office", t))
    hybrid = bool(re.search(r"\bhybrid\b|\bh[ií]brid[oa]\b", t))
    explicit_hiring = bool(re.search(r"hiring|contratando|estamos contratando|we.re hiring|vaga|opportunit|oportunidade|open position|job opening", t))
    area = "Manufatura" if manufacturing else "QA" if qa else "Projetos" if projects else "Outros"
    modality = "Remoto (citado)" if remote else "Híbrido (citado)" if hybrid else "Não informada"
    return {"area": area, "modality": modality, "review_priority": "high" if area != "Outros" and explicit_hiring else "low"}


def parse_feed(xml_text: str, day: str) -> list[dict]:
    """Keep only entries with a verifiable RSS publication date on UTC day."""
    root = ElementTree.fromstring(xml_text)
    found: dict[str, dict] = {}
    for item in root.findall(".//item"):
        title = (item.findtext("title") or "").strip()
        url = (item.findtext("link") or "").strip()
        published = (item.findtext("pubDate") or "").strip()
        try:
            date = parsedate_to_datetime(published).astimezone(timezone.utc)
        except (TypeError, ValueError, OverflowError):
            continue
        if date.date().isoformat() != day or not url.startswith("https://"):
            continue
        labels = classify(title)
        if labels["review_priority"] != "high":
            continue
        found[url] = {
            "title": title[:240], "url": url, "published_at": date.isoformat(),
            "source": "Public web news index", "status": "needs_review", **labels,
        }
    return list(found.values())


def run() -> dict:
    day = datetime.now(timezone.utc).date().isoformat()
    jobs: dict[str, dict] = {}
    failures = []
    if os.environ.get("RECRUITER_MONITOR_DISABLED") == "1":
        state = "disabled"
    else:
        for query in SEARCHES:
            endpoint = "https://news.google.com/rss/search?" + urlencode({
                "q": query + " when:1d", "hl": "en-US", "gl": "US", "ceid": "US:en"
            })
            try:
                req = Request(endpoint, headers={"User-Agent": "AIJobHunter/1.0 (public RSS reader)"})
                with urlopen(req, timeout=12) as response:
                    xml = response.read(1_000_001)
                if len(xml) > 1_000_000:
                    raise ValueError("Feed too large")
                for result in parse_feed(xml.decode("utf-8"), day):
                    jobs[result["url"]] = result
            except Exception as exc:
                failures.append(type(exc).__name__)
        state = "partial" if failures else "ok"
    data = {
        "date_utc": day, "checked_at": datetime.now(timezone.utc).isoformat(),
        "status": state, "query_count": len(SEARCHES),
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
