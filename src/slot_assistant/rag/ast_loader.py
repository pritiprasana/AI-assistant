"""
AST-aware code parsing for intelligent chunking.

Uses Tree-Sitter to parse code into semantic units (classes, functions, methods)
instead of dumb character-based splitting. This preserves logical boundaries
so each chunk in the vector store represents a meaningful code unit.
"""

from pathlib import Path
from typing import List, Optional

from langchain.docstore.document import Document

try:
    from tree_sitter import Language, Parser
    from tree_sitter_javascript import language as js_language
    from tree_sitter_python import language as py_language
    HAS_TREE_SITTER = True
except ImportError:
    HAS_TREE_SITTER = False

# Try to import TypeScript parser (separate from JS)
HAS_TYPESCRIPT = False
try:
    from tree_sitter_typescript import language_typescript, language_tsx
    HAS_TYPESCRIPT = True
except ImportError:
    pass


# Node types we care about per language
CHUNK_NODE_TYPES = {
    'javascript': {
        'function_declaration',
        'class_declaration',
        'method_definition',
        'export_statement',
        'lexical_declaration',       # const/let
        'variable_declaration',      # var
        'arrow_function',
        'expression_statement',      # top-level calls, assignments
    },
    'typescript': {
        'function_declaration',
        'class_declaration',
        'method_definition',
        'export_statement',
        'lexical_declaration',
        'variable_declaration',
        'arrow_function',
        'expression_statement',
        'interface_declaration',
        'type_alias_declaration',
        'enum_declaration',
    },
    'python': {
        'function_definition',
        'class_definition',
        'decorated_definition',
    },
}

# Node types whose children should be extracted as individual chunks
# (e.g., class bodies should yield individual methods)
CONTAINER_NODE_TYPES = {
    'javascript': {'class_declaration', 'class_body'},
    'typescript': {'class_declaration', 'class_body'},
    'python': {'class_definition'},
}


