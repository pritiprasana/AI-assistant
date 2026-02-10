# RAG System Documentation

## What is RAG?

**Retrieval-Augmented Generation (RAG)** is a technique that enhances LLM responses by:
1. **Retrieving** relevant information from a knowledge base
2. **Augmenting** the LLM prompt with that information
3. **Generating** a response based on both the query and retrieved context

This prevents hallucination and grounds responses in actual codebase content.

## Our RAG Pipeline

### Overview
```
Query → Embed → Search → Retrieve → Deduplicate → Generate → Cite
```

### Components

#### 1. Embedding Model
**Model**: `sentence-transformers/all-mpnet-base-v2`

**Specifications**:
- Dimensions: 768
- Max sequence: 384 tokens
- Architecture: MPNet (Microsoft Permuted Language Model)
- Training: Paraphrase detection, semantic similarity

**Why this model?**
- ✅ Better code understanding than MiniLM
- ✅ 768 dimensions = more nuanced representations
- ✅ Good balance of speed vs. quality
- ❌ Slower than smaller models

**Alternative considered**: `all-MiniLM-L6-v2`
- Faster but only 384 dimensions
- Tested, but ranked GamePlayIntro.ts as #8 instead of #1

#### 2. Vector Database
**Technology**: ChromaDB

 **Configuration**:
- **Persist directory**: `./data/chroma`
- **Distance metric**: Cosine similarity
- **Collection**: Single collection for all code

**Storage**:
- Embeddings: 768-dimensional vectors
- Metadata: filename, class name, line range, node type
- Documents: Original code text

#### 3. Code Chunking

**AST-Aware Chunking**:
```python
# Instead of naive splitting:
chunk1 = code[0:512]
chunk2 = code[512:1024]

# We extract semantic units:
chunk1 = entire_class_definition()
chunk2 = entire_function_definition()
```

**Chunk Metadata**:
```json
{
  "filename": "GamePlayIntro.ts",
  "name": "GamePlayIntro",
  "node_type": "class_declaration",
  "start_line": 15,
  "end_line": 120,
  "source": "/path/to/GamePlayIntro.ts"
}
```

**Supported Node Types**:
- `class_declaration`
- `function_declaration`
- `method_definition`
- `export_statement`

**Text Splitting** (fallback):
- Chunk size: 512 characters
- Overlap: 50 characters
- Used when AST parsing fails or for non-code files

### 4. Retrieval Process

**Step 1: Query Embedding**
```python
query = "How does GamePlayIntro work?"
query_vector = embedding_model.encode(query)
# → 768-dimensional vector
```

**Step 2: Similarity Search**
```python
results = vector_store.query(
    query_vector,
    n_results=10  # Top-10 chunks
)
```

Returns:
- **Documents**: Code chunks
- **Metadata**: Filenames, line numbers
- **Distances**: Cosine similarity scores (0 = identical, 2 = opposite)

**Step 3: Deduplication**
```python
# Problem: Same chunk may appear multiple times
# IntroScreen.ts (lines 29-298) - appears 2x
# MainGameScreen.ts (lines 53-446) - appears 2x

# Solution: Track unique (filename, name, start_line, end_line)
seen = set()
for chunk in chunks:
    key = (chunk.filename, chunk.name, chunk.start_line, chunk.end_line)
    if key not in seen:
        unique_chunks.append(chunk)
        seen.add(key)
```

**Step 4: Context Construction**
```
=== CODEBASE CONTEXT - 6 UNIQUE CODE CHUNKS ===

--- Code Chunk 1 [GamePlayIntro.ts::GamePlayIntro] ---
export class GamePlayIntro extends AdjustableLayoutContainer {
    static isSimulationRunning: boolean = false;
    ...
}

--- Code Chunk 2 [IntroScreen.ts::IntroScreen] ---
export class IntroScreen extends AdjustableLayoutContainer {
    public gamePlayIntro: GamePlayIntro;
    ...
}

=== END - YOU MUST USE ALL FILES ABOVE ===
```

### 5. LLM Integration

**Prompt Structure**:
```
[System Prompt]
You are a specialized codebase assistant.
STRICT RULES:
1. ANALYZE EVERY FILE in the context
2. Cite filenames, class names, line numbers
3. If a class references another (e.g., gamePlayIntro: GamePlayIntro), explain that
...

[Context]
=== CODEBASE CONTEXT ===
[Retrieved code chunks]
===

[User Query]
How does IntroScreen work?
```

