# Microsserviços do MackAI (Módulo 7)

Documentação de desenvolvimento da divisão do MVP em três microsserviços, um por integrante. Cada serviço tem um documento próprio com o que implementar, como implementar e quais User Stories atende.

| Serviço | Responsável | Papel | Documento |
|---|---|---|---|
| `mackai-conversas` | Gabriel | Porta de entrada pública: front, sessões, histórico e feedback | [mackai-conversas.md](mackai-conversas.md) |
| `mackai-orquestrador` | Lucas | Monta o prompt, chama o Gemini e trata falhas; cuida da infraestrutura e do CI | [mackai-orquestrador.md](mackai-orquestrador.md) |
| `mackai-busca` | Danilo | Ingestão da base de conhecimento e busca por significado | [mackai-busca.md](mackai-busca.md) |

Fontes usadas: código do MVP (commit `83787d1`), backlog com as 100 User Stories, quadro do Miro (Kanban, épicos, personas e diagrama) e o relatório de arquitetura do grupo. O fork `LPBARRETO/MVP-Modulo-7` foi verificado em 09/11/2026: o último commit dele (`d2c74dc`) já está no `main`, então não há código novo a incorporar.

> Os links para o código apontam para o MVP antes da migração (`backend/` e `frontend/`). Depois da migração, esses arquivos deixam de existir.

## 1. Arquitetura

```text
Navegador
   │ HTTPS (único ponto público)
   ▼
mackai-conversas ──► conversas_db (PostgreSQL)
   │ POST /v1/answers
   ▼
mackai-orquestrador ──► API Gemini (geração de texto)
   │ POST /v1/search
   ▼
mackai-busca ──► busca_db (PostgreSQL + pgvector)
             └─► API Gemini (embeddings)
```

Regras que valem para os três serviços:
- As chamadas seguem sempre esse sentido. Nenhum serviço chama um serviço acima dele, e nenhum acessa o banco de outro.
- Só `mackai-conversas` é público. Os outros dois usam ingress interno no Azure Container Apps.
- Nenhum serviço importa código de outro. O Dockerfile de cada serviço só enxerga a própria pasta.

### Fluxo de uma pergunta
1. O front envia `POST /api/chat` com o token da sessão.
2. Conversas valida o token, o tamanho e o limite de requisições, carrega as 10 últimas mensagens da conversa e chama o Orquestrador.
3. O Orquestrador monta a consulta de busca. Se a pergunta for curta e houver histórico, junta a pergunta anterior.
4. A Busca devolve até 3 trechos acima do limiar de similaridade.
5. O Orquestrador monta o prompt e chama o Gemini. Sem trechos, responde com conhecimento geral e marca `grounded=false`.
6. Conversas grava a pergunta e a resposta e devolve ao front, que mostra as fontes ou o aviso de resposta geral.

### Quando algo falha

| Falha | Comportamento |
|---|---|
| Busca fora do ar ou lenta (mais de 5 s) | O Orquestrador responde sem fontes (`grounded=false`) e registra o erro no log |
| Gemini com erro ou lento (mais de 30 s) | O Orquestrador devolve a mensagem amigável (`mode=fallback`) com as fontes encontradas |
| Sem `GEMINI_API_KEY` | O Orquestrador entra em modo offline e devolve os trechos; a Busca usa TF-IDF |
| Orquestrador fora do ar (mais de 60 s) | Conversas retorna 503 com mensagem amigável e não grava nada; o front devolve o texto ao campo |

## 2. Épicos do Miro por serviço

| Épico | Serviço principal |
|---|---|
| 1. Motor RAG e orquestração de IA (US 21–30) | Orquestrador e Busca |
| 2. Interface e UX (US 31–40) | Conversas |
| 3. Engenharia de software, arquitetura e integrações (US 1–10, 41–60) | Orquestrador (respostas) e Busca (dados do projeto) |
| 4. Infraestrutura, deploy e hardware (US 11–20) | Orquestrador (respostas); a infraestrutura real fica com o Lucas |
| 5. Produto, negócio e escopo (US 61–80) | Busca (dados do projeto) e Orquestrador |
| 6. Gestão ágil, métricas e fluxo (US 81–100) | Orquestrador e Busca |
| 7. Microsserviços (novo; cards em cada documento) | Os três |

