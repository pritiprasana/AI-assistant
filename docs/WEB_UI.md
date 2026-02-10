# Web UI Documentation

## Overview

The Flair Assistant Web UI is a modern React-based chat interface for interacting with the RAG-powered codebase assistant.

## Technology Stack

- **Framework**: React 18
- **Build Tool**: Vite 6
- **Language**: TypeScript
- **Styling**: Tailwind CSS v4
- **HTTP Client**: Axios
- **State Management**: React hooks + localStorage

## Project Structure

```
web-ui/
├── src/
│   ├── components/       # React components
│   │   ├── Header.tsx           # Top bar with mode toggle
│   │   ├── ChatContainer.tsx    # Message history
│   │   ├── MessageBubble.tsx    # Individual messages
│   │   ├── CodeBlock.tsx        # Syntax highlighting
│   │   └── InputArea.tsx        # Input field + send
│   ├── services/         # External integrations
│   │   ├── api.ts              # API client
│   │   └── storage.ts          # localStorage wrapper
│   ├── types.ts          # TypeScript interfaces
│   ├── App.tsx           # Main application
│   ├── main.tsx          # Entry point
│   └── index.css         # Tailwind config
├── public/               # Static assets
├── index.html            # HTML template
├── vite.config.ts        # Vite configuration
├── tailwind.config.js    # Tailwind config
└── package.json          # Dependencies

## Components

### Header (`components/Header.tsx`)

**Purpose**: Top navigation bar with branding and mode selector

**Features**:
- Flair Assistant logo/title
- Mode toggle buttons (General ⇄ Flair)
- Gradient effect on active Flair mode

**Props**:
```typescript
interface HeaderProps {
  mode: Mode;
  onModeChange: (mode: Mode) => void;
}
```

**Styling**:
- Pill-shaped toggle buttons
- Purple-to-gold gradient on Flair button
- Smooth hover transitions

### ChatContainer (`components/ChatContainer.tsx`)

**Purpose**: Scrollable message history

**Features**:
- Auto-scroll to bottom on new message
- Displays all messages in conversation
- Loading indicator during API calls

**Props**:
```typescript
interface ChatContainerProps {
  messages: Message[];
  isLoading: boolean;
}
```

**Auto-scroll Logic**:
```typescript
useEffect(() => {
  messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
}, [messages]);
```

### MessageBubble (`components/MessageBubble.tsx`)

**Purpose**: Individual message display with optional code rendering

**Features**:
- Different styling for user vs. assistant
- Code block detection and syntax highlighting
- Expandable sources panel (assistant messages only)
- Markdown support for formatting

**Props**:
```typescript
interface MessageBubbleProps {
  message: Message;
}

interface Message {
  role: 'user' | 'assistant';
  content: string;
  sources?: Source[];  // Only for assistant
}
```

**Sources Display**:
```typescript
// Collapsible section showing retrieved code files
<div className=\"sources-panel\">
  <button onClick={() => setShowSources(!showSources)}>
    📄 Retrieved {sources.length} sources
  </button>
  {showSources && (
    <ul>
      {sources.map(source => (
        <li>{source.filename} (lines {source.lines})</li>
      ))}
    </ul>
  )}
</div>
```

### CodeBlock (`components/CodeBlock.tsx`)

**Purpose**: Syntax-highlighted code with copy functionality

**Features**:
- Language detection from markdown code blocks
- Syntax highlighting colors
- Copy button with success feedback
- Gradient border (purple-to-gold)

**Props**:
```typescript
interface CodeBlockProps {
  code: string;
  language?: string;
}
```

**Copy Logic**:
```typescript
const copyToClipboard = async () => {
  await navigator.clipboard.writeText(code);
  setCopied(true);
  setTimeout(() => setCopied(false), 2000);
};
```

### InputArea (`components/InputArea.tsx`)

**Purpose**: Message composition and submission

**Features**:
- Multi-line textarea with auto-resize
- Send button (keyboard: Enter)
- Disabled state during loading
- Placeholder text

**Props**:
```typescript
interface InputAreaProps {
  onSendMessage: (message: string) => void;
  disabled: boolean;
}
```

**Keyboard Handling**:
```typescript
const handleKeyDown = (e: React.KeyboardEvent) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    handleSend();
  }
  // Shift+Enter for newline
};
```

## State Management

### App State (`App.tsx`)

```typescript
const [messages, setMessages] = useState<Message[]>([]);
const [mode, setMode] = useState<Mode>('general');
const [isLoading, setIsLoading] = useState(false);
```

### Persistence

**Chat History** (localStorage):
```typescript
// Save on every message
useEffect(() => {
  storage.saveMessages(messages);
}, [messages]);

