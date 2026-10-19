# AI Career Hunter — operação Local First

O CV permanece no seu Ubuntu. **Não envie o PDF para o GitHub.** O repositório e o GitHub Pages são públicos.

## Preparação (Ubuntu)

```bash
git clone https://github.com/lucianoribeiro/ai-job-hunter.git
cd ai-job-hunter
git checkout feature/monica-career-agent
python3 -m venv .venv
source .venv/bin/activate
pip install pypdf python-docx
mkdir -p private/profiles/monica
chmod 700 private private/profiles private/profiles/monica
# Copie manualmente o PDF para private/profiles/monica/curriculum.pdf
chmod 600 private/profiles/monica/curriculum.pdf
```

## Teste sem publicar o CV

```bash
python -m unittest discover -s tests -v
python -m src.project_jobs_poc --config config/project_boards.example.json --output data/project_jobs_poc.json
python -m src.monica_pipeline --cv private/profiles/monica/curriculum.pdf --projects data/project_jobs_poc.json --check-links --output site/monica-opportunities.json
python -m src.monica_page --input site/monica-opportunities.json --output site/monica.html
```

Abra `site/monica.html` localmente para revisar as análises. A extração aceita PDF com texto selecionável, DOCX e TXT. PDFs escaneados sem texto não são suportados.

## Limitações e privacidade

- Somente competências genéricas extraídas do CV são usadas. Nome, contatos, texto do documento e dados pessoais não são exportados intencionalmente.
- O ranking atual é **heurístico**, não um modelo de linguagem analisando semanticamente o conteúdo inteiro.
- `--check-links` consulta apenas ATS públicos permitidos (Greenhouse, Lever, Ashby, SmartRecruiters). Outros links permanecem *não verificados*.
- Página com indicação de botão Apply não garante candidatura ativa ou inscrição concluída. Links bloqueados também permanecem não verificados.
- Verifique `site/monica-opportunities.json` e `site/monica.html` antes de compartilhar: títulos e descrições podem ter informações inseridas pelo anunciante.
- **Nenhuma publicação automática do arquivo local ocorre nesta fase.** GitHub Actions não tem acesso ao Ubuntu; a integração de publicação requer um canal autenticado só para resultados sanitizados, a ser configurado.
- A execução automatizada local pode ser agendada posteriormente com cron/systemd enquanto o computador estiver ligado.
