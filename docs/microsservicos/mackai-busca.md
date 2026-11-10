# mackai-busca

> **Responsável:** Danilo · **Épico do Miro:** 1 (motor RAG: busca semântica), e os dados que respondem a US dos Épicos 3, 5 e 6 · **Exposição:** interna · **Porta local:** 8002 · **Banco:** `busca_db` (PostgreSQL + pgvector)

Visão geral, convenções e cronograma comum: [README.md](README.md).

## 1. Missão
Transformar o código e os documentos do projeto em trechos pesquisáveis e devolver, para cada pergunta, os trechos mais parecidos em significado. É isso que faz do MackAI um RAG, e não um chat genérico.

**Não faz:** chamar o modelo de geração de texto, montar prompt nem conhecer usuários ou conversas.

O serviço ficou com o Danilo por ser o mais autocontido: depende só do próprio banco e da API de embeddings.

## 2. Posição na arquitetura

```text
mackai-orquestrador ──POST /v1/search──► mackai-busca ──► busca_db (pgvector)
                                                 └──► Gemini (embeddings)
```

## 3. User Stories

### 3.1 Entregues por este serviço (dados do projeto)
Todas essas perguntas são respondidas pelo Orquestrador; a Busca precisa entregar os trechos certos. Para validar, façam a pergunta do critério de aceite e confiram as fontes que aparecem na resposta.

| US | Perfil | História | Dado necessário | Critério de aceite |
|---|---|---|---|---|
| 1 | Dev | Quero perguntar ao assistente RAG "Como funciona o serviço de pagamento?", para entender a lógica implementada no projeto | Código do serviço de pagamento (repositório de outro grupo) | Pendente até o grupo liberar o repositório. Até lá, "Como funciona o serviço de Busca?" traz arquivos de `services/busca` |
| 2 | Dev | Quero perguntar ao assistente RAG "Quais bibliotecas de cache são recomendadas para nossa stack?", para aplicar a melhor curadoria arquitetural | `requirements.txt` e `package.json` dos serviços | "Quais bibliotecas de cache são recomendadas para nossa stack?" traz um desses arquivos nas fontes |
| 7 | Dev | Quero perguntar ao assistente RAG sobre métodos HTTP específicos aplicados no projeto, para garantir que minhas rotas RESTful estejam dentro do padrão | Arquivos de rotas dos três serviços | "Quais métodos HTTP o projeto usa?" traz arquivos de rotas nas fontes |
| 45 | Dev | Quero pedir ao RAG para escrever um teste de integração para o endpoint de busca semântica, para garantir que o vetor retornado está correto | Código e testes do endpoint `/v1/search` | "Escreva um teste de integração para o endpoint de busca" traz as rotas da Busca nas fontes |
| 61 | PO | Quero interrogar o assistente RAG sobre a cobertura atual do código em relação aos Épicos definidos, para garantir a entrega de valor | Código e matriz de US e épicos (`docs/microsservicos/README.md`) | "Quais épicos já têm código?" traz a matriz e pelo menos um arquivo de código |
| 64 | PO | Quero usar o chat para gerar resumos executivos das features implementadas na semana, para apresentar nas reuniões de Review | Histórico do git exportado no build (`historico_git.txt`) | "O que foi implementado esta semana?" traz o histórico nas fontes (pode ser cortado) |
| 65 | PO | Quero perguntar ao RAG se as regras de negócio de pagamentos estão blindadas contra fraudes lógicas no código, mitigando riscos financeiros | Código do serviço de pagamento (repositório de outro grupo) | Pendente até o grupo dono do serviço liberar o repositório |
| 66 | PO | Quero que o assistente valide se o fatiamento de histórias (usando metodologias como SPIDR) está coerente com os Épicos cadastrados no sistema | Matriz de US e épicos | "O fatiamento das histórias está coerente com os épicos?" traz a matriz nas fontes |
| 67 | PO | Quero solicitar ao chat ideias de Product Roadmaps a partir das features técnicas entregues, para visualizar os próximos passos da plataforma | Documentos dos serviços e README | "Que roadmap você sugere a partir do que foi entregue?" traz esses documentos nas fontes |
| 68 | PO | Quero consultar o assistente sobre quais User Stories no backlog podem ser simplificadas, para acelerar a entrega do MVP | Backlog de US | Já funciona no MVP; manter o backlog indexado |
| 74 | PO | Quero que o RAG identifique funcionalidades redundantes lendo a documentação gerada pelos desenvolvedores, para enxugar o escopo | Documentos dos serviços | "Existem funcionalidades redundantes?" traz documentos de mais de um serviço |
| 75 | PO | Quero usar o assistente para rascunhar respostas para formulários de submissão do projeto, destacando o valor analítico e técnico da entrega | README, documentos dos serviços e personas exportadas do Miro | "Rascunhe a descrição do projeto para o formulário de submissão" traz README ou documentos nas fontes |
| 76 | PO | Quero solicitar ao RAG que faça uma análise cruzada entre os requisitos iniciais e o que foi de fato codificado, para medir o desvio de escopo | Backlog e código | "O que dos requisitos já foi codificado?" traz o backlog e código nas fontes |
| 89 | PM | Quero perguntar ao assistente como calcular a velocidade da equipe (Velocity) baseado nos commits recentes, para calibrar a capacidade de entrega da próxima semana | Histórico do git | "Qual a velocidade do time pelos commits recentes?" traz o histórico nas fontes (pode ser cortado) |
| 91 | PM | Quero usar o assistente para identificar riscos no cronograma baseados na documentação técnica inserida no projeto | Documentos com cronograma e riscos | "Quais riscos o cronograma tem?" traz o cronograma dos documentos nas fontes |
| 100 | PM | Quero que o RAG me sugira roteiros de demonstração (scripts de apresentação) para o MVP, garantindo que o fluxo técnico seja exibido de forma fluida para os avaliadores | README, documentos dos serviços e matriz de US | "Sugira um roteiro de demonstração do MVP" traz README ou documentos nas fontes |

