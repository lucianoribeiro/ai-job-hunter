"""Inline Monica vacancy cards in the existing premium regional dashboard."""
from pathlib import Path
import json
import html
from src.monica_page import eligible
from src.monica_dates import publication_date, display_date

def render(data):
    esc=lambda x:html.escape(str(x if x is not None else ""),quote=True)
    items=[j for j in data.get("jobs",[]) if isinstance(j,dict) and eligible(j,50)]
    def sort(j):
        day=publication_date(j.get("published_at") or j.get("published"))
        return (day is None, -(int(day.replace("-","")) if day else 0), -int(j.get("score") or 0))
    items.sort(key=sort)
    cards=[]
    for j in items:
        url=str(j.get("url") or "")
        if not url.startswith("https://"):continue
        matched=(j.get("requirement_analysis") or {}).get("matched_requirements") or []
        skills="".join("<li>"+esc(x.get("requirement"))+"</li>" for x in matched[:4])
        if not skills: skills="<li>Requisitos ainda não comprovados no texto disponível</li>"
        status="Candidatura indicada" if j.get("application_status")=="apply_indicated" else "Inscrição a confirmar"
        location=j.get("location") or "Local não informado"
        cards.append('<article class="regional-card" style="padding:15px">'
           +'<strong>'+esc(j.get("title"))+'</strong>'
           +'<p>'+esc(j.get("company"))+' · '+esc(location)+'</p>'
           +'<p>Publicação: '+display_date(j.get("published_at") or j.get("published"))+'</p>'
           +'<p>Aderência heurística: '+esc(j.get("score"))+'/100 · '+esc(status)+'</p>'
           +'<strong>Competências alinhadas</strong><ul>'+skills+'</ul>'
           +'<a href="'+esc(url)+'" target="_blank" rel="noopener noreferrer">Ver anúncio original ↗</a></article>')
    if not cards:
        archive=Path("data/monica_linkedin_jobs.json")
        if archive.is_file():
            for j in json.loads(archive.read_text(encoding="utf-8")).get("jobs",[]):
                url=str(j.get("url") or "")
                state="Encerrada" if j.get("application_status")=="closed" else "Candidatura não verificada"
                link=('<a href="'+esc(url)+'" target="_blank" rel="noopener noreferrer">Consultar anúncio ↗</a>'
                      if url.startswith("https://") and not j.get("source_listing_only") else "Link individual pendente")
                cards.append('<article class="regional-card" style="padding:15px"><strong>'+esc(j.get("title"))+
                    '</strong><p>'+esc(j.get("company"))+' · '+esc(j.get("location"))+'</p><p>'+state+
                    ' · Data não informada</p><p>Match CV × Vaga: aguardando perfil privado.</p>'+link+'</article>')
    # Show the four reviewed public advertisements directly in the regional dashboard,
    # including when the private CV profile is not configured in GitHub Actions.
    reviewed=Path("data/monica_regional_reviewed.json")
    if reviewed.is_file():
        imported_cards=[]
        existing=set()
        for job in items:
            existing.add(str(job.get("url") or "").rstrip("/").lower())
        for job in json.loads(reviewed.read_text(encoding="utf-8")).get("jobs",[]):
            url=str(job.get("url") or "")
            if not url.startswith("https://") or url.rstrip("/").lower() in existing:
                continue
            existing.add(url.rstrip("/").lower())
            imported_cards.append('<article class="regional-card" style="padding:15px"><strong>'+
                esc(job.get("title"))+'</strong><p>'+esc(job.get("company"))+' · '+
                esc(job.get("location"))+'</p><p>Origem: '+esc(job.get("source"))+
                '</p><p><strong>Vaga importada · Região de Nova Odessa</strong></p><p>Candidatura não verificada · anúncio previamente identificado</p>'+
                '<p>Match CV × Vaga: avaliação preliminar; não é pontuação calculada nesta coleta.</p>'+
                '<a href="'+esc(url)+'" target="_blank" rel="noopener noreferrer">Consultar anúncio ↗</a></article>')
        cards=imported_cards+cards
    notice=('<p>Nenhuma oportunidade elegível foi publicada nesta execução. '
            'A lista depende das fontes disponíveis e do perfil configurado.</p>')
    return ('<section id="monica-inline" aria-labelledby="monica-inline-title" style="margin:20px 0">'
        '<h2 id="monica-inline-title">Oportunidades para Mônica</h2>'
        '<div style="display:flex;gap:12px;align-items:center;margin:12px 0">'
        '<button type="button" id="monica-bell" style="background:#2a261f;border:1px solid #b9914f;border-radius:12px;padding:8px 12px;color:#ffe1a8;cursor:pointer" aria-label="Novas vagas da Mônica">&#128276; <span id="monica-new-count" aria-live="polite">0</span> novas</button>'
        '<small id="monica-bell-hint">Novas desde a última visita neste navegador</small></div>'
        '<p><strong>Como funciona o match CV × Vaga:</strong> o agente lê um perfil profissional privado, '
        'identifica competências comprovadas no currículo e compara com os requisitos declarados '
        'em cada anúncio. A pontuação é uma estimativa heurística, não chance de contratação. '
        'Vagas encerradas são descartadas; candidaturas não verificadas permanecem sinalizadas.</p>'
        '<p>'+str(len(cards))+' vaga(s) selecionada(s) nesta coleta. '
        'Exibição da publicação mais recente primeiro quando a data é conhecida.</p>'
        '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(245px,1fr));gap:12px">'
        +("".join(cards) if cards else notice)+'</div></section>')

def main():
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--dashboard",type=Path,required=True)
    p.add_argument("--feed",type=Path,required=True)
    a=p.parse_args()
    content=a.dashboard.read_text(encoding="utf-8")
    mark="<!-- MONICA_OPPORTUNITIES_SLOT -->"
    if content.count(mark)!=1:raise ValueError("Monica inline placeholder missing or duplicated")
    data=json.loads(a.feed.read_text(encoding="utf-8"))
    a.dashboard.write_text(content.replace(mark,render(data)),encoding="utf-8")
if __name__=="__main__":main()
