import { useRef, useEffect } from 'react';
import type { Message } from '../types';
import MessageBubble from './MessageBubble';

interface ChatContainerProps {
    messages: Message[];
    isLoading?: boolean;
}

export default function ChatContainer({ messages, isLoading }: ChatContainerProps) {
    const bottomRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    return (
        <div className="flex-1 overflow-y-auto px-4 py-6">
            <div className="max-w-4xl mx-auto">
                {messages.length === 0 ? (
                    <div className="flex flex-col items-center justify-center h-full text-center py-20">
                        <div className="text-6xl mb-4">⚡</div>
                        <h2 className="text-2xl font-bold text-white mb-2">Welcome to Flair Assistant</h2>
                        <p className="text-gray-400 max-w-md">
                            Ask me anything about the Flair framework, your codebase, or general coding concepts.
                            Toggle between General and Flair modes to get the best answers.
                        </p>
                    </div>
                ) : (
                    <>
                        {messages.map((message) => (
                            <MessageBubble key={message.id} message={message} />
                        ))}
                        {isLoading && (
                            <div className="flex items-center gap-2 text-gray-400 mb-4">
                                <div className="w-6 h-6 rounded-full bg-gradient-to-br from-primary to-secondary flex items-center justify-center text-xs animate-pulse">
                                    ⚡
                                </div>
                                <span className="animate-pulse">Thinking...</span>
                            </div>
                        )}
                    </>
                )}
                <div ref={bottomRef} />
            </div>
        </div>
    );
}
