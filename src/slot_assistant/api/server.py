"""
FastAPI server for Flair Assistant.

This module provides the REST API for the RAG-powered codebase assistant.
It handles chat requests, retrieves relevant code from the vector store,
and integrates with the MLX-based LLM for response generation.

Key endpoints:
- POST /chat: Main chat endpoint with optional RAG retrieval
- GET /rag/status: Check vector store indexing status
- GET /health: Simple health check

The server uses CORS middleware to allow requests from the React web UI.
"""

from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from slot_assistant.cli.main import get_llm_response
from slot_assistant.rag.store import VectorStore

# Initialize FastAPI app with metadata
app = FastAPI(
    title="Flair Assistant API",
    description="API for the Slot Game Framework AI Assistant with RAG",
    version="0.1.0",
)

# Add CORS middleware to allow web UI requests from localhost:5173
# This permits the React frontend to call the API from a different port
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)


class ChatRequest(BaseModel):
    """
    Request model for chat endpoint.
    
    Attributes:
        message: User's query (e.g., "How does GamePlayIntro work?")
        context: Optional additional context (e.g., copy from IDE selection)
        use_rag: Whether to retrieve code from vector store (True for "Flair" mode)
    """
    message: str
    context: Optional[str] = None
    use_rag: bool = True


class ChatResponse(BaseModel):
    """
    Response model for chat endpoint.
    
    Attributes:
        response: LLM-generated answer
        context_used: Full context string sent to LLM (for debugging)
        sources: List of source file metadata (filename, lines) for UI display
    """
    response: str
    context_used: Optional[str] = None
    sources: list[dict] = []  # List of {"filename": str, "name": str, "lines": str}


@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring.
    
    Returns:
        Simple {"status": "ok"} response
    """
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint with RAG retrieval and LLM generation.
    
    Flow:
    1. Build context from user-provided context (if any)
    2. If RAG enabled, query vector store for relevant code chunks
    3. Deduplicate retrieved chunks to avoid sending duplicate code to LLM
    4. Build formatted context string with all unique chunks
    5. Call LLM with context + user query
    6. Return response with source metadata for UI
    
    Args:
        request: ChatRequest with message, optional context, and RAG flag
    
    Returns:
        ChatResponse with LLM answer, context used, and source metadata
    
    Raises:
        HTTPException: If LLM inference fails or other error occurs
    """
    context = ""
    results = None  # Store RAG results for later source extraction
    
    # 1. User-provided context (e.g., code selection from IDE)
    if request.context:
        context += f"Context provided:\n```\n{request.context}\n```\n\n"
    
    # 2. RAG Context: Retrieve relevant code from vector store
    if request.use_rag:
        try:
            store = VectorStore()
            
            # Only query if we have indexed documents
            if store.count() > 0:
                # Query vector store for semantically similar code chunks
                # Returns top-10 chunks with highest cosine similarity to query
                results = store.collection.query(
                    query_texts=[request.message],
                    n_results=10,  # Retrieve more to ensure good coverage
                    include=['documents', 'metadatas']  # Include both code and metadata
                )
                
                if results and results.get('documents') and results['documents'][0]:
                    docs = results['documents'][0]
                    metas = results.get('metadatas', [[]])[0]
                    
                    # Deduplicate chunks to avoid sending same code multiple times
                    # Problem: Same file may match query multiple times due to vector search
                    # Solution: Track unique (filename, name, start_line, end_line) tuples
                    seen = set()
                    unique_pairs = []
                    for doc, meta in zip(docs, metas):
                        if meta:
                            # Create unique key for this chunk
                            key = (meta.get('filename'), meta.get('name'), 
                                  meta.get('start_line'), meta.get('end_line'))
                            if key not in seen:
                                seen.add(key)
                                unique_pairs.append((doc, meta))
                    
                    # Build context header with count (for LLM awareness)
                    context += f"\n\n=== {len(unique_pairs)} UNIQUE CODE CHUNKS ===\n"
                    
                    # Add each unique code chunk with metadata
                    for i, (doc, meta) in enumerate(unique_pairs):
                        # Build source info header (filename::class_name or just filename)
                        source_info = ""
                        if meta:
                            if meta.get('name') and meta.get('name') != 'anonymous':
                                source_info = f"[{meta.get('filename', 'unknown')}::{meta.get('name')}]"
                            else:
                                source_info = f"[{meta.get('filename', 'unknown')}]"
                        
                        # Add formatted chunk to context
                        context += f"\n--- Code Chunk {i+1} {source_info} ---\n{doc}\n"
                    
                    # Add footer instructing LLM to use all files
                    context += "\n" + "="*60 + "\n"
                    context += "END - YOU MUST USE ALL FILES ABOVE IN YOUR ANSWER\n"
                    context += "="*60 + "\n\n"
                    
        except Exception as e:
            # Log error but continue without RAG (fallback to LLM's general knowledge)
            print(f"RAG Error: {e}")
    
    try:
        # 3. Generate response using LLM with context
        response = get_llm_response(request.message, context)
        
        # 4. Extract sources for UI display (deduplicated)
        sources = []
        if request.use_rag and results and results.get('metadatas'):
            seen = set()  # Track which sources we've already added
            
            for meta in results['metadatas'][0]:
                if meta:
                    # Create unique key (same as context deduplication)
                    key = (meta.get('filename'), meta.get('name'), 
                          meta.get('start_line'), meta.get('end_line'))
                    
                    # Skip if we've already added this source
                    if key in seen:
                        continue
                    
                    seen.add(key)
                    
                    # Build source object for UI
                    source = {
                        'filename': meta.get('filename', 'unknown'),
                        'name': meta.get('name'),
                        'nodeType': meta.get('node_type'),
                        'lines': f"{meta.get('start_line')}-{meta.get('end_line')}" if meta.get('start_line') else None
                    }
                    sources.append(source)
        
        return ChatResponse(
            response=response,
            context_used=context,  # For debugging/transparency
            sources=sources  # For UI source panel
        )
        
    except Exception as e:
        # Return 500 error if LLM inference fails
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/rag/status")
async def rag_status():
    """
    Check RAG vector store status and document count.
    
    Useful for verifying that indexing completed successfully and 
    monitoring the size of the indexed codebase.
    
    Returns:
        Dictionary with:
        - status: "ok" or "error"
        - indexed_documents: Number of chunks in vector store
        - detail: Error message if status is "error"
    
    Example:
        >>> curl http://localhost:8000/rag/status
        {"status": "ok", "indexed_documents": 6230}
    """
    try:
        store = VectorStore()
        count = store.count()
        return {
            "status": "ok",
            "indexed_documents": count
        }
    except Exception as e:
        return {
            "status": "error",
            "detail": str(e)
        }
