# mackai-conversas

> **Responsável:** Gabriel · **Épico do Miro:** 2 (Interface e UX) · **Exposição:** pública (o único serviço público) · **Porta local:** 8000 · **Banco:** `conversas_db`

Visão geral, convenções e cronograma comum: [README.md](README.md).

## 1. Missão
Ser a porta de entrada do MackAI: entregar o front, identificar cada navegador com uma sessão anônima, guardar conversas, mensagens e feedback e repassar as perguntas ao Orquestrador.

**Não faz:** montar prompt, chamar o Gemini, buscar trechos nem acessar o `busca_db`.

O serviço ficou com o Gabriel por ser o mais direto dos três. Ele reaproveita o front e a maior parte das rotas do MVP, usa padrões conhecidos (CRUD em PostgreSQL e token JWT) e não depende da chave do Gemini nem de cotas externas.

## 2. Posição na arquitetura

```text
Navegador ──HTTPS──► mackai-conversas ──► conversas_db
                           │ POST /v1/answers (timeout de 60 s)
                           ▼
                     mackai-orquestrador
```

## 3. User Stories

### 3.1 Entregues por este serviço
| US | Perfil | História | O que implementar | Critério de aceite |
|---|---|---|---|---|
| 30 | Dev | Quero usar o chat para testar pequenas variações de temperatura (temperature) do LLM, para avaliar o nível de criatividade nas respostas do bot | Slider de temperatura de 0 a 1 no campo de mensagem; valor enviado em `/api/chat` e repassado ao Orquestrador | Mover o slider muda `temperature` na requisição; valores fora de 0 a 1 retornam 422 |
| 31 | Dev | Quero que o chat formate blocos de código com syntax highlighting, para facilitar a leitura de trechos em Python ou React | Manter o `rehype-highlight` nos blocos de código | Bloco com linguagem marcada aparece colorido nos temas claro e escuro |
| 32 | Dev | Quero ter um botão de "Copiar Código" nas respostas do RAG, para agilizar a colagem na minha IDE | Manter o botão "Copiar código" em cada bloco | O botão copia só o conteúdo do bloco e mostra o aviso de copiado |
| 33 | Dev | Quero que a interface do assistente permita renderização de markdown, para exibir tabelas e listas organizadas sugeridas pela IA | Manter `react-markdown` com `remark-gfm` | Tabelas e listas em markdown aparecem formatadas |
| 34 | Dev | Quero visualizar um indicador de "IA digitando...", para saber que minha solicitação de orquestração está em processamento | Indicador "IA digitando..." do envio até a resposta ou o erro | O indicador some em caso de sucesso, de 429, de 503 e de timeout |
| 35 | Dev | Quero poder dar um feedback de "útil/não útil" (polegar para cima/baixo) na resposta do RAG, para gerar dados de calibração do modelo | Voto na coluna `messages.feedback`, permitido só ao dono da conversa | Recarregar a conversa mostra o voto salvo; votar em mensagem de outro usuário retorna 404 |
| 36 | Dev | Quero que o assistente mantenha o histórico de mensagens da sessão ativa, para que eu possa fazer perguntas de acompanhamento sobre o mesmo código | Histórico no PostgreSQL; as 10 últimas mensagens vão para o Orquestrador | Depois de reiniciar o serviço, a conversa continua; a pergunta de acompanhamento chega com o histórico |
| 37 | Dev | Quero iniciar uma "Nova Conversa" no chat, para limpar o contexto do modelo e abordar um microsserviço completamente diferente | "Nova conversa" zera o estado no front; o próximo envio cria uma conversa sem histórico | A primeira pergunta da nova conversa chega ao Orquestrador com `history` vazio |
| 38 | Dev | Quero que o RAG exiba as fontes (trechos de código de onde tirou a informação), para validar a veracidade da resposta | Mostrar módulo, arquivo, linhas, similaridade e trecho; aviso quando `grounded=false` | Resposta sobre o código mostra as fontes; resposta geral mostra o aviso de que não veio do projeto |
| 39 | Dev | Quero enviar blocos de erro extensos (stack traces) no input de texto sem travar a interface, para debugar falhas severas | Aceitar até 20.000 caracteres, com contador perto do limite | Um stack trace de 15.000 caracteres é enviado sem travar; acima de 20.000, o front avisa e a API retorna 422 |
| 40 | Dev | Quero acessar a interface do chat em modo noturno (dark mode), para reduzir a fadiga visual durante o desenvolvimento | Manter o tema escuro salvo no navegador | O tema escolhido continua depois de recarregar a página |

