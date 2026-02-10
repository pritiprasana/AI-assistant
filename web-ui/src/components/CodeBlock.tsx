import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { useState } from 'react';

interface CodeBlockProps {
    code: string;
    language?: string;
    filename?: string;
}

export default function CodeBlock({ code, language = 'typescript', filename }: CodeBlockProps) {
    const [copied, setCopied] = useState(false);

    const handleCopy = () => {
        navigator.clipboard.writeText(code);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    return (
        <div className="relative my-3 rounded-2xl overflow-hidden bg-gradient-to-r from-[#8b5cf6] to-[#fbbf24] p-[2px]">
            <div className="bg-dark-code rounded-2xl overflow-hidden">
                {filename && (
                    <div className="px-4 py-3 bg-gradient-to-r from-purple-900/40 to-yellow-900/40 text-sm text-gray-200 border-b border-gray-700/50">
                        ⚡ Based on <span className="text-yellow-300 font-semibold">{filename}</span> in your codebase:
                    </div>
                )}
                <div className="relative">
                    <button
                        onClick={handleCopy}
                        className="absolute top-3 right-3 px-3 py-1.5 bg-gray-800/80 hover:bg-gray-700 text-gray-200 text-xs rounded-lg transition-all flex items-center gap-1.5 shadow-md backdrop-blur-sm"
                    >
                        {copied ? (
                            <>
                                <span>✓</span>
                                <span>Copied</span>
                            </>
                        ) : (
                            <>
                                <span>📋</span>
                                <span>Copy</span>
                            </>
                        )}
                    </button>
                    <SyntaxHighlighter
                        language={language}
                        style={vscDarkPlus}
                        customStyle={{
                            margin: 0,
                            padding: '1.25rem',
                            background: '#0f0f16',
                            fontSize: '0.9rem',
                            borderRadius: '0 0 1rem 1rem',
                        }}
                    >
                        {code}
                    </SyntaxHighlighter>
                </div>
            </div>
        </div>
    );
}
