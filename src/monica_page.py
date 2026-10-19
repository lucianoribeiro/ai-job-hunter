"""Build a public career summary from sanitized matching results (no CV data)."""
import argparse
import html
import json
from pathlib import Path

def render(data):
    entries = data.get("jobs", [])
    cards = []
    for item in entries:
        esc = lambda x: html.escape(str(x or ""), quote=True)
        url = esc(item.get("url"))
        if not url.startswith("https://"):
            continue
        score = int(item.get("score") or 0)
        reasons = "".join("<li>"+esc(s)+"</li>" for s in item.get("evidence", [])[:5]) or "<li>Sem requisito comprovado no anúncio.</li>"
        issues = "".join("<li>"+esc(s)+"</li>" for s in item.get("gaps", [])[:5])
        cards.append(f'<article class="card"><div class="top"><h2>{esc(item.get("title"))}</h2><strong>{score}/100</strong></div>'
                     f'<p>{esc(item.get("company"))} · {esc(item.get("location"))}</p>'
                     f'<p class="state">Candidatura: {esc(item.get("application_status"))}</p>'
                     f'<h3>Por que pode interessar</h3><ul>{reasons}</ul><h3>Pontos de atenção</h3>'
                     f'<ul>{issues or "<li>Sem informações adicionais.</li>"}</ul>'
                     f'<a href="{url}" target="_blank" rel="noopener noreferrer">Consultar anúncio original ↗</a></article>')
    body = "".join(cards) or '<p>Nenhuma oportunidade analisada nesta coleta. Aguardando perfil privado e vagas verificáveis.</p>'
    return """<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Oportunidades para Mônica | AI Job Hunter</title><style>
:root{color-scheme:dark;font-family:system-ui}body{background:#091522;color:#e9f5fc;margin:auto;max-width:1100px;padding:30px 18px}
a{color:#9de4fd}header{margin-bottom:30px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(290px,1fr));gap:16px}
.card{background:#102538;border:1px solid #345066;border-radius:16px;padding:18px}.top{display:flex;gap:12px;justify-content:space-between}
h2{font-size:1.15rem;margin:0}.top strong{color:#9de4fd;white-space:nowrap}.state{color:#e4c990}h3{font-size:.95rem;margin-bottom:4px}
li{margin-bottom:6px}footer{margin-top:25px;color:#a9bfd0}</style>
<header><p><a href="./">← AI Job Hunter</a></p><h1>Oportunidades de Gestão de Projetos · Mônica</h1>
<p>Avaliação inicial CV × Vaga. Verifique o anúncio oficial antes de se candidatar. Nenhum status de inscrição foi confirmado automaticamente.</p></header>
<main class="grid">""" + body + """</main><footer>Notas: notas heurísticas de aderência, não probabilidade de contratação. Anúncios sem validação não são apresentados como abertos.</footer></html>"""

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--input",type=Path,default=Path("site/monica-opportunities.json"))
    parser.add_argument("--output",type=Path,default=Path("site/monica.html"))
    a=parser.parse_args()
    data=json.loads(a.input.read_text(encoding="utf-8")) if a.input.exists() else {"jobs":[]}
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(render(data),encoding="utf-8")

if __name__=="__main__": main()
