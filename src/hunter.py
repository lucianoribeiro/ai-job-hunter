"""Public job-board aggregation and explainable job ranking (Python stdlib only)."""
from __future__ import annotations

import csv
import html
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config.json"
DATA = ROOT / "data"
USER_AGENT = "AIJobHunter/1.0 (public job listing aggregator)"


def fetch_json(url: str) -> dict:
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
    for name, fn in (("remotive", remotive), ("arbeitnow", arbeitnow)):
        if name not in config["sources"]:
            continue
        try:
            raw.extend(fn())
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
