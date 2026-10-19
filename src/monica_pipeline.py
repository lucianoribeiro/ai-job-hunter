"""Generate public-safe career matching feed from a private structured profile.
No CV file is committed. The workflow supplies profile JSON using a secret.
"""
from __future__ import annotations
import argparse
import csv
import json
from pathlib import Path
from src.monica_match import assess

def collect(project_path, qa_path=None):
    document = json.loads(Path(project_path).read_text(encoding="utf-8"))
    if isinstance(document, list):
        records = document
    elif isinstance(document, dict):
        records = next((document[k] for k in ("jobs", "results", "vacancies") if isinstance(document.get(k), list)), [])
    else:
        records = []
    return [item for item in records if isinstance(item, dict)]

def build(profile, jobs):
    if not isinstance(profile, dict) or not isinstance(profile.get("competencies"), list):
        raise ValueError("A private structured profile with competencies is required")
    seen = set()
    output = []
    for job in jobs:
        url = str(job.get("url") or job.get("apply_url") or "")
        if not url or url in seen:
            continue
        seen.add(url)
        result = assess(job, profile)
        if result["recommendation"] == "exclude":
            continue
        # Do not claim a posting is open without inspecting the official live page.
        # These entries are intentionally shown as unverified until validation exists.
        output.append(result)
    return sorted(output, key=lambda x: (-x["score"], x["title"]))[:100]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", type=Path, required=True, help="Private structured JSON outside repository")
    parser.add_argument("--projects", type=Path, default=Path("data/project_jobs_poc.json"))
    parser.add_argument("--output", type=Path, default=Path("site/monica-opportunities.json"))
    args = parser.parse_args()
    profile = json.loads(args.profile.read_text(encoding="utf-8"))
    results = build(profile, collect(args.projects))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"profile_id": str(profile.get("id") or "monica"),
       "privacy": "public_job_metadata_only", "jobs": results}, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(f"Public-safe assessments: {len(results)}; no CV data exported")

if __name__ == "__main__":
    main()
