"""
Vector store implementation using ChromaDB for semantic code search.

Handles document indexing and similarity search. AST-parsed documents are
stored as-is (they're already semantically chunked). Non-AST documents
get split by a text splitter as fallback.
"""

import hashlib
import os
from pathlib import Path
from typing import Dict, List, Optional

import chromadb
from chromadb.utils import embedding_functions
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter


class VectorStore:
    """Manages the RAG vector store using ChromaDB."""

    def __init__(self, persist_directory: Optional[str] = None):
        self.persist_directory = persist_directory or os.getenv(
            "CHROMA_PERSIST_DIR", "./data/chroma"
        )
        Path(self.persist_directory).mkdir(parents=True, exist_ok=True)

        self.client = chromadb.PersistentClient(path=self.persist_directory)

        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=os.getenv(
                "EMBEDDING_MODEL", "sentence-transformers/all-mpnet-base-v2"
            )
        )

        self.collection = self.client.get_or_create_collection(
            name="slot_framework",
            embedding_function=self.embedding_fn,
        )

        # Text splitter ONLY for non-AST documents (simple/fallback loaded files)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1500,
            chunk_overlap=200,
            length_function=len,
        )

    def reset(self):
        """Delete and recreate the collection. Used for force re-indexing."""
        self.client.delete_collection("slot_framework")
        self.collection = self.client.get_or_create_collection(
            name="slot_framework",
            embedding_function=self.embedding_fn,
        )

    def add_documents(self, documents: List[Document], batch_size: int = 100):
        """Add documents to the vector store.

        AST-parsed documents (metadata.parse_method == 'ast') are stored as-is
        since they already represent semantic code units. Other documents get
        split by the text splitter.
        """
        ast_docs = []
        raw_docs = []

        for doc in documents:
            if doc.metadata.get('parse_method') == 'ast':
                ast_docs.append(doc)
            else:
                raw_docs.append(doc)

        # Split only non-AST docs
        split_docs = self.text_splitter.split_documents(raw_docs) if raw_docs else []

        all_chunks = ast_docs + split_docs
        print(
            f"Adding {len(all_chunks)} chunks to vector store "
            f"({len(ast_docs)} AST, {len(split_docs)} text-split)..."
        )

        for i in range(0, len(all_chunks), batch_size):
            batch = all_chunks[i:i + batch_size]

            # Use content hash for stable, deduplicated IDs
            ids = [self._content_id(chunk) for chunk in batch]
            texts = [chunk.page_content for chunk in batch]
            metadatas = [self._clean_metadata(chunk.metadata) for chunk in batch]

            self.collection.upsert(
                ids=ids,
                documents=texts,
                metadatas=metadatas,
            )

            batch_num = i // batch_size + 1
            total_batches = (len(all_chunks) + batch_size - 1) // batch_size
            print(f"Processed batch {batch_num}/{total_batches}")

    def query(
        self, query_text: str, n_results: int = 10
    ) -> List[Dict]:
        """Search for relevant documents. Returns list of {content, metadata, distance}."""
        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results,
            include=['documents', 'metadatas', 'distances'],
        )

        if not results["documents"] or not results["documents"][0]:
            return []

        docs = results["documents"][0]
        metas = results.get("metadatas", [[]])[0]
        dists = results.get("distances", [[]])[0]

        return [
            {"content": doc, "metadata": meta, "distance": dist}
            for doc, meta, dist in zip(docs, metas, dists)
        ]

    def count(self) -> int:
        return self.collection.count()

    @staticmethod
    def _content_id(doc: Document) -> str:
        """Generate a stable ID from content + source path."""
        key = f"{doc.metadata.get('source', '')}:{doc.metadata.get('start_line', '')}:{doc.metadata.get('name', '')}"
        return hashlib.sha256(key.encode()).hexdigest()[:16]

    @staticmethod
    def _clean_metadata(metadata: dict) -> dict:
        """Ensure all metadata values are ChromaDB-compatible (str, int, float, bool)."""
        clean = {}
        for k, v in metadata.items():
            if v is None:
                clean[k] = ''
            elif isinstance(v, (str, int, float, bool)):
                clean[k] = v
            else:
                clean[k] = str(v)
        return clean
