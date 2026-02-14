"""
Document loading utilities for ingesting codebases into the vector store.
"""

import os
from pathlib import Path
from typing import List

from langchain.docstore.document import Document


# Default directories to skip during indexing
DEFAULT_EXCLUDE_PATTERNS = [
    'node_modules',
    'dist',
    'build',
    '.git',
    '__pycache__',
    '.next',
    '.venv',
    'venv',
    'coverage',
    '.cache',
    '.tsbuildinfo',
]

# File extensions we can index
SUPPORTED_EXTENSIONS = {
    # Code (AST-parseable)
    '.py', '.js', '.ts', '.tsx', '.jsx',
    # Code (simple load)
    '.html', '.css', '.json',
    '.c', '.cpp', '.h', '.java', '.go', '.rs',
    # Docs
    '.md', '.txt', '.rst', '.yaml', '.yml',
}

# Extensions where AST parsing should be attempted
AST_EXTENSIONS = {'.py', '.js', '.ts', '.tsx', '.jsx'}


class DirectoryLoader:
    """Loads documents from a directory recursively with AST-aware parsing."""

    def __init__(
        self,
        root_dir: str,
        glob_pattern: str = "**/*",
        exclude_hidden: bool = True,
        use_ast: bool = True,
        exclude_patterns: List[str] = None,
    ):
        self.root_dir = root_dir
        self.glob_pattern = glob_pattern
        self.exclude_hidden = exclude_hidden
        self.use_ast = use_ast
        self.exclude_patterns = exclude_patterns or DEFAULT_EXCLUDE_PATTERNS

        self.ast_loader = None
        if self.use_ast:
            try:
                from slot_assistant.rag.ast_loader import ASTCodeLoader
                self.ast_loader = ASTCodeLoader()
                print("AST-aware parsing enabled")
            except ImportError as e:
                print(f"AST parsing unavailable: {e}. Falling back to simple parsing.")
                self.use_ast = False

    def _should_exclude(self, file_path: Path) -> bool:
        path_str = str(file_path)
        for pattern in self.exclude_patterns:
            if pattern in path_str:
                return True
        return False

    def load(self) -> List[Document]:
        """Load documents recursively with AST parsing."""
        documents = []
        path = Path(self.root_dir)

        if not path.exists():
            print(f"Warning: Directory {self.root_dir} does not exist.")
            return []

        print(f"Scanning {self.root_dir}...")

        for file_path in path.rglob(self.glob_pattern):
            if not file_path.is_file():
                continue

            if self.exclude_hidden and any(
                part.startswith('.') for part in file_path.parts
            ):
                continue

            if self._should_exclude(file_path):
                continue

            if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                continue

            # Use AST parsing for code files if available
            if (
                self.use_ast
                and self.ast_loader
                and file_path.suffix.lower() in AST_EXTENSIONS
            ):
                try:
                    chunks = self.ast_loader.load_file(file_path)
                    documents.extend(chunks)
                    print(f"  AST parsed: {file_path.name} ({len(chunks)} chunks)")
                    continue
                except Exception as e:
                    print(f"  AST parse failed for {file_path.name}: {e}")
                    # Fall through to simple loading

            # Simple loading for non-code or fallback
            try:
                content = file_path.read_text(encoding='utf-8')
                prefix = f"// File: {file_path.name}\n"
                metadata = {
                    "source": str(file_path),
                    "filename": file_path.name,
                    "extension": file_path.suffix,
                    "relative_path": str(file_path.relative_to(path)),
                    "parse_method": "simple",
                }
                documents.append(
                    Document(page_content=prefix + content, metadata=metadata)
                )
                print(f"  Loaded: {file_path.name}")
            except UnicodeDecodeError:
                continue
            except Exception as e:
                print(f"  Error loading {file_path}: {e}")
                continue

        print(f"\nLoaded {len(documents)} document chunks.")
        return documents


def load_directory(path: str, use_ast: bool = True) -> List[Document]:
    """Convenience function to load a directory. Used by CLI ingest command."""
    loader = DirectoryLoader(root_dir=path, use_ast=use_ast)
    return loader.load()
