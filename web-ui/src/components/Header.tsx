import type { Mode } from '../types';

interface HeaderProps {
    mode: Mode;
    onModeChange: (mode: Mode) => void;
    onSettingsClick: () => void;
}

export default function Header({ mode, onModeChange, onSettingsClick }: HeaderProps) {
    return (
        <header className="bg-[#3a3a52] border-b border-gray-700 px-6 py-5 shadow-lg">
            <div className="flex items-center justify-between max-w-6xl mx-auto">
                {/* Logo */}
                <div className="flex items-center gap-3">
                    <span className="text-3xl">⚡</span>
                    <h1 className="text-2xl font-bold text-white">Flair Assistant</h1>
                </div>

                {/* Mode Toggle */}
                <div className="flex gap-2 bg-[#2a2a3e] rounded-full p-1.5 shadow-inner">
                    <button
                        onClick={() => onModeChange('general')}
                        className={`px-6 py-2.5 rounded-full transition-all font-medium text-sm ${mode === 'general'
                            ? 'bg-gray-600 text-white shadow-md'
                            : 'text-gray-400 hover:text-white hover:bg-gray-700/50'
                            }`}
                    >
                        💡 General
                    </button>
                    <button
                        onClick={() => onModeChange('flair')}
                        className={`px-6 py-2.5 rounded-full transition-all font-medium text-sm ${mode === 'flair'
                            ? 'bg-gradient-to-r from-[#8b5cf6] to-[#fbbf24] text-white shadow-lg shadow-purple-500/50'
                            : 'text-gray-400 hover:text-white hover:bg-gray-700/50'
                            }`}
                    >
                        ⚡ Flair
                    </button>
                </div>

                {/* Settings */}
                <button
                    onClick={onSettingsClick}
                    className="text-gray-400 hover:text-white transition-colors p-2 hover:bg-gray-700/30 rounded-lg"
                >
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
                        />
                        <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                        />
                    </svg>
                </button>
            </div>
        </header>
    );
}
