"""Opt-in LinkedIn link importer: no LinkedIn requests, login, scraping or redistribution.

Input is a user's own curated list of job URLs. The job metadata is intentionally
unverified until the user independently confirms it. Posts can be saved as links,
but cannot be assumed to be job postings.
"""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path
from urllib.parse import urlsplit

from src.linkedin_alerts import canonical_job_url

POST_ID = re.compile(r"^/posts/[A-Za-z0-9_-]{6,}/?$")
ACTIVITY_ID = re.compile(r"^/feed/update/urn:li:activity:\d+/?$")


def canonical_shared_url(raw: str) -> tuple[str, str] | None:
    job = canonical_job_url(raw)
    if job:
        return job, "job"
    try:
        value = urlsplit(raw.strip())
    except ValueError:
        return None
    if value.scheme != "https" or (value.hostname or "").lower() not in ("linkedin.com", "www.linkedin.com"):
        return None
    try:
        if value.username or value.password or value.port not in (None, 443):
            return None
    except ValueError:
        return None
    if POST_ID.fullmatch(value.path) or ACTIVITY_ID.fullmatch(value.path):
        return "https://www.linkedin.com" + value.path.rstrip("/"), "post"
    return None


def import_links(lines: list[str]) -> list[dict]:
    found = {}
    for item in lines:
        parsed = canonical_shared_url(item)
        if not parsed:
            continue
        url, kind = parsed
        found[url] = {
            "url": url, "kind": kind, "source": "LinkedIn (link compartilhado)",
            "title": "Não verificado", "company": "Não verificada",
            "location": "Não informada", "remote_evidence": "unknown",
            "status": "revisão manual necessária",
        }
    return list(found.values())


def main():
    p = argparse.ArgumentParser(description="Importar apenas links fornecidos voluntariamente")
    p.add_argument("input", type=Path, help="Arquivo .txt com uma URL por linha")
    p.add_argument("--output", type=Path, default=Path("data/linkedin_shared_jobs.json"))
    args = p.parse_args()
    if args.input.suffix.lower() != ".txt" or not args.input.is_file() or args.input.is_symlink():
        raise ValueError("Entrada deve ser um arquivo .txt regular")
    if args.input.stat().st_size > 100_000:
        raise ValueError("Arquivo muito grande")
    records = import_links(args.input.read_text(encoding="utf-8").splitlines())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{len(records)} links importados; nenhuma consulta ao LinkedIn realizada")


if __name__ == "__main__":
    main()
