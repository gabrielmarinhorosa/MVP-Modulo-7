# MVP Módulo 7 – MackAI (Assistente RAG)

Assistente conversacional com busca semântica (RAG) sobre o código, a documentação e o backlog do projeto, com orquestração de chamadas ao LLM (Gemini).

- **Backend:** Python + FastAPI (`backend/`)
- **Frontend:** React + TypeScript + Vite (`frontend/`), baseado no protótipo do Figma e no Guia de Identidade Visual do Módulo 6 (`frontend/src/identidade_visual/tokens.css`)

Detalhes da arquitetura e dos endpoints: [`backend/busca_semantica/base_de_conhecimento/arquitetura_mvp.md`](backend/busca_semantica/base_de_conhecimento/arquitetura_mvp.md).

## Arquitetura (Screaming Architecture)
As pastas são organizadas pelas capacidades do Módulo 7, e não por camadas técnicas. Só de olhar a estrutura dá para saber o que o sistema faz:

```
backend/
├── assistente_conversacional/   # Assistente conversacional via RAG: API de chat, conversas e feedback
│   └── api.py
├── busca_semantica/             # Mecanismo de busca semântica: chunking, embeddings e similaridade
│   ├── motor_de_busca.py
│   └── base_de_conhecimento/    # Documentos indexados pelo RAG
├── orquestracao_llm/            # Orquestração de chamadas ao LLM (Gemini) e modo offline
│   └── gemini.py
└── tests/

frontend/src/
├── main.tsx                     # Ponto de entrada
├── assistente_conversacional/   # Tela do chat, cliente da API e estilos
│   ├── AssistenteConversacional.tsx
│   ├── api.ts
│   └── assistente.css
└── identidade_visual/           # Tokens do Guia de Identidade Visual (Módulo 6)
    └── tokens.css
```

Regra de dependência: `assistente_conversacional` usa `busca_semantica` e `orquestracao_llm`; `orquestracao_llm` usa apenas `busca_semantica`; `busca_semantica` não depende de nenhuma outra pasta.

## Como rodar

Pré-requisitos: Python 3.11+ e Node 18+.

### 1. Backend (porta 8000)
```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # coloque sua GEMINI_API_KEY (opcional)
uvicorn assistente_conversacional.api:app --reload
```
Sem `GEMINI_API_KEY`, o assistente roda em **modo offline**: faz a busca semântica e devolve os trechos mais relevantes, sem gerar texto com IA.

### 2. Frontend (porta 5173)
```bash
cd frontend
npm install
npm run dev
```
Acesse http://localhost:5173.

### Testes do backend
```bash
cd backend
pip install -r requirements-dev.txt
pytest
```

## Deploy no Azure (plano gratuito)
Um único App Service no plano **Free F1** roda o backend e entrega o frontend compilado. O deploy é automático a cada push na `main`, pelo workflow `.github/workflows/deploy-azure.yml` (roda os testes, compila o frontend e publica).

### 1. Ativar a conta de estudante
Acesse https://azure.microsoft.com/free/students e entre com o e-mail da faculdade. Não precisa de cartão de crédito.

