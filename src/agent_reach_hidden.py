"""Experimental, login-free Agent Reach discovery of hidden QA hiring signals.

Read-only adapter. Search results are hypotheses, not hidden vacancies.
No credentials, cookies, or LinkedIn sessions are handled here.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from src.hunter import DATA

QUERIES = (
    '"building our QA team" "remote"',
    '"quality engineering" "hiring" "lead"',
    '"establishing a QA function" engineering',
    '"head of quality engineering" hiring',
    '"looking for quality engineering leadership" startup',
    '"scaling our testing" "engineering" team',
)
QA = re.compile(r"\b(?:qa|qe|quality assurance|quality engineering|software quality|test automation|sdet|testing)\b", re.I)
INTENT = re.compile(r"\b(?:hiring|hire|recruiting|looking for|seeking|building (?:our|a|the) (?:qa|quality|test)|expanding (?:our|the) (?:qa|quality|test)|establishing (?:a|our) (?:qa|quality|test))\b", re.I)
LINK = re.compile(r"https?://[^\s<>\]\[)(']+", re.I)


def canonical(url: str) -> str:
    parts = urlsplit(url.strip().rstrip(".,;"))
    if parts.scheme != "https" or not parts.hostname:
        return ""
    return urlunsplit(("https", parts.netloc.lower(), parts.path.rstrip("/"), "", ""))


def classify(records: list[dict], known_urls: set[str] | None = None) -> dict:
    known_urls = known_urls or set()
    seen, accepted, rejected = set(), [], 0
    for record in records:
        url = canonical(str(record.get("url") or ""))
        excerpt = re.sub(r"\s+", " ", str(record.get("excerpt") or ""))[:1200]
        if not url or url in seen:
            continue
        seen.add(url)
        if not (QA.search(excerpt) and INTENT.search(excerpt)):
            rejected += 1
            continue
        accepted.append({
            "id": hashlib.sha256(url.encode()).hexdigest()[:16],
            "url": url,
            "excerpt": excerpt,
            "source": "Agent Reach / public web",
            "status": "potential_unconfirmed",
            "role_relevance": "quality_engineering",
            "already_known_url": url in known_urls,
            "evidence_type": "public_search_excerpt",
            "verified_hidden_opening": False,
            "brazil_eligibility": "unverified",
            "usd_compensation": "unverified",
        })
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "queries": list(QUERIES),
        "records_examined": len(records),
        "signals": len(accepted),
        "not_in_baseline_by_url": sum(not x["already_known_url"] for x in accepted),
        "rejected": rejected,
        "items": accepted,
        "disclaimer": "Public search signals only. No confirmed hidden vacancies.",
    }


def search_agent_reach() -> tuple[list[dict], list[dict]]:
    if not shutil.which("agent-reach"):
        return [], [{"error": "agent-reach not installed", "mode": "disabled"}]
    found, errors = [], []
    for query in QUERIES:
        try:
            result = subprocess.run(
                ["agent-reach", "web", "search", query],
                capture_output=True, text=True, timeout=35, check=False,
            )
            if result.returncode:
                errors.append({"query": query, "error": result.stderr[:250] or "nonzero exit"})
                continue
            output = result.stdout[:35000]
            # Agent Reach channel output may be plain text and change across versions.
            # Preserve only locally adjacent text with each public HTTPS result.
            for match in LINK.finditer(output):
                start, end = max(0, match.start() - 220), min(len(output), match.end() + 400)
                found.append({"url": match.group(), "excerpt": output[start:end], "query": query})
        except (OSError, subprocess.TimeoutExpired) as exc:
            errors.append({"query": query, "error": str(exc)[:250]})
    return found, errors


def baseline_urls(path: Path) -> set[str]:
    if not path.exists():
        return set()
    import csv
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return {canonical(str(r.get("url") or "")) for r in csv.DictReader(stream)} - {""}


def render(report: dict) -> str:
    e = lambda x: html.escape(str(x), quote=True)
    cards = "".join(
        '<article><strong>Hidden Opportunity · Potencial</strong><p>' + e(x["excerpt"][:300]) +
        '</p><a rel="noopener noreferrer" target="_blank" href="' + e(x["url"]) +
        '">Abrir evidência pública</a><p>Brasil / USD: não verificado</p></article>'
        for x in report["items"]
    )
    return (
        '<!doctype html><html lang="pt-BR"><meta charset="utf-8">'
        '<title>Hidden Opportunities · Experimental</title>'
        '<style>body{font:16px system-ui;max-width:900px;margin:40px auto;padding:0 16px}'
        'article{border:1px solid #ddd;padding:20px;border-radius:12px;margin:12px 0}</style>'
        '<h1>Hidden Opportunities — Agent Reach</h1>'
        '<p>Pesquisa de sinais públicos, não vagas ocultas confirmadas.</p>'
        '<p>Registros inspecionados: ' + e(report["records_examined"]) +
        ' · Sinais relevantes: ' + e(report["signals"]) +
        ' · URLs ausentes do CSV: ' + e(report["not_in_baseline_by_url"]) + '</p>' +
        (cards or '<p>Nenhum sinal validado nesta execução.</p>') + '</html>'
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, help="Optional public Agent Reach export JSON list")
    parser.add_argument("--output", type=Path, default=DATA / "hidden_opportunities.json")
    args = parser.parse_args()
    if args.input:
        records = json.loads(args.input.read_text(encoding="utf-8"))
        errors = []
        if not isinstance(records, list):
            raise ValueError("Input must be a JSON list of {url, excerpt}")
    else:
        records, errors = search_agent_reach()
    report = classify(records, baseline_urls(DATA / "jobs.csv"))
    report["errors"] = errors
    report["collector_status"] = "unavailable" if errors and not records else ("complete" if not errors else "partial")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    args.output.with_suffix(".html").write_text(render(report), encoding="utf-8")
    print(json.dumps({k: report[k] for k in
                      ("collector_status", "records_examined", "signals", "not_in_baseline_by_url")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
