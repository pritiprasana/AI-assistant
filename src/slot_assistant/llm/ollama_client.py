"""
Ollama LLM client for cross-platform support.

Ollama is a cross-platform LLM runtime that works on Windows, macOS, and Linux.
This module provides integration with Ollama's REST API for LLM inference.

Installation:
- Download from https://ollama.ai/download
- Run: `ollama pull qwen2.5-coder:7b`
- Server runs on http://localhost:11434
"""

import os
import requests
from typing import Optional


def get_ollama_response(prompt: str, context: str = "", system_prompt: str = "") -> str:
    """
    Get response from Ollama API.
    
    Ollama runs as a local server and provides a REST API for LLM inference.
    This is the cross-platform alternative to MLX for Windows/Linux users.
    
    Args:
        prompt: User's question/query
        context: Retrieved code context from RAG
        system_prompt: System instructions for the LLM
    
    Returns:
        Generated response from the LLM
    
    Raises:
        requests.RequestException: If Ollama server is not running or unreachable
        
    Environment Variables:
        OLLAMA_HOST: Ollama server URL (default: http://localhost:11434)
        OLLAMA_MODEL: Model to use (default: qwen2.5-coder:7b)
    
    Example:
        >>> response = get_ollama_response(
        ...     prompt="How does GamePlayIntro work?",
        ...     context="[Code from RAG]",
        ...     system_prompt="You are a code assistant"
        ... )
    """
    # Get Ollama configuration from environment
    ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    model = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b")
    
    # Build the full prompt with system instructions and context
    full_prompt = ""
    if system_prompt:
        full_prompt += f"{system_prompt}\n\n"
    if context:
        full_prompt += f"{context}\n\n"
    full_prompt += prompt
    
    try:
        # Call Ollama generate API
        # stream=False returns the full response at once (simpler but slower perceived latency)
        response = requests.post(
            f"{ollama_host}/api/generate",
            json={
                "model": model,
                "prompt": full_prompt,
                "stream": False  # Get full response at once
            },
            timeout=120  # 2 minutes timeout for long responses
        )
        response.raise_for_status()
        
        # Extract response text from JSON
        return response.json().get("response", "")
        
    except requests.exceptions.ConnectionError:
        raise RuntimeError(
            f"Could not connect to Ollama at {ollama_host}. "
            "Make sure Ollama is installed and running.\n"
            "Install: https://ollama.ai/download\n"
            f"Run: ollama pull {model}"
        )
    except requests.exceptions.Timeout:
        raise RuntimeError(
            "Ollama request timed out. The model might be too large or the query too complex."
        )
    except Exception as e:
        raise RuntimeError(f"Ollama error: {e}")


def check_ollama_available() -> bool:
    """
    Check if Ollama server is running and accessible.
    
    Returns:
        True if Ollama is available, False otherwise
        
    Example:
        >>> if check_ollama_available():
        ...     print("Ollama is ready!")
    """
    ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    
    try:
        response = requests.get(f"{ollama_host}/api/tags", timeout=5)
        return response.status_code == 200
    except:
        return False


def list_ollama_models() -> list[str]:
    """
    List all models available in Ollama.
    
    Returns:
        List of model names
        
    Example:
        >>> models = list_ollama_models()
        >>> print(models)
        ['qwen2.5-coder:7b', 'llama2:7b']
    """
    ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    
    try:
        response = requests.get(f"{ollama_host}/api/tags", timeout=5)
        response.raise_for_status()
        models = response.json().get("models", [])
        return [model["name"] for model in models]
    except:
        return []
