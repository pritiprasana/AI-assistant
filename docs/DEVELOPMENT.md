# Development Guide

## Setting Up Development Environment

### Prerequisites

- macOS with Apple Silicon (M1/M2/M3)
- Python 3.9+
- Node.js 18+
- VS Code (recommended)

### Initial Setup

1. **Clone and install backend**:
   ```bash
   git clone <repository-url>
   cd AI-assistant
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -e ".[dev]"  # Includes dev dependencies
   ```

2. **Install frontend dependencies**:
   ```bash
   cd web-ui
   npm install
   ```

3. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit CODEBASE_PATH to point to a test codebase
   ```

4. **Index test data**:
   ```bash
   slot-assistant ingest --force
   ```

## Project Layout

```
AI-assistant/
├── src/slot_assistant/       # Python backend
│   ├── cli/                   # CLI commands
│   ├── api/                   # FastAPI server
│   └── rag/                   # RAG system
├── web-ui/                    # React frontend
├── vscode-extension/          # VS Code extension
├── tests/                     # Python tests
├── docs/                      # Documentation
└── data/chroma/              # Vector database (gitignored)
```

## Development Workflow

### Backend Development

**Running API server**:
```bash
source .venv/bin/activate
slot-assistant serve
# Or with auto-reload:
uvicorn slot_assistant.api.server:app --reload
```

**Testing RAG**:
```bash
# Check status
curl http://localhost:8000/rag/status

# Test query
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "test", "use_rag": true}'
```

**Python console debugging**:
```python
from slot_assistant.rag.store import VectorStore

store = VectorStore()
print(f"Documents: {store.count()}")

results = store.collection.query(
    query_texts=["test"],
    n_results=5
)
print(results)
```

### Frontend Development

**Running dev server**:
```bash
cd web-ui
npm run dev
# Runs on http://localhost:5173
```

**Building**:
```bash
npm run build
npm run preview  # Test production build
```

**TypeScript type checking**:
```bash
npm run type-check
```

### VS Code Extension Development

1. Open `vscode-extension/` in VS Code
2. Press `F5` to launch Extension Development Host
3. Test extension in the new window
4. Make changes and reload window

## Code Structure

### Backend (`src/slot_assistant/`)

**`cli/main.py`**: Entry point
- `app`: Typer CLI app
- `get_llm_response()`: MLX integration
- `ingest()`: Index codebase command

**`api/server.py`**: FastAPI server
- `POST /chat`: Main endpoint
- `GET /rag/status`: Status check
- RAG retrieval + deduplication logic

**`rag/store.py`**: Vector store
- `VectorStore` class
- ChromaDB initialization
- Embedding model loading
- Query and add operations

**`rag/loader.py`**: Directory loader
- Recursive file scanning
- Exclusion patterns (node_modules, etc.)
- AST parsing invocation

**`rag/ast_loader.py`**: AST parser
- TypeScript/JavaScript parsing
- Python parsing
- Chunk extraction (classes, functions)

### Frontend (`web-ui/src/`)

**Components**:
- `Header.tsx`: Top bar + mode toggle
- `ChatContainer.tsx`: Message list
- `MessageBubble.tsx`: Individual messages + sources
- `CodeBlock.tsx`: Syntax highlighting
- `InputArea.tsx`: Message input

**Services**:
- `api.ts`: HTTP client
- `storage.ts`: localStorage wrapper

**Types**:
- `types.ts`: TypeScript interfaces

## Adding Features

### Backend: New API Endpoint

1. Edit `src/slot_assistant/api/server.py`:
   ```python
   @app.get("/new-endpoint")
   async def new_endpoint():
       return {"message": "Hello"}
   ```

2. Restart server to apply changes

### Frontend: New Component

1. Create `web-ui/src/components/NewComponent.tsx`:
   ```typescript
   export function NewComponent() {
     return <div>New Component</div>;
   }
   ```

2. Import in `App.tsx`:
   ```typescript
   import { NewComponent } from './components/NewComponent';
   ```

### RAG: Custom Chunking Strategy

Edit `src/slot_assistant/rag/ast_loader.py`:
```python
def extract_chunks(self, tree, code, filepath):
    # Add custom node types
    for node in tree.root_node.named_children:
        if node.type == 'custom_node_type':
            # Extract custom chunks
            pass
