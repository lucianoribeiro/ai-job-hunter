"""Retain public LinkedIn-indexed recruiter discoveries across daily runs.

These are indexed public posts, not verified LinkedIn job listings.
"""
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from src.hunter import DATA

OUTPUT = DATA / "linkedin_history.json"

def retain(existing, feed):
    records = dict(existing)
    for item in feed.get("items", []):
        if not isinstance(item, dict) or item.get("area") not in ("QA", "Manufatura"):
            continue
        url = str(item.get("url") or "")
        title = str(item.get("title") or "").strip()
        published = str(item.get("published_at") or "")
        if not url.startswith("https://") or not title or not published:
            continue
        try:
            datetime.fromisoformat(published.replace("Z", "+00:00"))
        except ValueError:
            continue
        identity = hashlib.sha256(url.encode("utf-8")).hexdigest()[:24]
        if identity not in records:
            records[identity] = {
                "title": title, "url": url, "published_at": published,
                "area": item["area"], "source": "LinkedIn public web index",
                "evidence": "indexed_recruiter_post", "first_seen": feed.get("date_utc"),
                "last_seen": feed.get("date_utc"),
                "post_origin": item.get("post_origin", "Não verificada"),
            }
        else:
            records[identity]["last_seen"] = feed.get("date_utc")
            if item.get("post_origin") in ("Empresa", "Recrutador"):
                records[identity]["post_origin"] = item["post_origin"]
    return records

def run():
    feed_path = DATA / "recruiter_monitor.json"
    feed = json.loads(feed_path.read_text(encoding="utf-8")) if feed_path.exists() else {}
    old = json.loads(OUTPUT.read_text(encoding="utf-8")) if OUTPUT.exists() else {}
    records = retain(old, feed)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Retained {len(records)} indexed recruiter posts")

if __name__ == "__main__":
    run()
