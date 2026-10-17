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
JOB_PATH = re.compile(r"^/jobs/\d+(?:[/?#]|$)")
REGIONAL = ("sumaré", "sumare", "campinas", "paulínia", "paulinia", "nova odessa", "americana", "hortolândia", "hortolandia")
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

def extract_jobs(html_text, base_url, company):
    parser = Links()
    parser.feed(html_text)
    result = {}
    host = urlsplit(base_url).hostname
    for href, label in parser.found:
        link = urljoin(base_url, href)
        parts = urlsplit(link)
        if parts.scheme != "https" or parts.hostname != host or not JOB_PATH.match(parts.path):
            continue
        match = re.search(r"/jobs/(\d+)", parts.path)
        if not match:
            continue
        url = base_url.rstrip("/") + "/jobs/" + match.group(1)
        result[url] = {"company": company, "title": label or "Título não disponível",
                       "location": "Não informado", "url": url,
                       "source": "Portal oficial", "published": "",
                       "regional": any(x in label.casefold() for x in REGIONAL),
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

def collect(config, fetcher=fetch_page):
    jobs, statuses = [], []
    for item in config["companies"]:
        url = item["url"]
        company = item["name"]
        try:
            page = fetcher(url)
            if len(page) > 2_000_000:
                raise ValueError("Response exceeds safety limit")
            found = extract_jobs(page, url, company)
            jobs.extend(found)
            statuses.append({"company": company, "state": "ok" if found else "needs_connector",
                             "found": len(found)})
        except (OSError, ValueError, UnicodeError) as exc:
            statuses.append({"company": company, "state": "error", "error": type(exc).__name__, "found": 0})
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
