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
    cards = []
    for item in items:
        evidence = "".join(
            '<li><a href="' + escape(e["url"]) + '" target="_blank" rel="noopener noreferrer">' +
            escape(e["title"]) + '</a></li>'
            for e in item.get("evidence", []) if str(e.get("url", "")).startswith("https://")
        )
        cards.append('<article style="border:1px solid #4b6181;border-radius:12px;padding:16px;background:#1a2b45;margin:12px 0">'
            '<p><strong>' + escape(item.get("company", "")) + '</strong> '
            '<span style="display:inline-block;border-radius:20px;background:#51418c;color:white;padding:4px 10px">Hidden Job · Potencial</span></p>'
            '<p>Prioridade: ' + escape(item.get("priority", "low")) + ' · Engenharia: ' +
            escape(item.get("engineering_roles", 0)) + ' · QA anunciado neste portal: ' +
            escape(item.get("qa_roles", 0)) + '</p><ul>' + evidence + '</ul></article>')
    section = ('<section id="hidden-job-market" style="margin:20px 0;padding:22px;border:1px solid #415574;border-radius:18px;background:#152540;color:#f3f6fc">'
        '<h2>Hidden Job Market <span style="font-size:.6em;border-radius:20px;padding:5px 10px;background:#51418c;color:white">Hidden Job</span></h2>'
        '<p>Empresas com sinais públicos de contratação em engenharia, sem anúncio de QA detectado no portal consultado. '
        'Não são vagas ocultas confirmadas, nem há confirmação de elegibilidade no Brasil ou pagamento em USD.</p>'
        '<p><strong>Empresas consultadas:</strong> ' + escape(data.get("companies_checked", 0)) +
        ' · <strong>Falhas:</strong> ' + escape(data.get("companies_failed", 0)) +
        ' · <strong>Sinais:</strong> ' + escape(len(items)) + '</p>'
        + ("".join(cards) if cards else '<p>Nenhum sinal encontrado nesta coleta.</p>') + '</section>')
    # Optional Agent Reach signals: separate evidence from confirmed job listings.
    reach_path = Path("data/hidden_opportunities.json")
    if reach_path.exists():
        reach = json.loads(reach_path.read_text(encoding="utf-8"))
        reach_cards = "".join(
            '<article style="padding:12px;border:1px solid #425875;border-radius:10px;margin:10px 0">'
            '<strong>Hidden Opportunity · Potencial</strong>'
            '<p>' + escape(it.get("excerpt", "")[:320]) + '</p>'
            '<a target="_blank" rel="noopener noreferrer" href="' + escape(it["url"]) + '">Evidência pública</a>'
            '<p>Fonte: Agent Reach · Brasil e remuneração não verificados</p></article>'
            for it in reach.get("items", [])[:20] if str(it.get("url", "")).startswith("https://")
        )
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
