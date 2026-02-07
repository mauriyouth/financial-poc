import { api, API_BASE_URL } from './client';
import { DocumentMetadata } from './documents';

export interface BBox {
    // PDF coordinates
    page?: number;
    x?: number;
    y?: number;
    width?: number;
    height?: number;

    // Web/HTML selectors
    selector?: string;
    xpath?: string;
    offset?: number;

    // Text positions
    line_start?: number;
    line_end?: number;
    char_start?: number;
    char_end?: number;
}

export interface Citation {
    id: string;
    chunk_id: string;
    source_name: string;
    source_type: string;
    content: string;
    bbox?: BBox;
    metadata?: Record<string, unknown>;
}

export interface Message {
    id: string;
    conversation_id: string;
    role: 'user' | 'assistant';
    content: string;
    sources?: DocumentMetadata[];
    citations?: Citation[];  // NEW: Citations with bbox
    attachments?: DocumentMetadata[];  // For files attached to user messages
    created_at: string;
    thinking_steps?: string[]; // Legacy: raw text thinking
    reasoning_events?: StreamEvent[]; // Structured reasoning events for ReasoningPanel
    agent_transitions?: Array<{ from: string; to: string; reason: string }>;  // NEW: Agent transitions
}

export interface Conversation {
    id: string;
    title?: string;
    created_at: string;
    messages: Message[];
}

export const createConversation = async (title?: string): Promise<Conversation> => {
    const response = await api.post<Conversation>('/chat/conversations', { title });
    return response.data;
};

export const sendMessage = async (
    conversationId: string,
    content: string,
    provider: string = "adk",  // Use agent system by default
    model?: string,
    agentName?: string
): Promise<Message> => {
    const response = await api.post<Message>('/chat/messages', {
        conversation_id: conversationId,
        content,
        provider,
        model,
        agent_name: agentName,
    });
    return response.data;
};

export const getMessages = async (conversationId: string): Promise<Message[]> => {
    const response = await api.get<Message[]>(`/chat/conversations/${conversationId}/messages`);
    return response.data;
};

export const getConversations = async (): Promise<Conversation[]> => {
    const response = await api.get<Conversation[]>('/chat/conversations');
    return response.data;
};


export interface StreamEvent {
    type: 'thinking' | 'content' | 'thinking_start' | 'block_stop' | 'done' | 'error' | 'tool_call' | 'tool_result' | 'llm_error' | 'agent_start' | 'agent_end';
    content?: string;
    agent_name?: string;
    model?: string;
    tools_available?: string[];
    tool_name?: string;
    arguments?: Record<string, unknown>;
    result?: Record<string, unknown>;
    error_code?: string;
    error_message?: string;
}

export const streamMessage = async (
    conversationId: string,
    content: string,
    provider: string = "anthropic",
    onEvent: (event: StreamEvent) => void,
    model?: string,
    agentName?: string
): Promise<void> => {
    const response = await fetch(`${API_BASE_URL}/chat/stream`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            conversation_id: conversationId,
            content,
            provider,
            model,
            agent_name: agentName,
        }),
    });

    if (!response.body) return;

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        // Split on newlines to handle multiple JSON objects
        const lines = buffer.split('\n');
        buffer = lines.pop() || ''; // Keep the last incomplete line in buffer

        for (const line of lines) {
            if (line.trim()) {
                try {
                    const event = JSON.parse(line) as StreamEvent;
                    onEvent(event);
                } catch (e) {
                    console.error('Failed to parse JSON:', line, e);
                }
            }
        }
    }
};

export interface Model {
    id: string;
    name: string;
}

export const getModels = async (): Promise<Model[]> => {
    const response = await api.get<Model[]>('/chat/models');
    return response.data;
};

export const improvePrompt = async (prompt: string, provider: string = "adk", model?: string): Promise<string> => {
    const response = await api.post<{ improved_prompt: string }>('/chat/improve-prompt', {
        prompt,
        provider,
        model
    });
    return response.data.improved_prompt;
};

export interface Agent {
    name: string;
    description: string;
}

export const getAgents = async (): Promise<Agent[]> => {
    const response = await api.get<Agent[]>('/chat/agents');
    return response.data;
};
