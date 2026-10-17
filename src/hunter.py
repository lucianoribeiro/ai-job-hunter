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
    title = job["title"].lower()
    details = (job["type"] + " " + job["description"][:3000]).lower()
    combined = (title + " " + details)
    if any(term in title for term in config["blocked_title_terms"]):
        return None
    if not any(term in combined for term in config["full_time_keywords"]):
        return None
    remote = bool(job.get("remote")) or "remote" in (title + " " + job["location"] + " " + details[:1200]).lower()
    if config["remote_required"] and not remote:
        return None
    contractor = bool(re.search(r"\b(contract|contractor|freelanc|part.time|consultant|hourly)\w*", combined))
    category = "freelance" if contractor else "full-time/unspecified"
    usd = bool(re.search(r"(?:USD|US\$|\$)", job["salary"], re.I))
    flexibility = bool(re.search(r"\b(flexible|part.time|few hours|hours per (day|week))\b", combined))
    senior = bool(re.search(r"\b(lead|manager|head|principal|senior|staff)\b", title))
    score = 30 + (20 if senior else 0) + (20 if contractor else 0) + (15 if usd else 0) + (10 if flexibility else 0) + (5 if remote else 0)
    result = dict(job)
    result.update(score=score, category=category, remote=remote, usd_confirmed=usd,
                  flexibility_mentioned=flexibility, two_hours_confirmed=False)
    # Never infer exactly 2h/day from broad 'part-time' or 'flexible' language.
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
