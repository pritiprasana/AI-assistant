# Configuration Guide

## Environment Variables

All configuration is done through environment variables in `.env` file.

### Quick Setup

```bash
cp .env.example .env
# Edit .env to customize settings
```

## Variables Reference

### LLM Configuration

#### `SLOT_ASSISTANT_MODEL`
- **Description**: MLX model identifier (HuggingFace format)
- **Default**: `mlx-community/Qwen2.5-Coder-7B-Instruct-4bit`
- **Options**:
  - `mlx-community/Qwen2.5-Coder-7B-Instruct-4bit` (recommended)
  - `mlx-community/Qwen2.5-Coder-14B-Instruct-4bit` (more capable, slower)
  - `mlx-community/Qwen2.5-Coder-3B-Instruct-4bit` (faster, less capable)
- **Impact**: Model size affects quality and speed

**Example**:
```bash
SLOT_ASSISTANT_MODEL=mlx-community/Qwen2.5-Coder-7B-Instruct-4bit
```

### RAG Configuration

#### `CHROMA_PERSIST_DIR`
- **Description**: Vector database storage location
- **Default**: `./data/chroma`
- **Impact**: Where embeddings are stored
- **Note**: Delete this directory to reset the index

**Example**:
```bash
CHROMA_PERSIST_DIR=./data/chroma
```

#### `EMBEDDING_MODEL`
- **Description**: Sentence transformer model for embeddings
- **Default**: `sentence-transformers/all-mpnet-base-v2`
- **Options**:
  - `sentence-transformers/all-mpnet-base-v2` (recommended, 768-dim)
  - `sentence-transformers/all-MiniLM-L6-v2` (faster, 384-dim, lower quality)
- **Impact**: Quality of semantic search
- **Note**: Changing this requires re-indexing (`--force`)

**Example**:
```bash
EMBEDDING_MODEL=sentence-transformers/all-mpnet-base-v2
```

### API Configuration

#### `API_HOST`
- **Description**: API server bind address
- **Default**: `0.0.0.0`
- **Options**:
  - `0.0.0.0`: Accessible from all interfaces
  - `127.0.0.1`: Local only
- **Impact**: Network accessibility

**Example**:
```bash
API_HOST=0.0.0.0
```

#### `API_PORT`
- **Description**: API server port
- **Default**: `8000`
- **Impact**: Where server listens
- **Note**: Must match `VITE_API_URL` in web-ui/.env

**Example**:
```bash
API_PORT=8000
```

### Codebase Paths

#### `CODEBASE_PATH`
- **Description**: Path to codebase to index
- **Default**: `./data/raw/codebase`
- **Impact**: What code is indexed for RAG
- **Note**: Can be absolute or relative path

**Example**:
```bash
# Absolute path (recommended)
CODEBASE_PATH=/Users/yourname/projects/my-codebase

# Relative path
CODEBASE_PATH=./data/raw/codebase
```

#### `DOCS_PATH`
- **Description**: Path to documentation files
- **Default**: `./data/raw/docs`
- **Impact**: Additional context for RAG
- **Note**: Currently optional

**Example**:
```bash
DOCS_PATH=./data/raw/docs
```

### Logging

#### `LOG_LEVEL`
- **Description**: Logging verbosity
- **Default**: `INFO`
- **Options**: `DEBUG`, `INFO`, `WARNING`, `ERROR`
- **Impact**: Console output detail

**Example**:
```bash
LOG_LEVEL=INFO
```

## Example Configurations

### Development (Default)
```bash
# .env
SLOT_ASSISTANT_MODEL=mlx-community/Qwen2.5-Coder-7B-Instruct-4bit
CHROMA_PERSIST_DIR=./data/chroma
EMBEDDING_MODEL=sentence-transformers/all-mpnet-base-v2
API_HOST=0.0.0.0
API_PORT=8000
CODEBASE_PATH=./data/raw/codebase
DOCS_PATH=./data/raw/docs
LOG_LEVEL=DEBUG
```

### Production
```bash
# .env.production
SLOT_ASSISTANT_MODEL=mlx-community/Qwen2.5-Coder-7B-Instruct-4bit
CHROMA_PERSIST_DIR=/var/lib/flair-assistant/chroma
EMBEDDING_MODEL=sentence-transformers/all-mpnet-base-v2
API_HOST=127.0.0.1  # Local only
API_PORT=8000
CODEBASE_PATH=/opt/my-project/src
DOCS_PATH=/opt/my-project/docs
LOG_LEVEL=WARNING
```

