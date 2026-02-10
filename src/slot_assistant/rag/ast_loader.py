"""
AST-aware code parsing for intelligent chunking.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
from langchain.docstore.document import Document

try:
    from tree_sitter import Language, Parser
    from tree_sitter_javascript import language as js_language
    from tree_sitter_python import language as py_language
    HAS_TREE_SITTER = True
except ImportError:
    HAS_TREE_SITTER = False


class ASTCodeLoader:
    """Loads code and splits it by AST nodes (functions, classes, etc.)"""
    
    def __init__(self):
        if not HAS_TREE_SITTER:
            raise ImportError("tree-sitter not installed. Run: pip install tree-sitter tree-sitter-javascript tree-sitter-python")
        
        # Initialize parsers for different languages
        self.parsers = {
            'javascript': self._create_parser(js_language()),
            'python': self._create_parser(py_language()),
        }
        
        # Map file extensions to languages
        self.ext_to_lang = {
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.ts': 'javascript',  # TypeScript uses JS parser
            '.tsx': 'javascript',
            '.py': 'python',
        }
    
    def _create_parser(self, language) -> Parser:
        """Create a parser for a given language."""
        parser = Parser(Language(language))
        return parser
    
    def load_file(self, file_path: Path) -> List[Document]:
        """Load a file and extract code chunks using AST."""
        ext = file_path.suffix.lower()
        lang = self.ext_to_lang.get(ext)
        
        if not lang:
            # Fallback to simple loading for unsupported files
            return self._load_simple(file_path)
        
        try:
            code = file_path.read_text(encoding='utf-8')
            parser = self.parsers[lang]
            tree = parser.parse(bytes(code, 'utf-8'))
            
            chunks = []
            root = tree.root_node
            
            # Extract top-level nodes
            for node in root.children:
                chunk = self._extract_chunk(node, code, file_path, lang)
                if chunk:
                    chunks.append(chunk)
            
            return chunks if chunks else self._load_simple(file_path)
            
        except Exception as e:
            print(f"AST parsing failed for {file_path}: {e}. Falling back to simple loading.")
            return self._load_simple(file_path)
    
    def _extract_chunk(self, node, code: str, file_path: Path, lang: str) -> Optional[Document]:
        """Extract a code chunk from an AST node."""
        # Node types we want to extract as separate chunks
        chunk_types = {
            'javascript': [
                'function_declaration',
                'class_declaration', 
                'method_definition',
                'export_statement',
                'const',
                'let',
                'var'
            ],
            'python': [
                'function_definition',
                'class_definition',
                'decorated_definition'
            ]
        }
        
        target_types = chunk_types.get(lang, [])
        
        if node.type in target_types:
            start_byte = node.start_byte
            end_byte = node.end_byte
            chunk_code = code[start_byte:end_byte]
            
            # Get function/class name if available
            name = self._get_node_name(node)
            
            metadata = {
                'source': str(file_path),
                'filename': file_path.name,
                'extension': file_path.suffix,
                'node_type': node.type,
                'name': name,
                'start_line': node.start_point[0] +1,
                'end_line': node.end_point[0] + 1,
                'language': lang
            }
            
            return Document(page_content=chunk_code, metadata=metadata)
        
        return None
    
    def _get_node_name(self, node) -> str:
        """Extract the name of a function or class."""
        # Try to find identifier node for the name
        for child in node.children:
            if child.type == 'identifier':
                return child.text.decode('utf-8')
        return 'anonymous'
    
    def _load_simple(self, file_path: Path) -> List[Document]:
        """Simple fallback loader for files that can't be AST-parsed."""
        try:
            content = file_path.read_text(encoding='utf-8')
            metadata = {
                'source': str(file_path),
                'filename': file_path.name,
                'extension': file_path.suffix,
                'parse_method': 'simple'
            }
            return [Document(page_content=content, metadata=metadata)]
        except Exception:
            return []
