"""Offline, read-only results page for project jobs POC."""
from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from urllib.parse import urlsplit


def esc(value: object) -> str:
    return html.escape(str(value if value is not None else ""), quote=True)


def link(url: object) -> str:
    value = str(url or "")
    parsed = urlsplit(value)
    if parsed.scheme != "https" or not parsed.netloc:
        return "#"
    return value


def render(report: dict) -> str:
    jobs = report.get("jobs") or []
    rows = []
    for job in jobs:
        url = link(job.get("url"))
        rows.append(
            "<tr><td><a target='_blank' rel='noopener noreferrer' href='" + esc(url) + "'>" +
            esc(job.get("title")) + "</a></td><td>" + esc(job.get("company")) +
            "</td><td>" + esc(job.get("location")) + "</td><td>" + esc(job.get("source")) +
            "</td><td>" + esc(job.get("remote_evidence", "unknown")) + "</td></tr>"
        )
    metrics = report.get("boards") or {}
    fetched = sum(int(v.get("fetched", 0)) for v in metrics.values())
    board_lines = "".join("<li>" + esc(k) + " — " + esc(v.get("fetched", 0)) +
                          " consultadas, " + esc(v.get("matched", 0)) + " encontradas</li>"
                          for k, v in metrics.items())
    errors = "".join("<li>" + esc(e.get("board")) + " (" + esc(e.get("error")) + ")</li>"
                     for e in report.get("errors", []))
    return """<!DOCTYPE html><html lang='pt-BR'><head><meta charset='utf-8'>
<meta name='viewport' content='width=device-width,initial-scale=1'>
<title>Project Jobs — validação</title><style>
:root{font-family:system-ui,Arial,sans-serif;color:#19243a;background:#f4f6fa}
body{max-width:1200px;margin:36px auto;padding:0 20px}
header{padding:26px;background:#172340;color:white;border-radius:16px}
h1{margin:0 0 6px}.muted{opacity:.8}section{background:white;padding:22px;
margin-top:18px;border-radius:16px;box-shadow:0 3px 15px #19243a0a}
.metrics{display:flex;flex-wrap:wrap;gap:14px}
.metric{background:#e9eef8;border-radius:12px;padding:14px 22px}
.metric strong{display:block;font-size:27px}
table{border-collapse:collapse;width:100%;min-width:750px}
th,td{text-align:left;padding:12px;border-bottom:1px solid #e4e8ef}
th{background:#f5f7fb}a{color:#1757b8}.scroll{overflow-x:auto}
small{color:#677389}</style></head><body>
<header><h1>Vagas de Gerência e Coordenação de Projetos</h1>
<div class='muted'>Prova de conceito • somente leitura • origem das vagas preservada</div></header>
<section><div class='metrics'><div class='metric'>Vagas únicas<strong>""" + str(len(jobs)) + """</strong></div>
<div class='metric'>Anúncios consultados<strong>""" + str(fetched) + """</strong></div>
<div class='metric'>Fontes consultadas<strong>""" + str(len(metrics)) + """</strong></div></div>
<p><small>Vagas não foram verificadas individualmente. Remoto não implica elegibilidade no Brasil.
Datas ausentes não são inferidas. Verifique a vaga no site da empresa antes de candidatar-se.</small></p></section>
<section><h2>Oportunidades</h2><div class='scroll'><table>
<thead><tr><th>Cargo</th><th>Empresa</th><th>Localização</th><th>Origem</th><th>Evidência remoto</th></tr></thead>
<tbody>""" + ("".join(rows) or "<tr><td colspan='5'>Nenhuma vaga encontrada nesta execução</td></tr>") + """</tbody></table></div></section>
<section><h2>Cobertura por fonte</h2><ul>""" + (board_lines or "<li>Nenhuma fonte respondeu</li>") + """</ul>
<h2>Erros</h2><ul>""" + (errors or "<li>Nenhum erro informado</li>") + """</ul>
<p><small>Gerado: """ + esc(report.get("generated_at")) + """</small></p></section></body></html>"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path("data/project_jobs_poc.json"))
    parser.add_argument("--output", type=Path, default=Path("data/project_jobs_poc.html"))
    args = parser.parse_args()
    report = json.loads(args.input.read_text(encoding="utf-8"))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render(report), encoding="utf-8")
    print(f"HTML report created: {args.output}")


if __name__ == "__main__":
    main()
