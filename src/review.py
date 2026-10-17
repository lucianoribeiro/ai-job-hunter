"""Maintain an explainable, review-first application pipeline.

Never submits applications. Persisted fields contain public job metadata only.
"""
from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from src.hunter import DATA

HISTORY = DATA / "history.json"
QUEUE = DATA / "applications.json"
JOBS = DATA / "jobs.csv"

VALID_STATUSES = {"pending_review", "approved", "dismissed", "applied", "interview", "rejected", "offer"}
REPUTATION = {
    "status": "unverified",
    "reason": "Company reputation requires independent verification",
}


def identity(url: str) -> str:
    parts = urlsplit(url.strip())
    normalized = urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path.rstrip("/"), "", ""))
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def assess(job: dict) -> dict:
    """Evidence-only flags: 'USD' and 2h/day are not inferred from job type."""
    title = job.get("title", "").lower()
    salary = job.get("salary", "")
    location = job.get("location", "").lower()
    reasons = []
    if any(term in title for term in ("qa lead", "qa manager", "quality engineering manager", "test lead")):
        reasons.append("Matches QA leadership target")
    elif any(term in title for term in ("qa", "quality", "test", "sdet")):
        reasons.append("Matches QA/testing target")
    if str(job.get("usd_confirmed", "")).lower() == "true":
        reasons.append("USD compensation indicated in the listing")
    if "brazil" in location or "worldwide" in location or "anywhere" in location or "global" in location:
        reasons.append("Location text may include Brazil; confirm eligibility")
    if job.get("category") == "freelance":
        reasons.append("Contract/freelance terms detected; confirm daily hours")
    return {
        "fit_reasons": reasons,
        "company_reputation": dict(REPUTATION),
        "brazil_eligibility": "needs_review",
        "two_hours_per_day": "unverified",
        "salary_currency": "USD_indicated" if str(job.get("usd_confirmed", "")).lower() == "true" else "unspecified",
    }


def reconcile(jobs: list[dict], history: dict, queue: dict, today: str) -> tuple[dict, dict, list[dict]]:
    new_jobs = []
    for job in jobs:
        url = str(job.get("url", "")).strip()
        if not url.startswith(("https://", "http://")):
            continue
        job_id = identity(url)
        if job_id not in history:
            history[job_id] = {"first_seen": today}
            new_jobs.append(job)
        history[job_id].update({
            "last_seen": today,
            "title": job.get("title", ""),
            "company": job.get("company", ""),
            "url": url,
            "source": job.get("source", ""),
            "score": int(job.get("score", 0)),
        })
        if job_id not in queue:
            queue[job_id] = {"status": "pending_review", "created_at": today, "notes": ""}
        previous = queue[job_id]
        previous.setdefault("status_updated_at", previous.get("created_at", today))
        previous.setdefault("status_history", [{"status": previous.get("status"), "date": previous["status_updated_at"]}])
        if previous.get("status") not in VALID_STATUSES:
            raise ValueError(f"Invalid status for {job_id}: {previous.get('status')}")
        previous.update({
            "job_id": job_id, "url": url, "company": job.get("company", ""),
            "title": job.get("title", ""), "score": int(job.get("score", 0)),
            "category": job.get("category", ""), "assessment": assess(job),
        })
    return history, queue, new_jobs


def run() -> None:
    if not JOBS.exists():
        raise FileNotFoundError(f"Run the hunter first: {JOBS}")
    with JOBS.open(newline="", encoding="utf-8") as fp:
        jobs = list(csv.DictReader(fp))
    linkedin_path = DATA / "linkedin_jobs.json"
    if linkedin_path.exists():
        imported = json.loads(linkedin_path.read_text(encoding="utf-8"))
        if not isinstance(imported, list):
            raise ValueError("linkedin_jobs.json must be a JSON list")
        jobs.extend(imported)
    today = datetime.now(timezone.utc).date().isoformat()
    history, queue, new_jobs = reconcile(jobs, load_json(HISTORY), load_json(QUEUE), today)
    DATA.mkdir(exist_ok=True)
    HISTORY.write_text(json.dumps(history, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    QUEUE.write_text(json.dumps(queue, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    lines = ["# Applications awaiting review", "",
             "No applications are submitted automatically. Verify employer reputation, Brazil eligibility, pay and hours.", "",
             f"New matches in this run: **{len(new_jobs)}**", "",
             "## Pending review", ""]
    pending = sorted((j for j in queue.values() if j["status"] == "pending_review"),
                     key=lambda item: -item["score"])
    for item in pending[:100]:
        title = item["title"].replace("[", "").replace("]", "")
        lines.append(f"- [{title}]({item['url']}) — {item['company']} | score {item['score']} | {item['category']} | employer unverified")
    if not pending:
        lines.append("No pending jobs.")
    (DATA / "applications.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Review queue: {len(pending)} pending; {len(new_jobs)} new")


if __name__ == "__main__":
    run()
