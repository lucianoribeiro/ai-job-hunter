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
    comparison = data.get("comparison", {})
    candidates = comparison.get("qa_opportunities", [])
    qa_cards = "".join(
        '<article style="border:1px solid #405a73;border-radius:10px;padding:12px;margin:10px 0">'
        '<strong>' + escape(job.get("company", "")) + '</strong> · '
        '<a target="_blank" rel="noopener noreferrer" href="' + escape(job.get("url", "")) + '">' +
        escape(job.get("title", "")) + '</a> '
        '<span style="background:#205b60;color:white;border-radius:20px;padding:3px 8px">' +
        ('Nova no radar' if job.get("status") == "not_in_baseline" else 'Já coletada') +
        '</span><p>Elegibilidade Brasil: não verificada · Local: ' + escape(job.get("location", "")) + '</p></article>'
        for job in candidates[:25]
    )
    qa_section = ('<div style="border-top:1px solid #415574;padding-top:16px">'
                  '<h3>Vagas públicas de QA encontradas pelo radar</h3><p>'
                  'Vagas QA identificadas: ' + escape(comparison.get("qa_public_openings", 0)) +
                  ' · Já coletadas: ' + escape(comparison.get("qa_already_collected", 0)) +
                  ' · Não encontradas no CSV principal: ' +
                  escape(comparison.get("qa_not_in_baseline") if comparison.get("qa_not_in_baseline") is not None else "não comparável") +
                  '</p><p>Comparação baseada em URLs normalizadas; não confirma vaga oculta nem disponibilidade para brasileiros.</p>' +
                  (qa_cards or '<p>Nenhuma vaga pública de QA encontrada nas empresas monitoradas.</p>') + '</div>')
    section = ('<section id="hidden-job-market" style="margin:20px 0;padding:22px;border:1px solid #415574;border-radius:18px;background:#152540;color:#f3f6fc">'
        '<h2>Hidden Job Market <span style="font-size:.6em;border-radius:20px;padding:5px 10px;background:#51418c;color:white">Hidden Job</span></h2>'
        '<p>Empresas com sinais públicos de contratação em engenharia, sem anúncio de QA detectado no portal consultado. '
        'Não são vagas ocultas confirmadas, nem há confirmação de elegibilidade no Brasil ou pagamento em USD.</p>'
        '<p><strong>Empresas consultadas:</strong> ' + escape(data.get("companies_checked", 0)) +
        ' · <strong>Falhas:</strong> ' + escape(data.get("companies_failed", 0)) +
        ' · <strong>Sinais:</strong> ' + escape(len(items)) + '</p>'
        + ("".join(cards) if cards else '<p>Nenhum sinal encontrado nesta coleta.</p>') + qa_section + '</section>')
    marker = '<div id="mainPanelGeneral" class="primary-panel" role="tabpanel" aria-labelledby="mainTabGeneral">'
    if marker not in source:
        raise ValueError("Public General tab marker missing; cannot publish Hidden Job section")
    source = source.replace(marker, marker + section, 1)
    page.write_text(source, encoding="utf-8")

if __name__ == "__main__":
    embed(Path("site/index.html"), Path("data/hidden_market.json"))
