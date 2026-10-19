"""Generate public-safe career matching feed from a private structured profile.
No CV file is committed. The workflow supplies profile JSON using a secret.
"""
from __future__ import annotations
import argparse
import csv
import json
from pathlib import Path
from src.monica_match import assess
from src.monica_verify import verify
from src.monica_local import read_cv, structured_profile
from src.monica_location import location_category
from src.monica_job_enrichment import enrich
from src.monica_evidence import explain

def collect(project_path, qa_path=None):
    document = json.loads(Path(project_path).read_text(encoding="utf-8"))
    if isinstance(document, list):
        records = document
    elif isinstance(document, dict):
        records = next((document[k] for k in ("jobs", "results", "vacancies") if isinstance(document.get(k), list)), [])
    else:
        records = []
    return [item for item in records if isinstance(item, dict)]

def build(profile, jobs, check_links=False, verifier=verify, enrich_links=False, enricher=enrich):
    if not isinstance(profile, dict) or not isinstance(profile.get("competencies"), list):
        raise ValueError("A private structured profile with competencies is required")
    seen = set()
    output = []
    for job in jobs:
        url = str(job.get("url") or job.get("apply_url") or "")
        if not url or url in seen:
            continue
        seen.add(url)
        job = enricher(job) if enrich_links else job
        location_class = location_category(job)
        if location_class == "out_of_scope":
            continue
        verification = verifier(job) if check_links else {"status": "unverified", "reason": "Validação não executada"}
        result = assess(job, profile,
                        "Não aceita mais candidaturas" if verification["status"] == "closed" else
                        "Apply for this job" if verification["status"] == "apply_indicated" else "",
                        verification["status"] != "unverified")
        result["verification_reason"] = verification.get("reason", "")
        result["requirement_analysis"] = explain(job, profile)
        result["location_class"] = location_class
        result["location_evidence"] = job.get("location_evidence", "unverified")
        result["tier"] = ("recommended" if result["score"] >= 70 else "review" if result["score"] >= 50 else "low")
        if result["recommendation"] == "exclude" or result["tier"] == "low":
            continue
        # Do not claim a posting is open without inspecting the official live page.
        # These entries are intentionally shown as unverified until validation exists.
        output.append(result)
    return sorted(output, key=lambda x: (-x["score"], x["title"]))[:100]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", type=Path, help="Private structured JSON outside repository")
    parser.add_argument("--cv", type=Path, help="Local private PDF, DOCX or TXT curriculum")
    parser.add_argument("--projects", type=Path, default=Path("data/project_jobs_poc.json"))
    parser.add_argument("--output", type=Path, default=Path("site/monica-opportunities.json"))
    parser.add_argument("--extra-jobs", type=Path, nargs="*", default=[],
                        help="Additional public vacancy JSON feeds from verified regional sources")
    parser.add_argument("--enrich-links", action="store_true", help="Read JobPosting location metadata from supported ATS pages")
    parser.add_argument("--check-links", action="store_true", help="Check allowlisted ATS pages; unknown remains unverified")
    args = parser.parse_args()
    if bool(args.profile) == bool(args.cv):
        parser.error("Provide exactly one of --profile or --cv")
    profile = structured_profile(read_cv(args.cv)) if args.cv else json.loads(args.profile.read_text(encoding="utf-8"))
    jobs = collect(args.projects)
    # Use the existing official regional company watcher when its feed is present.
    # No data is invented when monitoring returns an empty list.
    regional_feed = Path("data/strategic_jobs.json")
    extras = [regional_feed] + args.extra_jobs
    for extra in extras:
        if extra.is_file():
            jobs.extend(collect(extra))
    results = build(profile, jobs, check_links=args.check_links, enrich_links=args.enrich_links)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"profile_id": str(profile.get("id") or "monica"),
       "privacy": "public_job_metadata_only", "jobs": results}, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(f"Public-safe assessments: {len(results)}; no CV data exported")

if __name__ == "__main__":
    main()