**Response Requirements**:
- Must list ALL files provided
- Must cite specific files/classes/methods
- Must explain relationships between components
- Must quote exact code from context

## Search Quality

### Current Performance

**Test Query**: "GamePlayIntro"

**Before Improvements**:
- Rank: #8 out of 10
- Distance: 0.682
- Files above it: SlotGameEvent.ts, transact-4.json, background.json

**Why?**
- Pure vector search doesn't handle exact keyword matches well
- "GamePlayIntro" in query vs. "GamePlayIntro" in filename
- Filename wasn't embedded, so no keyword match

**After Deduplication**:
- Duplicates removed
- Cleaner source list
- Still not #1 rank (vector search limitation)

### Known Limitations

1. **Exact Matches**: Doesn't prioritize exact filename matches
2. **Distance Clustering**: All distances within 0.667-0.682 (2% variance)
3. **Semantic Drift**: May retrieve semantically similar but irrelevant files

### Proposed Solutions

**Option 1: Hybrid Search** (Recommended)
```python
# Combine BM25 (keyword) + Vector (semantic)
bm25_results = bm25_index.search("GamePlayIntro", n=10)
vector_results = vector_store.query("GamePlayIntro", n=10)

# Weighted combination
final_results = 0.7 * bm25_results + 0.3 * vector_results
```

**Option 2: Metadata in Embeddings**
```python
# Include filename/class name in embedded text
enriched_text = f"""
File: GamePlayIntro.ts
Class: GamePlayIntro
{original_code}
"""
```

**Option 3: Reranking**
```python
# Use cross-encoder to rerank top-100
top_100 = vector_store.query(query, n=100)
reranked = cross_encoder.rank(query, top_100, n=10)
```

## Metrics & Monitoring

### Indexing Metrics
- Total documents indexed
- Indexing duration
- Failed files (with reasons)

### Query Metrics
- Retrieval latency
- Number of chunks retrieved
- Deduplication rate (% removed)
- LLM generation time

### Quality Metrics
- User feedback (implicit/explicit)
- Citation accuracy
- Hallucination rate

## Configuration

### Tunable Parameters

| Parameter | Default | Impact |
|-----------|---------|--------|
| `n_results` | 10 | More chunks = better coverage, larger context |
| `chunk_size` | 512 | Smaller = more granular, more chunks |
| `chunk_overlap` | 50 | More overlap = less context loss at boundaries |
| `embedding_model` | all-mpnet-base-v2 | Larger = better quality, slower |

### Editing Retrieval Count

In `src/slot_assistant/api/server.py`:
```python
results = store.collection.query(
    query_texts=[request.message],
    n_results=10,  # ← Change this
    include=['documents', 'metadatas']
)
```

Higher `n_results`:
- ✅ Better chance of finding relevant code
- ❌ More noise, larger context
- ❌ Slower LLM inference

## Debugging RAG

### Check Indexed Documents
```bash
curl http://localhost:8000/rag/status
# Returns: {"status": "ok", "indexed_documents": 6230}
```

### Inspect Retrieval
```python
from slot_assistant.rag.store import VectorStore

store = VectorStore()
results = store.collection.query(
    query_texts=["GamePlayIntro"],
    n_results=10,
    include=['documents', 'metadatas', 'distances']
)

for meta, dist in zip(results['metadatas'][0], results['distances'][0]):
    print(f"{meta['filename']} - distance: {dist}")
```

### Test Query
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Test query", "use_rag": true}' \
  | python3 -m json.tool
```

Check `sources` array in response.

## Best Practices

1. **Re-index after major changes**: Run `slot-assistant ingest --force`
2. **Monitor source quality**: Check UI sources panel - are they relevant?
3. **Verify citations**: LLM should cite line numbers - verify they're correct
4. **Avoid generic queries**: "How does it work?" → "How does GamePlayIntro initialize?"

## Common Issues

### Retrieved code doesn't match query
- **Cause**: Semantic mismatch
- **Fix**: Try more specific query with exact class/function names

### Duplicate sources in UI
- **Status**: Fixed via deduplication
- **If persists**: Restart server to reload code

### Generic responses despite RAG
- **Cause**: LLM ignoring context
- **Fix**: Check system prompt enforcement (already strict)

### Empty sources list
- **Cause**: No documents indexed or RAG disabled
- **Fix**: Run `slot-assistant ingest` and ensure `use_rag=true`
