# Slot Assistant VS Code Extension

AI-powered coding assistant for the Slot Game Framework.

## Features

- **Ask Slot Assistant**: `Cmd+Shift+P` -> `Ask Slot Assistant` to chat with the AI.
- **Explain Selection**: Select code, Right Click -> `Slot Assistant: Explain Selection`.

## Setup

1. **Start the API Server**:
   ```bash
   slot-assistant serve
   ```
   (Ensure `slot-assistant` is in your environment and Mock Mode is on if on M5 Mac)

2. **Configuration**:
   - `slot-assistant.apiUrl`: Set if your server is not at `http://localhost:8000`.

## Requirements

- Python API server running.
