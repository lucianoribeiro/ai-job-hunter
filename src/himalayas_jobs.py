"""Read-only Himalayas remote job search. Source attribution and original URLs retained."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from urllib.parse import urlencode, urlsplit
from src.project_jobs_poc import load_json, qualify

QUERIES = ("quality assurance", "QA engineer", "project manager", "project coordinator")


def collect(getter=load_json):
    jobs, errors, seen = [], [], set()
    for term in QUERIES:
        url = "https://himalayas.app/jobs/api/search?" + urlencode({"q": term, "sort": "recent", "page": 1})
        try:
            payload = getter(url)
            if not isinstance(payload, dict) or not isinstance(payload.get("jobs"), list):
                raise ValueError("Unexpected Himalayas response")
            for item in payload["jobs"]:
                title = str(item.get("title") or "")
                area = ("QA" if any(k in title.casefold() for k in ("qa", "quality assurance", "quality engineer", "test engineer", "sdet")) else
                        "Projetos" if qualify({"title":title, "location":"", "description":""}) else "")
                if not area:
                    continue
                link = str(item.get("applicationLink") or item.get("url") or "")
                if not link.startswith("https://") or not urlsplit(link).hostname:
                    continue
                key = link.split("?")[0].rstrip("/")
                if key in seen:
                    continue
                seen.add(key)
                places = item.get("locationRestrictions") or []
                if isinstance(places, list):
                    location = ", ".join(str(x) for x in places if isinstance(x, str))
                else:
                    location = ""
                jobs.append({"area": area, "title": title, "company": str(item.get("companyName") or ""),
                    "location": location or "Remoto — elegibilidade não verificada", "url": link,
                    "source": "Himalayas", "remote_evidence": "explicit",
                    "published": item.get("pubDate") or item.get("publishedAt"),
                    "description": str(item.get("description") or item.get("jobDescription") or item.get("requirements") or "")[:12000],
                    "brazil_eligible": "unverified"})
        except (OSError, ValueError, KeyError, TypeError) as exc:
            errors.append({"query": term, "error": type(exc).__name__})
    return {"jobs": jobs, "errors": errors, "source": "Himalayas",
            "attribution_url": "https://himalayas.app"}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--output", type=Path, default=Path("data/himalayas_jobs.json"))
    args = p.parse_args()
    result = collect()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Himalayas: {len(result['jobs'])} matched listings; {len(result['errors'])} query errors")


if __name__ == "__main__":
    main()
