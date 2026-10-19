import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from busca_semantica.motor_de_busca import KnowledgeBase
from orquestracao_llm import gemini

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
KNOWLEDGE_DIR = Path(os.getenv("KNOWLEDGE_DIR", BASE_DIR / "busca_semantica" / "base_de_conhecimento"))
FEEDBACK_FILE = Path(os.getenv("FEEDBACK_FILE", BASE_DIR / "data" / "feedback.jsonl"))
FRONTEND_DIR = BASE_DIR / "frontend_dist"

# 1º CRIAR A APLICAÇÃO ANTES DE QUALQUER MIDDLEWARE
app = FastAPI(title="MackAI - Módulo 7")

# A URL exata do seu front (sem a barra / no final) e o localhost para testes
origens_permitidas = [
    "http://localhost:5173",
    "https://mvp-modulo7-front-ahgzdygpbmahapc0.brazilsouth-01.azurewebsites.net"
]

# 2º ADICIONAR O CORS À APP CRIADA ACIMA
app.add_middleware(
    CORSMiddleware,
    allow_origins=origens_permitidas,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

knowledge = KnowledgeBase(KNOWLEDGE_DIR)
knowledge.load()
indexed_at = datetime.now(timezone.utc)

# Conversas ficam em memória enquanto o servidor estiver rodando.
conversations: dict[str, dict] = {}


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    conversation_id: str | None = None
    profile: str = "Desenvolvedor"
    temperature: float = Field(default=0.4, ge=0, le=2)


class FeedbackRequest(BaseModel):
    message_id: str
    value: Literal["up", "down"] | None


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_conversation() -> dict:
    conversation = {"id": str(uuid.uuid4()), "title": "Nova conversa", "created_at": now(), "messages": []}
    conversations[conversation["id"]] = conversation
    return conversation


def summary(conversation: dict) -> dict:
    return {k: conversation[k] for k in ("id", "title", "created_at")}


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "llm": "gemini" if gemini.is_enabled() else "offline",
        "documents": knowledge.documents,
        "chunks": len(knowledge.chunks),
        "indexed_at": indexed_at.isoformat(),
    }


@app.get("/api/conversations")
def list_conversations():
    items = sorted(conversations.values(), key=lambda c: c["created_at"], reverse=True)
    return [summary(c) for c in items if c["messages"]]


@app.post("/api/conversations")
def create_conversation():
    return summary(new_conversation())


@app.get("/api/conversations/{conversation_id}")
def get_conversation(conversation_id: str):
    if conversation_id not in conversations:
        raise HTTPException(404, "Conversa não encontrada")
    return conversations[conversation_id]


@app.post("/api/chat")
def chat(request: ChatRequest):
    conversation = conversations.get(request.conversation_id or "") or new_conversation()
    history = [{"role": m["role"], "content": m["content"]} for m in conversation["messages"]]

    question = request.message.strip()
    conversation["messages"].append({"id": str(uuid.uuid4()), "role": "user", "content": question, "created_at": now()})
    if conversation["title"] == "Nova conversa":
        conversation["title"] = question[:60]

    results = knowledge.search(question)
    answer = {
        "id": str(uuid.uuid4()),
        "role": "assistant",
        "content": gemini.generate_answer(question, request.profile, request.temperature, results, history),
        "sources": [
            {"path": c.path, "start_line": c.start_line, "end_line": c.end_line,
             "similarity": round(score, 2), "excerpt": c.text[:300]}
            for c, score in results
        ],
        "feedback": None,
        "created_at": now(),
    }
    conversation["messages"].append(answer)
    return {"conversation_id": conversation["id"], "message": answer}


@app.post("/api/feedback")
def feedback(request: FeedbackRequest):
    for conversation in conversations.values():
        for message in conversation["messages"]:
            if message["id"] == request.message_id and message["role"] == "assistant":
                message["feedback"] = request.value
                FEEDBACK_FILE.parent.mkdir(parents=True, exist_ok=True)
                with FEEDBACK_FILE.open("a", encoding="utf-8") as f:
                    f.write(json.dumps({"message_id": request.message_id, "value": request.value,
                                        "answer": message["content"], "created_at": now()}, ensure_ascii=False) + "\n")
                return {"ok": True}
    raise HTTPException(404, "Mensagem não encontrada")


# Em produção (Azure), o mesmo servidor entrega o frontend compilado. Fica por último para não cobrir as rotas /api.
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
