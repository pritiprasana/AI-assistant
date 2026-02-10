# Windows Setup Guide

Complete guide for setting up Flair Assistant on Windows.

## ⚠️ Important Note

The original project uses **MLX** which only works on Apple Silicon Macs. For Windows users, we use **Ollama** as the LLM backend, which provides similar functionality with cross-platform support.

## Prerequisites

### 1. Python 3.9 or higher

**Check if installed**:
```powershell
python --version
```

**Install if needed**:
- Download from [python.org](https://python.org/downloads/)
- **Important**: Check "Add Python to PATH" during installation
- Or use winget: `winget install Python.Python.3.11`

### 2. Node.js 18 or higher

**Check if installed**:
```powershell
node --version
```

**Install if needed**:
- Download from [nodejs.org](https://nodejs.org/)
- Or use winget: `winget install OpenJS.NodeJS`

### 3. Ollama (LLM Backend)

**Download and install**:
1. Go to [ollama.ai/download/windows](https://ollama.ai/download/windows)
2. Download the installer
3. Run the installer (Ollama will start automatically as a Windows service)
4. Verify installation:
   ```powershell
   ollama --version
   ```

**Download the model**:
```powershell
ollama pull qwen2.5-coder:7b
```

This downloads the 7B parameter code model (~4.7GB). Wait for it to complete.

**Verify Ollama is running**:
```powershell
curl http://localhost:11434/api/tags
```

You should see a JSON response with available models.

## Installation

### 1. Clone the Repository

```powershell
git clone <repository-url>
cd AI-assistant
```

### 2. Create Virtual Environment

```powershell
python -m venv .venv
```

### 3. Activate Virtual Environment

**PowerShell**:
```powershell
.venv\Scripts\Activate.ps1
```

**Command Prompt**:
```cmd
.venv\Scripts\activate.bat
```

> **Note**: If you get an execution policy error in PowerShell:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

### 4. Install Python Dependencies

```powershell
pip install -e .
```

This installs the project and its dependencies (excluding MLX, which is Mac-only).

### 5. Configure Environment

```powershell
copy .env.example .env
```

Edit `.env` in Notepad or your favorite editor:

```bash
# Ollama Configuration (Windows uses Ollama instead of MLX)
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen2.5-coder:7b

# RAG Configuration
CHROMA_PERSIST_DIR=./data/chroma
EMBEDDING_MODEL=sentence-transformers/all-mpnet-base-v2

# API Configuration  
API_HOST=0.0.0.0
API_PORT=8000

# Paths - IMPORTANT: Update to your codebase
# Use forward slashes (/) or double backslashes (\\)
CODEBASE_PATH=C:/path/to/your/codebase
DOCS_PATH=./data/raw/docs

# Logging
LOG_LEVEL=INFO
```

**Important**: Windows paths can use:
- Forward slashes: `C:/Users/YourName/project`
- Double backslashes: `C:\\Users\\YourName\\project`

### 6. Index Your Codebase

```powershell
slot-assistant ingest --force
```

This will:
- Parse TypeScript/JavaScript files using AST
- Generate embeddings
- Store in ChromaDB vector database

**Expected output**:
```
Indexing codebase from: C:/path/to/your/codebase
Loading code files...
Found 250 documents
Adding 1500 chunks to vector store...
✓ Indexing complete! Total documents: 1500
```

### 7. Start the API Server

```powershell
slot-assistant serve
```

**Expected output**:
```
Starting API server with OLLAMA backend
Server will be available at http://0.0.0.0:8000

INFO:     Started server process [12345]
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

Keep this terminal window open.

### 8. Start the Web UI

Open a **new terminal** (keep the server running):

```powershell
cd web-ui
npm install
npm run dev
```

**Expected output**:
```
  VITE v6.0.0  ready in 1200 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

## Using Flair Assistant

1. Open your browser to http://localhost:5173
2. Click the **⚡ Flair** mode button
3. Ask a question:
   ```
   How does the IntroScreen class work?
   ```

4. The system will:
   - Retrieve relevant code from your indexed codebase
   - Send to Ollama for analysis
   - Display the response with source file citations

## Troubleshooting

### Ollama Not Running

**Error**: `Could not connect to Ollama at http://localhost:11434`

**Fix**:
1. Check if Ollama is running:
   ```powershell
   Get-Process ollama
   ```

2. If not running, start it:
   ```powershell
   ollama serve
   ```

3. Or restart the Ollama service:
   - Open Services (Win+R → `services.msc`)
   - Find "Ollama Service"
   - Right-click → Restart

### Model Not Found

**Error**: `model 'qwen2.5-coder:7b' not found`

**Fix**:
```powershell
ollama pull qwen2.5-coder:7b
```

Verify downloaded models:
```powershell
ollama list
```

### Python Not in PATH

**Error**: `'python' is not recognized`

**Fix**:
1. Find Python location: `C:\Users\YourName\AppData\Local\Programs\Python\Python311`
2. Add to PATH:
   - Win+R → `sysdm.cpl` → Advanced → Environment Variables
   - Edit "Path" variable
   - Add Python directory and Scripts directory

### Port 8000 Already in Use

**Error**: `Address already in use`

**Fix**:
1. Find process using port 8000:
   ```powershell
   netstat -ano | findstr :8000
   ```

2. Kill the process:
   ```powershell
   taskkill /PID <process-id> /F
   ```

3. Or use a different port:
   ```powershell
   slot-assistant serve --port 8001
   ```

### Web UI Can't Connect to API

**Error**: Network error in browser console

**Fix**:
1. Verify API server is running on port 8000
2. Check `web-ui/.env`:
   ```bash
   VITE_API_URL=http://localhost:8000
   ```
3. Restart web UI after changing .env

### Slow Performance

**Issue**: Responses take a long time

**Solutions**:

1. **Use smaller model**:
   ```powershell
   ollama pull qwen2.5-coder:3b
   ```
   
   Edit `.env`:
   ```bash
   OLLAMA_MODEL=qwen2.5-coder:3b
   ```

2. **Reduce retrieval count** in `src/slot_assistant/api/server.py`:
   ```python
   n_results=5  # Change from 10 to 5
   ```

3. **Check GPU**: Ollama uses GPU if available (NVIDIA or AMD)
   - GPU: 2-5 seconds per response
   - CPU only: 10-30 seconds per response

## Windows-Specific Tips

### PowerShell vs Command Prompt

- **PowerShell** (recommended): Modern shell, better features
- **Command Prompt**: Traditional Windows shell

Most commands work in both, but activation scripts differ:
- PowerShell: `.venv\Scripts\Activate.ps1`
- CMD: `.venv\Scripts\activate.bat`

### Path Separators

Python and most tools accept forward slashes (`/`) on Windows:
```bash
CODEBASE_PATH=C:/Users/YourName/project  # ✅ Works
CODEBASE_PATH=C:\\Users\\YourName\\project  # ✅ Also works
CODEBASE_PATH=C:\Users\YourName\project  # ❌ Might not work in .env
```

### Terminal Recommendations

While PowerShell and CMD work, consider:
- **Windows Terminal**: Modern, tabbed terminal (built into Windows 11)
- **Git Bash**: Unix-like shell (comes with Git for Windows)

## Differences from Mac Version

| Feature | Mac (MLX) | Windows (Ollama) |
|---------|-----------|------------------|
| LLM Backend | MLX | Ollama |
| Performance | Faster | Slightly slower |
| Installation | pip install mlx-lm | Download Ollama installer |
| Model Download | Automatic on first use | Manual via `ollama pull` |
| GPU Support | Apple Silicon (M1/M2/M3) | NVIDIA, AMD, or CPU |

## Advanced Configuration

### Using a Different Model

Ollama supports many models:
```powershell
# List available models
ollama list

# Pull a different model
ollama pull codellama:7b

# Update .env
OLLAMA_MODEL=codellama:7b
```

### GPU Acceleration

**Check if GPU is being used**:
1. Run a query
2. Open Task Manager
3. Check GPU usage under "Performance" tab

If GPU is not being used:
- Update GPU drivers (NVIDIA or AMD)
- Ollama automatically uses GPU if available

### Running in Background

**Option 1**: Use Windows Service (default)
- Ollama runs as a service automatically
- Starts on boot

**Option 2**: Run manually
```powershell
ollama serve
```

## Next Steps

1. **Test the system**: Ask questions about your codebase
2. **Review sources**: Check if retrieved code is relevant
3. **Provide feedback**: Report issues or suggestions
4. **Explore features**: Try different models and configurations

## Getting Help

If you encounter issues:

1. **Check logs**:
   - API server: Console output where you ran `slot-assistant serve`
   - Ollama: `%LOCALAPPDATA%\Ollama\logs`

2. **Verify installation**:
   ```powershell
   python --version
   node --version
   ollama --version
   slot-assistant --help
   ```

3. **Test each component**:
   ```powershell
   # Test Ollama
   curl http://localhost:11434/api/tags
   
   # Test API
   curl http://localhost:8000/health
   
   # Test RAG
   curl http://localhost:8000/rag/status
   ```

4. **Report issues**: Contact project maintainer with:
   - Windows version
   - Python version
   - Error messages
   - Steps to reproduce