```

## Testing

### Python Tests

```bash
pytest tests/
```

**Writing tests**:
```python
# tests/test_store.py
def test_vector_store():
    store = VectorStore()
    assert store.count() >= 0
```

### Frontend Tests

```bash
cd web-ui
npm test
```

**Writing tests** (add Vitest):
```typescript
// tests/Header.test.tsx
import { render } from '@testing-library/react';
import { Header } from '../src/components/Header';

test('renders header', () => {
  const { getByText } = render(<Header mode="general" onModeChange={() => {}} />);
  expect(getByText('Flair Assistant')).toBeInTheDocument();
});
```

## Code Quality

### Linting

**Python (ruff)**:
```bash
ruff check src/
ruff format src/  # Auto-fix
```

**TypeScript (ESLint)**:
```bash
cd web-ui
npm run lint
```

### Type Checking

**Python (mypy)**:
```bash
mypy src/
```

**TypeScript**:
```bash
cd web-ui
npm run type-check
```

## Debugging

### Backend

**Using Python debugger**:
```python
import pdb; pdb.set_trace()
```

**Logging**:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.debug("Debug message")
```

### Frontend

**Browser DevTools**:
- F12 to open
- Console for logs
- Network tab for API calls

**React DevTools**:
- Install browser extension
- Inspect component state/props

## Common Tasks

### Re-index codebase
```bash
slot-assistant ingest --force
```

### Clear vector database
```bash
rm -rf data/chroma
slot-assistant ingest --force
```

### Change embedding model
1. Edit `src/slot_assistant/rag/store.py`
2. Update `EMBEDDING_MODEL` in `.env`
3. Re-index (`--force`)

### Change LLM model
1. Set `SLOT_ASSISTANT_MODEL` in `.env`
2. Restart server

### Inspect ChromaDB
```python
from slot_assistant.rag.store import VectorStore

store = VectorStore()
data = store.collection.get(limit=10, include=['metadatas', 'documents'])
for meta, doc in zip(data['metadatas'], data['documents']):
    print(f"{meta['filename']}: {doc[:100]}...")
```

## Performance Profiling

### Backend

**Using cProfile**:
```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()
# Code to profile
profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumtime')
stats.print_stats(10)
```

### Frontend

**React DevTools Profiler**:
1. Open React DevTools
2. Click "Profiler" tab
3. Start recording
4. Perform actions
5. Stop and analyze

## Deployment Considerations

### Production Build

**Backend**:
- Use production ASGI server (Uvicorn with Gunicorn)
- Set proper logging levels
- Use environment-specific `.env`

**Frontend**:
```bash
npm run build
# Serve dist/ with nginx or similar
```

### Environment Variables

Create `.env.production`:
```bash
CODEBASE_PATH=/path/to/prod/codebase
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=WARNING
```

## Contributing

### Pull Request Process

1. Fork the repository
2. Create feature branch: `git checkout -b feature/my-feature`
3. Make changes
4. Add tests
5. Run linters: `ruff check`, `npm run lint`
6. Commit: `git commit -m "Add my feature"`
7. Push: `git push origin feature/my-feature`
8. Open pull request

### Code Style

**Python**:
- Follow PEP 8
- Use type hints
- Add docstrings to public functions

**TypeScript**:
- Use functional components
- Prefer const over let
- Add JSDoc comments

### Commit Messagesformat

```
type(scope): brief description

Longer explanation if needed

Closes #123
```

Types: `feat`, `fix`, `docs`, `refactor`, `test`

## Resources

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [React Docs](https://react.dev/)
- [ChromaDB Docs](https://docs.trychroma.com/)
- [MLX Docs](https://ml-explore.github.io/mlx/)
- [Tailwind CSS v4](https://tailwindcss.com/)
