# Catálogo de fontes — verificação e ativação

A plataforma exibe **somente fontes com vagas reais no resultado**, nunca 20 opções fictícias.

| Fonte | Estado em código | Condição de ativação |
|---|---|---|
| Adzuna | Conector criado, opcional | `ADZUNA_APP_ID`, `ADZUNA_APP_KEY`; homologar acesso BR |
| Jooble | Conector criado, opcional | `JOOBLE_API_KEY`; homologar acesso e termos |
| Careerjet | Não integrado | Avaliar affiliate ID, documentação e licença |
| Remotive | Integrado | Feed público |
| RemoteOK | Não integrado | Verificar atribuição, limites e estabilidade |
| Jobicy | Conector criado | Endpoint público; verificar execução real na CI |
| Himalayas | Integrado | Feed remoto público, atribuição |
| Arbeitnow | Integrado | Feed público |
| The Muse | Não integrado | Verificar endpoint e termos atuais |
| USAJOBS | Não integrado | Exige autorização e relevância para elegibilidade Brasil |
| Reed | Não integrado | Exige chave; foco Reino Unido |
| Findwork | Não integrado | Verificar disponibilidade de API e licença |
| Greenhouse | Conector integrado | Empresa precisa de board público validado |
| Lever | Conector integrado | Empresa precisa de board público validado |
| Ashby | Conector integrado | Empresa precisa de board público validado |
| SmartRecruiters | Conector integrado | Empresa precisa de board público validado |
| Workable | Não integrado | API de anúncios públicos por empresa; validar slug da empresa |
| Gupy não oficial | Não integrado | Acesso não oficial: não usar sem autorização e termos compatíveis |
| GitHub Issues | Não integrado | Repositório real de vagas precisa existir e permitir consumo |
| Dados.gov.br / CAGED / RAIS | Não é feed de vagas | Dados históricos/estatísticos, não anúncios individuais |

**Importante:** endpoints públicos não implicam direito irrestrito de redistribuição comercial. Fontes que exigem chaves não têm suas credenciais em Git. As vagas devem conservar link/atribuição de origem. Datas `updated` não devem ser apresentadas como data original de publicação. A chave do Jooble deve permanecer nos secrets do Actions se o usuário ativar o provedor; não a colocar na página estática. As pesquisas Adzuna/Jooble partem de Campinas e raio de 80 km; isso depende do comportamento da API e não comprova distância por rota.

**Publicação:** o Pages ativo usa workflow na `main` e executa o coletor da branch de desenvolvimento. Alterações na branch isoladamente não garantem nova publicação; aguardar validação e disparar deploy autorizado na `main`.
