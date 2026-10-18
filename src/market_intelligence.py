"""Evidence-based market intelligence over retained public job records."""
from __future__ import annotations

import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from src.hunter import DATA

OUTPUT = DATA / "market_insights.json"


def classify(title: str, description: str = "") -> str | None:
    title, description = title.casefold(), description.casefold()
    if re.search(r"\b(qa manager|quality assurance manager|test manager|gerente de qa|gerente de qualidade de software)\b", title):
        return "QA Manager"
    if re.search(r"\b(qa|quality assurance|quality engineer|software test|test automation|sdet|quality lead|test lead)\b", title):
        return "QA"
    if re.search(r"\b(manufacturing|manufatura|production manager|production coordinator|gerente de produção|coordenador de produção)\b", title):
        return "Manufatura"
    if re.search(r"\b(project manager|gerente de projetos|coordenador de projetos)\b", title) and re.search(r"\b(manufacturing|manufatura|industrial|fábrica|factory|produção)\b", description):
        return "Manufatura"
    return None


def summarize(history: dict, today: str | None = None, linkedin_history: dict | None = None) -> dict:
    now = datetime.fromisoformat(today).date() if today else datetime.now(timezone.utc).date()
    months = [((now.year * 12 + now.month - 1 - offset) // 12, (now.year * 12 + now.month - 1 - offset) % 12 + 1) for offset in range(23, -1, -1)]
    buckets = defaultdict(set)
    companies = defaultdict(set)
    sources = defaultdict(set)
    observed = set()
    for identity, job in history.items():
        if not isinstance(job, dict):
            continue
        category = classify(str(job.get("title") or ""), str(job.get("description") or ""))
        if not category:
            continue
        raw = str(job.get("published") or job.get("first_seen") or "")[:10]
        try:
            date = datetime.fromisoformat(raw).date()
        except ValueError:
            continue
        if date > now or (date.year, date.month) not in months:
            continue
        key = (date.year, date.month, category)
        buckets[key].add(identity)
        observed.add((date.year, date.month))
        if job.get("company"):
            companies[key].add(str(job["company"]).strip().casefold())
        if job.get("source"):
            sources[(date.year, date.month)].add(str(job["source"]))
    series = {}
    for category in ("QA", "QA Manager", "Manufatura"):
        values = [len(buckets[(year, month, category)]) for year, month in months]
        previous, current = values[-3:-2], values[-2:-1]  # complete months only
        change = None
        if len(observed) >= 3 and previous and previous[0] > 0:
            change = round((current[0] - previous[0]) / previous[0] * 100, 1)
        series[category] = {
            "monthly": values,
            "companies_last_complete_month": len(companies[(months[-2][0], months[-2][1], category)]),
            "change_last_complete_month_pct": change,
        }
    linkedin_buckets = defaultdict(set)
    linkedin_scope_buckets = defaultdict(set)
    linkedin_observed = set()
    linkedin_coverage = (linkedin_history or {}).get("_coverage") or {}
    for identity, post in (linkedin_history or {}).items():
        if not isinstance(post, dict) or post.get("area") not in ("QA", "Manufatura"):
            continue
        try:
            date = datetime.fromisoformat(str(post.get("published_at", "")).replace("Z", "+00:00")).date()
        except ValueError:
            continue
        if date > now or (date.year, date.month) not in months:
            continue
        linkedin_buckets[(date.year, date.month, post["area"])].add(identity)
        scope = post.get("market_scope") if post.get("market_scope") in ("Brasil", "Internacional", "Não identificado") else "Não identificado"
        linkedin_scope_buckets[(date.year, date.month, post["area"], scope)].add(identity)
        linkedin_observed.add((date.year, date.month))
    linkedin = {
        "source": "LinkedIn public web index (not official LinkedIn API)",
        "metric": "indexed_recruiter_posts_not_verified_vacancies",
        "observed_months": len(linkedin_observed),
        "categories": {
            category: {"monthly": [
                len(linkedin_buckets[(year, month, category)])
                if linkedin_coverage.get(f"{year:04d}-{month:02d}", {}).get(category) == "ok" or (year, month) in linkedin_observed
                else None
                for year, month in months
            ]}
            for category in ("QA", "Manufatura")
        },
        "scopes": {
            scope: {
                category: {"monthly": [
                    len(linkedin_scope_buckets[(year, month, category, scope)])
                    if linkedin_coverage.get(f"{year:04d}-{month:02d}", {}).get(category) == "ok" or (year, month) in linkedin_observed
                    else None
                    for year, month in months
                ]}
                for category in ("QA", "Manufatura")
            }
            for scope in ("Brasil", "Internacional", "Não identificado")
        },
        "coverage": {
            f"{month:02d}/{year}": {
                category: linkedin_coverage.get(f"{year:04d}-{month:02d}", {}).get(category, "unqueried")
                for category in ("QA", "Manufatura")
            }
            for year, month in months
        },
    }
    years = {year for year, month in observed}
    seasonal_ready = len(years) >= 2 and len(observed) >= 18
    return {
        "generated_at": now.isoformat(),
        "months": [f"{month:02d}/{year}" for year, month in months],
        "observed_months": len(observed),
        "seasonality_ready": seasonal_ready,
        "best_month_to_search": None,
        "source_coverage": {f"{month:02d}/{year}": len(sources[(year, month)]) for year, month in months},
        "categories": series,
        "linkedin": linkedin,
        "disclaimer": "Amostra de vagas coletadas; variações de cobertura das fontes afetam as tendências. Não representa todas as contratações.",
    }


def run() -> None:
    path = DATA / "history.json"
    history = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    DATA.mkdir(parents=True, exist_ok=True)
    linkedin_path = DATA / "linkedin_history.json"
    linkedin_history = json.loads(linkedin_path.read_text(encoding="utf-8")) if linkedin_path.exists() else {}
    OUTPUT.write_text(json.dumps(summarize(history, linkedin_history=linkedin_history), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Market intelligence written to {OUTPUT}")


if __name__ == "__main__":
    run()
