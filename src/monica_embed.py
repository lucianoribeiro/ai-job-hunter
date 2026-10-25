"""Inline Monica vacancy cards in the existing premium regional dashboard."""
from pathlib import Path
import json
import html
import re
from datetime import datetime
from zoneinfo import ZoneInfo
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
    priority_count=0
    for j in items:
        url=str(j.get("url") or "")
        if not url.startswith("https://"):continue
        matched=(j.get("requirement_analysis") or {}).get("matched_requirements") or []
        skills="".join("<li>"+esc(x.get("requirement"))+"</li>" for x in matched[:4])
        if not skills: skills="<li>Requisitos ainda não comprovados no texto disponível</li>"
        status="Candidatura indicada" if j.get("application_status")=="apply_indicated" else "Inscrição a confirmar"
        location=j.get("location") or "Local não informado"
        score=j.get('score')
        if isinstance(score,(int,float)) and score>=80: priority_count+=1
        cards.append('<article class="regional-card" style="padding:15px">'
           +'<strong>'+esc(j.get("title"))+'</strong>'
           +'<p>'+esc(j.get("company"))+' · '+esc(location)+'</p>'
           +'<p>Publicação: '+display_date(j.get("published_at") or j.get("published"))+'</p>'
           +'<p><strong>Aderência calculada: '+esc(j.get("score"))+'/100</strong> · '+esc(status)+'</p>'
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
                    ' · Data não informada</p><p><strong>Aderência: a calcular</strong> · aguardando configuração do perfil privado.</p>'+link+'</article>')
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
            preliminary=job.get('preliminary_match_score')
            if isinstance(preliminary,(int,float)) and preliminary>=80: priority_count+=1
            imported_cards.append('<article class="regional-card" style="padding:15px"><strong>'+
                esc(job.get("title"))+'</strong><p>'+esc(job.get("company"))+' · '+
                esc(job.get("location"))+'</p><p>Origem: '+esc(job.get("source"))+
                '</p><p><strong>Vaga importada · Região de Nova Odessa</strong></p><p>Candidatura não verificada · anúncio previamente identificado</p>'+
                '<p style="font-size:15px;color:#e8bd78"><strong>Aderência: '+esc(preliminary)+'/100</strong></p><p>Estimativa preliminar da análise do currículo; ainda não recalculada automaticamente.</p>'+
                '<a href="'+esc(url)+'" target="_blank" rel="noopener noreferrer">Consultar anúncio ↗</a></article>')
        cards=imported_cards+cards
    # Render current public regional discoveries even when a private matching profile
    # is not configured. These are unscored leads, never CV-matched opportunities.
    live_feed = Path("data/monica_regional_sp.json")
    if live_feed.is_file():
        existing_urls = {str(j.get("url") or "").rstrip("/").lower() for j in items}
        for archive_path in (Path("data/monica_linkedin_jobs.json"),
                             Path("data/monica_regional_reviewed.json")):
            if archive_path.is_file():
                for j in json.loads(archive_path.read_text(encoding="utf-8")).get("jobs", []):
                    existing_urls.add(str(j.get("url") or "").rstrip("/").lower())
        fresh_cards = []
        for job in json.loads(live_feed.read_text(encoding="utf-8")).get("jobs", []):
            if not isinstance(job, dict) or job.get("application_status") == "closed" or job.get("source_listing_only"):
                continue
            url = str(job.get("url") or "")
            identity = url.rstrip("/").lower()
            if not url.startswith("https://") or identity in existing_urls:
                continue
            existing_urls.add(identity)
            fresh_cards.append('<article class="regional-card" style="padding:15px"><strong>'+
                esc(job.get("title") or "Cargo não informado")+'</strong><p>'+
                esc(job.get("company") or "Empresa não informada")+' · '+
                esc(job.get("location") or "Local não informado")+'</p><p>Origem: '+
                esc(job.get("source") or "Fonte pública")+'</p><p><strong>Vaga coletada automaticamente</strong></p>'+
                '<p>Candidatura não verificada · Aderência: a calcular (perfil privado indisponível ou análise pendente)</p>'+
                '<a href="'+esc(url)+'" target="_blank" rel="noopener noreferrer">Consultar anúncio ↗</a></article>')
        cards += fresh_cards
    # Sort the complete mixed catalog by the actual advertisement publication date.
    # Collection/import timestamps must never be substituted for publication dates.
    publication_by_url = {}
    first_seen_by_url = {}
    stale_urls = set()
    sources = [items]
    for source_path in (Path("data/monica_linkedin_jobs.json"),
                        Path("data/monica_regional_reviewed.json"),
                        Path("data/monica_regional_sp.json")):
        if source_path.is_file():
            sources.append(json.loads(source_path.read_text(encoding="utf-8")).get("jobs", []))
    for source in sources:
        for job in source:
            if not isinstance(job, dict):
                continue
            identity = str(job.get("url") or "").rstrip("/").lower()
            first_seen = str(job.get("first_seen_at") or "")
            if identity and first_seen and (identity not in first_seen_by_url or first_seen < first_seen_by_url[identity]):
                first_seen_by_url[identity] = first_seen
            if identity and job.get("not_seen_in_latest_collection"):
                stale_urls.add(identity)
            published = publication_date(job.get("published_at") or job.get("published"))
            if identity and published and (identity not in publication_by_url or published > publication_by_url[identity]):
                publication_by_url[identity] = published

    def card_publication(card):
        links = re.findall(r'href="([^"]+)"', card)
        for link in links:
            identity = html.unescape(link).rstrip("/").lower()
            if identity in publication_by_url:
                return publication_by_url[identity]
        return None

    dated_cards = []
    for card in cards:
        published = card_publication(card)
        links = re.findall(r'href="([^"]+)"', card)
        identity = html.unescape(links[-1]).rstrip("/").lower() if links else ""
        first_seen = first_seen_by_url.get(identity)
        if first_seen:
            try:
                dt = datetime.fromisoformat(first_seen.replace("Z", "+00:00"))
                day_label = dt.astimezone(ZoneInfo("America/Sao_Paulo")).strftime("%d/%m/%Y às %Hh%M") if dt.tzinfo else dt.strftime("%d/%m/%Y")
            except ValueError:
                day_label = "Data não informada"
            card = card.replace("</article>", '<p class="meta">Encontrada em: '+esc(day_label)+'</p></article>')
        if identity in stale_urls:
            card = card.replace("</article>", '<p class="meta">Não identificada na última coleta · disponibilidade pendente de confirmação</p></article>')
        if "Publicação:" not in card and "Publicado em:" not in card:
            label = display_date(published) if published else "Data não informada"
            card = card.replace("</article>",
                                '<p class="meta">Publicado em: ' + esc(label) + '</p></article>')
        dated_cards.append((first_seen, published, card))
    dated_cards.sort(key=lambda entry: (entry[0] or "", entry[1] or ""), reverse=True)
    cards = [card for _, _, card in dated_cards]
    # Show the timestamp of the real regional collection, never the page build time.
    collection_label = "Não disponível"
    if live_feed.is_file():
        try:
            raw = json.loads(live_feed.read_text(encoding="utf-8")).get("collected_at")
            if raw:
                instant = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
                if instant.tzinfo is not None:
                    local = instant.astimezone(ZoneInfo("America/Sao_Paulo"))
                    collection_label = local.strftime("%d/%m/%Y às %Hh%M")
        except (ValueError, TypeError, OSError):
            pass
    collection_card = ('<div id="monica-last-collection" style="background:#203040;'
        'border:1px solid #496078;border-radius:12px;padding:12px 16px;margin:12px 0;'
        'max-width:360px"><small>Última coleta regional</small><p style="margin:6px 0;'
        'font-weight:700">'+esc(collection_label)+'</p><small>Horário de Brasília · '
        'Vagas públicas; candidatura e aderência podem estar pendentes de verificação</small></div>')
    # Count the exact HTML cards built, rather than feed records.
    rendered_count=sum(card.count('<article class="regional-card"') for card in cards)
    if rendered_count != len(cards):
        raise ValueError("Monica card total differs from generated HTML")
    notice=('<p>Nenhuma oportunidade elegível foi publicada nesta execução. '
            'A lista depende das fontes disponíveis e do perfil configurado.</p>')
    return ('<section id="monica-inline" aria-labelledby="monica-inline-title" style="margin:20px 0">'
        '<h2 id="monica-inline-title">Oportunidades para Mônica</h2>'
        +collection_card+
        '<div style="display:flex;gap:12px;align-items:center;margin:12px 0">'
        '<button type="button" id="monica-bell" style="background:#2a261f;border:1px solid #b9914f;border-radius:12px;padding:8px 12px;color:#ffe1a8;cursor:pointer" aria-label="Novas vagas da Mônica">&#128276; <span id="monica-new-count" aria-live="polite">0</span> novas</button>'
        '<small id="monica-bell-hint">Novas desde a última visita neste navegador</small></div>'
        '<p><strong>Como funciona o match CV × Vaga:</strong> o agente lê um perfil profissional privado, '
        'identifica competências comprovadas no currículo e compara com os requisitos declarados '
        'em cada anúncio. A pontuação é uma estimativa heurística, não chance de contratação. '
        'Vagas encerradas são descartadas; candidaturas não verificadas permanecem sinalizadas.</p>'
        '<div role="status" id="monica-priority-alert" style="border:1px solid #b9914f;border-radius:10px;padding:12px;margin:12px 0"><strong>Prioridade para Mônica: '+str(priority_count)+' oportunidades com aderência estimada de pelo menos 80/100.</strong><p>Essas vagas merecem ser analisadas primeiro porque apresentam maior compatibilidade com a experiência profissional dela. As notas preliminares vêm de uma revisão manual. O envio automático por e-mail ocorre apenas para vagas novas, com candidatura verificável e nota calculada pelo agente.</p></div>'
        '<p><strong id="monica-total-cards">'+str(rendered_count)+'</strong> cartão(ões) de vagas disponível(is) nesta página. '
        'Ordenação pela primeira identificação da vaga; anúncios sem histórico podem aparecer depois.</p>'
        '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(245px,1fr));gap:12px">'
        +("".join(cards) if cards else notice)+'</div>'
        '<p id="monica-end-of-list" style="padding:14px 0;color:#bbc3cc">Fim da lista · '+str(rendered_count)+' cartões exibidos.</p></section>')

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