## 3. Convenções comuns
- **Stack:** Python 3.12, FastAPI, Pydantic v2, uvicorn, `httpx` nas chamadas entre serviços e `pytest`. Cada serviço fixa as versões no próprio `requirements.txt`.
- **Portas locais:** Conversas 8000, Orquestrador 8001, Busca 8002 e PostgreSQL 5432. Dentro do container, todos escutam na porta 8000.
- **Saúde:** todo serviço expõe `GET /health` → `{"status": "ok"}`, usado pelas sondas do Container Apps.
- **Erros:** handler global de exceções (US 50) com o corpo `{"detail": "mensagem legível", "code": "CODIGO"}`. Erros de validação continuam no 422 padrão do FastAPI.
- **Chave do Gemini:** a chave do Lucas fica só nos secrets do Azure (Orquestrador e Busca) e do GitHub. Ela nunca é enviada por chat nem entra no repositório. No desenvolvimento local, cada pessoa usa a própria chave gratuita do Google AI Studio ou roda sem chave (Orquestrador em modo offline, Busca com TF-IDF). Em produção, geração de texto e embeddings dividem a cota da mesma chave.
- **Rastreamento:** Conversas gera o cabeçalho `X-Request-ID`. Cada serviço repassa esse cabeçalho e o inclui nos logs.
- **Versões:** rotas internas começam com `/v1`. Mudança que quebra contrato exige `/v2` ou acordo do grupo.
- **Banco:** cada serviço cria as próprias tabelas na inicialização com `CREATE TABLE IF NOT EXISTS` (arquivo `schema.sql`). Sem ORM.
- **Git:** branch `feature/<servico>-<tema>` → Pull Request para `develop`, revisado por outra pessoa → `develop` para `main`, que dispara o deploy.

## 4. Estrutura do repositório

```text
services/
  conversas/        # mackai-conversas (Gabriel), inclui o frontend/
  orquestrador/     # mackai-orquestrador (Lucas)
  busca/            # mackai-busca (Danilo)
contracts/          # OpenAPI exportado de cada serviço
postman/            # coleções e ambientes exportados
infra/              # script de criação dos bancos para o docker-compose
docs/
  microsservicos/   # esta documentação
  produto/          # backlog, personas e guia visual (indexados pela Busca)
docker-compose.yml
.github/workflows/  # um workflow por serviço + integração
```

O código atual em `backend/` e `frontend/` é migrado conforme a seção "Migração do código atual" de cada documento. O deploy atual no App Service F1 continua ligado até o novo ambiente passar no teste de fumaça (D5). Ele é o plano B da apresentação.

## 5. Contratos
No D1, cada serviço define seus modelos Pydantic, exporta o OpenAPI para `contracts/` e importa no Postman. Os detalhes estão em cada documento.

| Serviço | Rotas |
|---|---|
| Conversas (público) | `POST /api/sessions`, `GET /api/health`, `GET` e `POST /api/conversations`, `GET /api/conversations/{id}`, `POST /api/chat`, `POST /api/feedback` |
| Orquestrador (interno) | `POST /v1/answers`, `GET /v1/status` |
| Busca (interna) | `POST /v1/search`, `GET /v1/stats`, `POST /v1/documents`, `POST /v1/reindex` |

## 6. Postman
- Um workspace do grupo, com uma coleção por serviço e dois ambientes: `local` (portas 8000 a 8002) e `azure` (só a URL pública de Conversas, porque os outros serviços são internos).
- No D1, cada coleção gera um mock server a partir do OpenAPI. Até o D4, cada pessoa desenvolve contra os mocks dos outros dois serviços.
- Toda requisição da coleção testa o status e os campos obrigatórios. O CI roda as coleções com Newman contra o `docker-compose`; a configuração fica com o Lucas.
- Exportem as coleções para `postman/` a cada mudança de contrato.

## 7. Cronograma comum
D1 = terça, 10/11/2026. Ajustem as datas se a entrega mudar.

