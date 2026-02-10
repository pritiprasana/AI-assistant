import * as vscode from 'vscode';
import axios from 'axios';

export class ChatViewProvider implements vscode.WebviewViewProvider {
    public static readonly viewType = 'slot-assistant.chatView';
    private _view?: vscode.WebviewView;
    private _messages: { role: string; content: string }[] = [];

    constructor(private readonly _extensionUri: vscode.Uri) { }

    public resolveWebviewView(
        webviewView: vscode.WebviewView,
        _context: vscode.WebviewViewResolveContext,
        _token: vscode.CancellationToken
    ) {
        this._view = webviewView;

        webviewView.webview.options = {
            enableScripts: true,
            localResourceRoots: [this._extensionUri]
        };

        webviewView.webview.html = this._getHtmlForWebview();

        // Handle messages from the webview
        webviewView.webview.onDidReceiveMessage(async (data) => {
            switch (data.type) {
                case 'sendMessage':
                    await this._handleUserMessage(data.message);
                    break;
                case 'clear':
                    this._messages = [];
                    this._updateChat();
                    break;
            }
        });
    }

    private async _handleUserMessage(message: string) {
        // Add user message
        this._messages.push({ role: 'user', content: message });
        this._updateChat();

        // Get AI response
        const config = vscode.workspace.getConfiguration('slot-assistant');
        const apiUrl = config.get<string>('apiUrl', 'http://localhost:8000');

        try {
            // Get selected code as context
            const editor = vscode.window.activeTextEditor;
            const selectedCode = editor ? editor.document.getText(editor.selection) : null;

            const response = await axios.post(`${apiUrl}/chat`, {
                message: message,
                context: selectedCode || null,
                use_rag: true
            });

            this._messages.push({ role: 'assistant', content: response.data.response });
        } catch (error: any) {
            this._messages.push({
                role: 'assistant',
                content: `❌ Error: ${error.message}\n\nMake sure the API server is running:\n\`slot-assistant serve\``
            });
        }

        this._updateChat();
    }

    private _updateChat() {
        if (this._view) {
            this._view.webview.postMessage({
                type: 'updateMessages',
                messages: this._messages
            });
        }
    }

