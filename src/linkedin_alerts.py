"""Opt-in import of locally supplied LinkedIn job-alert .eml files.

No Gmail or LinkedIn login. Does not export email bodies, subjects, addresses,
tracking pixels or subscriber details. Only job URLs and tentative titles.
"""
from __future__ import annotations

import argparse
import json
import re
from email import policy
from email.parser import BytesParser
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit, urlunsplit

from src.hunter import DATA

JOB_ID = re.compile(r"/jobs/view/(?:[^/?#]*/)?(\d{6,})(?:[/?#]|$)")
ALLOWED_HOSTS = {"linkedin.com", "www.linkedin.com", "lnkd.in"}


def canonical_job_url(raw: str) -> str | None:
    """Only accept explicit LinkedIn /jobs/view/<numeric-id> links.

    Some alert links use LinkedIn tracking redirects; we intentionally skip them
    rather than following network redirects or unintentionally storing tokens.
    """
    raw = raw.replace("&amp;", "&").strip()
    try:
        parsed = urlsplit(raw)
    except ValueError:
        return None
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or host not in ALLOWED_HOSTS:
        return None
    if host == "lnkd.in":
        return None
    match = JOB_ID.search(parsed.path)
    if not match:
        return None
    return f"https://www.linkedin.com/jobs/view/{match.group(1)}/"


class JobAnchorParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.current_url: str | None = None
        self.text_parts: list[str] = []
        self.found: dict[str, str] = {}

    def handle_starttag(self, tag, attrs):
        if tag != "a":
            return
        href = dict(attrs).get("href", "")
        self.current_url = canonical_job_url(href)
        self.text_parts = []

    def handle_data(self, data):
        if self.current_url:
            self.text_parts.append(data)

    def handle_endtag(self, tag):
        if tag == "a" and self.current_url:
            title = re.sub(r"\s+", " ", " ".join(self.text_parts)).strip()
            self.found.setdefault(self.current_url, title[:160] or "LinkedIn job")
            self.current_url = None
            self.text_parts = []


def extract_eml(path: Path) -> dict[str, str]:
    if path.suffix.lower() != ".eml" or path.is_symlink():
        raise ValueError("Only regular .eml files are accepted")
    if path.stat().st_size > 2_000_000:
        raise ValueError("EML exceeds the 2MB safety limit")
    message = BytesParser(policy=policy.default).parsebytes(path.read_bytes())
    found: dict[str, str] = {}
    for part in message.walk():
        if part.get_content_disposition() == "attachment":
            continue
        content_type = part.get_content_type()
        if content_type not in ("text/plain", "text/html"):
            continue
        try:
            content = part.get_content()
        except (UnicodeError, LookupError, ValueError):
            continue
        if not isinstance(content, str):
            continue
        if content_type == "text/html":
            parser = JobAnchorParser()
            parser.feed(content)
            found.update(parser.found)
        else:
            for raw in re.findall(r"https://[^\s<>\"']+", content):
                url = canonical_job_url(raw.rstrip(").,;"))
                if url:
                    found.setdefault(url, "LinkedIn job")
    return found


def import_files(paths: list[Path]) -> list[dict]:
    found: dict[str, str] = {}
    for path in paths:
        found.update(extract_eml(path))
    return [{"id": url.split("/")[-2], "url": url, "title": title,
             "company": "Unverified", "source": "LinkedIn alert",
             "location": "Not stated", "salary": "", "category": "unspecified",
             "score": 0, "remote": False, "usd_confirmed": False}
            for url, title in sorted(found.items())]


def main() -> None:
    parser = argparse.ArgumentParser(description="Opt-in LinkedIn alert importer (.eml)")
    parser.add_argument("files", nargs="+", type=Path)
    args = parser.parse_args()
    jobs = import_files(args.files)
    DATA.mkdir(exist_ok=True)
    output = DATA / "linkedin_jobs.json"
    existing = json.loads(output.read_text(encoding="utf-8")) if output.exists() else []
    if not isinstance(existing, list):
        raise ValueError("linkedin_jobs.json must be a JSON list")
    merged = {job["url"]: job for job in existing}
    merged.update({job["url"]: job for job in jobs})
    output.write_text(json.dumps(list(merged.values()), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Imported {len(jobs)} unique job links; {len(merged)} stored. Raw emails are not saved.")


if __name__ == "__main__":
    main()
