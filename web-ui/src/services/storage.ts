import { Message } from '../types';

const STORAGE_KEY = 'flair_assistant_messages';

export const messageStorage = {
    save: (messages: Message[]) => {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(messages));
    },

    load: (): Message[] => {
        const stored = localStorage.getItem(STORAGE_KEY);
        return stored ? JSON.parse(stored) : [];
    },

    clear: () => {
        localStorage.removeItem(STORAGE_KEY);
    },
};