### 3.2 Participação em outras US e guias técnicos
| US | Perfil | História | Como este serviço participa |
|---|---|---|---|
| 21 | Dev | Quero consultar o assistente sobre como integrar a biblioteca `google-genai` no meu código, para facilitar a orquestração de chamadas de IA | Mesma biblioteca para gerar os embeddings |
| 24 | Dev | Quero entender via chat como funciona o processo de criação de embeddings textuais, para aprimorar o motor de busca semântica do RAG | Embeddings de 768 dimensões com modelo configurável |
| 26 | Dev | Quero consultar o RAG sobre estratégias de chunking (divisão de texto), para garantir que documentos grandes sejam lidos corretamente pela IA | Chunking de 30 linhas com 5 de sobreposição, mantido do MVP |
| 27 | Dev | Quero pedir ao chat métodos para calcular a similaridade de cosseno, para refinar os resultados da busca semântica | Similaridade de cosseno no pgvector (`<=>`) e no TF-IDF |
| 28 | Dev | Quero solicitar ao assistente alternativas de bancos de dados vetoriais compatíveis com Python, para armazenar o conhecimento do repositório | pgvector no PostgreSQL Flexible |
| 29 | Dev | Quero perguntar como isolar as chaves de API da IA generativa no backend, para evitar exposição acidental de credenciais no repositório | Filtro que impede indexar arquivos com segredos |
| 38 | Dev | Quero que o RAG exiba as fontes (trechos de código de onde tirou a informação), para validar a veracidade da resposta | Devolver `source`, `path`, linhas e similaridade de cada trecho |
| 42 | Dev | Quero pedir ao assistente para gerar mocks de dados em formato JSON, para realizar testes unitários na minha API FastAPI | Embedder falso e documentos de exemplo nos testes |
| 45 | Dev | Quero pedir ao RAG para escrever um teste de integração para o endpoint de busca semântica, para garantir que o vetor retornado está correto | O teste de integração de `/v1/search` é um entregável do serviço |
| 49 | Dev | Quero submeter meu código SQL ao RAG para receber sugestões de otimização de índices, acelerando as consultas do sistema | Índice único `(source, path)`; HNSW opcional |
| 50 | Dev | Quero pedir ao assistente dicas de como implementar tratamento global de exceções, para padronizar os retornos de erro da API | Handler global de exceções no formato `{detail, code}` |

