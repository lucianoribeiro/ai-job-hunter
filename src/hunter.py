"""Public job-board aggregation and explainable job ranking (Python stdlib only)."""
from __future__ import annotations

import csv
import html
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config.json"
DATA = ROOT / "data"
USER_AGENT = "AIJobHunter/1.0 (public job listing aggregator)"


def fetch_json(url: str) -> dict | list:
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urlopen(request, timeout=25) as response:
        return json.load(response)


def plain(value: object) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]*>", " ", str(value or "")))).strip()


def remotive() -> list[dict]:
    data = fetch_json("https://remotive.com/api/remote-jobs?search=quality%20assurance")
    return [{
        "id": "remotive:" + str(j.get("id", "")),
        "title": plain(j.get("title")), "company": plain(j.get("company_name")),
        "url": str(j.get("url", "")), "location": plain(j.get("candidate_required_location")),
        "salary": plain(j.get("salary")), "type": plain(j.get("job_type")),
        "description": plain(j.get("description")), "source": "Remotive",
        "published": str(j.get("publication_date", "")),
    } for j in data.get("jobs", [])]


def arbeitnow() -> list[dict]:
    data = fetch_json("https://www.arbeitnow.com/api/job-board-api")
    return [{
        "id": "arbeitnow:" + str(j.get("slug", "")),
        "title": plain(j.get("title")), "company": plain(j.get("company_name")),
        "url": str(j.get("url", "")), "location": plain(j.get("location")),
        "salary": "", "type": " ".join(j.get("job_types", []) or []),
        "description": plain(j.get("description")), "source": "Arbeitnow",
        "published": str(j.get("created_at", "")),
        "remote": bool(j.get("remote", False)),
    } for j in data.get("data", [])]



def jobicy() -> list[dict]:
    data = fetch_json("https://jobicy.com/api/v2/remote-jobs?count=200")
    return [{
        "id": "jobicy:" + str(j.get("id", "")),
        "title": plain(j.get("jobTitle")), "company": plain(j.get("companyName")),
        "url": str(j.get("url", "")), "location": plain(j.get("jobGeo", "Remote")),
        "salary": plain(j.get("annualSalaryMin") and (
            "USD " + str(j.get("annualSalaryMin")) + "-" + str(j.get("annualSalaryMax") or j.get("annualSalaryMin")) + " annual"
        ) if j.get("salaryCurrency") == "USD" else ""),
        "type": plain(j.get("jobType")), "description": plain(j.get("jobDescription")),
        "source": "Jobicy", "published": str(j.get("pubDate", "")), "remote": True,
    } for j in data.get("jobs", []) if isinstance(j, dict)]


def himalayas() -> list[dict]:
    jobs = []
    for keyword in ("quality assurance", "project manager", "qa engineer"):
        data = fetch_json("https://himalayas.app/jobs/api/search?q=" + quote(keyword) + "&sort=recent&page=1")
        for j in data.get("jobs", []):
            if not isinstance(j, dict):
                continue
            currency = str(j.get("currency") or "")
            minimum, maximum = j.get("minSalary"), j.get("maxSalary")
            period = str(j.get("salaryPeriod") or "annual")
            salary = (f"{currency} {minimum}-{maximum or minimum} {period}" if minimum and currency else "")
            jobs.append({
                "id": "himalayas:" + str(j.get("guid") or j.get("id") or ""),
                "title": plain(j.get("title")), "company": plain(j.get("companyName")),
                "url": str(j.get("applicationLink") or j.get("url") or ""),
                "location": plain(", ".join(j.get("locationRestrictions") or []) or j.get("location") or "Remote"),
                "salary": salary, "type": plain(j.get("employmentType")),
                "description": plain(j.get("description")),
                "source": "Himalayas", "published": str(j.get("pubDate") or j.get("publishedAt") or ""),
                "remote": True,
            })
    return jobs


