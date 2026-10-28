"""Publish public Hidden Job Market signals inside the actual GitHub Pages dashboard."""
import html
import json
from pathlib import Path

def embed(page: Path, report: Path) -> None:
    source = page.read_text(encoding="utf-8")
    if 'id="hidden-job-market"' in source:
        return
    data = json.loads(report.read_text(encoding="utf-8"))
    items = [i for i in data.get("items", []) if i.get("signal") == "engineering_hiring_without_public_qa_listing"]
    escape = lambda value: html.escape(str(value), quote=True)
    # Preserve the legacy section identifier but stop presenting unrelated engineering
    # openings (GitLab/Ramp) as new QA opportunities.
    section = ('<section id="hidden-job-market" style="margin:20px 0;padding:22px;border:1px solid #415574;border-radius:18px;background:#152540;color:#f3f6fc">'
        '<h2>Hidden Opportunities · Quality Engineering</h2>'
        '<p>Somente evidências potenciais de contratação em QA são exibidas abaixo. '
        'Contratações gerais de desenvolvedores não são vagas ocultas de QA.</p>'
        '<p>O radar geral consultou ' + escape(data.get("companies_checked", 0)) +
        ' empresas; esses sinais não contam como vagas novas de QA.</p></section>')
    # Optional Agent Reach signals: separate evidence from confirmed job listings.
    reach_path = Path("data/hidden_opportunities.json")
    if reach_path.exists():
        reach = json.loads(reach_path.read_text(encoding="utf-8"))
        def card(it: dict) -> str:
            url = str(it.get("url") or "")
            if not url.startswith("https://"):
                return ""
            excerpt = str(it.get("excerpt") or "").strip()
            title = str(it.get("title") or excerpt.split(" # ")[0])[:150]
            # An advertised job is accessible but not a hidden opportunity.
            advertised = any(term in excerpt.lower() for term in (
                "contract qa lead:", "salary:", "£ / year", "at a glance - tasks",
                "apply now", "apply here", "applications are open"))
            kind = "Vaga pública identificada · verificar" if advertised else "Hidden Opportunity · Potencial — não confirmado"
            detail = ("Esta publicação parece descrever uma vaga já anunciada, não uma oportunidade oculta."
                      if advertised else
                      "A publicação não confirma a existência de uma vaga oculta.")
            return (
                '<article style="padding:16px;border:1px solid #425875;border-radius:10px;margin:10px 0">'
                '<strong>' + escape(title or "Publicação sobre QA") + '</strong>'
                '<p>' + escape(kind) + '</p>'
                '<p>' + escape(excerpt[:450]) + '</p>'
                '<p>' + escape(detail) + '</p>'
                '<p><a href="' + escape(url) + '" target="_blank" rel="noopener noreferrer" '
                'style="display:inline-block;background:#287c75;color:white;padding:10px 14px;border-radius:8px;'
                'text-decoration:none;font-weight:700">Abrir publicação original ↗</a></p>'
                '<p style="overflow-wrap:anywhere;font-size:.85em">Endereço: '
                '<a target="_blank" rel="noopener noreferrer" href="' + escape(url) + '">' + escape(url) + '</a></p>'
                '<p>Elegibilidade no Brasil, remuneração e disponibilidade: não verificadas.</p></article>')
        reach_cards = "".join(card(it) for it in reach.get("items", [])[:20])
        reach_section = (
            '<div id="hidden-opportunities-agent-reach" style="border-top:1px solid #425875;padding-top:16px;margin-top:16px">'
            '<h3>Hidden Opportunities · Agent Reach (experimental)</h3>'
            '<p>Publicações sobre possíveis necessidades de QA, não vagas confirmadas. '
            'URLs não encontradas no CSV não comprovam oportunidades inéditas.</p>'
            '<p>Registros examinados: ' + escape(reach.get("records_examined", 0))
            + ' · Sinais potenciais: ' + escape(reach.get("signals", 0))
            + ' · Coleta: ' + escape(reach.get("collector_status", "desconhecido")) + '</p>'
            + (reach_cards or '<p>Nenhum sinal qualificado nesta coleta.</p>') + '</div>')
        section = section.replace('</section>', reach_section + '</section>', 1)
    marker = '<div id="mainPanelGeneral" class="primary-panel" role="tabpanel" aria-labelledby="mainTabGeneral">'
    if marker not in source:
        raise ValueError("Public General tab marker missing; cannot publish Hidden Job section")
    source = source.replace(marker, marker + section, 1)
    page.write_text(source, encoding="utf-8")

if __name__ == "__main__":
    embed(Path("site/index.html"), Path("data/hidden_market.json"))