// Load on mount
useEffect(() => {
  const saved = storage.loadMessages();
  setMessages(saved || []);
}, []);
```

**Mode Preference** (localStorage):
```typescript
const handleModeChange = (newMode: Mode) => {
  setMode(newMode);
  localStorage.setItem('flair-mode', newMode);
};
```

## API Integration

### Service Layer (`services/api.ts`)

```typescript
export const api = {
  async sendMessage(message: string, useRag: boolean): Promise<ChatResponse> {
    const response = await axios.post(`${API_URL}/chat`, {
      message,
      use_rag: useRag,
    });
    return response.data;
  },
  
  async getStatus(): Promise<RagStatus> {
    const response = await axios.get(`${API_URL}/rag/status`);
    return response.data;
  },
};
```

### Message Flow

```typescript
const handleSendMessage = async (text: string) => {
  // Add user message
  const userMessage = { role: 'user', content: text };
  setMessages(prev => [...prev, userMessage]);
  
  setIsLoading(true);
  
  try {
    // Call API (RAG enabled if Flair mode)
    const response = await api.sendMessage(text, mode === 'flair');
    
    // Add assistant response
    const assistantMessage = {
      role: 'assistant',
      content: response.response,
      sources: response.sources,  // Only in Flair mode
    };
    setMessages(prev => [...prev, assistantMessage]);
    
  } catch (error) {
    // Show error message
    const errorMessage = {
      role: 'assistant',
      content: `Error: ${error.message}`,
    };
    setMessages(prev => [...prev, errorMessage]);
  } finally {
    setIsLoading(false);
  }
};
```

## Styling

### Tailwind CSS v4 Configuration

**`index.css`**:
```css
@import "tailwindcss";

@theme {
  --color-primary: #9333ea;     /* purple-600 */
  --color-secondary: #eab308;   /* yellow-500 (gold) */
  --color-dark: #1e293b;        /* slate-800 */
  --color-darker: #0f172a;      /* slate-900 */
}
```

### Key Styles

**Gradient Backgrounds**:
```css
/* Flair button */
.bg-gradient-to-r.from-purple-600.to-yellow-500

/* Message bubbles (assistant) */
.bg-gradient-to-br.from-slate-700.to-slate-800
```

**Rounded Corners**:
```css
/* Mode toggle buttons */
.rounded-full           /* Fully rounded pills */

/* Message bubbles */
.rounded-3xl            /* Very rounded (24px) */
```

### Responsive Design

```typescript
// Adapts to different screen sizes
<div className=\"
  max-w-4xl           /* Max width on large screens */
  mx-auto             /* Center align */
  px-4 sm:px-6        /* Padding adjusts by breakpoint */
\">
```

## Environment Variables

**`.env`** (in `web-ui/`):
```bash
VITE_API_URL=http://localhost:8000
```

**Usage**:
```typescript
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
```

## Development

### Running Locally

```bash
cd web-ui
npm install
npm run dev
```

Runs on http://localhost:5173

### Building for Production

```bash
npm run build
```

Output in `dist/` directory.

### Preview Production Build

```bash
npm run preview
```

## Troubleshooting

### Styles not applying
- **Check**: Tailwind CSS v4 syntax (`@import` not `@tailwind`)
- **Fix**: Clear cache and restart dev server

### API connection errors
- **Check**: Is API server running on port 8000?
- **Check**: CORS configuration in `server.py`
- **Fix**: Verify `VITE_API_URL` in `.env`

### Sources not showing
- **Check**: Is mode set to "Flair"?
- **Check**: Does API response include `sources` array?
- **Fix**: Restart API server to reload deduplication logic

### Messages not persisting
- **Check**: Browser localStorage enabled?
- **Fix**: Check console for storage errors

## Future Enhancements

- [ ] Streaming responses for faster perceived latency
- [ ] Export chat history to file
- [ ] Dark/light theme toggle
- [ ] Syntax highlighting theme selector
- [ ] Voice input
- [ ] Mobile-optimized UI