| Dia | Em conjunto | Gabriel (Conversas) | Danilo (Busca) | Lucas (Orquestrador) |
|---|---|---|---|---|
| D1 | Contratos, esqueleto, `docker-compose` e mocks | Modelos e OpenAPI de Conversas | Modelos e OpenAPI da Busca | Modelos e OpenAPI do Orquestrador; testa chave e modelo do Gemini; cria os recursos no Azure |
| D2 | | Banco e sessões | Ingestão e pgvector | Prompt, cliente do Gemini e fallback |
| D3 | | Limites e front | Busca, TF-IDF e filtro de segredos | Cliente da Busca, `grounded` e CI |
| D4 | Integração no `docker-compose` e Newman | | | |
| D5 | Deploy no Azure e teste de fumaça | | | |
| D6 | Código congelado; relatório e Miro atualizados | | | |
| D7 | Ensaio da demonstração e folga | | | |

**Se atrasar, cortem nesta ordem:**
1. Histórico do git na base de conhecimento (US 64 e 89).
2. Reescrita da consulta em perguntas de acompanhamento.
3. Newman no CI, rodando só localmente.
4. Embeddings e pgvector, mantendo o TF-IDF atrás do mesmo contrato e declarando isso no relatório.

**Não cortem:** os três deploys separados, os contratos, a persistência das conversas, o isolamento entre usuários, a indexação do código e o tratamento de falha do Gemini.

## 8. O que precisa ser corrigido fora do código
- **Diagrama do Miro:** trocar Flask por FastAPI e o Load Balancer pelo ingress do Container Apps, remover o streaming, separar os três serviços e os dois bancos e incluir a Busca.
- **Kanban do Miro:** mover para Revisão as US 30–33, 35, 36, 38–40 e 80 (hoje em Backlog) e as US 21, 34 e 37 (hoje em andamento), que já estão implementadas. Criar o Épico 7 com os cards de cada documento.
- **Relatório:** substituir a descrição de monólito modular pela arquitetura desta página. Cada responsável escreve a seção do seu serviço a partir do roteiro no fim do seu documento.

## 9. Matriz das 100 User Stories
Tipos:
- **Funcionalidade** (12): comportamento do produto que precisa ser implementado.
- **Dados do projeto** (16): perguntas que só têm resposta útil se a Busca indexar o código, o backlog ou os documentos.
- **Conhecimento geral** (69): perguntas que o assistente responde com o conhecimento do LLM ou com o conteúdo colado pelo usuário. Não exigem código específico, mas o prompt do Orquestrador precisa permitir esse tipo de resposta.
- **Fora desta entrega** (3): dependem de algo que não existe no projeto.

"Responsável" é quem entrega a US. "Também envolve" lista os serviços que participam dela ou que a usam como guia técnico de implementação.