As US 30–33, 35, 36 e 38–40 já funcionam no MVP, mas com estado em memória. O trabalho é mantê-las funcionando com o banco, o token e o novo formato de resposta. A US 34 também já existe e precisa tratar os novos erros (429 e 503).

### 3.2 Participação em outras US e guias técnicos
| US | Perfil | História | Como este serviço participa |
|---|---|---|---|
| 5 | Dev | Quero pedir ao RAG sugestões de como estruturar endpoints assíncronos no FastAPI, para aumentar a vazão de requisições do meu microsserviço | Rotas `async` e chamada ao Orquestrador com um `httpx.AsyncClient` reutilizado |
| 7 | Dev | Quero perguntar ao assistente RAG sobre métodos HTTP específicos aplicados no projeto, para garantir que minhas rotas RESTful estejam dentro do padrão | REST na API pública: `GET` lê, `POST` cria; códigos 401, 404, 422, 429 e 503 |
| 9 | Dev | Quero pedir ao assistente RAG para validar se meu código CSS possui uma estrutura de layout responsiva adequada, para manter a consistência visual da plataforma | Conferir o layout do chat em 375 px depois das mudanças no front |
| 20 | Dev | Quero consultar o RAG sobre a configuração de middlewares de autenticação, para garantir que os endpoints estejam protegidos antes do deploy no Azure | Dependência do FastAPI que valida o token em todas as rotas `/api/*`, exceto `sessions` e `health` |
| 42 | Dev | Quero pedir ao assistente para gerar mocks de dados em formato JSON, para realizar testes unitários na minha API FastAPI | Respostas JSON falsas do Orquestrador nos testes |
| 48 | Dev | Quero perguntar ao assistente como monitorar o uso de memória do backend, para evitar vazamentos (memory leaks) nas chamadas repetitivas ao LLM | Dicionário global de conversas substituído pelo banco |
| 49 | Dev | Quero submeter meu código SQL ao RAG para receber sugestões de otimização de índices, acelerando as consultas do sistema | Índices `(owner_id, created_at)` e `(conversation_id, created_at)` |
| 50 | Dev | Quero pedir ao assistente dicas de como implementar tratamento global de exceções, para padronizar os retornos de erro da API | Handler global de exceções no formato `{detail, code}` |

## 4. Cards do Épico 7

| Card | Pronto quando |
|---|---|
| Persistir conversas e feedback | Reiniciar o serviço não perde conversas nem votos |
| Isolar usuários | Um segundo token recebe 404 ao ler ou votar na conversa do primeiro e não a vê na lista |
| Proteger a entrada | Mensagem acima de 20.000 caracteres retorna 422; excesso de requisições retorna 429 |
| Front no novo contrato | O front envia o token e mostra o módulo nas fontes, o aviso de resposta geral e as mensagens de 429 e 503 |

## 5. Contrato da API
Todas as rotas `/api/*` exigem `Authorization: Bearer <token>`, exceto `/api/sessions` e `/api/health`. Sem token, ou com token inválido, a resposta é 401.

### `POST /api/sessions`
Cria uma sessão anônima. Não tem corpo.

```json
{ "token": "eyJhbGciOi...", "expires_at": "2026-12-10T12:00:00Z" }
```

### `GET /api/health`
Agrega o estado do Orquestrador (`GET /v1/status`) e mantém o formato que o front já usa.

```json
{ "status": "ok", "llm": "gemini", "documents": 42, "chunks": 380, "indexed_at": "2026-11-12T10:00:00Z" }
```

Se o Orquestrador não responder, o retorno é `status: "degraded"`, `llm: "offline"`, `documents: 0`, `chunks: 0` e `indexed_at: null`.

