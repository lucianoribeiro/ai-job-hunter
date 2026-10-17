# AI Career Studio — estado e uso seguro

Quatro tarefas LLM opt-in no módulo `src.ai_career_studio`:

- `fit`: compatibilidade CV × vaga, evidências, lacunas e restrição geográfica.
- `cv`: versão profissional e compatível com ATS, sem criar experiências fictícias.
- `application`: rascunho de carta e mensagem, sem enviar candidaturas.
- `career`: sugestões de desenvolvimento e preparação para entrevistas.

## Execução local, sem armazenar CV no repositório

Use arquivos de texto UTF-8 **fora do diretório git**. Nunca envie seus documentos pessoais para este repositório público. Não use GitHub Actions público para processar CVs privados.

```bash
export OPENAI_API_KEY="configure-em-ambiente-privado"
python -m src.ai_career_studio fit --profile /caminho/seguro/meu-perfil.txt --job /caminho/seguro/vaga.txt
python -m src.ai_career_studio cv --profile /caminho/seguro/meu-perfil.txt
python -m src.ai_career_studio application --profile /caminho/seguro/meu-perfil.txt --job /caminho/seguro/vaga.txt
python -m src.ai_career_studio career --profile /caminho/seguro/meu-perfil.txt --job /caminho/seguro/vaga.txt
```

O resultado é emitido no terminal e deve ser revisado antes de uso. A API do provedor pode ter custo mesmo em contas com assinatura do ChatGPT. O componente é opcional: sem chave, nenhuma chamada de IA é feita. Os testes automatizados utilizam respostas falsas **somente na suíte de testes**, nunca como resultado de vagas.

## Não confundir módulo com plataforma em produção

Este MVP implementa a lógica dos quatro recursos, mas **não é ainda uma interface web com upload de PDF, DOCX ou export do LinkedIn**, nem conta com usuários, banco privado, cobrança ou backend hospedado. É necessário implementar autenticação, isolamento por usuário, retenção/exclusão, rate limiting, gestão de custos e consentimento antes de disponibilizar dados pessoais em SaaS. Não disponibilizar a chave no frontend nem em artefatos do Actions.

Os textos gerados por IA são rascunhos, não alegações verificadas. Não há Easy Apply, envio de CV ou envio de mensagens automáticos.