### Fast Indexing (Smaller Model)
```bash
# .env
SLOT_ASSISTANT_MODEL=mlx-community/Qwen2.5-Coder-3B-Instruct-4bit
CHROMA_PERSIST_DIR=./data/chroma
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2  # Faster
API_HOST=0.0.0.0
API_PORT=8000
CODEBASE_PATH=./my-large-codebase
LOG_LEVEL=INFO
```

## Web UI Configuration

### `web-ui/.env`

```bash
VITE_API_URL=http://localhost:8000
```

- **`VITE_API_URL`**: Backend API URL
  - Must match backend `API_HOST` and `API_PORT`
  - Must include protocol (`http://` or `https://`)

## Indexing Configuration

### Codebase Structure

**Recommended structure**:
```
my-codebase/
├── src/              # Main source code
├── tests/            # Test files (excluded by default)
├── node_modules/     # Excluded by default
├── dist/             # Excluded by default
└── package.json
```

**Excluded by default**:
- `node_modules/`
- `dist/`
- `build/`
- `.git/`
- `__pycache__/`
- `.next/`
- `.venv/`
- `venv/`
- `coverage/`
- `.cache/`

### Indexing Options

**Force re-index**:
```bash
slot-assistant ingest --force
```

**Custom paths** (override env):
```bash
slot-assistant ingest \
  --code-path /path/to/code \
  --docs-path /path/to/docs \
  --force
```

## Advanced Configuration

### Chunk Size Tuning

Edit `src/slot_assistant/rag/store.py`:
```python
self.text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=512,  # Change this
    chunk_overlap=50,  # And this
    length_function=len,
)
```

**Trade-offs**:
- **Smaller chunks** (256):
  - More granular
  - More chunks to search
  - May split context
  
- **Larger chunks** (1024):
  - More context per chunk
  - Fewer chunks
  - May include irrelevant code

### Retrieval Count

Edit `src/slot_assistant/api/server.py`:
```python
results = store.collection.query(
    query_texts=[request.message],
    n_results=10,  # Change this
    include=['documents', 'metadatas']
)
```

**Trade-offs**:
- **More results** (20):
  - Better coverage
  - More context for LLM
  - Slower inference
  
- **Fewer results** (5):
  - Faster
  - Less context
  - May miss relevant code

### CORS Origins

Edit `src/slot_assistant/api/server.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://my-domain.com",  # Add production domain
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Troubleshooting

### Model Download Issues

Models are downloaded on first use and cached:
```bash
# Cache location
~/.cache/huggingface/

# Clear cache if corrupted
rm -rf ~/.cache/huggingface/hub/models--mlx-community--*
```

### ChromaDB Errors

**Reset database**:
```bash
rm -rf data/chroma
slot-assistant ingest --force
```

**Change location** (if disk space issue):
```bash
# In .env
CHROMA_PERSIST_DIR=/path/to/large/disk/chroma
```

### Path Resolution

**Relative paths** are resolved from project root:
```bash
# Current directory
CODEBASE_PATH=./src

# Resolved to
/Users/you/AI-assistant/src
```

**Absolute paths** are used as-is:
```bash
CODEBASE_PATH=/Users/you/my-project/src
```

## Performance Tuning

### For Large Codebases (10K+ files)

1. **Use smaller embedding model**:
   ```bash
   EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
   ```

2. **Increase chunk size**:
   Edit `store.py`: `chunk_size=1024`

3. **Reduce retrieval count**:
   Edit `server.py`: `n_results=5`

### For Better Quality

1. **Use larger LLM**:
   ```bash
   SLOT_ASSISTANT_MODEL=mlx-community/Qwen2.5-Coder-14B-Instruct-4bit
   ```

2. **Keep 768-dim embeddings**:
   ```bash
   EMBEDDING_MODEL=sentence-transformers/all-mpnet-base-v2
   ```

3. **Increase retrieval**:
   Edit `server.py`: `n_results=15`

## Environment Variable Priority

1. **Command-line arguments** (highest)
2. **`.env` file**
3. **Default values** (lowest)

**Example**:
```bash
# .env has: CODEBASE_PATH=./default

#This uses .env value
slot-assistant ingest

# This overrides .env
slot-assistant ingest --code-path /custom/path
```
