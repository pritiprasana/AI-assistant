"""
Vector store implementation using ChromaDB for semantic code search.

This module provides the VectorStore class which manages:
- ChromaDB persistent database initialization
- Sentence-transformer embedding model (all-mpnet-base-v2, 768-dim)
- Document indexing with batch processing
- Semantic similarity search with metadata
"""

import os
from pathlib import Path
from typing import List, Optional

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter


class VectorStore:
    """
    Manages the RAG vector store using ChromaDB for semantic code search.
    
    This class handles:
    - Initializing persistent ChromaDB instance
    - Loading sentence-transformer embedding model (all-mpnet-base-v2)
    - Adding code chunks with metadata to the database
    - Performing similarity searches for retrieval
    
    The vector store uses 768-dimensional embeddings for better code understanding.
    All data is persists to disk for reuse across sessions.
    
    Example:
        >>> store = VectorStore()
        >>> documents = [Document(page_content="code", metadata={"filename": "test.ts"})]
        >>> store.add_documents(documents)
        >>> results = store.query("test query", n_results=5)
    """

    def __init__(self, persist_directory: Optional[str] = "./data/chroma"):
        """
        Initialize the vector store with ChromaDB and embedding model.
        
        Args:
            persist_directory: Path to store ChromaDB data. Defaults to ./data/chroma.
                             This directory will be created if it doesn't exist.
        
        Note:
            - Uses PersistentClient for disk-based storage
            - Embedding model: all-mpnet-base-v2 (768-dim, good for technical text)
            - Collection name: "slot_framework"
            - Text splitter: 1000 chars with 200 char overlap
        """
        self.persist_directory = persist_directory or "./data/chroma"
        
        # Ensure directory exists before initializing ChromaDB
        Path(self.persist_directory).mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB persistent client (saves to disk, reloads on restart)
        self.client = chromadb.PersistentClient(path=self.persist_directory)
        
        # Use sentence-transformers for embeddings
        # all-mpnet-base-v2: 768-dimensional embeddings, better quality for code
        # Alternative considered: all-MiniLM-L6-v2 (384-dim, faster but lower quality)
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="sentence-transformers/all-mpnet-base-v2"
        )
        
        # Get or create collection for this codebase
        # Collection persists across restarts - data is not lost
        self.collection = self.client.get_or_create_collection(
            name="slot_framework",
            embedding_function=self.embedding_fn
        )
        
        # Text splitter for fallback chunking (when AST doesn't extract specific nodes)
        # Recursive: tries different separators (\n\n, \n, space) to avoid mid-sentence splits
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,  # Max characters per chunk
            chunk_overlap=200,  # Overlap to preserve context at boundaries
            length_function=len,
        )

    def add_documents(self, documents: List[Document], batch_size: int = 100):
        """
        Add documents to the vector store with automatic chunking and embedding.
        
        Documents are split into smaller chunks, embedded using the sentence-transformer
        model, and added to ChromaDB with their metadata. Processing happens in batches
        to avoid memory issues with large codebases.
        
        Args:
            documents: List of LangChain Document objects with page_content and metadata
            batch_size: Number of chunks to process at once (default: 100)
        
        Note:
            - Each document is split into chunks using RecursiveCharacterTextSplitter
            - Metadata (filename, class name, line numbers) is preserved per chunk
            - Progress is printed to console for monitoring long-running indexing
        
        Example:
            >>> docs = [Document(page_content="class Foo {...}", metadata={"filename": "foo.ts"})]
            >>> store.add_documents(docs, batch_size=50)
            Adding 3 chunks to vector store...
            Processed batch 1/1
        """
        # Split documents into smaller chunks for better retrieval granularity
        # AST-extracted chunks may already be small, but this ensures consistency
        chunks = self.text_splitter.split_documents(documents)
        
        print(f"Adding {len(chunks)} chunks to vector store...")
        
        # Process in batches to avoid excessive memory usage
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            
            # Generate unique IDs for each chunk
            ids = [f"doc_{j}" for j in range(i, i + len(batch))]
            
            # Extract text content and metadata
            texts = [chunk.page_content for chunk in batch]
            metadatas = [chunk.metadata for chunk in batch]
            
            # Add to ChromaDB (automatically generates embeddings)
            self.collection.add(
                ids=ids,
                documents=texts,
                metadatas=metadatas
            )
            
            # Progress indicator
            batch_num = i // batch_size + 1
            total_batches = (len(chunks) + batch_size - 1) // batch_size
            print(f"Processed batch {batch_num}/{total_batches}")

    def query(self, query_text: str, n_results: int = 5) -> List[str]:
        """
        Search for relevant documents using semantic similarity.
        
        The query is embedded using the same model as the documents, then ChromaDB
        performs cosine similarity search to find the most relevant chunks.
        
        Args:
            query_text: Natural language query (e.g., "How does GamePlayIntro work?")
            n_results: Number of top results to return (default: 5)
        
        Returns:
            List of document contents (strings) sorted by relevance.
            Empty list if no results found.
        
        Note:
            - Uses cosine similarity for distance metric
            - Lower distance = more similar (0 = identical, 2 = opposite)
            - Results include metadata (filename, line numbers) in metadatas field
        
        Example:
            >>> results = store.query("GamePlayIntro", n_results=10)
            >>> print(results[0])  # Most relevant code chunk
        """
        # Query ChromaDB with embedded query vector
        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results
        )
        
        # Handle empty results
        if not results["documents"]:
            return []
            
        # Return list of document contents (first query result)
        return results["documents"][0]

    def count(self) -> int:
        """
        Return total number of documents in the vector store.
        
        Useful for checking if indexing worked and monitoring database size.
        
        Returns:
            Integer count of stored document chunks.
        
        Example:
            >>> store.count()
            6230
        """
        return self.collection.count()