def remoteok() -> list[dict]:
    data = fetch_json("https://remoteok.com/api")
    return [{
        "id": "remoteok:" + str(j.get("id", "")),
        "title": plain(j.get("position")), "company": plain(j.get("company")),
        "url": str(j.get("url") or j.get("apply_url") or ""),
        "location": plain(j.get("location") or "Remote"),
        "salary": (f"USD {j.get('salary_min')}-{j.get('salary_max')} annual"
                   if j.get("salary_min") else ""),
        "type": plain(j.get("tags")), "description": plain(j.get("description")),
        "source": "Remote OK", "published": str(j.get("date") or ""),
        "remote": True,
    } for j in data if isinstance(j, dict) and j.get("position")]



def _boards(config: dict, provider: str) -> list[dict]:
    return [b for b in config.get("company_boards", []) if b.get("provider") == provider and b.get("slug")]


def company_ats(config: dict, provider: str) -> list[dict]:
    jobs = []
    for board in _boards(config, provider):
        slug = quote(str(board["slug"]), safe="")
        company = board.get("company") or slug
        if provider == "greenhouse":
            records = fetch_json(f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true").get("jobs", [])
        elif provider == "lever":
            records = fetch_json(f"https://api.lever.co/v0/postings/{slug}?mode=json")
        else:
            records = fetch_json(f"https://api.ashbyhq.com/posting-api/job-board/{slug}?includeCompensation=true").get("jobs", [])
        for j in records:
            if provider == "greenhouse":
                location = (j.get("location") or {}).get("name", "")
                url = j.get("absolute_url", "")
                description = j.get("content", "")
                salary = ""
                published = j.get("updated_at", "")
                remote = "remote" in location.lower()
            elif provider == "lever":
                cats = j.get("categories") or {}
                location = cats.get("location") or ""
                url = j.get("hostedUrl") or j.get("applyUrl") or ""
                description = j.get("descriptionPlain") or j.get("description") or ""
                salary = plain(j.get("salaryDescriptionPlain") or "")
                published = str(j.get("createdAt") or "")
                remote = (j.get("workplaceType") or "").lower() == "remote"
            else:
                location = j.get("location") or ""
                url = j.get("jobUrl") or j.get("applyUrl") or ""
                description = j.get("descriptionPlain") or j.get("descriptionHtml") or ""
                compensation = j.get("compensation") or {}
                salary = plain(compensation.get("compensationTierSummary") or compensation.get("scrapeableCompensationSalarySummary") or "")
                published = j.get("publishedAt") or ""
                remote = bool(j.get("isRemote"))
            jobs.append({"id": f"{provider}:{slug}:{j.get('id', '')}", "title": plain(j.get("title")),
                         "company": plain(company), "url": str(url), "location": plain(location),
                         "salary": salary, "type": plain(j.get("employmentType") or ""),
                         "description": plain(description), "source": provider.title(),
                         "published": str(published), "remote": remote})
    return jobs


def adzuna() -> list[dict]:
    app_id, key = os.getenv("ADZUNA_APP_ID"), os.getenv("ADZUNA_APP_KEY")
    if not app_id or not key:
        raise ValueError("Missing ADZUNA_APP_ID / ADZUNA_APP_KEY")
    jobs = []
    for country in ("br", "us"):
        data = fetch_json(f"https://api.adzuna.com/v1/api/jobs/{country}/search/1?app_id={quote(app_id)}&app_key={quote(key)}&results_per_page=50&what=quality%20assurance")
        for j in data.get("results", []):
            salary = (f"{j.get('salary_min')} - {j.get('salary_max')} {country.upper()} annual" if j.get("salary_min") else "")
            jobs.append({"id": "adzuna:" + str(j.get("id")), "title": plain(j.get("title")),
                         "company": plain((j.get("company") or {}).get("display_name")),
                         "url": j.get("redirect_url", ""), "location": plain((j.get("location") or {}).get("display_name")),
                         "salary": salary, "type": plain(j.get("contract_type") or ""),
                         "description": plain(j.get("description")), "source": "Adzuna",
                         "published": j.get("created", "")})
    return jobs


def jooble() -> list[dict]:
    key = os.getenv("JOOBLE_API_KEY")
    if not key:
        raise ValueError("Missing JOOBLE_API_KEY")
    from urllib.request import Request
    request = Request("https://jooble.org/api/" + quote(key),
                      data=json.dumps({"keywords": "QA engineer", "page": 1}).encode(),
                      headers={"Content-Type": "application/json", "User-Agent": USER_AGENT}, method="POST")
    with urlopen(request, timeout=25) as response:
        data = json.load(response)
    return [{"id": "jooble:" + str(j.get("id") or j.get("link")),
             "title": plain(j.get("title")), "company": plain(j.get("company")),
             "url": j.get("link", ""), "location": plain(j.get("location")),
             "salary": plain(j.get("salary")), "type": plain(j.get("type")),
             "description": plain(j.get("snippet")), "source": "Jooble",
             "published": str(j.get("updated") or "")} for j in data.get("jobs", [])]


def reed() -> list[dict]:
    key = os.getenv("REED_API_KEY")
    if not key:
        raise ValueError("Missing REED_API_KEY")
    import base64
    token = base64.b64encode((key + ":").encode()).decode()
    request = Request("https://www.reed.co.uk/api/1.0/search?keywords=quality%20assurance&resultsToTake=100",
                      headers={"Authorization": "Basic " + token, "User-Agent": USER_AGENT})
    with urlopen(request, timeout=25) as response:
        data = json.load(response)
    return [{"id": "reed:" + str(j.get("jobId")), "title": plain(j.get("jobTitle")),
             "company": plain(j.get("employerName")), "url": j.get("jobUrl", ""),
             "location": plain(j.get("locationName")), "salary": plain(j.get("minimumSalary") or ""),
             "type": "", "description": plain(j.get("jobDescription")),
             "source": "Reed", "published": str(j.get("date") or "")} for j in data.get("results", [])]


def usajobs() -> list[dict]:
    key, email = os.getenv("USAJOBS_API_KEY"), os.getenv("USAJOBS_USER_AGENT")
    if not key or not email:
        raise ValueError("Missing USAJOBS_API_KEY / USAJOBS_USER_AGENT")
    request = Request("https://data.usajobs.gov/api/search?Keyword=quality%20assurance&ResultsPerPage=100",
                      headers={"Authorization-Key": key, "User-Agent": email, "Host": "data.usajobs.gov"})
    with urlopen(request, timeout=25) as response:
        data = json.load(response)
    jobs = []
    for item in (data.get("SearchResult") or {}).get("SearchResultItems", []):
        j = item.get("MatchedObjectDescriptor") or {}
        pay = j.get("PositionRemuneration") or []
        salary = (str(pay[0].get("MinimumRange", "")) + " - " + str(pay[0].get("MaximumRange", "")) + " USD " + str(pay[0].get("RateIntervalCode", ""))) if pay else ""
        jobs.append({"id": "usajobs:" + str(j.get("PositionID")), "title": plain(j.get("PositionTitle")),
                     "company": plain(j.get("OrganizationName")), "url": j.get("PositionURI", ""),
                     "location": plain(j.get("PositionLocationDisplay")), "salary": salary,
                     "type": "", "description": plain(j.get("QualificationSummary")),
                     "source": "USAJOBS", "published": j.get("PublicationStartDate", "")})
    return jobs

def classify(job: dict, config: dict) -> dict | None:
    title = str(job.get("title") or "").lower()
    location = str(job.get("location") or "").lower()
    job_type = str(job.get("type") or "").lower()
    description = str(job.get("description") or "").lower()
    if any(term in title for term in config["blocked_title_terms"]):
        return None
    # QA terms in descriptions do not establish that a role itself is in QA.
    allowed = config["full_time_keywords"] + config.get("freelance_keywords", [])
    if not any(term in title for term in allowed):
        return None
    context = title + " " + location + " " + job_type
    negative = bool(re.search(r"\b(not remote|no remote|on.site|onsite|on site|in.office|office.based|hybrid)\b", context))
    explicit_remote = bool(job.get("remote")) or bool(re.search(r"\b(remote|worldwide remote|work from anywhere|distributed)\b", context))
    remote = explicit_remote and not negative
    if config["remote_required"] and not remote:
        return None
    contract = bool(re.search(r"\b(freelanc\w*|independent contractor|contractor|contract|part.time|hourly|project.based)\b", title + " " + job_type))
    category = "freelance" if contract else "full-time/unspecified"
    salary = str(job.get("salary") or "")
    usd = bool(re.search(r"\bUSD\b|US\$|\$", salary, re.I))
    flexible = bool(re.search(r"\b(flexible|part.time|few hours|hours per (day|week))\b", title + " " + job_type + " " + description[:1500]))
    hours = bool(re.search(r"\b(?:2|two)\s+hours?\s+(?:per|a|/)\s+day\b|\b(?:up to|maximum|max)\s+10\s+hours?\s+(?:per|a|/)\s+week\b", title + " " + job_type + " " + description[:2000]))
    senior = bool(re.search(r"\b(lead|manager|head|principal|senior|staff)\b", title))
    score = min(100, 30 + (20 if senior else 0) + (20 if contract else 0) + (15 if usd else 0) + (10 if flexible else 0) + (5 if remote else 0))
    result = dict(job)
    result.update(score=score, category=category, remote=remote, usd_confirmed=usd,
                  flexibility_mentioned=flexible, two_hours_confirmed=hours)
    result.pop("description", None)
    return result


def collect(config: dict) -> tuple[list[dict], list[str]]:
    raw, errors = [], []
    source_counts = {}
    for name, fn in (("remotive", remotive), ("arbeitnow", arbeitnow), ("jobicy", jobicy), ("himalayas", himalayas), ("remoteok", remoteok), ("greenhouse", lambda: company_ats(config, "greenhouse")), ("lever", lambda: company_ats(config, "lever")), ("ashby", lambda: company_ats(config, "ashby")), ("adzuna", adzuna), ("jooble", jooble), ("reed", reed), ("usajobs", usajobs)):
        if name not in config["sources"]:
            continue
        try:
            fetched = fn()
            if not isinstance(fetched, list):
                raise ValueError("Unexpected source response: expected list")
            source_counts[name] = len(fetched)
            raw.extend(fetched)
        except (OSError, ValueError, KeyError, TypeError) as error:
            errors.append(f"{name}: {error}")
    seen, ranked = set(), []
    for job in raw:
        url = job.get("url", "").split("?")[0].rstrip("/").lower()
        identity = url or (job.get("company", "").lower(), job.get("title", "").lower())
        if identity in seen or not job.get("url"):
            continue
        seen.add(identity)
        match = classify(job, config)
        if match:
            ranked.append(match)
    ranked.sort(key=lambda x: (-x["score"], x["company"].lower(), x["title"].lower()))
    print("Source results: " + ", ".join(f"{name}={count}" for name, count in source_counts.items()))
    return ranked[: config.get("max_results", 100)], errors


FIELDS = ["score", "category", "title", "company", "location", "salary", "type",
          "remote", "usd_confirmed", "flexibility_mentioned", "two_hours_confirmed",
          "published", "source", "url", "id"]


def write_outputs(jobs: list[dict], errors: list[str]) -> None:
    DATA.mkdir(exist_ok=True)
    with (DATA / "jobs.csv").open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(jobs)
    lines = ["# QA opportunities", "",
             "Generated: " + datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"), "",
             f"Matched listings: **{len(jobs)}**", "",
             "Review all job terms manually. USD/2h-day are **not assumed** when absent.", ""]
    for category in ("freelance", "full-time/unspecified"):
        lines += ["## " + category.title(), ""]
        matches = [j for j in jobs if j["category"] == category]
        if not matches:
            lines += ["No matching listings returned.", ""]
        for j in matches[:40]:
            title = j["title"].replace("[", "").replace("]", "")
            company = j["company"].replace("\n", " ")
            lines.append(f"- **{j['score']} pts** [{title}]({j['url']}) — {company} | {j['location']} | salary: {j['salary'] or 'not stated'}")
        lines.append("")
    if errors:
        lines += ["## Source errors", ""] + ["- " + e for e in errors] + [""]
    (DATA / "report.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    jobs, errors = collect(config)
    write_outputs(jobs, errors)
    print(f"Saved {len(jobs)} jobs; source errors: {len(errors)}")
    for error in errors:
        print(error, file=sys.stderr)
    return 1 if errors and len(errors) == len(config["sources"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
