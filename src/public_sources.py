"""Read-only adapters for public company job feeds (stdlib only)."""
import json
import re
from urllib.parse import quote
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET

USER_AGENT = "AIJobHunter/1.0 (public job discovery)"

def get(url, xml=False):
    req = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/xml" if xml else "application/json"})
    with urlopen(req, timeout=25) as response:
        return ET.fromstring(response.read()) if xml else json.load(response)

def slug(value):
    value = str(value)
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,100}", value):
        raise ValueError("Invalid public company board identifier")
    return quote(value)

def normalized(source, company, identifier, title, url, location="", description="", published="", salary="", job_type="", remote=False):
    return {"id": f"{source.lower()}:{company}:{identifier}", "title": str(title or ""), "company": str(company),
            "url": str(url or ""), "location": str(location or ""), "salary": str(salary or ""),
            "type": str(job_type or ""), "description": str(description or ""), "source": source,
            "published": str(published or ""), "remote": bool(remote)}

def greenhouse(company, board):
    data = get(f"https://boards-api.greenhouse.io/v1/boards/{slug(board)}/jobs?content=true")
    return [normalized("Greenhouse", company, j.get("id"), j.get("title"), j.get("absolute_url"),
                       (j.get("location") or {}).get("name"), j.get("content"),
                       j.get("first_published") or "", job_type="") for j in data.get("jobs", [])]

def lever(company, board):
    data = get(f"https://api.lever.co/v0/postings/{slug(board)}?mode=json")
    return [normalized("Lever", company, j.get("id"), j.get("text"), j.get("hostedUrl"),
                       (j.get("categories") or {}).get("location"), j.get("descriptionPlain") or j.get("description"),
                       job_type=(j.get("categories") or {}).get("commitment"),
                       remote=str(j.get("workplaceType") or "").lower() == "remote") for j in data]

def ashby(company, board):
    data = get(f"https://api.ashbyhq.com/posting-api/job-board/{slug(board)}?includeCompensation=true")
    return [normalized("Ashby", company, j.get("id") or j.get("jobUrl"), j.get("title"),
                       j.get("jobUrl") or j.get("applyUrl"), j.get("location"), j.get("descriptionPlain") or j.get("descriptionHtml"),
                       j.get("publishedAt") or "", (j.get("compensation") or {}).get("compensationTierSummary", "") if isinstance(j.get("compensation"), dict) else "",
                       j.get("employmentType"), j.get("isRemote", False)) for j in data.get("jobs", []) if j.get("isListed", True)]

def personio(company, board):
    root = get(f"https://{slug(board)}.jobs.personio.de/xml?language=en", xml=True)
    result = []
    for j in root.findall(".//position"):
        val = lambda key: j.findtext(key, default="")
        desc = " ".join((node.text or "") for node in j.findall(".//jobDescription/*"))
        result.append(normalized("Personio", company, val("id"), val("name"),
                                 f"https://{slug(board)}.jobs.personio.de/job/{quote(val('id'))}",
                                 val("office"), desc, val("createdAt"), job_type=val("employmentType")))
    return result

def workable(company, board):
    # Public careers endpoint; verify availability for each employer before enabling.
    data = get(f"https://apply.workable.com/api/v3/accounts/{slug(board)}/jobs")
    return [normalized("Workable", company, j.get("shortcode"), j.get("title"),
                       j.get("url") or f"https://apply.workable.com/{slug(board)}/j/{quote(str(j.get('shortcode') or ''))}/",
                       (j.get("location") or {}).get("city") if isinstance(j.get("location"), dict) else j.get("location"),
                       j.get("description"), j.get("published_on") or "", job_type=j.get("employment_type"))
            for j in data.get("results", [])]


def smartrecruiters(company, board):
    """Read public published postings, with bounded pagination."""
    jobs = []
    for offset in range(0, 500, 100):
        data = get(f"https://api.smartrecruiters.com/v1/companies/{slug(board)}/postings?limit=100&offset={offset}")
        items = data.get("content", [])
        for j in items:
            loc = j.get("location") or {}
            place = ", ".join(str(loc.get(k) or "") for k in ("city", "region", "country") if loc.get(k))
            jobs.append(normalized("SmartRecruiters", company, j.get("id"), j.get("name"),
                                   j.get("ref") or f"https://jobs.smartrecruiters.com/{slug(board)}/{quote(str(j.get('id') or ''))}",
                                   place, j.get("jobAd", {}).get("sections", {}).get("jobDescription", {}).get("text", "") if isinstance(j.get("jobAd"), dict) else "",
                                   j.get("releasedDate") or j.get("createdOn") or "",
                                   job_type=j.get("typeOfEmployment", {}).get("label", "") if isinstance(j.get("typeOfEmployment"), dict) else "",
                                   remote=bool(loc.get("remote", False))))
        if not items or offset + len(items) >= int(data.get("totalFound", 0)):
            break
    return jobs

def recruitee(company, board):
    data = get(f"https://{slug(board)}.recruitee.com/api/offers/")
    return [normalized("Recruitee", company, j.get("id"), j.get("title"),
                       j.get("careers_url") or j.get("url") or f"https://{slug(board)}.recruitee.com/o/{quote(str(j.get('slug') or ''))}",
                       ", ".join(str(loc.get("city") or "") for loc in j.get("locations", []) if isinstance(loc, dict)) or j.get("city", ""),
                       j.get("description") or "", j.get("published_at") or j.get("created_at") or "",
                       job_type=j.get("employment_type", ""), remote=bool(j.get("remote", False)))
            for j in data.get("offers", []) if j.get("status", "published") == "published"]

ADAPTERS = {"greenhouse": greenhouse, "lever": lever, "ashby": ashby, "personio": personio, "workable": workable, "smartrecruiters": smartrecruiters, "recruitee": recruitee}

def collect_boards(config):
    jobs, errors = [], []
    for source, companies in config.get("company_boards", {}).items():
        if source not in ADAPTERS:
            errors.append(f"Unknown source: {source}")
            continue
        if not isinstance(companies, list):
            errors.append(f"{source}: company boards must be a list")
            continue
        for item in companies:
            try:
                jobs.extend(ADAPTERS[source](item["company"], item["board"]))
            except (OSError, ValueError, KeyError, TypeError, AttributeError, ET.ParseError) as exc:
                errors.append(f"{source}/{item.get('company', '?')}: {exc}")
    return jobs, errors