### `GET /api/conversations`
Lista as conversas do dono do token que têm mensagens, das mais recentes para as mais antigas.

```json
[{ "id": "uuid", "title": "Como funciona a busca?", "created_at": "2026-11-12T10:00:00Z" }]
```

### `POST /api/conversations`
Cria uma conversa vazia e devolve o resumo no mesmo formato da lista.

### `GET /api/conversations/{id}`
Devolve a conversa com as mensagens. Retorna 404 se ela não existir ou for de outro dono.

### `POST /api/chat`

```json
{ "message": "Como funciona a busca?", "conversation_id": null, "profile": "Desenvolvedor", "temperature": 0.4 }
```

- `message`: de 1 a 20.000 caracteres.
- `profile`: `Desenvolvedor`, `Product Owner` ou `Gerente de Projetos`.
- `temperature`: de 0 a 1.

Resposta 200:

```json
{
  "conversation_id": "uuid",
  "message": {
    "id": "uuid",
    "role": "assistant",
    "content": "markdown...",
    "sources": [
      {
        "source": "modulo-7",
        "path": "services/busca/busca_semantica/rotas.py",
        "start_line": 1,
        "end_line": 30,
        "similarity": 0.82,
        "excerpt": "primeiros 300 caracteres do trecho"
      }
    ],
    "grounded": true,
    "mode": "gemini",
    "feedback": null,
    "created_at": "2026-11-12T10:00:00Z"
  }
}
```

Erros: 404 (conversa de outro dono), 422 (validação), 429 com `code: "RATE_LIMITED"` e 503 com `code: "ORQUESTRADOR_INDISPONIVEL"`.

### `POST /api/feedback`

```json
{ "message_id": "uuid", "value": "up" }
```

`value` aceita `up`, `down` ou `null` (remove o voto). Retorna 200 `{"ok": true}`, ou 404 se a mensagem não for do dono ou não for do assistente.

### Front (`/`)
Os arquivos do build do Vite são servidos pelo próprio serviço, montados depois das rotas `/api`. Como front e API ficam na mesma origem, não é preciso CORS.

## 6. Dados (`conversas_db`)

```sql
CREATE TABLE IF NOT EXISTS conversations (
  id          UUID PRIMARY KEY,
  owner_id    UUID NOT NULL,
  title       TEXT NOT NULL DEFAULT 'Nova conversa',
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS conversations_owner_idx ON conversations (owner_id, created_at DESC);

CREATE TABLE IF NOT EXISTS messages (
  id               UUID PRIMARY KEY,
  conversation_id  UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
  role             TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
  content          TEXT NOT NULL,
  sources          JSONB NOT NULL DEFAULT '[]',
  grounded         BOOLEAN,
  mode             TEXT,
  feedback         TEXT CHECK (feedback IN ('up', 'down')),
  feedback_at      TIMESTAMPTZ,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS messages_conversation_idx ON messages (conversation_id, created_at);
```

Regras:
- A pergunta e a resposta são gravadas na mesma transação, só depois que o Orquestrador responde.
- O título da conversa é formado pelos primeiros 60 caracteres da primeira pergunta.
- O histórico enviado ao Orquestrador tem as 10 últimas mensagens, cada uma cortada em 4.000 caracteres.
- O feedback fica na coluna `messages.feedback` e substitui o arquivo `feedback.jsonl`. Os dados de calibração (US 35) saem de uma consulta SQL.

## 7. Sessão e limites
- **Token:** JWT HS256 assinado com `SESSION_SECRET` (biblioteca PyJWT), com `sub` igual ao UUID do usuário anônimo e validade de 30 dias. O front guarda o token no `localStorage`. Se receber 401, pede um novo token e repete a requisição uma vez.
- **O que o token garante:** isolamento entre navegadores. Não é login: quem perde o token perde o histórico. Login real (por exemplo, com Microsoft Entra ID) entra no relatório como próximo passo.
- **Limites, em memória e com janela de 1 minuto:**
  - 10 perguntas por usuário;
  - 60 perguntas no total, que protegem a cota do Gemini mesmo que alguém crie muitas sessões;
  - 10 sessões novas por IP, lido do cabeçalho `X-Forwarded-For` do ingress.

  Como o app roda com no máximo 1 réplica, contadores em memória são suficientes.

