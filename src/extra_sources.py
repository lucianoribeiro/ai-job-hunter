"""Optional public and credentialed jobs feeds; no scraping or fabricated vacancies."""
from __future__ import annotations
import argparse
import json
import os
import re
import sys
from pathlib import Path
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen

QA = re.compile(r"\b(qa|quality assurance|quality engineer|software tester|test engineer|sdet|test automation|test lead)\b", re.I)
PROJECT = re.compile(r"\b(project|program|projeto|projetos|projetista|projetos industriais)\b", re.I)
LEAD = re.compile(r"\b(manager|coordinator|lead|gerente|coordenador|coordenadora|gestor)\b", re.I)


def category(title):
    if QA.search(title):
        return "QA"
    if PROJECT.search(title) and (LEAD.search(title) or re.search(r"\b(project management|gerenciamento de projetos)\b", title, re.I)):
        return "Projetos"
    return ""


def read_json(url, headers=None, payload=None):
    req = Request(url, data=payload, headers={"User-Agent": "AIJobHunter/1.0 (+https://github.com/lucianoribeiro/ai-job-hunter)", "Accept": "application/json", **(headers or {})})
    with urlopen(req, timeout=22) as response:
        return json.load(response)


def candidate(title, company, url, location, published, source, *, explicit_remote=False):
    title = str(title or "").strip()
    kind = category(title)
    url = str(url or "").strip()
    p = urlsplit(url)
    if not kind or p.scheme != "https" or not p.hostname:
        return None
    return {"area": kind, "title": title, "company": str(company or ""),
            "url": url, "location": str(location or ""), "published": published,
            "source": source, "remote_evidence": "explicit" if explicit_remote else "unknown",
            "brazil_eligible": "Não verificado"}


def jobicy(getter=read_json):
    data = getter("https://jobicy.com/api/v2/remote-jobs?count=200")
    if not isinstance(data, dict) or not isinstance(data.get("jobs"), list):
        raise ValueError("Unexpected Jobicy payload")
    return [x for j in data["jobs"] if (x := candidate(j.get("jobTitle"), j.get("companyName"), j.get("url"), j.get("jobGeo") or "Remote", j.get("pubDate"), "Jobicy", explicit_remote=True))]


def adzuna(getter=read_json):
    app_id, key = os.getenv("ADZUNA_APP_ID"), os.getenv("ADZUNA_APP_KEY")
    if not app_id or not key:
        return [], "credentials_required"
    jobs = []
    for term in ("quality assurance", "gerente de projetos", "coordenador de projetos"):
        url = "https://api.adzuna.com/v1/api/jobs/br/search/1?" + urlencode({"app_id": app_id, "app_key": key, "results_per_page": 50, "what": term, "where": "Campinas", "distance": 80, "content-type": "application/json"})
        data = getter(url)
        if not isinstance(data.get("results"), list):
            raise ValueError("Unexpected Adzuna payload")
        for j in data["results"]:
            loc = j.get("location") or {}
            x = candidate(j.get("title"), (j.get("company") or {}).get("display_name"), j.get("redirect_url"), loc.get("display_name"), j.get("created"), "Adzuna")
            if x: jobs.append(x)
    return jobs, "active"


def jooble(getter=read_json):
    key = os.getenv("JOOBLE_API_KEY")
    if not key:
        return [], "credentials_required"
    jobs = []
    for term in ("quality assurance", "gerente de projetos", "coordenador de projetos"):
        body = json.dumps({"keywords": term, "location": "Campinas", "radius": "80", "page": "1"}).encode("utf-8")
        data = getter("https://jooble.org/api/" + key, {"Content-Type": "application/json"}, body)
        if not isinstance(data.get("jobs"), list):
            raise ValueError("Unexpected Jooble payload")
        for j in data["jobs"]:
            x = candidate(j.get("title"), j.get("company"), j.get("link"), j.get("location"), j.get("updated"), "Jooble")
            # Jooble's updated timestamp is NOT necessarily publication date.
            if x:
                x["published"] = None
                jobs.append(x)
    return jobs, "active"



def remoteok(getter=read_json):
    data = getter("https://remoteok.com/api")
    if not isinstance(data, list):
        raise ValueError("Unexpected RemoteOK payload")
    jobs = []
    for j in data:
        if not isinstance(j, dict) or not j.get("position"):
            continue
        x = candidate(j.get("position"), j.get("company"), j.get("url") or j.get("apply_url"),
                      j.get("location") or "Remoto — país não confirmado", j.get("date"),
                      "RemoteOK", explicit_remote=True)
        if x:
            jobs.append(x)
    return jobs


def themuse(getter=read_json):
    jobs = []
    for page in (0, 1, 2):
        data = getter("https://www.themuse.com/api/public/jobs?" + urlencode({"page": page}))
        if not isinstance(data, dict) or not isinstance(data.get("results"), list):
            raise ValueError("Unexpected The Muse payload")
        for j in data["results"]:
            places = j.get("locations") or []
            location = ", ".join(str(x.get("name") or "") for x in places if isinstance(x, dict))
            company = j.get("company") or {}
            x = candidate(j.get("name"), company.get("name") if isinstance(company, dict) else "",
                          (j.get("refs") or {}).get("landing_page"), location,
                          j.get("publication_date"), "The Muse")
            if x:
                jobs.append(x)
    return jobs


def workable(getter=read_json):
    """Only explicitly configured public employer boards, not arbitrary URL guesses."""
    slugs = [x.strip() for x in os.getenv("WORKABLE_COMPANIES", "").split(",") if x.strip()]
    if not slugs:
        return [], "boards_required"
    jobs = []
    for slug in slugs:
        if not re.fullmatch(r"[a-zA-Z0-9_-]{2,70}", slug):
            raise ValueError("Invalid Workable company slug")
        data = getter("https://www.workable.com/api/accounts/" + slug + "?details=false")
        if not isinstance(data, dict) or not isinstance(data.get("jobs"), list):
            raise ValueError("Unexpected Workable payload")
        for j in data["jobs"]:
            loc = ", ".join(filter(None, [j.get("city"), j.get("state"), j.get("country")]))
            x = candidate(j.get("title"), data.get("name") or slug,
                          j.get("application_url") or j.get("url") or j.get("shortlink"),
                          loc, j.get("published_on"), "Workable",
                          explicit_remote=j.get("workplace_type") == "remote")
            if x: jobs.append(x)
    return jobs, "active"

def collect(getter=read_json):
    results, status = [], {}
    for name, fn in (("Jobicy", jobicy), ("RemoteOK", remoteok), ("The Muse", themuse), ("Workable", workable), ("Adzuna", adzuna), ("Jooble", jooble)):
        try:
            value = fn(getter)
            jobs, state = value if isinstance(value, tuple) else (value, "active")
            status[name] = {"status": state, "count": len(jobs)}
            results.extend(jobs)
        except (OSError, ValueError, TypeError, KeyError) as exc:
            status[name] = {"status": "error", "error_type": type(exc).__name__, "count": 0}
    seen, unique = set(), []
    for job in results:
        url = job["url"].split("?", 1)[0].rstrip("/").lower()
        if url not in seen:
            unique.append(job); seen.add(url)
    return {"jobs": unique, "sources": status}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--output", type=Path, default=Path("data/extra_jobs.json"))
    args = p.parse_args()
    report = collect()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Extra feeds:", {k: (v["status"], v["count"]) for k, v in report["sources"].items()})


if __name__ == "__main__":
    main()