class ASTCodeLoader:
    """Loads code files and splits them into semantic chunks using AST parsing.

    Instead of splitting at arbitrary character boundaries, this uses Tree-Sitter
    to identify functions, classes, methods, interfaces, etc. Each chunk is a
    complete semantic unit that makes sense on its own for retrieval.
    """

    def __init__(self):
        if not HAS_TREE_SITTER:
            raise ImportError(
                "tree-sitter not installed. Run: "
                "pip install tree-sitter tree-sitter-javascript tree-sitter-python"
            )

        self.parsers = {
            'javascript': self._create_parser(js_language()),
            'python': self._create_parser(py_language()),
        }

        if HAS_TYPESCRIPT:
            self.parsers['typescript'] = self._create_parser(language_typescript())
            self.parsers['tsx'] = self._create_parser(language_tsx())

        self.ext_to_lang = {
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.py': 'python',
        }

        # TypeScript gets its own parser (JS parser chokes on TS syntax)
        if HAS_TYPESCRIPT:
            self.ext_to_lang['.ts'] = 'typescript'
            self.ext_to_lang['.tsx'] = 'tsx'
        else:
            # Fallback: use JS parser for TS (imperfect but better than nothing)
            self.ext_to_lang['.ts'] = 'javascript'
            self.ext_to_lang['.tsx'] = 'javascript'

    def _create_parser(self, language) -> Parser:
        parser = Parser(Language(language))
        return parser

    def load_file(self, file_path: Path) -> List[Document]:
        """Load a file and extract semantic code chunks using AST."""
        ext = file_path.suffix.lower()
        lang = self.ext_to_lang.get(ext)

        if not lang:
            return self._load_simple(file_path)

        # Resolve the chunk types — tsx/typescript share the 'typescript' config
        lang_key = 'typescript' if lang in ('typescript', 'tsx') else lang

        try:
            code = file_path.read_text(encoding='utf-8')
            parser = self.parsers[lang]
            tree = parser.parse(bytes(code, 'utf-8'))

            chunks = []
            self._walk_tree(tree.root_node, code, file_path, lang_key, chunks, parent_name=None)

            return chunks if chunks else self._load_simple(file_path)

        except Exception as e:
            print(f"AST parsing failed for {file_path}: {e}. Falling back to simple loading.")
            return self._load_simple(file_path)

    def _walk_tree(
        self,
        node,
        code: str,
        file_path: Path,
        lang: str,
        chunks: List[Document],
        parent_name: Optional[str],
    ):
        """Recursively walk the AST and extract meaningful chunks.

        For container nodes (classes), we recurse into their children to extract
        individual methods/properties. For leaf-level semantic nodes (functions,
        methods), we extract the whole node as one chunk.
        """
        chunk_types = CHUNK_NODE_TYPES.get(lang, set())
        container_types = CONTAINER_NODE_TYPES.get(lang, set())

        for child in node.children:
            # If this is a container (like a class), we want BOTH:
            # - The entire class as one chunk (for "what is class X?" queries)
            # - Individual methods as separate chunks (for "how does method Y work?" queries)
            if child.type in container_types:
                class_name = self._get_node_name(child)

                # Extract the full class as one chunk
                chunk = self._make_chunk(child, code, file_path, lang, parent_name)
                if chunk:
                    chunks.append(chunk)

                # Then recurse to also extract individual methods/properties
                self._walk_tree(child, code, file_path, lang, chunks, parent_name=class_name)

            elif child.type in chunk_types:
                chunk = self._make_chunk(child, code, file_path, lang, parent_name)
                if chunk:
                    chunks.append(chunk)
            else:
                # Keep walking for nodes we don't directly extract
                # (e.g., program -> export_statement -> class_declaration)
                self._walk_tree(child, code, file_path, lang, chunks, parent_name=parent_name)

    def _make_chunk(
        self,
        node,
        code: str,
        file_path: Path,
        lang: str,
        parent_name: Optional[str],
    ) -> Optional[Document]:
        """Create a Document chunk from an AST node with enriched metadata."""
        chunk_code = code[node.start_byte:node.end_byte]

        # Skip trivially small chunks (e.g., empty export statements)
        if len(chunk_code.strip()) < 10:
            return None

        name = self._get_node_name(node)

        # Build a metadata-enriched prefix so the embedding captures context.
        # Without this, searching for "GamePlayIntro" won't match a chunk
        # whose body doesn't mention the name explicitly.
        prefix_parts = [f"// File: {file_path.name}"]
        if parent_name and parent_name != 'anonymous':
            prefix_parts.append(f"// Class: {parent_name}")
        if name and name != 'anonymous':
            prefix_parts.append(f"// {node.type}: {name}")
        prefix = "\n".join(prefix_parts) + "\n"

        enriched_content = prefix + chunk_code

        metadata = {
            'source': str(file_path),
            'filename': file_path.name,
            'extension': file_path.suffix,
            'node_type': node.type,
            'name': name,
            'parent_class': parent_name or '',
            'start_line': node.start_point[0] + 1,
            'end_line': node.end_point[0] + 1,
            'language': lang,
            'parse_method': 'ast',
        }

        return Document(page_content=enriched_content, metadata=metadata)

    def _get_node_name(self, node) -> str:
        """Extract the name identifier from a function, class, interface, etc."""
        # Direct children named 'identifier' or 'property_identifier'
        for child in node.children:
            if child.type in ('identifier', 'property_identifier', 'type_identifier'):
                return child.text.decode('utf-8')
        # For export statements, look inside the declaration
        for child in node.children:
            if 'declaration' in child.type:
                return self._get_node_name(child)
        return 'anonymous'

    def _load_simple(self, file_path: Path) -> List[Document]:
        """Fallback loader when AST parsing isn't available or fails."""
        try:
            content = file_path.read_text(encoding='utf-8')
            # Add file context prefix for better embedding
            prefix = f"// File: {file_path.name}\n"
            metadata = {
                'source': str(file_path),
                'filename': file_path.name,
                'extension': file_path.suffix,
                'parse_method': 'simple',
            }
            return [Document(page_content=prefix + content, metadata=metadata)]
        except Exception:
            return []
