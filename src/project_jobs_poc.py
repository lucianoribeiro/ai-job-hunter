"""Opt-in, read-only project/coordination job discovery proof of concept.

Greenhouse and Lever publish company-scoped listings, not a global search API.
No credentials, LinkedIn scraping, application submissions, or personal data.
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit, urlunsplit
from urllib.request import Request, urlopen

from src.hunter import plain

ROOT = Path(__file__).resolve().parents[1]
TITLE = re.compile(r"\b(project|program|portfolio|projetos?|programas?|proyectos?|pm o|pmo)\b", re.I)
LEVEL = re.compile(r"\b(manager|management|coordinat(?:or|ion)|gerente|gest(?:a|ã)o|coordenad(?:or|ora)|lead|diretor|director)\b", re.I)
EXCLUDE = re.compile(r"\b(software engineer|developer|product manager|sales manager|account manager)\b", re.I)
REMOTE = re.compile(r"\b(remote|remoto|remota|home.office|work from anywhere)\b", re.I)


def load_json(url: str) -> object:
    request = Request(url, headers={"Accept": "application/json", "User-Agent": "AIJobHunter/1.0"})
    with urlopen(request, timeout=20) as response:
        return json.load(response)


def safe_slug(value: str) -> str:
    if not re.fullmatch(r"[a-zA-Z0-9_-]{2,90}", value):
        raise ValueError("Invalid company board slug")
    return value


def greenhouse(company: str, board: str, getter=load_json) -> list[dict]:
    slug = safe_slug(board)
    payload = getter(f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true")
    return [{
        "id": "greenhouse:" + slug + ":" + str(j["id"]),
        "source": "Greenhouse", "company": company, "title": plain(j.get("title")),
        "url": str(j.get("absolute_url") or ""), "location": plain((j.get("location") or {}).get("name")),
        "description": plain(j.get("content")), "published": None,
        "updated": j.get("updated_at"), "employment_type": "not stated",
    } for j in payload.get("jobs", [])]


def lever(company: str, site: str, getter=load_json, region: str = "global") -> list[dict]:
    slug = safe_slug(site)
    if region not in ("global", "eu"):
        raise ValueError("Invalid Lever region")
    host = "api.eu.lever.co" if region == "eu" else "api.lever.co"
    result = []
    skip, limit = 0, 100
    for _ in range(20):  # bounded pagination
        payload = getter(f"https://{host}/v0/postings/{slug}?mode=json&skip={skip}&limit={limit}")
        if not isinstance(payload, list):
            raise ValueError("Unexpected Lever payload")
        for j in payload:
            categories = j.get("categories") or {}
            result.append({
                "id": "lever:" + slug + ":" + str(j["id"]),
                "source": "Lever", "company": company, "title": plain(j.get("text")),
                "url": str(j.get("hostedUrl") or j.get("applyUrl") or ""),
                "location": plain(categories.get("location")),
                "description": plain(j.get("descriptionPlain") or j.get("description")),
                "published": None, "updated": None,
                "employment_type": plain(categories.get("commitment")),
            })
        if len(payload) < limit:
            break
        skip += limit
    return result


def canonical(url: str) -> str:
    parts = urlsplit(url)
    if parts.scheme != "https" or not parts.hostname:
        return ""
    return urlunsplit(("https", parts.netloc.lower(), parts.path.rstrip("/"), "", ""))


def qualify(job: dict) -> dict | None:
    title = job["title"]
    from src.recruiter_monitor import industrial_project_role
    industrial_match = industrial_project_role(title, str(job.get("description") or ""))
    if not ((TITLE.search(title) and LEVEL.search(title)) or industrial_match) or EXCLUDE.search(title):
        return None
    location = job.get("location", "")
    details = job.get("description", "")[:2500]
    remote_text = bool(REMOTE.search(title + " " + location))
    remote_description = bool(REMOTE.search(details))
    remote = "explicit" if remote_text else ("description_only" if remote_description else "unknown")
    job = {**job, "remote_evidence": remote, "brazil_eligible": "unverified",
           "publication_date_verified": False, "application": "external_link_only"}
    return job


def discover(config: dict, getter=load_json) -> dict:
    jobs, errors, counts = [], [], {}
    for item in config.get("boards", []):
        source = item.get("source")
        company = item.get("company", "")
        slug = item.get("slug", "")
        key = f"{source}:{slug}"
        try:
            if source == "greenhouse":
                fetched = greenhouse(company, slug, getter)
            elif source == "lever":
                fetched = lever(company, slug, getter, item.get("region", "global"))
            elif source in ("ashby", "smartrecruiters"):
                from src.ats_sources import ashby, smartrecruiters
                fetched = (ashby if source == "ashby" else smartrecruiters)(company, slug, getter)
            else:
                raise ValueError("Unsupported source")
            counts[key] = {"fetched": len(fetched), "matched": 0}
            for job in fetched:
                match = qualify(job)
                if match:
                    jobs.append(match)
                    counts[key]["matched"] += 1
        except (HTTPError, URLError, TimeoutError, ValueError, KeyError, TypeError, OSError) as exc:
            errors.append({"board": key, "error": type(exc).__name__})
    unique = {}
    for job in jobs:
        key = canonical(job["url"])
        if key:
            unique.setdefault(key, job)
    ordered = sorted(unique.values(), key=lambda x: (x["company"].casefold(), x["title"].casefold()))
    return {"generated_at": datetime.now(timezone.utc).isoformat(), "boards": counts,
            "errors": errors, "total_unique": len(ordered), "jobs": ordered,
            "limitations": ["Company-specific boards only", "Published date often unavailable",
                            "Remote and Brazil eligibility require human verification",
                            "No automated applications"]}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=ROOT / "config" / "project_boards.example.json")
    parser.add_argument("--output", type=Path, default=ROOT / "data" / "project_jobs_poc.json")
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    report = discover(config)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Boards: {len(report['boards'])}; matches: {report['total_unique']}; source errors: {len(report['errors'])}")
    return 1 if not report["boards"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
