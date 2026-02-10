"""
CLI interface for Flair Assistant.

Provides command-line tools for:
- Asking questions with optional RAG context
- Ingesting and indexing codebases
- Starting the API server

Supports dual LLM backends:
- MLX: Apple Silicon (M1/M2/M3) Macs - best performance
- Ollama: Windows, Linux, Intel Macs - cross-platform
"""

import os
import platform
import importlib.util
import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

app = typer.Typer(
    name="slot-assistant",
    help="AI-powered coding assistant for slot game framework",
    add_completion=False,
)
console = Console()


def detect_llm_backend() -> str:
    """
    Detect which LLM backend to use based on platform and available libraries.
    
    Returns:
        "mlx" for Apple Silicon Macs with MLX installed
        "ollama" for Windows, Linux, or Macs without MLX
    
    Priority:
    1. Check SLOT_ASSISTANT_BACKEND environment variable (manual override)
    2. If macOS + Apple Silicon + MLX installed → use MLX
    3. Otherwise → use Ollama
    """
    # Allow manual backend selection via env var
    backend = os.getenv("SLOT_ASSISTANT_BACKEND", "").lower()
    if backend in ["mlx", "ollama"]:
        return backend
    
    # Auto-detect based on platform and available libraries
    is_mac_arm = platform.system() == "Darwin" and platform.machine() == "arm64"
    has_mlx = importlib.util.find_spec("mlx_lm") is not None
    
    if is_mac_arm and has_mlx:
        return "mlx"
    else:
        return "ollama"


def get_llm_response(prompt: str, context: str = "") -> str:
    """
    Get response from LLM using appropriate backend.
    
    Automatically selects between MLX (Mac) and Ollama (Windows/Linux) based
    on platform detection. Both backends use the same system prompt for consistency.
    
    Args:
        prompt: User's question/query
        context: Retrieved code context from RAG (optional)
    
    Returns:
        Generated response from the LLM
    
    Raises:
        RuntimeError: If neither backend is available or inference fails
    """
    # System prompt (same for both backends to ensure consistent behavior)
    system_prompt = """You are a specialized codebase analysis assistant for slot game development.

STRICT RULES - YOU MUST FOLLOW THESE:
1. ANALYZE EVERY FILE in the context - list ALL files you received in your answer
2. If a class has a property referencing another class (e.g., 'gamePlayIntro: GamePlayIntro'), you MUST explain that relationship
3. ALWAYS cite specific filenames, class names, properties, and methods from ALL files
4. When multiple files are provided, explain how they work together
5. If context doesn't contain enough info, say: "Based on these N files: [list ALL files]. I don't see [X] specifically."
6. DO NOT skip or ignore any retrieved files - mention every single one
7. When showing code, quote EXACTLY from the provided context

FORMAT your response:
- List ALL files you received in the context
- For each major component/property, cite which file it comes from
- Explain relationships between files/classes (who uses who)
- Quote relevant code sections from each file"""
    
    # Detect which backend to use
    backend = detect_llm_backend()
    
    if backend == "mlx":
        return _get_mlx_response(prompt, context, system_prompt)
    else:
        return _get_ollama_response(prompt, context, system_prompt)


def _get_mlx_response(prompt: str, context: str, system_prompt: str) -> str:
    """
    Get response using MLX (Apple Silicon optimized).
    
    MLX provides the best performance on Apple Silicon but only works on M1/M2/M3 Macs.
    """
    try:
        from mlx_lm import load, generate
        
        full_prompt = f"{context}\n\n{prompt}" if context else prompt
        
        # Model can be set via env var (use HuggingFace model ID for MLX)
        model_name = os.getenv("SLOT_ASSISTANT_MODEL", "mlx-community/Qwen2.5-Coder-7B-Instruct-4bit")
        
        # Load model (cached after first load)
        model, tokenizer = load(model_name)
        
        # Format as chat
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": full_prompt},
        ]
        chat_prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        
        # Generate response
        response = generate(model, tokenizer, prompt=chat_prompt, max_tokens=1024)
        return response
        
    except ImportError:
        raise RuntimeError(
            "MLX is not installed. Either:\n"
            "1. Install MLX: pip install mlx-lm\n"
            "2. Or use Ollama instead (set SLOT_ASSISTANT_BACKEND=ollama)"
        )
    except Exception as e:
        raise RuntimeError(f"MLX inference error: {e}")


