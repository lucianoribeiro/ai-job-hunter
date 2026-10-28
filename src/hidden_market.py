"""Evidence-based hidden job market signals from public company ATS listings.

A signal is NOT an unadvertised vacancy. Only organizations already configured
in config.json are checked; no people or private contact data are scraped.
"""
from __future__ import annotations

import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

from src.hunter import CONFIG, DATA, fetch_json

QA = re.compile(r"\b(?:qa|quality assurance|quality engineering|software quality|sdet|software test|test automation|test engineer)\b", re.I)
ENG = re.compile(r"\b(?:software engineer|software developer|backend|back.end|front.end|full.stack|platform engineer|devops|site reliability|engineering manager|engineering director)\b", re.I)
REMOTE = re.compile(r"\\b(?:remote|worldwide|global|anywhere|brazil|brasil|latam|latin america)\\b", re.I)
LEAD = re.compile(r"\b(?:lead|manager|head|director|principal|staff)\b", re.I)


def board_jobs(board: dict) -> list[dict]:
    provider, slug = board["provider"], quote(str(board["slug"]), safe="")
    if provider == "greenhouse":
        data = fetch_json(f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs")
        return [{"title": j.get("title", ""), "url": j.get("absolute_url", ""), "location": (j.get("location") or {}).get("name", "")} for j in data.get("jobs", [])]
    if provider == "lever":
        data = fetch_json(f"https://api.lever.co/v0/postings/{slug}?mode=json")
        return [{"title": j.get("text", ""), "url": j.get("hostedUrl", ""), "location": (j.get("categories") or {}).get("location", "")} for j in data]
    if provider == "ashby":
        data = fetch_json(f"https://api.ashbyhq.com/posting-api/job-board/{slug}")
        return [{"title": j.get("title", ""), "url": j.get("jobUrl", ""), "location": j.get("location", "")} for j in data.get("jobs", [])]
    raise ValueError("Unsupported provider")


def evaluate(board: dict, jobs: list[dict]) -> dict:
    qa = [j for j in jobs if QA.search(str(j.get("title") or ""))]
    engineering = [j for j in jobs if ENG.search(str(j.get("title") or "")) and not QA.search(str(j.get("title") or ""))]
    leadership = [j for j in engineering if LEAD.search(str(j.get("title") or ""))]
    qa_leadership = [j for j in qa if LEAD.search(str(j.get("title") or ""))]
    remote_engineering = [j for j in engineering if REMOTE.search(str(j.get("location") or ""))]
    # This is a prioritization score, not a probability of an actual hidden vacancy.
    # A company's open engineering roles are hiring evidence, not proof of QA budget.
    score = min(100, 15 + min(len(engineering), 10) * 5 + min(len(leadership), 5) * 4 + min(len(remote_engineering), 5) * 3)
    if qa:
        score = min(score, 50)
    return {
        "company": str(board.get("company") or board["slug"]),
        "provider": board["provider"],
        "slug": board["slug"],
        "signal": "engineering_hiring_without_public_qa_listing" if engineering and not qa
                  else ("engineering_hiring_with_public_qa_listing" if engineering else "no_engineering_hiring_signal"),
        "confidence": "moderate" if len(engineering) >= 3 and not qa else "low",
        "score": score,
        "engineering_roles": len(engineering),
        "qa_roles": len(qa),
        "engineering_leadership_roles": len(leadership),
        "qa_leadership_roles": len(qa_leadership),
        "remote_engineering_roles": len(remote_engineering),
        "priority": "high" if score >= 70 and not qa else ("medium" if score >= 45 and not qa else "low"),
        "reason": "Evidence of engineering hiring without QA roles on this board" if engineering and not qa else "No specific evidence of an unadvertised QA role",
        "evidence": [{"title": str(j.get("title") or ""), "url": str(j.get("url") or "")}
                     for j in engineering[:5] if str(j.get("url") or "").startswith("https://")],
        "contact_channel": "official_careers_page",
        "verified_hidden_opening": False,
        "brazil_eligibility": "unverified",
        "usd_compensation": "unverified",
    }


def collect(config: dict) -> dict:
    items, errors = [], []
    for board in config.get("company_boards", []):
        if board.get("provider") not in ("greenhouse", "lever", "ashby") or not board.get("slug"):
            continue
        try:
            items.append(evaluate(board, board_jobs(board)))
        except (OSError, ValueError, KeyError, TypeError) as exc:
            errors.append({"company": board.get("company", board["slug"]), "error": str(exc)[:240]})
    return {"generated_at": datetime.now(timezone.utc).isoformat(),
            "method": "public ATS engineering-hiring proxy; not confirmed hidden vacancies",
            "companies_checked": len(items), "companies_failed": len(errors),
            "items": sorted(items, key=lambda j: (-j["score"], j["company"])), "errors": errors}


def render(report: dict) -> str:
    esc = lambda v: html.escape(str(v), quote=True)
    cards = []
    for item in report["items"]:
        links = "".join(
            '<li><a target="_blank" rel="noopener noreferrer" href="' + esc(e["url"]) + '">' +
            esc(e["title"]) + '</a></li>' for e in item["evidence"]
        )
        cards.append('<article><h2>' + esc(item["company"]) + '</h2><p><strong>Sinal: ' +
                     esc(item["score"]) + '/100</strong> · Vagas engenharia: ' +
                     esc(item["engineering_roles"]) + ' · QA anunciadas: ' +
                     esc(item["qa_roles"]) + ' · Prioridade: ' + esc(item["priority"]) + '</p><p>' +
                     ('Engenharia contratando sem vaga QA encontrada neste ATS.' if
                      item["signal"] == "engineering_hiring_without_public_qa_listing" else
                      'Sem evidência específica de vaga QA oculta.') +
                     ' Elegibilidade Brasil e remuneração não verificadas.</p><ul>' + links +
                     '</ul></article>')
    return ('<!doctype html><html lang="pt-BR"><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            '<title>Hidden Job Market · AI Job Hunter</title><style>'
            'body{font:16px system-ui;margin:0 auto;max-width:1000px;padding:32px;color:#18243b;background:#f6f8fc}'
            'article{background:white;border:1px solid #ddd;border-radius:14px;padding:18px;margin:16px 0}'
            'a{color:#2157cc}p{line-height:1.6}</style>'
            '<h1>Hidden Job Market Intelligence</h1>'
            '<p>Radar experimental de sinais públicos de contratação. <strong>Não são vagas ocultas confirmadas.</strong> '
            'Um sinal não comprova intenção de abrir vaga de QA; confirme com a empresa. '
            'Não coletamos contatos pessoais nem enviamos mensagens.</p>'
            '<p>Empresas consultadas: ' + esc(report["companies_checked"]) +
            ' · Falhas: ' + esc(report["companies_failed"]) + '</p>' +
            "".join(cards) + '</html>')


def main() -> None:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    report = collect(config)
    DATA.mkdir(exist_ok=True)
    (DATA / "hidden_market.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    (DATA / "hidden_market.html").write_text(render(report), encoding="utf-8")
    print(f"Hidden market: {report['companies_checked']} companies checked, {report['companies_failed']} failed")


if __name__ == "__main__":
    main()
