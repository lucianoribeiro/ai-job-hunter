"""Isolated hidden-opportunity investigation. No existing collector or Pages integration."""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

QA = re.compile(r"\b(?:qa|quality engineering|quality assurance|sdet|test automation|software quality)\b", re.I)
INTENT = re.compile(r"\b(?:hiring|recruiting|looking for|seeking|building (?:our|a) (?:qa|quality)|expanding (?:our|the) (?:qa|quality))\b", re.I)
LEAD = re.compile(r"\b(?:lead|manager|head|director|principal|staff|leadership|coordinator)\b", re.I)
EXCLUDE = re.compile(r"\b(?:open to work|open to new opportunities|looking for a job|no longer available|not accepting applications)\b", re.I)


def canonical_url(raw: str) -> str:
    p = urlsplit(str(raw or "").strip())
    if p.scheme != "https" or not p.hostname:
        return ""
    return urlunsplit(("https", p.netloc.lower(), p.path.rstrip("/"), "", ""))


def source_type(url: str) -> str:
    p = urlsplit(url)
    h, path = (p.hostname or "").lower(), p.path.lower()
    if h in ("linkedin.com", "www.linkedin.com"):
        return "social_post" if path.startswith(("/posts/", "/feed/update/")) else "excluded"
    if h in ("doi.org", "www.rabota.md", "rabota.md") or any(t in h for t in ("jobs.", "indeed.", "lever.co", "greenhouse.io", "ashbyhq.com", "remoteotter.")):
        return "excluded"
    if any(t in path for t in ("/jobs/", "/job/", "/careers/", "/search", "/position")):
        return "excluded"
    return "public_article"


def investigate(records: list[dict], known_urls: set[str] | None = None) -> dict:
    known = known_urls or set()
    items, rejected, seen = [], 0, set()
    for record in records:
        url = canonical_url(record.get("url", ""))
        if not url or url in seen:
            continue
        seen.add(url)
        text = " ".join(str(record.get(k) or "") for k in ("title", "excerpt", "snippet"))[:2000]
        text = re.sub(r"\s+", " ", text).strip()
        origin = source_type(url)
        if origin == "excluded" or EXCLUDE.search(text) or not (QA.search(text) and INTENT.search(text)):
            rejected += 1
            continue
        items.append({
            "id": hashlib.sha256(url.encode()).hexdigest()[:16],
            "evidence_url": url,
            "evidence_excerpt": text[:700],
            "source_type": origin,
            "potential_role": "quality_engineering_leadership" if LEAD.search(text) else "quality_engineering",
            "status": "potential_unconfirmed",
            "already_in_baseline": url in known,
            "published_at": record.get("published_at") or None,
            "company": str(record.get("company") or "")[:120],
            "contact_url": "",
            "confirmed_hidden_vacancy": False,
            "brazil_eligibility": "unverified",
            "usd_compensation": "unverified",
        })
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_input": len(records), "accepted_signals": len(items), "rejected": rejected,
        "absent_from_baseline_by_url": sum(not i["already_in_baseline"] for i in items),
        "confirmed_hidden_vacancies": 0, "items": items,
        "note": "Not present in baseline does not prove hidden or newly opened position.",
    }


def report_html(data: dict) -> str:
    esc = lambda v: html.escape(str(v), quote=True)
    cards = "".join(
        '<article><h2>' + esc(x["company"] or "Empresa não verificada") + '</h2>'
        '<p>Hidden Opportunity · Potencial — ' + esc(x["potential_role"]) + '</p>'
        '<p>' + esc(x["evidence_excerpt"]) + '</p>'
        '<a target="_blank" rel="noopener noreferrer" href="' + esc(x["evidence_url"]) + '">Ver fonte pública</a></article>'
        for x in data["items"])
    return ('<!doctype html><html lang="pt-BR"><meta charset="utf-8"><title>Hidden Opportunities Lab</title>'
            '<style>body{font:16px system-ui;max-width:960px;margin:30px auto;padding:16px}article{border:1px solid #ccc;padding:18px;margin:14px 0;border-radius:12px}</style>'
            '<h1>Hidden Opportunities Lab · Ambiente isolado</h1><p>Fontes potenciais, não vagas confirmadas.</p>'
            '<p>Sinais: ' + esc(data["accepted_signals"]) + ' · Confirmadas: 0</p>' + cards + '</html>')


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True, help="JSON list of public structured evidence")
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/hidden-opportunities-lab"))
    args = parser.parse_args()
    rows = json.loads(args.input.read_text(encoding="utf-8"))
    if not isinstance(rows, list):
        raise ValueError("Expected a JSON list")
    report = investigate(rows)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    (args.output_dir / "report.html").write_text(report_html(report), encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("total_input", "accepted_signals", "confirmed_hidden_vacancies")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