    private _getHtmlForWebview(): string {
        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Slot Assistant Chat</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: var(--vscode-font-family);
            background: var(--vscode-sideBar-background);
            color: var(--vscode-foreground);
            height: 100vh;
            display: flex;
            flex-direction: column;
        }
        .header {
            padding: 12px;
            background: var(--vscode-sideBarSectionHeader-background);
            border-bottom: 1px solid var(--vscode-sideBarSectionHeader-border);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .header h3 { font-size: 13px; font-weight: 600; }
        .clear-btn {
            background: transparent;
            border: none;
            color: var(--vscode-foreground);
            cursor: pointer;
            opacity: 0.7;
            font-size: 12px;
        }
        .clear-btn:hover { opacity: 1; }
        .messages {
            flex: 1;
            overflow-y: auto;
            padding: 12px;
        }
        .message {
            margin-bottom: 16px;
            animation: fadeIn 0.2s ease;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(5px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .message.user .bubble {
            background: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
            margin-left: 20%;
        }
        .message.assistant .bubble {
            background: var(--vscode-editor-background);
            border: 1px solid var(--vscode-editorWidget-border);
            margin-right: 10%;
        }
        .bubble {
            padding: 10px 14px;
            border-radius: 12px;
            font-size: 13px;
            line-height: 1.5;
            white-space: pre-wrap;
            word-break: break-word;
        }
        .bubble code {
            background: var(--vscode-textCodeBlock-background);
            padding: 2px 6px;
            border-radius: 4px;
            font-family: var(--vscode-editor-font-family);
            font-size: 12px;
        }
        .bubble pre {
            background: var(--vscode-textCodeBlock-background);
            padding: 12px;
            border-radius: 6px;
            overflow-x: auto;
            margin: 8px 0;
        }
        .bubble pre code {
            padding: 0;
            background: transparent;
        }
        .input-area {
            padding: 12px;
            border-top: 1px solid var(--vscode-sideBarSectionHeader-border);
            background: var(--vscode-sideBar-background);
        }
        .input-wrapper {
            display: flex;
            gap: 8px;
        }
        textarea {
            flex: 1;
            background: var(--vscode-input-background);
            color: var(--vscode-input-foreground);
            border: 1px solid var(--vscode-input-border);
            border-radius: 6px;
            padding: 10px 12px;
            font-family: var(--vscode-font-family);
            font-size: 13px;
            resize: none;
            min-height: 60px;
            max-height: 120px;
        }
        textarea:focus {
            outline: none;
            border-color: var(--vscode-focusBorder);
        }
        textarea::placeholder { color: var(--vscode-input-placeholderForeground); }
        .send-btn {
            background: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
            border: none;
            border-radius: 6px;
            padding: 0 16px;
            cursor: pointer;
            font-weight: 500;
            align-self: flex-end;
            height: 36px;
        }
        .send-btn:hover { background: var(--vscode-button-hoverBackground); }
        .send-btn:disabled { opacity: 0.5; cursor: not-allowed; }
        .typing {
            display: flex;
            gap: 4px;
            padding: 8px 12px;
        }
        .typing span {
            width: 8px;
            height: 8px;
            background: var(--vscode-foreground);
            border-radius: 50%;
            opacity: 0.4;
            animation: typing 1s infinite;
        }
        .typing span:nth-child(2) { animation-delay: 0.2s; }
        .typing span:nth-child(3) { animation-delay: 0.4s; }
        @keyframes typing {
            0%, 100% { opacity: 0.4; transform: scale(1); }
            50% { opacity: 1; transform: scale(1.1); }
        }
        .welcome {
            text-align: center;
            padding: 40px 20px;
            opacity: 0.7;
        }
        .welcome h2 { font-size: 16px; margin-bottom: 8px; }
        .welcome p { font-size: 12px; }
    </style>
</head>
<body>
    <div class="header">
        <h3>🎰 Slot Assistant</h3>
        <button class="clear-btn" onclick="clearChat()">Clear</button>
    </div>
    
    <div class="messages" id="messages">
        <div class="welcome">
            <h2>Ask me about slot game code!</h2>
            <p>I can help with reels, symbols, paylines, and more.</p>
        </div>
    </div>
    
    <div class="input-area">
        <div class="input-wrapper">
            <textarea 
                id="input" 
                placeholder="Ask about slot game framework..."
                onkeydown="handleKey(event)"
            ></textarea>
            <button class="send-btn" id="sendBtn" onclick="sendMessage()">Send</button>
        </div>
    </div>

    <script>
        const vscode = acquireVsCodeApi();
        const messagesEl = document.getElementById('messages');
        const inputEl = document.getElementById('input');
        const sendBtn = document.getElementById('sendBtn');
        let isWaiting = false;

        function handleKey(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        }

        function sendMessage() {
            const message = inputEl.value.trim();
            if (!message || isWaiting) return;
            
            inputEl.value = '';
            isWaiting = true;
            sendBtn.disabled = true;
            
            vscode.postMessage({ type: 'sendMessage', message });
        }

        function clearChat() {
            vscode.postMessage({ type: 'clear' });
            messagesEl.innerHTML = '<div class="welcome"><h2>Ask me about slot game code!</h2><p>I can help with reels, symbols, paylines, and more.</p></div>';
        }

        function formatMessage(content) {
            // Simple markdown-like formatting
            return content
                .replace(/\`\`\`(\\w+)?\\n([\\s\\S]*?)\`\`\`/g, '<pre><code>$2</code></pre>')
                .replace(/\`([^\`]+)\`/g, '<code>$1</code>');
        }

        window.addEventListener('message', (event) => {
            const { type, messages } = event.data;
            if (type === 'updateMessages') {
                isWaiting = false;
                sendBtn.disabled = false;
                
                if (messages.length === 0) {
                    messagesEl.innerHTML = '<div class="welcome"><h2>Ask me about slot game code!</h2><p>I can help with reels, symbols, paylines, and more.</p></div>';
                    return;
                }
                
                messagesEl.innerHTML = messages.map(m => 
                    '<div class="message ' + m.role + '">' +
                    '<div class="bubble">' + formatMessage(m.content) + '</div>' +
                    '</div>'
                ).join('');
                
                messagesEl.scrollTop = messagesEl.scrollHeight;
            }
        });
    </script>
</body>
</html>`;
    }
}
