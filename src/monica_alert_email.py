"""Opt-in daily alerts. Only newly identified, verified, Brazil-eligible vacancies."""
import argparse
import hashlib
import html
import json
import os
from email.message import EmailMessage
from pathlib import Path
import smtplib

def key(job):
    return hashlib.sha256(str(job.get("url") or "").strip().lower().encode()).hexdigest()
def qualified(job):
    return (job.get("application_status")=="apply_indicated"
            and job.get("location_class") in ("regional","remote_br")
            and int(job.get("score") or 0)>=70
            and str(job.get("url") or "").startswith("https://"))
def new_jobs(jobs,seen):
    return [j for j in jobs if qualified(j) and key(j) not in seen]
def render_email(jobs):
    lines=["Olá, Mônica!","",f"Encontramos {len(jobs)} nova(s) oportunidade(s) com candidatura indicada e boa aderência ao seu perfil.",""]
    for j in jobs:
        lines += [f"{j.get('title','')} — {j.get('company','')}",
                  f"Local: {j.get('location','')} | Aderência estimada: {j.get('score',0)}/100",
                  "Competências alinhadas: " + ", ".join((j.get("matches") or [])[:4]),
                  f"Link: {j.get('url','')}", ""]
    lines+=["A indicação de candidatura não garante que a inscrição será concluída.","AI Job Hunter"]
    return "\n".join(lines)
def run(feed,state_file,send=False,mailer=None):
    jobs=json.loads(Path(feed).read_text(encoding="utf-8")).get("jobs",[])
    if Path(state_file).exists():
        seen=set(json.loads(Path(state_file).read_text(encoding="utf-8")).get("seen",[]))
        initial=False
    else:
        seen=set(); initial=True
    current={key(j) for j in jobs if qualified(j)}
    fresh=[] if initial else new_jobs(jobs,seen)
    if fresh and send:
        if mailer is None: mailer=send_smtp
        mailer(fresh)
    # Do not advance delivery state if email is not configured or delivery failed.
    if initial or send:
        Path(state_file).parent.mkdir(parents=True,exist_ok=True)
        Path(state_file).write_text(json.dumps({"seen":sorted(seen|current)})+"\n",encoding="utf-8")
    return {"eligible":len(current),"new":len(fresh),"initial":initial,"sent":len(fresh) if send else 0}
def send_smtp(jobs):
    required=["MONICA_ALERT_TO","SMTP_HOST","SMTP_PORT","SMTP_USERNAME","SMTP_PASSWORD","SMTP_FROM"]
    missing=[name for name in required if not os.getenv(name)]
    if missing:raise RuntimeError("SMTP settings missing: "+", ".join(missing))
    message=EmailMessage()
    message["From"]=os.environ["SMTP_FROM"]
    message["To"]=os.environ["MONICA_ALERT_TO"]
    message["Subject"]=f"AI Job Hunter | {len(jobs)} nova(s) oportunidade(s) para Mônica"
    message.set_content(render_email(jobs))
    with smtplib.SMTP_SSL(os.environ["SMTP_HOST"],int(os.environ["SMTP_PORT"]),timeout=20) as client:
        client.login(os.environ["SMTP_USERNAME"],os.environ["SMTP_PASSWORD"])
        client.send_message(message)
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--feed",type=Path,required=True)
    ap.add_argument("--state",type=Path,required=True)
    ap.add_argument("--send",action="store_true")
    args=ap.parse_args()
    print(run(args.feed,args.state,send=args.send))
if __name__=="__main__":main()
