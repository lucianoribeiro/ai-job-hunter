"""Half-hourly vacancy inventory and three daily email digests.

State is public job metadata only, restored by a single GitHub Actions cache.
The first successful scan is a baseline, not a flood of old listings.
"""
import argparse
import json
from pathlib import Path
from src.monica_alert_email import qualified, key, send_smtp

def update(feed, state_path, digest=False, enabled=False, mailer=None):
    jobs=json.loads(Path(feed).read_text(encoding="utf-8")).get("jobs",[])
    # Only verified, region-eligible, high-scoring adverts are considered.
    eligible={key(j):j for j in jobs if qualified(j)}
    path=Path(state_path)
    if path.exists():
        state=json.loads(path.read_text(encoding="utf-8"))
        known=set(state.get("known",[]))
        pending=dict(state.get("pending",{}))
        initial=False
    else:
        known=set(eligible)
        pending={}
        initial=True
    for ident,job in eligible.items():
        if ident not in known:
            pending[ident]={field:job.get(field) for field in
                ("url","title","company","location","location_class","score",
                 "application_status","matches")}
            known.add(ident)
    delivered=0
    if digest and enabled and pending:
        # Send only listings that are still verified in the current scan.
        current=[eligible[i] for i in pending if i in eligible]
        if current:
            (mailer or send_smtp)(current)
            delivered=len(current)
        pending.clear()
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps({"known":sorted(known),"pending":pending},
                               ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return {"eligible":len(eligible),"queued":len(pending),"sent":delivered,
            "initial":initial,"digest":digest,"enabled":enabled}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--feed",type=Path,required=True)
    ap.add_argument("--state",type=Path,required=True)
    ap.add_argument("--digest",action="store_true")
    ap.add_argument("--send",action="store_true")
    args=ap.parse_args()
    print(json.dumps(update(args.feed,args.state,args.digest,args.send),ensure_ascii=False))

if __name__=="__main__":
    main()
