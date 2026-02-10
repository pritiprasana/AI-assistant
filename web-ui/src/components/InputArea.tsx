import { useState, type KeyboardEvent } from 'react';

interface InputAreaProps {
    onSendMessage: (message: string) => void;
    disabled?: boolean;
    mode: 'general' | 'flair';
}

export default function InputArea({ onSendMessage, disabled, mode }: InputAreaProps) {
    const [input, setInput] = useState('');

    const handleSend = () => {
        if (input.trim() && !disabled) {
            onSendMessage(input.trim());
            setInput('');
        }
    };

    const handleKeyPress = (e: KeyboardEvent<HTMLTextAreaElement>) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    const placeholder =
        mode === 'flair'
            ? 'Ask about Flair framework or your codebase...'
            : 'Ask about general coding concepts...';

    return (
        <div className="border-t border-gray-700/50 bg-[#2c2c40] p-6 shadow-2xl">
            <div className="max-w-4xl mx-auto flex gap-3">
                <textarea
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKeyPress}
                    placeholder={placeholder}
                    disabled={disabled}
                    className="flex-1 bg-[#1a1a2e] border-2 border-gray-700 rounded-3xl px-6 py-4 text-white placeholder-gray-500 resize-none focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500 disabled:opacity-50 shadow-inner"
                    rows={1}
                    style={{ minHeight: '56px', maxHeight: '150px' }}
                />
                <button
                    onClick={handleSend}
                    disabled={disabled || !input.trim()}
                    className="bg-[#6366f1] hover:bg-[#5558e3] disabled:opacity-50 disabled:cursor-not-allowed text-white px-8 rounded-full transition-all flex items-center gap-2 shadow-lg shadow-blue-500/30 hover:shadow-blue-500/50"
                >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M14 5l7 7m0 0l-7 7m7-7H3"
                        />
                    </svg>
                </button>
            </div>
        </div>
    );
}