| US | Perfil | Feature | História | Tipo | Responsável | Também envolve |
|---|---|---|---|---|---|---|
| 1 | Dev | 3.1 | Quero perguntar ao assistente RAG "Como funciona o serviço de pagamento?", para entender a lógica implementada no projeto | Dados do projeto | Busca | — |
| 2 | Dev | 3.1 | Quero perguntar ao assistente RAG "Quais bibliotecas de cache são recomendadas para nossa stack?", para aplicar a melhor curadoria arquitetural | Dados do projeto | Busca | — |
| 3 | Dev | 3.1 | Quero enviar trechos de código TypeScript no chat, para que o RAG sugira tipagens genéricas mais seguras | Conhecimento geral | Orquestrador | — |
| 4 | Dev | 3.1 | Quero consultar o assistente sobre o ciclo de vida de componentes React no frontend, para resolver problemas de renderização indesejada | Conhecimento geral | Orquestrador | — |
| 5 | Dev | 3.1 | Quero pedir ao RAG sugestões de como estruturar endpoints assíncronos no FastAPI, para aumentar a vazão de requisições do meu microsserviço | Conhecimento geral | Orquestrador | Conversas |
| 6 | Dev | 3.1 | Quero consultar o assistente sobre como utilizar o framework Flask em conjunto com conteinerização, para padronizar o ambiente de desenvolvimento local | Conhecimento geral | Orquestrador | — |
| 7 | Dev | 3.1 | Quero perguntar ao assistente RAG sobre métodos HTTP específicos aplicados no projeto, para garantir que minhas rotas RESTful estejam dentro do padrão | Dados do projeto | Busca | Conversas |
| 8 | Dev | 3.1 | Quero solicitar ao chat exemplos práticos de injeção de dependência em Python, para manter o código do backend desacoplado | Conhecimento geral | Orquestrador | — |
| 9 | Dev | 3.1 | Quero pedir ao assistente RAG para validar se meu código CSS possui uma estrutura de layout responsiva adequada, para manter a consistência visual da plataforma | Conhecimento geral | Orquestrador | Conversas |
| 10 | Dev | 3.1 | Quero usar o chat para buscar referências de código de operações CRUD em Flutter/Dart, caso a equipe decida construir integrações mobile no futuro | Conhecimento geral | Orquestrador | — |
| 11 | Dev | 4.1 | Quero pedir ao RAG um modelo de Dockerfile otimizado para Python, para reduzir o tamanho da imagem do meu microsserviço | Conhecimento geral | Orquestrador | — |
| 12 | Dev | 4.1 | Quero consultar o assistente sobre como configurar variáveis de ambiente no WSL (Windows Subsystem for Linux), para testar integrações locais de forma segura | Conhecimento geral | Orquestrador | — |
| 13 | Dev | 4.1 | Quero perguntar ao RAG como estruturar pipelines de CI/CD para o Azure App Services, para automatizar o deploy do Módulo 7 | Conhecimento geral | Orquestrador | — |
| 14 | Dev | 4.1 | Quero submeter logs de erro de build do Docker ao assistente, para que ele identifique rapidamente a dependência ausente | Conhecimento geral | Orquestrador | — |
| 15 | Dev | 4.1 | Quero pedir ao assistente instruções sobre como gerenciar imagens de containers diretamente pela IDE (como PyCharm), para acelerar meus testes | Conhecimento geral | Orquestrador | — |
| 16 | Dev | 4.1 | Quero consultar o RAG sobre padrões de publicação e assinatura (Pub/Sub) usando tópicos MQTT, para integrar simulações de IoT ao projeto | Conhecimento geral | Orquestrador | — |
| 17 | Dev | 4.1 | Quero perguntar ao assistente como usar conversores de nível lógico em hardwares como o ESP32, para fins de validação em disciplinas de integração de hardware | Conhecimento geral | Orquestrador | — |
| 18 | Dev | 4.1 | Quero pedir ao chat exemplos de implementação de timers não bloqueantes, para otimizar o consumo de recursos em serviços em background | Conhecimento geral | Orquestrador | — |
| 19 | Dev | 4.1 | Quero questionar o assistente sobre protocolos de comunicação serial (UART, I2C, SPI), para expandir o ecossistema do projeto para camadas de borda | Conhecimento geral | Orquestrador | — |
| 20 | Dev | 4.1 | Quero consultar o RAG sobre a configuração de middlewares de autenticação, para garantir que os endpoints estejam protegidos antes do deploy no Azure | Conhecimento geral | Orquestrador | Conversas |
| 21 | Dev | 1.1 | Quero consultar o assistente sobre como integrar a biblioteca `google-genai` no meu código, para facilitar a orquestração de chamadas de IA | Conhecimento geral | Orquestrador | Busca |
| 22 | Dev | 1.1 | Quero perguntar ao RAG quais os limites de tokens e parâmetros do modelo `gemini-2.5-flash`, para otimizar os custos computacionais do módulo | Conhecimento geral | Orquestrador | — |
| 23 | Dev | 1.1 | Quero buscar exemplos no assistente de como converter logs textuais estruturados em apresentações usando bibliotecas como `python-pptx` | Conhecimento geral | Orquestrador | — |
| 24 | Dev | 1.1 | Quero entender via chat como funciona o processo de criação de embeddings textuais, para aprimorar o motor de busca semântica do RAG | Conhecimento geral | Orquestrador | Busca |
| 25 | Dev | 1.1 | Quero pedir ao assistente sugestões de prompts dinâmicos, para que a IA consiga extrair o contexto correto do banco de dados vetorial | Conhecimento geral | Orquestrador | — |
| 26 | Dev | 1.1 | Quero consultar o RAG sobre estratégias de chunking (divisão de texto), para garantir que documentos grandes sejam lidos corretamente pela IA | Conhecimento geral | Orquestrador | Busca |
| 27 | Dev | 1.1 | Quero pedir ao chat métodos para calcular a similaridade de cosseno, para refinar os resultados da busca semântica | Conhecimento geral | Orquestrador | Busca |
| 28 | Dev | 1.1 | Quero solicitar ao assistente alternativas de bancos de dados vetoriais compatíveis com Python, para armazenar o conhecimento do repositório | Conhecimento geral | Orquestrador | Busca |
| 29 | Dev | 1.1 | Quero perguntar como isolar as chaves de API da IA generativa no backend, para evitar exposição acidental de credenciais no repositório | Conhecimento geral | Orquestrador | Busca |
| 30 | Dev | 1.1 | Quero usar o chat para testar pequenas variações de temperatura (temperature) do LLM, para avaliar o nível de criatividade nas respostas do bot | Funcionalidade | Conversas | Orquestrador |
| 31 | Dev | 2.1 | Quero que o chat formate blocos de código com syntax highlighting, para facilitar a leitura de trechos em Python ou React | Funcionalidade | Conversas | — |
| 32 | Dev | 2.1 | Quero ter um botão de "Copiar Código" nas respostas do RAG, para agilizar a colagem na minha IDE | Funcionalidade | Conversas | — |
| 33 | Dev | 2.1 | Quero que a interface do assistente permita renderização de markdown, para exibir tabelas e listas organizadas sugeridas pela IA | Funcionalidade | Conversas | — |
| 34 | Dev | 2.1 | Quero visualizar um indicador de "IA digitando...", para saber que minha solicitação de orquestração está em processamento | Funcionalidade | Conversas | — |
| 35 | Dev | 2.1 | Quero poder dar um feedback de "útil/não útil" (polegar para cima/baixo) na resposta do RAG, para gerar dados de calibração do modelo | Funcionalidade | Conversas | — |
| 36 | Dev | 2.1 | Quero que o assistente mantenha o histórico de mensagens da sessão ativa, para que eu possa fazer perguntas de acompanhamento sobre o mesmo código | Funcionalidade | Conversas | Orquestrador |
| 37 | Dev | 2.1 | Quero iniciar uma "Nova Conversa" no chat, para limpar o contexto do modelo e abordar um microsserviço completamente diferente | Funcionalidade | Conversas | — |
| 38 | Dev | 2.1 | Quero que o RAG exiba as fontes (trechos de código de onde tirou a informação), para validar a veracidade da resposta | Funcionalidade | Conversas | Busca, Orquestrador |
| 39 | Dev | 2.1 | Quero enviar blocos de erro extensos (stack traces) no input de texto sem travar a interface, para debugar falhas severas | Funcionalidade | Conversas | — |
| 40 | Dev | 2.1 | Quero acessar a interface do chat em modo noturno (dark mode), para reduzir a fadiga visual durante o desenvolvimento | Funcionalidade | Conversas | — |
| 41 | Dev | 3.2 | Quero colar logs de travamento de sistema (como análise de minidumps) no RAG, para que a IA sugira a causa raiz do problema | Conhecimento geral | Orquestrador | — |
| 42 | Dev | 3.2 | Quero pedir ao assistente para gerar mocks de dados em formato JSON, para realizar testes unitários na minha API FastAPI | Conhecimento geral | Orquestrador | Busca, Conversas |
| 43 | Dev | 3.2 | Quero consultar o RAG sobre como resolver conflitos complexos de merge no Git, para evitar a perda de código do grupo | Conhecimento geral | Orquestrador | — |
| 44 | Dev | 3.2 | Quero perguntar ao assistente sobre padrões de injeção de falhas (Chaos Engineering), para testar a resiliência do sistema | Conhecimento geral | Orquestrador | — |
| 45 | Dev | 3.2 | Quero pedir ao RAG para escrever um teste de integração para o endpoint de busca semântica, para garantir que o vetor retornado está correto | Dados do projeto | Busca | — |
| 46 | Dev | 3.2 | Quero usar o chat para entender alertas de segurança de dependências (ex: vulnerabilidades no npm ou pip), para corrigir brechas | Conhecimento geral | Orquestrador | — |
| 47 | Dev | 3.2 | Quero que o RAG me explique mensagens de erro crípticas do compilador TypeScript, para que eu saiba qual tipo de dado está divergente | Conhecimento geral | Orquestrador | — |
| 48 | Dev | 3.2 | Quero perguntar ao assistente como monitorar o uso de memória do backend, para evitar vazamentos (memory leaks) nas chamadas repetitivas ao LLM | Conhecimento geral | Orquestrador | Conversas |
| 49 | Dev | 3.2 | Quero submeter meu código SQL ao RAG para receber sugestões de otimização de índices, acelerando as consultas do sistema | Conhecimento geral | Orquestrador | Busca, Conversas |
| 50 | Dev | 3.2 | Quero pedir ao assistente dicas de como implementar tratamento global de exceções, para padronizar os retornos de erro da API | Conhecimento geral | Orquestrador | Busca, Conversas |
| 51 | Dev | 3.3 | Quero usar o RAG para tirar dúvidas sobre cálculos de engenharia (como cargas elétricas ou diagramas unifilares), para reaproveitar conceitos em outras disciplinas | Conhecimento geral | Orquestrador | — |
| 52 | Dev | 3.3 | Quero consultar o assistente sobre fórmulas de física ou estruturas de materiais (ex: redes de Bravais), usando a IA como apoio multidisciplinar | Conhecimento geral | Orquestrador | — |
| 53 | Dev | 3.3 | Quero pedir ao chat que gere scripts de automação em VBA ou Python para planilhas, para gerar relatórios de testes de carga | Conhecimento geral | Orquestrador | — |
| 54 | Dev | 3.3 | Quero perguntar ao RAG sobre integrações de software de streaming (como OBS Studio e máscaras faciais 3D), caso seja necessário para demonstrações de vídeo do projeto | Conhecimento geral | Orquestrador | — |
| 55 | Dev | 3.3 | Quero pedir ao assistente sugestões de atalhos e extensões de navegadores, para melhorar minha produtividade | Conhecimento geral | Orquestrador | — |
| 56 | Dev | 3.3 | Quero usar o RAG para formatar descrições detalhadas do meu código, facilitando a elaboração do meu portfólio profissional | Conhecimento geral | Orquestrador | — |
| 57 | Dev | 3.3 | Quero consultar o assistente sobre comandos avançados de Linux (baseados em certificações Cisco NetAcad), para otimizar servidores de produção | Conhecimento geral | Orquestrador | — |
| 58 | Dev | 3.3 | Quero solicitar ao RAG que resuma artigos técnicos longos em bullet points, para agilizar meus estudos de novas bibliotecas | Conhecimento geral | Orquestrador | — |
| 59 | Dev | 3.3 | Quero usar o chat para converter rascunhos feitos à mão em tablets (com stylus) em estruturas lógicas de código | Fora desta entrega | — | — |
| 60 | Dev | 3.3 | Quero que o RAG sugira nomes semânticos para variáveis e funções complexas, mantendo o Clean Code | Conhecimento geral | Orquestrador | — |
| 61 | PO | 5.1 | Quero interrogar o assistente RAG sobre a cobertura atual do código em relação aos Épicos definidos, para garantir a entrega de valor | Dados do projeto | Busca | — |
| 62 | PO | 5.1 | Quero pedir ao RAG que compare o código fonte atual com os mockups criados no Figma, para validar se a interface desenvolvida atende aos protótipos de design aprovados | Fora desta entrega | — | — |
| 63 | PO | 5.1 | Quero consultar o assistente sobre o impacto no negócio caso uma biblioteca legada continue sendo usada, para avaliar o débito técnico | Conhecimento geral | Orquestrador | — |
| 64 | PO | 5.1 | Quero usar o chat para gerar resumos executivos das features implementadas na semana, para apresentar nas reuniões de Review | Dados do projeto | Busca | — |
| 65 | PO | 5.1 | Quero perguntar ao RAG se as regras de negócio de pagamentos estão blindadas contra fraudes lógicas no código, mitigando riscos financeiros | Dados do projeto | Busca | — |
| 66 | PO | 5.1 | Quero que o assistente valide se o fatiamento de histórias (usando metodologias como SPIDR) está coerente com os Épicos cadastrados no sistema | Dados do projeto | Busca | — |
| 67 | PO | 5.1 | Quero solicitar ao chat ideias de Product Roadmaps a partir das features técnicas entregues, para visualizar os próximos passos da plataforma | Dados do projeto | Busca | — |
| 68 | PO | 5.1 | Quero consultar o assistente sobre quais User Stories no backlog podem ser simplificadas, para acelerar a entrega do MVP | Dados do projeto | Busca | — |
| 69 | PO | 5.1 | Quero submeter critérios de aceite (Acceptance Criteria) ao RAG, para que ele avalie se estão claros o suficiente para a equipe de desenvolvimento | Conhecimento geral | Orquestrador | — |
| 70 | PO | 5.1 | Quero perguntar ao assistente como a escolha de uma arquitetura baseada em eventos impacta a experiência final do usuário, para garantir alinhamento com a visão do produto | Conhecimento geral | Orquestrador | — |
| 71 | PO | 5.1 | Quero pedir ao RAG para traduzir explicações altamente técnicas (ex: refatoração de APIs FastAPI) para uma linguagem de negócios, facilitando minha comunicação com stakeholders | Conhecimento geral | Orquestrador | — |
| 72 | PO | 5.1 | Quero consultar o chat sobre modelos de precificação de IA (ex: consumo de tokens do Gemini), para garantir que o Módulo 7 não ultrapasse o orçamento do projeto | Conhecimento geral | Orquestrador | — |
| 73 | PO | 5.1 | Quero perguntar ao assistente sobre tendências de mercado em plataformas de desenvolvedores, para agregar inovações ao backlog | Conhecimento geral | Orquestrador | — |
| 74 | PO | 5.1 | Quero que o RAG identifique funcionalidades redundantes lendo a documentação gerada pelos desenvolvedores, para enxugar o escopo | Dados do projeto | Busca | — |
| 75 | PO | 5.1 | Quero usar o assistente para rascunhar respostas para formulários de submissão do projeto, destacando o valor analítico e técnico da entrega | Dados do projeto | Busca | — |
| 76 | PO | 5.1 | Quero solicitar ao RAG que faça uma análise cruzada entre os requisitos iniciais e o que foi de fato codificado, para medir o desvio de escopo | Dados do projeto | Busca | — |
| 77 | PO | 5.1 | Quero perguntar ao assistente sobre estratégias de lançamento fatiado (phased rollout), para reduzir o risco ao integrar os 7 módulos do projeto | Conhecimento geral | Orquestrador | — |
| 78 | PO | 5.1 | Quero usar o RAG para sugerir melhorias na jornada do usuário com base nas limitações técnicas informadas pela equipe | Conhecimento geral | Orquestrador | — |
| 79 | PO | 5.1 | Quero perguntar ao assistente como estruturar métricas de engajamento da plataforma, para medir o sucesso após o deploy funcional | Conhecimento geral | Orquestrador | — |
| 80 | PO | 5.1 | Quero consultar o RAG sobre planos de contingência caso a orquestração de LLMs falhe, garantindo que o usuário receba uma mensagem amigável no lugar de um erro críptico | Funcionalidade | Orquestrador | — |
| 81 | PM | 6.1 | Quero consultar o RAG sobre o significado de certos erros técnicos reportados, para compreender a real gravidade de um impedimento relatado pela equipe | Conhecimento geral | Orquestrador | — |
| 82 | PM | 6.1 | Quero perguntar ao assistente RAG como estruturar etiquetas de prioridade em quadros do Trello (ou YouTrack), para melhorar a visualização de gargalos pela equipe | Conhecimento geral | Orquestrador | — |
| 83 | PM | 6.1 | Quero pedir ao chat sugestões de como dividir tarefas muito complexas em cartões menores e mais gerenciáveis, otimizando o fluxo de trabalho | Conhecimento geral | Orquestrador | — |
| 84 | PM | 6.1 | Quero usar o assistente para entender a dependência técnica entre um serviço backend e uma interface web, para organizar a ordem das Sprints de forma lógica | Conhecimento geral | Orquestrador | — |
| 85 | PM | 6.1 | Quero submeter relatos de conflitos técnicos entre módulos (ex: Módulo 1 x Módulo 7) ao RAG para que ele sugira formas de mediar a solução | Conhecimento geral | Orquestrador | — |
| 86 | PM | 6.1 | Quero perguntar ao assistente RAG como configurar automações visuais em quadros Kanban, para que tarefas atrasadas mudem de cor automaticamente | Conhecimento geral | Orquestrador | — |
| 87 | PM | 6.1 | Quero consultar o chat sobre dinâmicas ágeis remotas utilizando o Miro, para melhorar o engajamento do grupo durante as retrospectivas de Sprint | Conhecimento geral | Orquestrador | — |
| 88 | PM | 6.1 | Quero pedir ao RAG para gerar um template de relatório de progresso, facilitando o acompanhamento do cronograma até o dia do Deploy Final | Conhecimento geral | Orquestrador | — |
| 89 | PM | 6.1 | Quero perguntar ao assistente como calcular a velocidade da equipe (Velocity) baseado nos commits recentes, para calibrar a capacidade de entrega da próxima semana | Dados do projeto | Busca | — |
| 90 | PM | 6.1 | Quero consultar o RAG sobre técnicas para reduzir o "context switching" (troca de contexto) dos desenvolvedores que estão atuando em DevOps e Frontend simultaneamente | Conhecimento geral | Orquestrador | — |
| 91 | PM | 6.1 | Quero usar o assistente para identificar riscos no cronograma baseados na documentação técnica inserida no projeto | Dados do projeto | Busca | — |
| 92 | PM | 6.1 | Quero solicitar ao RAG práticas para facilitar a comunicação entre o PO e a equipe técnica, agindo como ponte de facilitação ágil | Conhecimento geral | Orquestrador | — |
| 93 | PM | 6.1 | Quero consultar o chat sobre a eficiência de reuniões diárias (Daily Scrum) assíncronas em grupos acadêmicos, para otimizar o tempo dos colegas de classe | Conhecimento geral | Orquestrador | — |
| 94 | PM | 6.1 | Quero pedir ao assistente que sugira métricas de qualidade (além do burndown) para avaliar a robustez da integração de microsserviços do projeto | Conhecimento geral | Orquestrador | — |
| 95 | PM | 6.1 | Quero perguntar ao RAG como estruturar fóruns ou murais de conhecimento para evitar que a equipe de engenharia repita os mesmos erros ao configurar Docker | Conhecimento geral | Orquestrador | — |
| 96 | PM | 6.1 | Quero usar o assistente para revisar os registros de bugs no backlog e sugerir quais devem ser priorizados com base em dependências de arquitetura | Fora desta entrega | — | — |
| 97 | PM | 6.1 | Quero consultar o RAG sobre as melhores práticas para documentar decisões técnicas (ADRs), para que o histórico do projeto não seja perdido | Conhecimento geral | Orquestrador | — |
| 98 | PM | 6.1 | Quero pedir ao chat para traduzir a curva de aprendizado de uma nova linguagem para estimativas de tempo em semanas de Sprint | Conhecimento geral | Orquestrador | — |
| 99 | PM | 6.1 | Quero submeter planos de testes ao assistente para verificar se há tempo suficiente reservado no cronograma para a fase de Quality Assurance (QA) | Conhecimento geral | Orquestrador | — |
| 100 | PM | 6.1 | Quero que o RAG me sugira roteiros de demonstração (scripts de apresentação) para o MVP, garantindo que o fluxo técnico seja exibido de forma fluida para os avaliadores | Dados do projeto | Busca | — |