def _get_ollama_response(prompt: str, context: str, system_prompt: str) -> str:
    """
    Get response using Ollama (cross-platform).
    
    Ollama works on Windows, Linux, and macOS. Requires Ollama to be installed
    and running as a local server.
    """
    try:
        from slot_assistant.llm.ollama_client import get_ollama_response
        return get_ollama_response(prompt, context, system_prompt)
        
    except RuntimeError as e:
        # Ollama-specific errors (server not running, etc.)
        raise e
    except Exception as e:
        raise RuntimeError(
            f"Ollama error: {e}\n\n"
            "Make sure Ollama is installed and running:\n"
            "1. Download from https://ollama.ai/download\n"
            "2. Run: ollama pull qwen2.5-coder:7b\n"
            "3. Ollama server should start automatically"
        )


@app.command()
def ingest(
    code_path: str = typer.Option(
        os.getenv("CODEBASE_PATH", "./data/raw/codebase"), 
        help="Path to codebase (can also set CODEBASE_PATH env var)"
    ),
    docs_path: str = typer.Option(
        os.getenv("DOCS_PATH", "./data/raw/docs"), 
        help="Path to documentation (can also set DOCS_PATH env var)"
    ),
    force: bool = typer.Option(False, "--force", "-f", help="Force re-indexing"),
):
    """Ingest codebase and docs into the vector store."""
    from slot_assistant.rag.store import VectorStore
    from slot_assistant.rag.loader import load_directory
    
    console.print(f"[bold blue]Indexing codebase from:[/bold blue] {code_path}")
    
    # Initialize vector store
    store = VectorStore()
    
    # Check if already indexed
    if store.count() > 0 and not force:
        console.print(f"[yellow]Vector store already has {store.count()} documents.[/yellow]")
        console.print("[yellow]Use --force to re-index.[/yellow]")
        return
    
    # Load documents from codebase
    console.print("[cyan]Loading code files...[/cyan]")
    documents = load_directory(code_path)
    
    if not documents:
        console.print(f"[red]No documents found in {code_path}[/red]")
        return
    
    console.print(f"[green]Found {len(documents)} documents[/green]")
    
    # Add to vector store
    store.add_documents(documents)
    
    console.print(f"[bold green]✓ Indexing complete! Total documents: {store.count()}[/bold green]")


@app.command()
def ask(
    question: str = typer.Argument(..., help="Question to ask"),
    use_rag: bool = typer.Option(True, help="Use RAG to retrieve code context"),
):
    """Ask a question about the codebase."""
    from slot_assistant.rag.store import VectorStore
    
    # Detect and display backend
    backend = detect_llm_backend()
    console.print(f"[dim]Using {backend.upper()} backend[/dim]\n")
    
    context = ""
    
    if use_rag:
        console.print("[cyan]Retrieving relevant code...[/cyan]")
        store = VectorStore()
        
        if store.count() == 0:
            console.print("[yellow]No documents indexed. Run 'slot-assistant ingest' first.[/yellow]")
            use_rag = False
        else:
            results = store.query(question, n_results=5)
            if results:
                context = "\n\n".join(results)
                console.print(f"[green]Retrieved {len(results)} code chunks[/green]\n")
    
    console.print("[cyan]Generating response...[/cyan]\n")
    
    try:
        response = get_llm_response(question, context)
        
        # Display response
        md = Markdown(response)
        console.print(Panel(md, title="Response", border_style="green"))
        
    except RuntimeError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)


@app.command()
def serve(
    host: str = typer.Option(os.getenv("API_HOST", "0.0.0.0"), help="Host to bind to"),
    port: int = typer.Option(int(os.getenv("API_PORT", "8000")), help="Port to bind to"),
):
    """Start the API server."""
    import uvicorn
    from slot_assistant.api.server import app as fastapi_app
    
    # Display backend info
    backend = detect_llm_backend()
    console.print(f"[bold blue]Starting API server with {backend.upper()} backend[/bold blue]")
    console.print(f"[cyan]Server will be available at http://{host}:{port}[/cyan]\n")
    
    # Check backend availability
    if backend == "ollama":
        from slot_assistant.llm.ollama_client import check_ollama_available
        if not check_ollama_available():
            console.print("[bold yellow]Warning: Ollama server not detected![/bold yellow]")
            console.print("[yellow]Make sure Ollama is installed and running:[/yellow]")
            console.print("[yellow]  1. Download from https://ollama.ai/download[/yellow]")
            console.print("[yellow]  2. Run: ollama pull qwen2.5-coder:7b[/yellow]\n")
    
    uvicorn.run(
        fastapi_app,
        host=host,
        port=port,
        log_level="info"
    )


if __name__ == "__main__":
    app()