## 8. Configuração

| Variável | Exemplo | Observação |
|---|---|---|
| `DATABASE_URL` | `postgresql://mackai:***@localhost:5432/conversas_db` | Secret no Azure |
| `SESSION_SECRET` | 32 ou mais caracteres aleatórios | Secret no Azure |
| `ORQUESTRADOR_URL` | `http://localhost:8001` (local), `http://mackai-orquestrador` (Azure) | |
| `ORQUESTRADOR_TIMEOUT_S` | `60` | |
| `CHAT_LIMIT_PER_USER` | `10` | Por minuto |
| `CHAT_LIMIT_GLOBAL` | `60` | Por minuto |
| `SESSION_LIMIT_PER_IP` | `10` | Por minuto |
| `MAX_MESSAGE_CHARS` | `20000` | Mesmo valor usado no front |

## 9. Estrutura de pastas

```text
services/conversas/
  assistente_conversacional/
    main.py                   # app FastAPI, handler de erros e montagem do front
    rotas.py                  # rotas /api/*
    modelos.py                # modelos Pydantic (contrato)
    sessoes.py                # token e dependência de autenticação
    limites.py                # limites de requisição
    repositorio.py            # SQL de conversas e mensagens
    cliente_orquestrador.py   # httpx.AsyncClient reutilizado
    schema.sql
  frontend/                   # movido de /frontend
  tests/
  Dockerfile
  requirements.txt
```

`Dockerfile` em dois estágios, para que o front vá na mesma imagem:

