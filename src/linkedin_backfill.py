"""Best-effort 24-month backfill of public LinkedIn-indexed recruiter posts.

Uses Google News RSS search results, not the LinkedIn API. Coverage is recorded
per month and category so an unqueried/failed month is never displayed as zero.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from xml.etree import ElementTree

from src.hunter import DATA
from src.recruiter_monitor import classify

OUTPUT = DATA / "linkedin_history.json"
QUERIES = {
    "QA": 'site:linkedin.com/posts/ ("QA" OR "quality assurance" OR "quality engineer" OR "test engineer" OR "SDET") ("hiring" OR "vaga" OR "oportunidade")',
    "Manufatura": 'site:linkedin.com/posts/ ("manufacturing manager" OR "production manager" OR "gerente de produção" OR "coordenador de produção" OR "gerente industrial" OR "plant manager") ("hiring" OR "vaga" OR "oportunidade")',
}

RECRUITING_TERMS = re.compile(
    r"\b(vaga(?:s)?|contratando|contrata(?:ção|mos)|recrut(?:ando|amento)|oportunidade(?:s)?|hiring|job opening)\b",
    re.IGNORECASE,
)
BRAZIL_TERMS = re.compile(
    r"\b(brasil|brazil|clt|r\$|são paulo|sp|rio de janeiro|rj|minas gerais|mg|paraná|pr|"
    r"santa catarina|sc|rio grande do sul|rs|pernambuco|pe|amazonas|am|bahia|ba|ceará|ce)\b|\.com\.br",
    re.IGNORECASE,
)
INTERNATIONAL_TERMS = re.compile(
    r"\b(internacional|international|worldwide|global remote|portugal|moçambique|mozambique|"
    r"united states|usa|canada|méxico|mexico|europe|europa|reino unido|united kingdom|uk)\b",
    re.IGNORECASE,
)


def market_scope(text: str) -> str:
    if BRAZIL_TERMS.search(text):
        return "Brasil"
    if INTERNATIONAL_TERMS.search(text):
        return "Internacional"
    return "Não identificado"


def month_windows(today: date, count: int = 24):
    current = today.year * 12 + today.month - 1
    result = []
    for offset in range(count - 1, -1, -1):
        value = current - offset
        year, month = divmod(value, 12)
        start = date(year, month + 1, 1)
        next_value = value + 1
        next_year, next_month = divmod(next_value, 12)
        end = date(next_year, next_month + 1, 1)
        result.append((start, end))
    return result


def parse_month(xml_text: str, area: str, start: date, end: date) -> list[dict]:
    root = ElementTree.fromstring(xml_text)
    found = {}
    for item in root.findall(".//item"):
        title = (item.findtext("title") or "").strip()
        url = (item.findtext("link") or "").strip()
        try:
            published = parsedate_to_datetime(item.findtext("pubDate") or "").astimezone(timezone.utc)
        except (TypeError, ValueError, OverflowError):
            continue
        labels = classify(title)
        if (not url.startswith("https://") or not (start <= published.date() < end)
                or labels["area"] != area or not RECRUITING_TERMS.search(title)):
            continue
        found[url] = {
            "title": title[:240], "url": url, "published_at": published.isoformat(),
            "area": area, "source": "LinkedIn public web index",
            "evidence": "indexed_recruiter_post", "first_seen": datetime.now(timezone.utc).date().isoformat(),
            "market_scope": market_scope(title),
        }
    return list(found.values())


def fetch_month(area: str, start: date, end: date, opener=urlopen):
    query = QUERIES[area] + f" after:{start.isoformat()} before:{end.isoformat()}"
    endpoint = "https://news.google.com/rss/search?" + urlencode({
        "q": query, "hl": "pt-BR", "gl": "BR", "ceid": "BR:pt-419",
    })
    request = Request(endpoint, headers={"User-Agent": "AIJobHunter/1.0 (public RSS reader)"})
    with opener(request, timeout=15) as response:
        payload = response.read(1_000_001)
    if len(payload) > 1_000_000:
        raise ValueError("Feed too large")
    return parse_month(payload.decode("utf-8"), area, start, end)


def backfill(existing: dict, today: date, months: int = 24, fetcher=fetch_month) -> dict:
    windows = month_windows(today, months)
    start_date, end_date = windows[0][0], windows[-1][1]
    records = {}
    for key, value in existing.items():
        if key == "_coverage" or not isinstance(value, dict):
            continue
        try:
            published = datetime.fromisoformat(str(value.get("published_at", "")).replace("Z", "+00:00")).date()
        except ValueError:
            records[key] = value
            continue
        if not (start_date <= published < end_date):
            records[key] = value
    coverage = dict(existing.get("_coverage") or {})
    tasks = [(area, start, end) for start, end in windows for area in QUERIES]
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(fetcher, area, start, end): (area, start) for area, start, end in tasks}
        for future in as_completed(futures):
            area, start = futures[future]
            key = start.strftime("%Y-%m")
            coverage.setdefault(key, {})
            try:
                items = future.result()
                coverage[key][area] = "ok"
                for item in items:
                    identity = hashlib.sha256(item["url"].encode("utf-8")).hexdigest()[:24]
                    records.setdefault(identity, item)
            except Exception as exc:
                coverage[key][area] = "error:" + type(exc).__name__
    records["_coverage"] = coverage
    return records


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--months", type=int, default=24, choices=range(1, 25))
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    existing = json.loads(args.output.read_text(encoding="utf-8")) if args.output.exists() else {}
    result = backfill(existing, datetime.now(timezone.utc).date(), args.months)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    count = len([value for key, value in result.items() if key != "_coverage" and isinstance(value, dict)])
    print(f"LinkedIn public-index history: {count} retained posts; {args.months} months requested")


if __name__ == "__main__":
    main()
