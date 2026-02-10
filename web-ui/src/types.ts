export interface Message {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    timestamp: number;
    sources?: ContextSource[];  // RAG context sources
}

export interface ContextSource {
    filename: string;
    name?: string;
    nodeType?: string;
    lines?: string;
}

export interface ChatRequest {
    message: string;
    use_rag: boolean;
    context?: string;
}

export interface ChatResponse {
    response: string;
    context_used?: string;
    sources?: ContextSource[];
}

export type Mode = 'general' | 'flair';
