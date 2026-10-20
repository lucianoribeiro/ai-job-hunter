# Anúncios públicos do LinkedIn — entrada para análise

O agente aceita URLs e metadados de anúncios **já obtidos legitimamente** em um JSON local. Não faz login, bypass de bloqueio nem scraping autenticado do LinkedIn. Não afirmar que a candidatura está aberta sem validação independente.

Exemplo de `data/monica_linkedin_jobs.json`:

```json
{
  "jobs": [
    {
      "title": "Coordenador(a) de Projetos NPI",
      "company": "Empresa do anúncio",
      "location": "Campinas, SP",
      "url": "https://www.linkedin.com/jobs/view/ID_REAL",
      "source": "LinkedIn público",
      "description": "Descrição obtida do anúncio público"
    }
  ]
}
```

Não adicione o exemplo como se fosse vaga real. Troque pelos dados de cada anúncio de verdade. Se o anúncio não divulgar cidade, deixe `location` vazia; não use a sede da empresa como local da vaga.

Para combinar fontes atuais e LinkedIn no Ubuntu:

```bash
python3 -m src.monica_pipeline --cv private/profiles/monica/profile.pdf \
  --projects data/project_jobs_poc.json \
  --extra-jobs data/monica_linkedin_jobs.json \
  --enrich-links --check-links --output site/monica-opportunities.json
python3 -m src.monica_page --input site/monica-opportunities.json --output site/monica.html
```

As páginas LinkedIn não são validadas por `--check-links`; o status permanece não verificado. Para extrair dados de novos links em escala é preciso um fluxo de descoberta pública e fontes que permitam o acesso, sem contornar restrições.
