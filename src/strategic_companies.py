"""Public career-page watcher; no private ATS API, credentials or applications."""
import argparse
import json
import re
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlsplit
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
JOB_PATHS = {
    "gupy": re.compile(r"^/jobs/\d+(?:[/?#]|$)"),
    # SAP SuccessFactors career sites (currently used here by Solvay) expose
    # public job detail links in this format. No authenticated API is used.
    "successfactors": re.compile(r"^/job/[^?#]+/\d+(?:[/?#]|$)", re.I),
}
REGIONAL = ("sumaré", "sumare", "paulínia", "paulinia", "americana")
TITLE = re.compile(r"\b(qa|quality|qualidade|test|teste|projetos?|projects?|pmo|program manager|coordenador|gerente)\b", re.I)

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.href = None
        self.label = []
        self.found = []
    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.href = dict(attrs).get("href")
            self.label = []
    def handle_data(self, data):
        if self.href is not None:
            self.label.append(data)
    def handle_endtag(self, tag):
        if tag == "a" and self.href is not None:
            self.found.append((self.href, " ".join(self.label).strip()))
            self.href = None
            self.label = []

def inferred_city(title):
    """Extract only an explicit city from the job title, never the employer HQ."""
    value = str(title or "").casefold()
    if re.search(r"\bsumar[eé]\b", value):
        return "Sumaré"
    if re.search(r"\bpaul[ií]nia\b", value):
        return "Paulínia"
    if re.search(r"\bamericana\b", value):
        return "Americana"
    return ""


def extract_jobs(html_text, base_url, company, connector="gupy"):
    parser = Links()
    parser.feed(html_text)
    result = {}
    host = urlsplit(base_url).hostname
    job_path = JOB_PATHS.get(connector)
    if job_path is None:
        raise ValueError("Unsupported public careers connector")
    for href, label in parser.found:
        link = urljoin(base_url, href)
        parts = urlsplit(link)
        if parts.scheme != "https" or parts.hostname != host or not job_path.match(parts.path):
            continue
        if connector == "gupy":
            match = re.search(r"/jobs/(\d+)", parts.path)
            if not match:
                continue
            url = "https://" + host + "/jobs/" + match.group(1)
        else:
            url = parts._replace(query="", fragment="").geturl().rstrip("/") + "/"
        location_text = label + " " + parts.path.replace("-", " ")
        result[url] = {"company": company, "title": label or "Título não disponível",
                       "location": inferred_city(location_text) or "Não informado", "url": url,
                       "source": "Portal oficial", "published": "",
                       "regional": any(x in location_text.casefold() for x in REGIONAL),
                       "target_role": bool(TITLE.search(label)),
                       "verification": "Dados parciais; confirmar detalhes no anúncio"}
    return list(result.values())

def fetch_page(url):
    if not url.startswith("https://") or not urlsplit(url).hostname:
        raise ValueError("HTTPS public career page required")
    req = Request(url, headers={"User-Agent": "AIJobHunter/1.0", "Accept": "text/html"})
    with urlopen(req, timeout=20) as response:
        if response.url != url and urlsplit(response.url).hostname != urlsplit(url).hostname:
            raise ValueError("Cross-host redirect rejected")
        return response.read(2_000_001).decode("utf-8", "replace")

def workday_3m_jobs(company, endpoint="https://3m.wd1.myworkdayjobs.com/wday/cxs/3m/Search/jobs"):
    """Public Workday search, without authentication or private member endpoints."""
    found = {}
    for offset in (0, 20, 40, 60, 80):
        body = json.dumps({"appliedFacets": {}, "limit": 20, "offset": offset, "searchText": "Sumare"}).encode("utf-8")
        request = Request(endpoint, data=body, method="POST", headers={
            "Content-Type": "application/json", "Accept": "application/json",
            "User-Agent": "AIJobHunter/1.0",
        })
        with urlopen(request, timeout=20) as response:
            payload = json.load(response)
        postings = payload.get("jobPostings", [])
        if not isinstance(postings, list):
            raise ValueError("Unexpected Workday response")
        for post in postings:
            if not isinstance(post, dict):
                continue
            path = str(post.get("externalPath") or "")
            title = str(post.get("title") or "").strip()
            location = str(post.get("locationsText") or "")
            if not title or not path.startswith("/job/") or not re.search(r"sumar[eé]|sumare|paul[ií]nia|americana", title+" "+location, re.I):
                continue
            url = urljoin("https://3m.wd1.myworkdayjobs.com/en-US/Search/", path.lstrip("/"))
            city = inferred_city(title+" "+location)
            found[url] = {"company": company, "title": title, "location": city or "Não informado",
                          "url": url, "source": "Workday público", "published": "",
                          "regional": bool(city), "target_role": bool(TITLE.search(title)),
                          "verification": "Confirmar abertura e detalhes no portal oficial"}
        if len(postings) < 20:
            break
    return list(found.values())


def ppg_public_jobs(html_text, base_url, company):
    """Recognize actual official PPG job links, never fabricate vacancies."""
    parser = Links()
    parser.feed(html_text)
    found = {}
    for href, label in parser.found:
        url = urljoin(base_url, href)
        parsed = urlsplit(url)
        if parsed.hostname != "careers.ppg.com" or not re.search(r"/(?:br/pt|global/en)/job/", parsed.path, re.I):
            continue
        text = (label or "").strip()
        if not text or not re.search(r"sumar[eé]|sumare|paul[ií]nia|americana", text+" "+parsed.path, re.I):
            continue
        city = inferred_city(text+" "+parsed.path.replace("-", " "))
        found[url] = {"company": company, "title": text, "location": city or "Não informado",
                      "url": url, "source": "Portal oficial PPG", "published": "",
                      "regional": bool(city), "target_role": bool(TITLE.search(text)),
                      "verification": "Confirmar vaga ativa no portal oficial"}
    return list(found.values())


def collect(config, fetcher=fetch_page):
    jobs, statuses = [], []
    for item in config["companies"]:
        url = item["url"]
        company = item["name"]
        if item.get("monitor", "public_links") != "public_links":
            statuses.append({"company": company, "city": item.get("city", ""), "url": url, "state": "manual", "found": 0})
            continue
        try:
            connector = item.get("connector", "gupy")
            if connector == "workday_3m":
                found = workday_3m_jobs(company)
            else:
                page = fetcher(url)
                if len(page) > 2_000_000:
                    raise ValueError("Response exceeds safety limit")
                found = ppg_public_jobs(page, url, company) if connector == "ppg_public" else extract_jobs(page, url, company, connector)
            jobs.extend(found)
            statuses.append({"company": company, "state": "ok" if found else "needs_connector",
                             "found": len(found), "city": item.get("city", ""), "url": url})
        except (OSError, ValueError, UnicodeError) as exc:
            statuses.append({"company": company, "state": "error", "error": type(exc).__name__, "found": 0, "city": item.get("city", ""), "url": url})
    return {"generated_at": datetime.now(timezone.utc).isoformat(),
            "jobs": jobs, "sources": statuses,
            "note": "Only publicly exposed links; zero results do not prove no openings. ATS APIs may require authentication."}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=ROOT / "config/strategic_companies.json")
    parser.add_argument("--output", type=Path, default=ROOT / "data/strategic_jobs.json")
    args = parser.parse_args()
    result = collect(json.loads(args.config.read_text(encoding="utf-8")))
    args.output.parent.mkdir(exist_ok=True, parents=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Company monitoring:", result["sources"])

if __name__ == "__main__":
    main()