```dockerfile
FROM node:22-slim AS front
WORKDIR /front
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY assistente_conversacional/ assistente_conversacional/
COPY --from=front /front/dist frontend_dist/
EXPOSE 8000
CMD ["uvicorn", "assistente_conversacional.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 10. Migração do código atual

| De | Para | Mudança |
|---|---|---|
| [api.py:24-40](../../backend/assistente_conversacional/api.py#L24-L40) | (removido) | Sem CORS, porque a origem é a mesma. No desenvolvimento, o proxy do Vite cuida disso |
| [api.py:42-47](../../backend/assistente_conversacional/api.py#L42-L47) | (removido) | A base de conhecimento sai do serviço e o dicionário vira banco |
| [api.py:50-55](../../backend/assistente_conversacional/api.py#L50-L55) | `modelos.py` | `profile` vira `Literal` com os 3 perfis, `message` ganha limite de 20.000 caracteres e `temperature` passa a ir até 1 |
| [api.py:57-59](../../backend/assistente_conversacional/api.py#L57-L59) | `modelos.py` | Sem mudança |
| [api.py:62-73](../../backend/assistente_conversacional/api.py#L62-L73) | `repositorio.py` | Passa a usar SQL |
| [api.py:76-84](../../backend/assistente_conversacional/api.py#L76-L84) | `rotas.py` | Agrega `GET /v1/status` do Orquestrador |
| [api.py:87-102](../../backend/assistente_conversacional/api.py#L87-L102) | `rotas.py` | Filtro por dono |
| [api.py:105-129](../../backend/assistente_conversacional/api.py#L105-L129) | `rotas.py` e `cliente_orquestrador.py` | A busca (linha 115) e o Gemini (linha 119) viram uma chamada HTTP ao Orquestrador; o mapeamento das fontes (linhas 120–124) vai para o Orquestrador |
| [api.py:132-143](../../backend/assistente_conversacional/api.py#L132-L143) | `rotas.py` | `UPDATE` com filtro por dono, no lugar do laço; o JSONL sai |
| [api.py:146-148](../../backend/assistente_conversacional/api.py#L146-L148) | `main.py` | Sem mudança |
| [test_api.py:9-12, 36-53](../../backend/tests/test_api.py#L36-L53) | `tests/` | Passam a usar um Orquestrador falso |
| `frontend/` | `services/conversas/frontend/` | Ver a seção 11 |

## 11. Mudanças no front
- Mover `frontend/` para `services/conversas/frontend/`. O proxy do Vite continua mandando `/api` para `localhost:8000`.
- [api.ts:19-24](../../frontend/src/assistente_conversacional/api.ts#L19-L24): obter e guardar o token, enviar `Authorization` e, em 401, pedir um novo token e repetir uma vez. O erro lançado precisa carregar o status, para a tela diferenciar 401, 429 e 503.
- Tipos em [api.ts:1-10](../../frontend/src/assistente_conversacional/api.ts#L1-L10): adicionar `Source.source`, `Message.grounded` e `Message.mode`.
- [`SourceCard`](../../frontend/src/assistente_conversacional/AssistenteConversacional.tsx#L85-L97): mostrar `source/path`.
- [`AssistantAnswer`](../../frontend/src/assistente_conversacional/AssistenteConversacional.tsx#L99-L159): mostrar o aviso "Resposta geral, não baseada em arquivos do projeto" quando `grounded === false` e `mode !== "fallback"`.
- [`submit`](../../frontend/src/assistente_conversacional/AssistenteConversacional.tsx#L207-L229): em caso de erro, devolver o texto ao campo e mostrar mensagens específicas para 429 ("Muitas perguntas seguidas, aguarde um minuto") e 503.
- Mostrar um contador de caracteres a partir de 18.000 e bloquear o envio acima de 20.000 (US 39).

## 12. Testes
Rodam com o PostgreSQL do `docker-compose` e um Orquestrador falso (`httpx.MockTransport`).

| Cenário | Esperado |
|---|---|
| Requisição sem token | 401 |
| Token A cria uma conversa; token B lista, lê e vota nela | Lista vazia, 404 e 404 |
| Reiniciar o app (novo `TestClient` com o mesmo banco) | A conversa continua lá |
| 11ª pergunta no mesmo minuto | 429 |
| Mensagem com 20.001 caracteres; perfil inválido | 422 nos dois casos |
| Orquestrador em timeout | 503 e nada gravado |
| Primeira pergunta depois de "Nova conversa" | O Orquestrador falso recebe `history` vazio |
| Conversa com 14 mensagens | O Orquestrador falso recebe só as 10 últimas |
| Voto e remoção do voto | `feedback` vai para `up` e volta para `null` |

**Postman:** a coleção cobre todas as rotas. Um script de pre-request obtém o token em `/api/sessions` e o guarda numa variável da coleção.

## 13. Deploy
- Container App `mackai-conversas`, ingress **externo**, porta 8000, 0,25 vCPU e 0,5 GiB.
- Réplicas: mínimo 0 e máximo 1. No dia da apresentação, mínimo 1.
- Secrets: `DATABASE_URL` e `SESSION_SECRET`.
- Sondas de vida e de prontidão em `/health`.

## 14. Cronograma do Gabriel

| Dia | Entrega |
|---|---|
| D1 | Modelos Pydantic e OpenAPI de Conversas; mover o front para `services/conversas/`; esqueleto do serviço |
| D2 | `schema.sql`, repositório, sessões com token e rotas com filtro por dono |
| D3 | Limites, cliente do Orquestrador (contra o mock), mudanças no front e Dockerfile |
| D4 | Integração no `docker-compose`; coleção passando no Newman |
| D5 | Deploy junto com o Lucas; teste de fumaça do front |
| D6 | Seção do relatório; mover os cards do Épico 2 no Miro |
| D7 | Ensaio da demonstração |

## 15. Fora do escopo e riscos
- **Aceito:** quem perde o token perde o histórico, e os contadores de limite zeram quando o serviço reinicia.
- **Fora desta entrega:** login real, streaming de resposta (aparece no diagrama do Miro, mas nenhuma US exige) e exportação de feedback pela interface.
- **Risco:** o front quebrar com os novos campos. Por isso, `grounded` e `mode` são opcionais nos tipos do TypeScript.

## 16. Roteiro da seção no relatório
1. Responsabilidade do serviço e o que ele não faz.
2. Contrato (tabela de rotas) e modelo de dados.
3. Decisões: sessão anônima com token, um banco por serviço, front servido pelo próprio serviço e sem CORS.
4. US entregues, com o critério de aceite de cada uma.
5. Limitações e próximos passos.
