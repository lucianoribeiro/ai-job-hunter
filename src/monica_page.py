"""Focused, publicly safe career opportunities page for Monica."""
import argparse
import html
import json
from pathlib import Path
from src.monica_match import norm, REGIONAL

def eligible(item, minimum=70):
    location=norm(item.get("location"))
    # Remote vacancies require explicit Brazil eligibility from the source.
    regional=any(city in location for city in REGIONAL)
    remote=("remote" in location or "remoto" in location) and any(
        word in location for word in ("brasil","brazil","worldwide","anywhere","latam","global"))
    return (regional or remote) and int(item.get("score") or 0)>=minimum and item.get("application_status")!="closed"

def render(data, minimum=70):
    esc=lambda x:html.escape(str(x if x is not None else ""),quote=True)
    rows=[item for item in data.get("jobs",[]) if isinstance(item,dict) and eligible(item,minimum)]
    rows=sorted(rows,key=lambda item:-int(item.get("score") or 0))
    cards=[]
    for j in rows:
        url=esc(j.get("url") or "")
        if not url.startswith("https://"):continue
        score=int(j.get("score") or 0)
        summary="; ".join(j.get("evidence") or []) or "Aderência identificada; requisitos precisam de confirmação."
        warnings="; ".join(j.get("gaps") or []) or "Verificar requisitos completos na fonte oficial."
        status="Candidatura indicada" if j.get("application_status")=="apply_indicated" else "A confirmar"
        cards.append(f'<article><div class="heading"><h2>{esc(j.get("title"))}</h2><strong>{score}/100</strong></div>'
                     f'<p class="meta">{esc(j.get("company"))} · {esc(j.get("location"))}</p>'
                     f'<p class="status">{status}</p><p><b>Por que é interessante:</b> {esc(summary)}</p>'
                     f'<details><summary>Requisitos a confirmar</summary><p>{esc(warnings)}</p></details>'
                     f'<p><a href="{url}" target="_blank" rel="noopener noreferrer">Ver candidatura ↗</a></p></article>')
    body="".join(cards) or "<p>Nenhuma vaga atendeu aos critérios de aderência, localização e verificação nesta coleta. Não significa ausência de oportunidades no mercado.</p>"
    return f"""<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Oportunidades para Mônica | AI Job Hunter</title>
<style>:root{{color-scheme:dark;font-family:system-ui}}body{{background:#0e1520;color:#ecf4fc;margin:auto;max-width:960px;padding:30px 18px}}
a{{color:#92ddd7}}.meta,footer{{color:#a5b6c6}}.heading{{display:flex;gap:18px;justify-content:space-between}}strong{{white-space:nowrap;color:#92ddd7}}
main{{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px}}article{{background:#1d2531;border:1px solid #394657;border-radius:14px;padding:20px}}
h2{{font-size:1.06rem;margin:0}}.status{{color:#efc778}}details{{margin-top:12px}}footer{{margin-top:24px;font-size:.85rem}}</style>
<header><p><a href="./">← AI Job Hunter</a></p><h1>Oportunidades para Mônica</h1>
<p>Gestão de Projetos · NPI · Manufatura</p><p>{len(cards)} oportunidade(s) selecionada(s) · Aderência mínima {minimum}/100</p></header>
<main>{body}</main><footer>Aderência heurística, não probabilidade de contratação. Inscrição indicada não garante disponibilidade final. Vagas encerradas são excluídas.</footer></html>"""

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--input",type=Path,default=Path("site/monica-opportunities.json"))
    parser.add_argument("--output",type=Path,default=Path("site/monica.html"))
    parser.add_argument("--min-score",type=int,default=70)
    args=parser.parse_args()
    data=json.loads(args.input.read_text(encoding="utf-8")) if args.input.exists() else {"jobs":[]}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(render(data,args.min_score),encoding="utf-8")
if __name__=="__main__":main()
