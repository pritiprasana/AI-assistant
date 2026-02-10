# Architecture Overview

## System Design

Flair Assistant is a multi-tier application combining a RAG (Retrieval-Augmented Generation) system with local LLM inference for codebase-specific Q&A.

## High-Level Architecture

```
┌─────────────────┐
│   User Layer    │
├─────────────────┤
│  Web UI / VSCode│──┐
└─────────────────┘  │
                     │ HTTP
                     ▼
┌──────────────────────────────────┐
│      FastAPI Server              │
│  - /chat endpoint                │
│  - /rag/status endpoint          │
│  - CORS middleware               │
└──────────────────────────────────┘
         │                    │
         │ Query             │ Generate
         ▼                    ▼
┌─────────────────┐    ┌──────────────┐
│  Vector Store   │    │  MLX LLM     │
│  (ChromaDB)     │    │  (Qwen2.5)   │
│                 │    │              │
│ - Embeddings    │    │ - Inference  │
│ - Similarity    │    │ - Citations  │
└─────────────────┘    └──────────────┘
         ▲
         │ Ingest
         │
┌─────────────────┐
│  AST Parser     │
│  - TypeScript   │
│  - JavaScript   │
│  - Python       │
└─────────────────┘
         ▲
         │
┌─────────────────┐
│  Your Codebase  │
└─────────────────┘
```

## Components

### 1. Frontend Layer

#### Web UI (`web-ui/`)
- **Technology**: React 18 + TypeScript + Vite
- **Styling**: Tailwind CSS v4
- **State**: React hooks + localStorage
- **Components**:
  - `Header`: Mode toggle (General/Flair), branding
  - `ChatContainer`: Message history display
  - `MessageBubble`: Individual message with source citations
  - `CodeBlock`: Syntax-highlighted code with copy button
  - `InputArea`: Message input and submission

#### VS Code Extension (`vscode-extension/`)
- **Technology**: TypeScript + VS Code API
- **Features**:
  - Sidebar chat interface
  - Context menu integration
  - Webview for UI rendering

### 2. API Layer

#### FastAPI Server (`src/slot_assistant/api/server.py`)
- **Framework**: FastAPI
- **Endpoints**:
  - `POST /chat`: Main chat endpoint with RAG
  - `GET /rag/status`: Vector store status and document count
  - `GET /health`: Health check
  
- **CORS**: Configured for `localhost:5173` (Web UI)

**Request Flow**:
1. Receive user message
2. Query vector store (if RAG enabled)
3. Retrieve top-N code chunks
4. Deduplicate chunks
5. Build context string with code
6. Send to LLM for generation
7. Return response + source metadata

### 3. RAG System

#### Vector Store (`src/slot_assistant/rag/store.py`)
- **Database**: ChromaDB (persistent, local)
- **Embedding Model**: `sentence-transformers/all-mpnet-base-v2`
  - Dimensions: 768
  - Max sequence length: 384 tokens
  - Good for code and technical text

**Operations**:
- `query()`: Semantic search, returns top-N chunks
- `add_documents()`: Index new chunks
- `count()`: Get total documents

#### AST Loader (`src/slot_assistant/rag/ast_loader.py`)
- **Parsers**:
  - TypeScript/JavaScript: `tree-sitter-typescript`
  - Python: `tree-sitter-python`

**Chunking Strategy**:
- Extract: classes, functions, methods
- Metadata: filename, class name, line numbers
- Node type: for filtering/prioritization

#### Directory Loader (`src/slot_assistant/rag/loader.py`)
- **Recursive scanning**: `rglob` pattern
- **Exclusions**: `node_modules`, `.git`, `dist`, `build`
- **AST fallback**: Plain text if AST parsing fails

### 4. LLM Layer

#### MLX Integration (`src/slot_assistant/cli/main.py`)
- **Model**: `mlx-community/Qwen2.5-Coder-7B-Instruct-4bit`
  - 4-bit quantized for efficiency
  - Code-specialized (trained on code)
  - Apple Silicon optimized (MLX framework)

**System Prompt**:
- Enforce strict context adherence
- Require file/line citations
- Mandate analysis of ALL retrieved files
- Explain component relationships

**Generation**:
- Temperature: Model default
- Max tokens: Configurable
- Streaming: Not currently implemented

## Data Flow

### Indexing Flow
```
Codebase Files
    ↓
DirectoryLoader (filter, recursive)
    ↓
ASTCodeLoader (parse, chunk by function/class)
    ↓
Document chunks with metadata
    ↓
Text Splitter (512 chars, 50 overlap)
    ↓
Embedding Model (all-mpnet-base-v2)
    ↓
ChromaDB Vector Store (persist to disk)
```

### Query Flow
```
User Query
    ↓
Embedding Model (convert query to vector)
    ↓
Vector Store Similarity Search (cosine)
    ↓
Top-10 chunks retrieved
    ↓
Deduplication (by filename+name+lines)
    ↓
Context String Construction
    ↓
LLM Prompt (system + context + query)
    ↓
MLX Inference (generate response)
    ↓
Response + Source Metadata
    ↓
UI Display (with expandable sources)
```

## Key Design Decisions

### 1. **Local-First**
- All inference runs locally (no API calls)
- Data never leaves the machine
- Works offline
- **Trade-off**: Requires Apple Silicon, slower than cloud APIs

### 2. **AST-Aware Chunking**
- Semantic units (classes, functions) stay together
- Better retrieval quality vs. arbitrary splits
- **Trade-off**: More complex, slower indexing

### 3. **Deduplication**
- Same code chunk may match multiple times
- Remove duplicates to save context window
- **Trade-off**: Slightly more complex logic

### 4. **Hybrid Architecture**
- Web UI for new users (visual, accessible)
- VS Code extension for developers (integrated)
- CLI for automation/scripting
- **Trade-off**: Maintain 3 interfaces

### 5. **Embedding Model Choice**
- `all-mpnet-base-v2` vs. `all-MiniLM-L6-v2`
- 768-dim vs. 384-dim (better accuracy)
- Larger model size but worth it for quality
- **Trade-off**: 2x slower embedding, 2x storage

## Performance Characteristics

### Indexing
- **Speed**: ~50-100 files/second (depends on file size)
- **Storage**: ~10MB per 1000 code chunks
- **Bottleneck**: AST parsing + embedding generation

### Query
- **Latency**: 
  - Retrieval: ~50-100ms
  - LLM generation: 2-5 seconds (depends on response length)
- **Bottleneck**: LLM inference (can't parallelize within response)

### Scalability
- **Max codebase size**: Tested up to 10K files
- **Vector DB size**: Scales linearly with chunks
- **Memory**: ~2-4GB for model + embeddings

## Security Considerations

1. **No external calls**: All data stays local
2. **CORS restriction**: Only localhost origins allowed
3. **No authentication**: Assumes trusted local environment
4. **File system access**: Can read any file in CODEBASE_PATH

## Future Improvements

1. **Hybrid Search**: Add BM25 keyword matching for exact matches
2. **Reranking**: Cross-encoder model to improve top-N quality
3. **Incremental Indexing**: Only re-index changed files
4. **Streaming**: Stream LLM responses for faster perceived latency
5. **Multi-language**: Better support for more languages (Java, Go, Rust)
