import * as vscode from 'vscode';
import axios from 'axios';
import { ChatViewProvider } from './chatViewProvider';

let outputChannel: vscode.OutputChannel;

export function activate(context: vscode.ExtensionContext) {
    console.log('Slot Assistant is now active!');

    outputChannel = vscode.window.createOutputChannel("Slot Assistant");
    context.subscriptions.push(outputChannel);

    // Register Chat View Provider (Sidebar Panel like Copilot Chat)
    const chatViewProvider = new ChatViewProvider(context.extensionUri);
    context.subscriptions.push(
        vscode.window.registerWebviewViewProvider(
            ChatViewProvider.viewType,
            chatViewProvider
        )
    );

    // Command: Ask Slot Assistant
    let askCommand = vscode.commands.registerCommand('slot-assistant.ask', async () => {
        const input = await vscode.window.showInputBox({
            placeHolder: "Ask about the slot framework (e.g., 'How to create a reel?')",
            prompt: "Slot Assistant"
        });

        if (input) {
            await queryAssistant(input);
        }
    });

    // Command: Explain Selection
    let explainCommand = vscode.commands.registerCommand('slot-assistant.explain', async () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            vscode.window.showWarningMessage("No active editor found.");
            return;
        }

        const selection = editor.document.getText(editor.selection);
        if (!selection) {
            vscode.window.showWarningMessage("Please select some code to explain.");
            return;
        }

        await queryAssistant(`Explain this code:\n\n${selection}`, selection);
    });

    // Command: Open Chat (focuses the sidebar)
    let openChatCommand = vscode.commands.registerCommand('slot-assistant.openChat', async () => {
        await vscode.commands.executeCommand('slot-assistant.chatView.focus');
    });

    context.subscriptions.push(askCommand);
    context.subscriptions.push(explainCommand);
    context.subscriptions.push(openChatCommand);
}

async function queryAssistant(message: string, codeContext?: string) {
    const config = vscode.workspace.getConfiguration('slot-assistant');
    const apiUrl = config.get<string>('apiUrl', 'http://localhost:8000');

    outputChannel.show(true);
    outputChannel.appendLine(`\n> You: ${message}`);
    outputChannel.appendLine("> Assistant: Thinking...");

    try {
        const payload = {
            message: message,
            context: codeContext || null,
            use_rag: true
        };

        const response = await axios.post(`${apiUrl}/chat`, payload);
        const answer = response.data.response;

        outputChannel.appendLine(`\n${answer}`);
        outputChannel.appendLine("\n--------------------------------------------------");

    } catch (error: any) {
        outputChannel.appendLine(`\nError calling API: ${error.message}`);
        if (error.code === 'ECONNREFUSED') {
            outputChannel.appendLine("Make sure the API server is running ('slot-assistant serve')");
        }
        vscode.window.showErrorMessage(`Slot Assistant Error: ${error.message}`);
    }
}

export function deactivate() { }
