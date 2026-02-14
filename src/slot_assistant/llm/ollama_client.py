"""
Ollama LLM client for cross-platform support.

Uses the /api/chat endpoint with proper message roles (system, user)
so the model correctly distinguishes instructions from user queries.
"""

import os
import requests


def get_ollama_response(prompt: str, context: str = "", system_prompt: str = "") -> str:
    """Get response from Ollama using the chat API with proper message roles."""
    ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    model = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b")

    # Build the user message with context
    user_content = ""
    if context:
        user_content += f"{context}\n\n"
    user_content += prompt

    # Build messages array with proper roles
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_content})

    try:
        response = requests.post(
            f"{ollama_host}/api/chat",
            json={
                "model": model,
                "messages": messages,
                "stream": False,
                "options": {
                    "num_ctx": 8192,  # Larger context window for code
                },
            },
            timeout=180,
        )
        response.raise_for_status()

        return response.json().get("message", {}).get("content", "")

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
    """Check if Ollama server is running and accessible."""
    ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    try:
        response = requests.get(f"{ollama_host}/api/tags", timeout=5)
        return response.status_code == 200
    except Exception:
        return False


def list_ollama_models() -> list[str]:
    """List all models available in Ollama."""
    ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    try:
        response = requests.get(f"{ollama_host}/api/tags", timeout=5)
        response.raise_for_status()
        models = response.json().get("models", [])
        return [model["name"] for model in models]
    except Exception:
        return []
