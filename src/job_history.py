"""Merge collected public job rows into a deduplicated repository history."""
from __future__ import annotations
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from src.hunter import DATA

OUTPUT = DATA / "history.json"

def retain(existing: dict, rows: list[dict], day: str) -> dict:
    records = dict(existing)
    for row in rows:
        url = str(row.get("url") or "").strip()
        title = str(row.get("title") or "").strip()
        if not url.startswith("https://") or not title:
            continue
        key = hashlib.sha256(url.split("#", 1)[0].encode()).hexdigest()[:24]
        old = records.get(key, {})
        if not isinstance(old, dict):
            old = {}
        records[key] = {
            **old,
            "title": title,
            "url": url,
            "company": str(row.get("company") or old.get("company") or ""),
            "source": str(row.get("source") or old.get("source") or ""),
            "published": str(row.get("published") or old.get("published") or ""),
            "first_seen": old.get("first_seen") or day,
            "last_seen": day,
        }
    return records

def run() -> None:
    day = datetime.now(timezone.utc).date().isoformat()
    csv_path = DATA / "jobs.csv"
    rows = list(csv.DictReader(csv_path.open(encoding="utf-8", newline=""))) if csv_path.exists() else []
    old = json.loads(OUTPUT.read_text(encoding="utf-8")) if OUTPUT.exists() else {}
    updated = retain(old, rows, day)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(updated, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Stored {len(updated)} historical vacancies (+{len(updated)-len(old)} new)")

if __name__ == "__main__":
    run()