## 4. Cards do Épico 7

| Card | Pronto quando |
|---|---|
| Indexar código e documentos | Uma pergunta sobre o código traz arquivo e linhas de `services/` |
| Busca por significado | "Como esconder segredos da aplicação?" traz o trecho sobre `GEMINI_API_KEY`. Hoje o TF-IDF retorna 0 resultados para essa pergunta |
| Fontes configuráveis | Incluir o repositório de outro grupo só exige uma entrada em `fontes.json` e um novo deploy |
| Filtro de segredos | Arquivos `.env` ou com chave privada nunca entram no índice |

## 5. Contrato da API

### `POST /v1/search`

```json
{ "query": "Como esconder segredos da aplicação?", "top_k": 3 }
```

- `query`: de 1 a 4.000 caracteres. O Orquestrador pode juntar a pergunta anterior.
- `top_k`: de 1 a 10, padrão 3.

Resposta 200:

```json
{
  "strategy": "embedding",
  "results": [
    {
      "source": "modulo-7",
      "path": "services/orquestrador/orquestracao_llm/config.py",
      "start_line": 1,
      "end_line": 30,
      "similarity": 0.71,
      "text": "trecho completo"
    }
  ]
}
```

Só voltam resultados acima do limiar de similaridade, do maior para o menor. `text` traz o trecho inteiro; quem corta o pedaço exibido no front é o Orquestrador. Se não houver nada acima do limiar, `results` vem vazio (não é erro).

### `GET /v1/stats`

```json
{ "strategy": "embedding", "documents": 42, "chunks": 380, "sources": ["modulo-7"], "indexed_at": "2026-11-12T10:00:00Z", "indexing": false }
```

### `POST /v1/documents`
Indexa ou atualiza um documento avulso. É usado nos testes e numa futura opção de upload.

```json
{ "source": "modulo-7", "path": "docs/novo.md", "content": "texto do documento" }
```

Resposta: `{"chunks": 4}`.

### `POST /v1/reindex`
Reindexa todas as fontes configuradas.

```json
{ "documents": 42, "embedded_chunks": 12, "skipped_documents": 38, "removed_documents": 0 }
```

Erros: 422 (validação) e 503 com `code: "INDICE_INDISPONIVEL"` quando o banco não responde. O Orquestrador trata o 503 como Busca fora do ar.

## 6. Ingestão

### Fontes
O arquivo `fontes.json` vai na imagem:

```json
[
  { "source": "modulo-7", "path": "conhecimento/modulo-7" }
]
```

Antes do `docker build`, o CI copia para `services/busca/conhecimento/modulo-7/`:
- `services/**`, com os testes (eles ajudam na US 45);
- `contracts/*`, `docs/**/*.md` e `README.md`;
- `docs/produto/`: o backlog (movido de `base_de_conhecimento/`), o guia visual e as personas e épicos exportados do Miro;
- `historico_git.txt`, gerado com `git log --since="4 weeks ago" --date=short --format="%h %ad %an %s" --shortstat`, sem e-mails (este item pode ser cortado).

**Repositório de outro grupo**, quando chegar: o CI roda `git clone --depth 1 --branch <branch> <url> services/busca/conhecimento/modulo-N` e uma entrada `{"source": "modulo-N", ...}` é adicionada a `fontes.json`. Para repositório privado, o token de leitura fica num secret do GitHub. Nenhuma mudança de código é necessária.

