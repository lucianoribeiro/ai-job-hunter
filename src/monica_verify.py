"""Best-effort vacancy checks against approved public ATS domains only.
Unknown is never open. This is not login automation or browser bypass.
"""
from __future__ import annotations
import re
from urllib.parse import urlsplit
from urllib.request import Request, urlopen, build_opener, HTTPRedirectHandler
from src.monica_match import application_status

ATS_HOSTS = (
    "boards.greenhouse.io", "job-boards.greenhouse.io", "jobs.lever.co",
    "jobs.eu.lever.co", "jobs.ashbyhq.com", "careers.smartrecruiters.com",
)
class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None

def allowed(url):
    parsed = urlsplit(str(url or ""))
    return parsed.scheme == "https" and (parsed.hostname or "").lower() in ATS_HOSTS and not parsed.username

def verify(job, getter=None):
    """Check bounded HTML. A visible Apply CTA is only 'indicated', not proof of submission."""
    url = str(job.get("url") or "")
    if not allowed(url):
        return {"status": "unverified", "reason": "Fonte fora da lista ATS permitida"}
    if getter is None:
        def getter(u):
            req = Request(u, headers={"User-Agent": "AIJobHunter/1.0 public posting validation",
                                      "Accept": "text/html"})
            with build_opener(NoRedirect()).open(req, timeout=12) as result:
                if result.headers.get_content_type() != "text/html":
                    raise ValueError("Not an HTML page")
                return result.read(200_000).decode("utf-8", errors="replace")
    try:
        markup = getter(url)
        # Skip tags but retain visible words, never let a regex match a JS string literal.
        from html.parser import HTMLParser
        class Visible(HTMLParser):
            def __init__(self):
                super().__init__(); self.parts=[]; self.skip=0
            def handle_starttag(self, tag, attrs):
                if tag in ("script","style","template"): self.skip+=1
            def handle_endtag(self, tag):
                if tag in ("script","style","template") and self.skip: self.skip-=1
            def handle_data(self, data):
                if not self.skip: self.parts.append(data)
        parser=Visible(); parser.feed(markup)
        status = application_status(" ".join(parser.parts), source_verified=True)
        return {"status": status, "reason": ("Indicador de encerramento na página" if status=="closed"
             else "Formulário indicado na página" if status=="apply_indicated"
             else "Não foi possível verificar inscrição pela página")}
    except (OSError, ValueError, TimeoutError, UnicodeError):
        return {"status": "unverified", "reason": "Página indisponível ou bloqueada"}

