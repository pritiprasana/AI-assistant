"""
FastAPI server for Flair Assistant.

Endpoints:
- POST /chat: Main chat endpoint with optional RAG retrieval
- GET /rag/status: Check vector store indexing status
- GET /health: Simple health check
"""

from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from slot_assistant.cli.main import get_llm_response
from slot_assistant.rag.store import VectorStore

app = FastAPI(
    title="Flair Assistant API",
    description="API for the Slot Game Framework AI Assistant with RAG",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Singleton vector store — initialized once, reused across requests
_store: Optional[VectorStore] = None


def _get_store() -> VectorStore:
    global _store
    if _store is None:
        _store = VectorStore()
    return _store


class ChatRequest(BaseModel):
    message: str
    context: Optional[str] = None
    use_rag: bool = True


class ChatResponse(BaseModel):
    response: str
    context_used: Optional[str] = None
    sources: list[dict] = []


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Main chat endpoint with RAG retrieval and LLM generation."""
    context = ""
    rag_results = []

    # 1. User-provided context (e.g., code selection from IDE)
    if request.context:
        context += f"Context provided:\n```\n{request.context}\n```\n\n"

    # 2. RAG Context: Retrieve relevant code from vector store
    if request.use_rag:
        try:
            store = _get_store()

            if store.count() > 0:
                rag_results = store.query(request.message, n_results=10)

                if rag_results:
                    # Deduplicate by (filename, name, start_line)
                    seen = set()
                    unique = []
                    for r in rag_results:
                        meta = r["metadata"]
                        key = (
                            meta.get('filename'),
                            meta.get('name'),
                            meta.get('start_line'),
                        )
                        if key not in seen:
                            seen.add(key)
                            unique.append(r)

                    context += f"\n\n=== {len(unique)} RELEVANT CODE CHUNKS ===\n"

                    for i, r in enumerate(unique):
                        meta = r["metadata"]
                        source_info = ""
                        if meta.get('name') and meta.get('name') != 'anonymous':
                            source_info = f"[{meta.get('filename', 'unknown')}::{meta.get('name')}]"
                        else:
                            source_info = f"[{meta.get('filename', 'unknown')}]"

                        context += f"\n--- Chunk {i+1} {source_info} ---\n{r['content']}\n"

                    context += "\n" + "=" * 60 + "\n"

        except Exception as e:
            print(f"RAG Error: {e}")

    try:
        # 3. Generate response using LLM with context
        response = get_llm_response(request.message, context)

        # 4. Extract sources for UI display (deduplicated)
        sources = []
        seen = set()
        for r in rag_results:
            meta = r["metadata"]
            key = (meta.get('filename'), meta.get('name'), meta.get('start_line'))
            if key in seen:
                continue
            seen.add(key)
            sources.append({
                'filename': meta.get('filename', 'unknown'),
                'name': meta.get('name'),
                'nodeType': meta.get('node_type'),
                'lines': (
                    f"{meta.get('start_line')}-{meta.get('end_line')}"
                    if meta.get('start_line')
                    else None
                ),
            })

        return ChatResponse(
            response=response,
            context_used=context,
            sources=sources,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/rag/status")
async def rag_status():
    """Check RAG vector store status and document count."""
    try:
        store = _get_store()
        count = store.count()
        return {"status": "ok", "indexed_documents": count}
    except Exception as e:
        return {"status": "error", "detail": str(e)}
