"""Additional public, employer-scoped ATS connectors for the project-jobs POC.

Do not treat public endpoints as permission to republish data commercially.
"""
from __future__ import annotations

from src.hunter import plain
from src.project_jobs_poc import load_json, safe_slug


def ashby(company: str, slug: str, getter=load_json) -> list[dict]:
    board = safe_slug(slug)
    payload = getter(f"https://api.ashbyhq.com/posting-api/job-board/{board}?includeCompensation=true")
    if not isinstance(payload, dict) or not isinstance(payload.get("jobs"), list):
        raise ValueError("Unexpected Ashby payload")
    jobs = []
    for j in payload["jobs"]:
        if not j.get("isListed", True):
            continue
        compensation = j.get("compensation") or {}
        jobs.append({
            "id": "ashby:" + board + ":" + str(j.get("id") or j.get("jobUrl") or ""),
            "source": "Ashby", "company": company, "title": plain(j.get("title")),
            "url": str(j.get("jobUrl") or j.get("applyUrl") or ""),
            "location": plain(j.get("location")), "description": plain(j.get("descriptionPlain") or j.get("descriptionHtml")),
            "salary": plain(compensation.get("compensationTierSummary") if isinstance(compensation, dict) else ""),
            "published": None, "updated": None, "employment_type": plain(j.get("employmentType")),
            "remote": bool(j.get("isRemote")),
        })
    return jobs


def smartrecruiters(company: str, slug: str, getter=load_json) -> list[dict]:
    board = safe_slug(slug)
    result = []
    offset, limit = 0, 100
    for _ in range(20):
        payload = getter(f"https://api.smartrecruiters.com/v1/companies/{board}/postings?limit={limit}&offset={offset}")
        if not isinstance(payload, dict) or not isinstance(payload.get("content"), list):
            raise ValueError("Unexpected SmartRecruiters payload")
        records = payload["content"]
        for j in records:
            loc = j.get("location") or {}
            result.append({
                "id": "smartrecruiters:" + board + ":" + str(j.get("id") or ""),
                "source": "SmartRecruiters", "company": company, "title": plain(j.get("name")),
                "url": str(j.get("ref") or ""),
                "location": plain(", ".join(str(loc.get(k)) for k in ("city", "region", "country") if loc.get(k))),
                "description": "", "published": j.get("releasedDate"), "updated": None,
                "employment_type": plain((j.get("typeOfEmployment") or {}).get("label")),
            })
        if len(records) < limit:
            break
        offset += limit
    return result
