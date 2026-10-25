"""Isolated Sao Paulo regional discovery filter over existing public job feeds.

No scraping of arbitrary sites. Unknown locations remain in review, never
claimed to be in Sao Paulo. Existing QA pipeline is untouched.
"""
import argparse
from datetime import datetime, timezone
import json
import re
import unicodedata
from pathlib import Path
from src.monica_pipeline import collect

PRIORITY_1=("nova odessa","americana","sumare","santa barbara d oeste")
PRIORITY_2=("campinas","hortolandia","paulinia","jaguariuna","limeira","indaiatuba")
SP_CITIES=PRIORITY_1+PRIORITY_2+("sao paulo","piracicaba","valinhos","vinhedo","itu","jundiai")
ROLE=re.compile(r"\b(projetos?|projects?|project manager|program manager|pmo|npi|new product introduction)\b")
MANUFACTURING=re.compile(r"\b(manufatura|manufacturing|industrial|industria)\b")
REJECT=re.compile(r"\b(software developer|desenvolvedor|engenheiro de software|coordenador de producao)\b")
OTHER_STATES=re.compile(r"\b(rj|mg|pr|sc|rs|ba|pe|df|go|es|ce|parana|rio de janeiro|minas gerais)\b")

def norm(value):
    text=unicodedata.normalize("NFKD",str(value or "").lower())
    return "".join(c for c in text if not unicodedata.combining(c)).replace("’","'").replace("'"," ")

def regional_scope(job):
    title=norm(job.get("title"))
    loc=norm(job.get("location"))
    desc=norm(job.get("description"))
    if REJECT.search(title) or not (ROLE.search(title) or
            (MANUFACTURING.search(title) and re.search(r"\b(gerente|coordenador|especialista)\b",title))):
        return None
    remote=bool(re.search(r"\b(remoto|remote|home office)\b",loc))
    if remote and re.search(r"\b(brasil|brazil|sao paulo| sp\b)",loc):
        return 3
    for level,cities in ((1,PRIORITY_1),(2,PRIORITY_2),(3,SP_CITIES)):
        if any(re.search(r"(?<!\w)"+re.escape(city)+r"(?!\w)",loc) for city in cities):
            return level
    if OTHER_STATES.search(loc):return None
    if re.search(r"\b(sp|estado de sao paulo)\b",loc):return 3
    return None

def discover(paths,max_per_source=300):
    found={}
    stats={}
    for source in paths:
        try:jobs=collect(source)[:max_per_source]
        except (OSError,ValueError,TypeError,KeyError):
            stats[str(source)]={"status":"failed","input":0,"selected":0}
            continue
        count=0
        for job in jobs:
            priority=regional_scope(job)
            url=str(job.get("url") or "")
            if priority is None or not url.startswith("https://"):continue
            count+=1
            if url not in found or priority < found[url]["regional_priority"]:
                found[url]={**job,"regional_priority":priority,
                            "discovery_agent":"monica_regional_sp"}
        stats[str(source)]={"status":"ok","input":len(jobs),"selected":count}
    return sorted(found.values(),key=lambda j:(j["regional_priority"],j.get("title",""))),stats

def reconcile(current, previous, collected_at):
    """Retain earlier verified leads; a missing feed row is not proof of closure."""
    known = {str(j.get("url") or "").rstrip("/").lower(): j
             for j in previous if isinstance(j, dict) and j.get("url")}
    merged = {}
    for job in current:
        key = str(job.get("url") or "").rstrip("/").lower()
        older = known.get(key, {})
        if job.get("application_status") == "closed":
            continue
        merged[key] = {**older, **job,
                       "first_seen_at": older.get("first_seen_at") or collected_at,
                       "last_seen_at": collected_at,
                       "not_seen_in_latest_collection": False}
    for key, old in known.items():
        if key not in merged and old.get("application_status") != "closed":
            merged[key] = {**old, "not_seen_in_latest_collection": True}
    return sorted(merged.values(),
                  key=lambda j: (j.get("first_seen_at") is None,
                                 str(j.get("first_seen_at") or "")[:25]),
                  reverse=False)


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--sources",nargs="+",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--limit",type=int,default=300)
    args=p.parse_args()
    if not 1<=args.limit<=300:raise SystemExit("Limit must be 1-300")
    jobs,stats=discover(args.sources,args.limit)
    collected_at=datetime.now(timezone.utc).isoformat()
    historical=Path("data/monica_regional_history.json")
    try:
        previous=json.loads(historical.read_text(encoding="utf-8")).get("jobs",[]) if historical.exists() else []
    except (OSError,ValueError,TypeError):
        previous=[]
    jobs=reconcile(jobs,previous,collected_at)
    jobs.sort(key=lambda j: j.get("first_seen_at") or "",reverse=True)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps({"collected_at":collected_at,"jobs":jobs,"sources":stats},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("Regional SP:",len(jobs),"from",len(stats),"public feeds")

if __name__=="__main__":main()
