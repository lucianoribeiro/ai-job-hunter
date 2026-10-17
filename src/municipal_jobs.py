"""Read-only municipal job discovery with strict verification and no invented listings.

Municipal pages that do not expose individual, titled job links are recorded
as browse-only sources. This does not bypass login, CAPTCHA or access rules.
"""
from __future__ import annotations
import argparse
import html
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlsplit
from urllib.request import Request, urlopen
from datetime import datetime, timezone

SOURCES = (
    {"name": "PAT Sumaré", "url": "https://sumare.atende.net/cidadao/pagina/vagas-pat-disponiveis/", "city": "Sumaré"},
    {"name": "CPAT Campinas", "url": "https://cpat.campinas.sp.gov.br/vagas", "city": "Campinas"},
)
ROLE = re.compile(r"\b(?:gerente|coordenador(?:a)?|supervisor(?:a)?|l[ií]der|analista|engenheir[oa]|t[eé]cnic[oa]|operador(?:a)?|auxiliar|assistente|mec[aâ]nic[oa]|eletricista|soldador|torneiro|montador|projetos?|produ[cç][aã]o|manufatura|pcp)\b", re.I)

class Anchors(HTMLParser):
    def __init__(self):
        super().__init__()
        self.href = None
        self.words = []
        self.links = []
    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.href = dict(attrs).get("href")
            self.words = []
    def handle_data(self, data):
        if self.href is not None:
            self.words.append(data)
    def handle_endtag(self, tag):
        if tag == "a" and self.href is not None:
            self.links.append((self.href, " ".join(" ".join(self.words).split())))
            self.href = None

def collect_source(source, fetcher):
    base = source["url"]
    record = {**source, "status": "browse_only", "jobs": [], "reason": "Individual job listings not verified"}
    try:
        page = fetcher(base)
        parser = Anchors()
        parser.feed(page)
        seen = set()
        for href, title in parser.links:
            link = urljoin(base, href)
            parsed = urlsplit(link)
            # Restrict to the municipal domain; generic site links are not job listings.
            if (parsed.scheme != "https" or parsed.hostname != urlsplit(base).hostname
                or link.split("#")[0].rstrip("/") == base.rstrip("/")
                or not ROLE.search(title) or not re.search(r"/(?:vagas?|oportunidades?|empregos?|job|detalhe)", parsed.path, re.I)
                or link in seen):
                continue
            seen.add(link)
            record["jobs"].append({"title": title[:180], "company": "Não informada",
                                   "city": source["city"], "location_verified": False,
                                   "source": source["name"], "url": link,
                                   "published": None, "verification": "Confirmar anúncio na origem"})
        if record["jobs"]:
            record["status"] = "public_links"
            record["reason"] = "Individual links found; availability requires verification"
    except Exception as exc:
        record["status"] = "unavailable"
        record["reason"] = type(exc).__name__
    return record

def fetch(url):
    request = Request(url, headers={"User-Agent": "AIJobHunter/1.0", "Accept": "text/html"})
    with urlopen(request, timeout=15) as response:
        if urlsplit(response.url).hostname != urlsplit(url).hostname:
            raise ValueError("Cross-host redirect")
        raw = response.read(1_000_001)
        if len(raw) > 1_000_000:
            raise ValueError("Page too large")
        return raw.decode("utf-8", "replace")

def collect(fetcher=fetch):
    sources = [collect_source(source, fetcher) for source in SOURCES]
    return {"generated_at": datetime.now(timezone.utc).isoformat(),
            "sources": sources, "jobs": [job for s in sources for job in s["jobs"]]}

def inject_dashboard(page, report):
    cards = []
    for source in report["sources"]:
        url = html.escape(source["url"], quote=True)
        name = html.escape(source["name"])
        status = html.escape("Anúncios individuais encontrados" if source["jobs"] else "Consultar vagas no portal oficial")
        cards.append(f'<article style="border:1px solid #465473;border-radius:14px;padding:18px"><strong>{name}</strong><p>{status}</p><a href="{url}" target="_blank" rel="noopener noreferrer">Abrir portal oficial ↗</a></article>')
    listings = []
    for job in report["jobs"]:
        title = html.escape(job["title"])
        url = html.escape(job["url"], quote=True)
        source = html.escape(job["source"])
        listings.append(f'<article style="border:1px solid #465473;border-radius:12px;padding:14px"><strong>{title}</strong><p>{source} · Local da vaga não confirmado · Data não informada</p><a href="{url}" target="_blank" rel="noopener noreferrer">Verificar anúncio original ↗</a></article>')
    section = ('<section class="panel" id="municipal-jobs" aria-label="Fontes municipais de emprego">'
               '<h2>Vagas municipais · Região de Campinas</h2>'
               '<p>Fontes oficiais. Portais sem anúncios individuais verificáveis exibem apenas acesso à consulta. Nenhuma vaga é inventada.</p>'
               '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px">' +
               "".join(cards) + '</div><div style="display:grid;gap:10px;margin-top:16px">' +
               "".join(listings) + '</div></section>')
    # Premium dashboard is a static <body> document; older layouts used <main>.
    if 'id="municipal-jobs"' in page:
        raise ValueError("Municipal section already present")
    if "</main>" in page:
        return page.replace("</main>", section + "</main>", 1)
    if "</body>" in page:
        return page.replace("</body>", section + "</body>", 1)
    raise ValueError("Dashboard missing a supported closing container")

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dashboard", type=Path, default=Path("site/index.html"))
    p.add_argument("--output", type=Path, default=Path("data/municipal_jobs.json"))
    args = p.parse_args()
    report = collect()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    args.dashboard.write_text(inject_dashboard(args.dashboard.read_text(encoding="utf-8"), report), encoding="utf-8")
    print("Municipal portals:", {s["name"]: (s["status"], len(s["jobs"])) for s in report["sources"]})

if __name__ == "__main__":
    main()