### Filtro
- **Extensões aceitas:** as mesmas do MVP ([motor_de_busca.py:10](../../backend/busca_semantica/motor_de_busca.py#L10)).
- **Pastas ignoradas:** `node_modules`, `.git`, `dist`, `.venv`, `__pycache__` e `conhecimento` (para não indexar a si mesma).
- **Arquivos ignorados:** `.env*` (exceto `.env.example`), `*.pem`, `*.key`, `*.pfx`, `*.PublishSettings`, `package-lock.json` e qualquer arquivo acima de 200 KB.
- **Conteúdo suspeito:** arquivos que contêm `-----BEGIN ... PRIVATE KEY-----` ou o padrão `(api[_-]?key|secret|password)\s*[=:]\s*['"]?[A-Za-z0-9_\-]{16,}` ficam de fora. O log registra só o caminho, nunca o conteúdo.

### Processo
Roda em `POST /v1/reindex` e na inicialização, em segundo plano:
1. Calcula o SHA-256 de cada arquivo. Se `(source, path)` já existe com o mesmo hash, pula.
2. Senão, divide em trechos de 30 linhas com 5 de sobreposição (lógica do MVP), gera os embeddings em lotes e troca os trechos daquele documento numa única transação.
3. Documentos que estão no banco mas não estão mais nas fontes são apagados.
4. Atualiza `indexed_at`.

O `path` fica relativo à raiz da fonte, e o `source` vai em campo separado. O front mostra os dois juntos (`modulo-7/services/...`).

### Embeddings

```python
from google import genai
from google.genai import types

client = genai.Client(api_key=settings.gemini_api_key)  # criado uma vez

def embed(textos: list[str], tarefa: str) -> list[list[float]]:
    resposta = client.models.embed_content(
        model=settings.embedding_model,
        contents=textos,
        config=types.EmbedContentConfig(
            task_type=tarefa,  # "RETRIEVAL_DOCUMENT" para trechos, "RETRIEVAL_QUERY" para perguntas
            output_dimensionality=settings.embedding_dimensions,
        ),
    )
    return [e.values for e in resposta.embeddings]
```

- **Modelo:** padrão `gemini-embedding-001` com 768 dimensões. A documentação do Gemini também lista o `gemini-embedding-2`. No D1, testem qual responde com a chave do grupo; a troca é só por variável de ambiente.
- Trocar de modelo ou de dimensão exige reindexação completa (`TRUNCATE` nas duas tabelas).
- Como a busca usa similaridade de cosseno, não é preciso normalizar os vetores.
- **Cota:** os limites gratuitos de embeddings não estão publicados de forma oficial. Usem lotes de 20 textos e, em caso de 429, esperem e tentem de novo. Como o hash pula arquivos sem mudança, só os arquivos alterados consomem cota.

### Fallback com TF-IDF
Sem `GEMINI_API_KEY` (no CI e no desenvolvimento local sem chave), a Busca usa o [motor_de_busca.py](../../backend/busca_semantica/motor_de_busca.py) do MVP em memória e responde com `strategy: "tfidf"`. O contrato é o mesmo. A limitação, que deve constar no relatório, é que essa busca compara palavras, não significado.

### Limiar de similaridade
No D3, calibrem com 10 perguntas e escolham o valor que mantém as do projeto e corta as gerais:
- **Sobre o projeto:** "Como funciona a busca semântica?", "Onde a chave do Gemini é configurada?", "Quais rotas o serviço de conversas expõe?", "Quais User Stories são do PO?" e "Como esconder segredos da aplicação?".
- **Gerais:** "Como resolver conflito de merge no Git?", "O que é Chaos Engineering?", "Como usar um ESP32 com conversor de nível lógico?", "Explique redes de Bravais" e "Daily assíncrona funciona em grupos acadêmicos?".

Pontos de partida: 0,5 para embeddings e 0,1 para TF-IDF.

## 7. Dados (`busca_db`)

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS documents (
  id            SERIAL PRIMARY KEY,
  source        TEXT NOT NULL,
  path          TEXT NOT NULL,
  content_hash  TEXT NOT NULL,
  indexed_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (source, path)
);

CREATE TABLE IF NOT EXISTS chunks (
  id           SERIAL PRIMARY KEY,
  document_id  INT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  start_line   INT NOT NULL,
  end_line     INT NOT NULL,
  text         TEXT NOT NULL,
  embedding    vector(768) NOT NULL
);
```

Consulta de busca (o operador `<=>` é a distância de cosseno):

```sql
SELECT d.source, d.path, c.start_line, c.end_line, c.text,
       1 - (c.embedding <=> %(q)s) AS similarity
FROM chunks c JOIN documents d ON d.id = c.document_id
ORDER BY c.embedding <=> %(q)s
LIMIT %(top_k)s;
```

Usem o pacote `pgvector` (adaptador para psycopg) com `numpy` para passar os vetores. Com poucos milhares de trechos, a busca sem índice é rápida; um índice HNSW é opcional.

## 8. Configuração

| Variável | Exemplo | Observação |
|---|---|---|
| `DATABASE_URL` | `postgresql://mackai:***@localhost:5432/busca_db` | Secret no Azure |
| `GEMINI_API_KEY` | | Chave do Lucas, só como secret no Azure. Localmente, use a sua própria ou rode sem chave. Sem ela, a estratégia é TF-IDF |
| `EMBEDDING_MODEL` | `gemini-embedding-001` | |
| `EMBEDDING_DIMENSIONS` | `768` | Igual ao `vector(768)` do schema |
| `EMBEDDING_BATCH_SIZE` | `20` | |
| `MIN_SIMILARITY_EMBEDDING` | `0.5` | Calibrar no D3 |
| `MIN_SIMILARITY_TFIDF` | `0.1` | Calibrar no D3 |
| `FONTES_FILE` | `fontes.json` | |
| `MAX_FILE_KB` | `200` | |
| `REINDEX_ON_STARTUP` | `true` | |

## 9. Estrutura de pastas

```text
services/busca/
  busca_semantica/
    main.py          # app FastAPI, handler de erros e reindexação na inicialização
    rotas.py         # /v1/*
    modelos.py       # modelos Pydantic (contrato)
    ingestao.py      # fontes, filtro, hash e orquestração da indexação
    chunking.py      # divisão em trechos (do MVP)
    embeddings.py    # cliente do Gemini e embedder falso para testes
    repositorio.py   # SQL com pgvector
    tfidf.py         # fallback (motor_de_busca.py do MVP)
    schema.sql
  conhecimento/      # preenchido pelo CI; entra no .gitignore
  fontes.json
  tests/
  Dockerfile
  requirements.txt
```

## 10. Migração do código atual

| De | Para | Mudança |
|---|---|---|
| [motor_de_busca.py:10-12](../../backend/busca_semantica/motor_de_busca.py#L10-L12) | `ingestao.py` e `chunking.py` | Constantes viram configuração |
| [motor_de_busca.py:14-24](../../backend/busca_semantica/motor_de_busca.py#L14-L24) | `tfidf.py` | Sem mudança |
| [motor_de_busca.py:27-47](../../backend/busca_semantica/motor_de_busca.py#L27-L47) | `chunking.py` | `Chunk` ganha o campo `source` |
| [motor_de_busca.py:50-91](../../backend/busca_semantica/motor_de_busca.py#L50-L91) | `tfidf.py` | Vira a estratégia de fallback |
| `base_de_conhecimento/backlog_user_stories.md` | `docs/produto/` | Passa a entrar pela fonte `modulo-7` |
| `base_de_conhecimento/guia_visual_modulo6.txt` | `docs/produto/` | Idem |
| `base_de_conhecimento/arquitetura_mvp.md` | (removido) | Descreve o monólito. Se continuar indexado, o assistente vai responder com a arquitetura antiga. Esta pasta `docs/microsservicos/` o substitui |
| [test_api.py:15-33](../../backend/tests/test_api.py#L15-L33) | `tests/` | Sem mudança de lógica |

## 11. Testes

| Cenário | Esperado |
|---|---|
| Chunking, cosseno e TF-IDF | Testes atuais do MVP continuam passando |
| `.env` com chave, `.pem`, `package-lock.json` e arquivo de 300 KB na fonte | Nenhum deles entra no índice |
| Segunda ingestão sem mudança | Zero chamadas ao embedder falso |
| Arquivo apagado da fonte | Sai do índice |
| Documento inserido por `/v1/documents` com embedder falso e PostgreSQL real | Aparece em primeiro lugar quando se busca o próprio texto |
| Resultados abaixo do limiar | Não voltam |
| Sem `GEMINI_API_KEY` | `strategy: "tfidf"` |

O **embedder falso** gera vetores determinísticos a partir do texto, para testar pgvector sem gastar cota. O teste de integração do endpoint de busca é, ele próprio, o entregável técnico da US 45.

**Postman:** a coleção cobre `search`, `stats`, `documents` e `reindex`, com testes de status e de campos.

## 12. Deploy
- Container App `mackai-busca`, ingress **interno**, 0,25 vCPU e 0,5 GiB, réplicas de 0 a 1.
- Secrets: `DATABASE_URL` e `GEMINI_API_KEY`.
- A reindexação da inicialização roda em segundo plano: `/health` responde na hora, e `/v1/search` usa o que já está no banco enquanto isso.
- **Cota em produção:** os embeddings usam a mesma chave do Orquestrador, então a reindexação completa consome a cota que também atende as respostas. Evitem reindexar tudo perto da apresentação.
- **PostgreSQL:** o Lucas cria o servidor. O Danilo inclui `VECTOR` no parâmetro `azure.extensions` e roda o `schema.sql` no `busca_db`; o nome da extensão no `CREATE EXTENSION` é `vector`.

## 13. Cronograma do Danilo

| Dia | Entrega |
|---|---|
| D1 | Modelos e OpenAPI; mover a base para `docs/produto/`; exportar personas e épicos do Miro; retirar `arquitetura_mvp.md` |
| D2 | Schema com pgvector, ingestão (fontes, filtro, hash e chunking) e embeddings |
| D3 | `/v1/search`, fallback TF-IDF, calibração do limiar e testes |
| D4 | Integração; passo do CI que copia o conhecimento (junto com o Lucas) |
| D5 | Deploy, extensão `vector` no Azure e reindexação |
| D6 | Seção do relatório |
| D7 | Ensaio; incluir por configuração os repositórios de outros grupos que tiverem chegado |

## 14. Fora do escopo e riscos
- **Riscos:**
  - Cota de embeddings, mitigada com lotes, nova tentativa e hash.
  - Modelo de embedding indisponível para a chave, mitigado com o teste no D1.
  - US 1 e 65 continuam pendentes até o grupo dono do serviço de pagamento liberar o repositório.
- **Fora desta entrega:** upload de documentos pelo front, busca híbrida (palavras e significado juntos) e filtro por módulo na pergunta.

## 15. Roteiro da seção no relatório
1. Por que a busca é por significado (embeddings) e o que muda em relação ao TF-IDF, com o exemplo "Como esconder segredos da aplicação?".
2. Pipeline de ingestão: fontes, filtro de segredos, hash, chunking e pgvector.
3. Contrato e modelo de dados.
4. US de dados do projeto atendidas e as que dependem de outros grupos.
5. Limitações: cota, fallback por palavras e fontes ainda não conectadas.
