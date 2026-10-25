"""Collect real QA postings from confirmed employer ATS boards in the Campinas region."""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path

from src.project_jobs_poc import lever

QA = re.compile(r"\b(?:QA|SDET|quality assurance|quality engineer|software tester|test engineer|test automation|automation tester|test lead)\b", re.I)
LOCAL = re.compile(r"nova odessa|americana|sumar[eé]|santa b[aá]rbara|hortol[aâ]ndia|campinas", re.I)
BR = re.compile(r"brazil|brasil|homeoffice", re.I)


def select(jobs):
    seen = set()
    result = []
    for job in jobs:
        title, location = str(job.get("title") or ""), str(job.get("location") or "")
        if not QA.search(title) or not (LOCAL.search(location) or BR.search(location)):
            continue
        url = str(job.get("url") or "")
        if not url.startswith("https://jobs.lever.co/") or url in seen:
            continue
        seen.add(url)
        result.append({**job, "remote_evidence": "unknown", "brazil_eligible": "unverified",
                       "application": "external_link_only", "published": None})
    return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--output", type=Path, default=Path("data/regional_qa_jobs.json"))
    args = p.parse_args()
    try:
        raw = lever("CI&T", "ciandt")
    except Exception as exc:
        # An external ATS outage must not interrupt the dashboard deployment.
        print(f"CI&T ATS unavailable ({type(exc).__name__}); retaining previous snapshot")
        if args.output.exists():
            try:
                previous = json.loads(args.output.read_text(encoding="utf-8"))
                if isinstance(previous, list):
                    print(f"Retained {len(previous)} regional QA records")
                    return
            except (OSError, ValueError):
                pass
        raw = []
    jobs = select(raw)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(jobs, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"CI&T: {len(raw)} postings read, {len(jobs)} QA candidates for regional/Brazil review")


if __name__ == "__main__":
    main()