### 2. Criar o App Service
No portal (https://portal.azure.com): **Criar um recurso → Aplicativo Web** (*Web App*).

| Campo | Valor |
|---|---|
| Assinatura | Azure for Students |
| Grupo de recursos | Criar novo, ex.: `mackai-rg` |
| Nome | ex.: `mackai-modulo7` (anote, vai para o GitHub) |
| Publicar | Código |
| Pilha de runtime | Python 3.12 |
| Sistema operacional | Linux |
| Região | Brazil South (se aparecer erro de política, escolha outra região da lista) |
| Plano de preços | **Free F1** |

Na aba **Implantação** (*Deployment*): deixe a implantação contínua do GitHub Actions **desabilitada** (o workflow já está no repositório) e a **Autenticação básica** (*Basic authentication*) **habilitada**. Depois: **Revisar + criar → Criar**.

### 3. Configurar o App Service
Abra o app criado:

1. **Configurações → Variáveis de ambiente** (*Environment variables*) → adicione e clique em **Aplicar**:

   | Nome | Valor |
   |---|---|
   | `SCM_DO_BUILD_DURING_DEPLOYMENT` | `true` (obrigatória: faz o Azure instalar o `requirements.txt`) |
   | `FEEDBACK_FILE` | `/home/data/feedback.jsonl` (mantém os feedbacks entre reinícios) |
   | `GEMINI_API_KEY` | sua chave do Gemini (opcional: sem ela o assistente roda em modo offline) |

2. **Configurações → Configuração → Configurações gerais** (*General settings*) → **Comando de inicialização** (*Startup Command*) → **Salvar**:
   ```
   python -m uvicorn assistente_conversacional.api:app --host 0.0.0.0 --port 8000
   ```
3. **Visão geral** (*Overview*) → **Baixar perfil de publicação** (*Download publish profile*). Se o botão estiver desativado, ligue **Credenciais de publicação de Autenticação Básica do SCM** em *Configurações gerais* e salve. Esse arquivo é uma credencial: nunca faça commit dele.

### 4. Configurar o GitHub
No repositório: **Settings → Secrets and variables → Actions**.

- Aba **Secrets → New repository secret**: nome `AZURE_WEBAPP_PUBLISH_PROFILE`, valor = todo o conteúdo do arquivo `.PublishSettings` baixado.
- Aba **Variables → New repository variable**: nome `AZURE_WEBAPP_NAME`, valor = nome do App Service (ex.: `mackai-modulo7`).

### 5. Publicar
Faça push ou merge na `main`, ou rode manualmente em **Actions → Deploy no Azure → Run workflow**. Quando o workflow ficar verde, abra o endereço que aparece em **Visão geral → Domínio padrão** (*Default domain*).

**Limites do plano gratuito F1:** 60 minutos de CPU por dia e 1 GB de RAM. O app "dorme" depois de cerca de 20 minutos sem acesso, então o primeiro acesso seguinte demora alguns segundos. As conversas ficam em memória e se perdem quando o app reinicia.

## Base de conhecimento
Os arquivos de `backend/busca_semantica/base_de_conhecimento/` são indexados quando o backend inicia. Para o assistente responder sobre o código e a documentação de vocês, copie os arquivos (`.md`, `.txt`, `.py`, `.ts`, `.tsx`, `.sql`...) para essa pasta e reinicie o backend.

## User Stories atendidas
| Funcionalidade | US |
|---|---|
| Perguntas ao assistente RAG sobre código, arquitetura, backlog etc., com perfil Desenvolvedor / PO / PM | 1–30, 41–100 |
| Busca semântica com chunking, embeddings (TF-IDF) e similaridade de cosseno | 24, 26, 27 |
| Integração com `google-genai` / `gemini-2.5-flash` | 21, 22 |
| Chave de API isolada no backend (`.env`) | 29 |
| Ajuste de temperatura do LLM | 30 |
| Blocos de código com syntax highlighting | 31 |
| Botão "Copiar código" | 32 |
| Renderização de markdown (tabelas, listas) | 33 |
| Indicador "IA digitando..." | 34 |
| Feedback útil / não útil (salvo em `backend/data/feedback.jsonl`) | 35 |
| Histórico da conversa mantido e enviado como contexto | 36 |
| Nova conversa | 37 |
| Fontes consultadas com trecho e similaridade | 38 |
| Entrada de textos longos (stack traces, logs) | 39 |
| Modo escuro | 40 |
| Mensagem amigável quando o LLM falha | 80 |

## Fluxo de branches
- `main` – versão estável. Não faça commits diretos.
- `develop` – integração do time. Crie sua branch a partir dela (`feature/minha-mudanca`) e abra Pull Request para `develop`.
- Quando `develop` estiver estável, abra Pull Request de `develop` para `main`.
