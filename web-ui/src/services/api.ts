import axios from 'axios';
import { ChatRequest, ChatResponse } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const chatAPI = {
    sendMessage: async (request: ChatRequest): Promise<ChatResponse> => {
        const response = await axios.post<ChatResponse>(`${API_BASE_URL}/chat`, request);
        return response.data;
    },

    checkHealth: async (): Promise<boolean> => {
        try {
            await axios.get(`${API_BASE_URL}/health`);
            return true;
        } catch {
            return false;
        }
    },

    getRagStatus: async (): Promise<{ indexed_documents: number }> => {
        const response = await axios.get(`${API_BASE_URL}/rag/status`);
        return response.data;
    },
};
