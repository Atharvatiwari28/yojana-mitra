"""
main.py - Yojana Mitra API 🚀🇮🇳

Chalao (yojana-mitra folder mein, venv on karke):
    python -m uvicorn main:app --reload --port 8001

Docs: http://127.0.0.1:8001/docs
(Port 8001 kyunki 8000 pe tumhara Swiggy API chal sakta hai 😉)
"""

import os
from typing import Literal

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

import rag

load_dotenv()

# 📋 CORS guest list: kaun-kaun se frontend is API ko call kar sakte hain
# Local pe default list chalegi. Live hone par .env / server settings mein
# ALLOWED_ORIGINS=https://tumhara-frontend.vercel.app daal denge.
DEFAULT_ORIGINS = "http://localhost:5500,http://127.0.0.1:5500"
ALLOWED_ORIGINS = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", DEFAULT_ORIGINS).split(",")]


# ---------------------------------------------------------------------------
# 📝 Forms (Pydantic): API ka "contract", kya aayega aur kya jayega
# ---------------------------------------------------------------------------
class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class AskRequest(BaseModel):
    question: str = Field(min_length=2, max_length=500)
    history: list[ChatMessage] = []


class Source(BaseModel):
    pdf: str
    pages: list[int]


class AskResponse(BaseModel):
    answer: str
    evidence: str
    search_question: str
    sources: list[Source]


# ---------------------------------------------------------------------------
# 🚀 App
# ---------------------------------------------------------------------------
app = FastAPI(title="Yojana Mitra API 🇮🇳")

# 🚧 CORS: browser (security guard 👮) ko batao ki guest list mein kaun hai
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,   # ⚠️ production mein kabhi ["*"] mat karna
    allow_methods=["GET", "POST"],   # sirf yahi do methods chahiye
    allow_headers=["Content-Type"],  # JSON bhejne ke liye itna kaafi
)


@app.get("/")
def home():
    return {"message": "Namaste! Main Yojana Mitra hoon 🇮🇳. POST /ask pe sawaal bhejo."}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest):
    history = [m.model_dump() for m in req.history]
    result = rag.answer(req.question, history)

    # Same PDF ke pages ek jagah jodo (duplicate sources na dikhein)
    pages_by_pdf: dict[str, set[int]] = {}
    for c in result["chunks"]:
        pages_by_pdf.setdefault(c["source"], set()).update(c["pages"])
    sources = [Source(pdf=pdf, pages=sorted(pages)) for pdf, pages in pages_by_pdf.items()]

    return AskResponse(
        answer=result["answer"],
        evidence=result["evidence"],
        search_question=result["search_question"],
        sources=sources,
    )