import { Fragment } from 'react';
import type { Message } from '../types';
import CodeBlock from './CodeBlock';

interface MessageBubbleProps {
    message: Message;
}

interface ParsedContent {
    type: 'text' | 'code';
    content: string;
    language?: string;
}

export default function MessageBubble({ message }: MessageBubbleProps) {
    const isUser = message.role === 'user';

    // Parse code blocks from message content
    const parseContent = (content: string): ParsedContent[] => {
        const parts: ParsedContent[] = [];
        const codeBlockRegex = /```(\w+)?\n([\s\S]*?)```/g;
        let lastIndex = 0;
        let match;

        while ((match = codeBlockRegex.exec(content)) !== null) {
            // Add text before code block
            if (match.index > lastIndex) {
                const text = content.slice(lastIndex, match.index);
                if (text.trim()) {
                    parts.push({ type: 'text', content: text });
                }
            }

            // Add code block
            const language = match[1] || 'typescript';
            const code = match[2].trim();
            parts.push({ type: 'code', content: code, language });

            lastIndex = match.index + match[0].length;
        }

        // Add remaining text
        if (lastIndex < content.length) {
            const text = content.slice(lastIndex);
            if (text.trim()) {
                parts.push({ type: 'text', content: text });
            }
        }

        return parts.length > 0 ? parts : [{ type: 'text', content }];
    };

    const parsedContent = parseContent(message.content);

    return (
        <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4 px-4`}>
            <div className={`max-w-3xl ${isUser ? 'ml-auto' : ''}`}>
                <div
                    className={`rounded-2xl px-5 py-3 ${isUser
                        ? 'bg-gradient-to-r from-blue-600 to-blue-700 text-white'
                        : 'bg-gradient-to-r from-[#2a2a3e] to-[#2f2f45] text-gray-100 border border-gray-700'
                        }`}
                >
                    {parsedContent.map((part, idx) => (
                        <Fragment key={idx}>
                            {part.type === 'text' ? (
                                <div className="whitespace-pre-wrap break-words">{part.content}</div>
                            ) : (
                                <CodeBlock code={part.content} language={part.language || 'text'} />
                            )}
                        </Fragment>
                    ))}
                </div>

                {/* Show sources if available (for assistant messages with RAG context) */}
                {!isUser && message.sources && message.sources.length > 0 && (
                    <details className="mt-2 text-xs">
                        <summary className="cursor-pointer text-gray-400 hover:text-gray-300 flex items-center gap-1">
                            <span>📄</span>
                            <span>Retrieved {message.sources.length} source{message.sources.length > 1 ? 's' : ''} from codebase</span>
                        </summary>
                        <div className="mt-2 bg-[#1f1f2e] rounded-lg p-3 space-y-1.5">
                            {message.sources.map((source, idx) => (
                                <div key={idx} className="flex items-start gap-2 text-gray-300">
                                    <span className="text-purple-400">→</span>
                                    <div>
                                        <span className="font-mono text-blue-300">{source.filename}</span>
                                        {source.name && source.name !== 'anonymous' && (
                                            <span className="text-gray-400"> :: <span className="text-green-300">{source.name}</span></span>
                                        )}
                                        {source.lines && (
                                            <span className="text-gray-500"> (lines {source.lines})</span>
                                        )}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </details>
                )}
            </div>
        </div>
    );
}
