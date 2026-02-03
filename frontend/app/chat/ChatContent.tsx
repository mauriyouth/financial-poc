"use client";

import { useState, useEffect } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { ChatArea } from '@/components/chat-area';
import { DocumentPreview } from '@/components/document-preview';
import { ResizableHandle, ResizablePanel, ResizablePanelGroup } from '@/components/ui/resizable';
import {
    Message,
    getConversations,
    createConversation,
    getMessages,
    streamMessage,
    getModels
} from '@/lib/api/chat';
import { DocumentMetadata } from '@/lib/api/documents';

export function ChatContent() {
    const searchParams = useSearchParams();
    const router = useRouter();
    const [activeId, setActiveId] = useState<string | null>(null);
    const [messages, setMessages] = useState<Message[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [previewDocuments, setPreviewDocuments] = useState<DocumentMetadata[]>([]);
    const [activePreviewId, setActivePreviewId] = useState<string | null>(null);
    const [isPreviewFullscreen, setIsPreviewFullscreen] = useState(false);
    const [model, setModel] = useState<string>('');

    useEffect(() => {
        const loadModels = async () => {
            try {
                const models = await getModels();
                if (models && models.length > 0) {
                    const storedModel = localStorage.getItem('selectedModel');
                    if (storedModel) {
                        setModel(storedModel);
                    } else {
                        setModel(models[0].id);
                    }
                }
            } catch (error) {
                console.error('Failed to load models:', error);
                setModel('anthropic:claude-opus-4-5-20251101');
            }
        };
        loadModels();
        loadConversations();

        const idFromUrl = searchParams.get('id');
        if (idFromUrl) {
            setActiveId(idFromUrl);
        }

        const pendingMessage = localStorage.getItem('pendingMessage');
        if (pendingMessage && idFromUrl) {
            try {
                const { content, model: pendingModel } = JSON.parse(pendingMessage);
                localStorage.removeItem('pendingMessage');
                if (pendingModel) setModel(pendingModel);
                setTimeout(() => {
                    handleSendMessage(content);
                }, 500);
            } catch (e) {
                console.error('Failed to parse pending message', e);
            }
        }
    }, [searchParams]);

    useEffect(() => {
        if (activeId) {
            loadMessages(activeId);
            router.push(`/chat?id=${activeId}`, { scroll: false });
        }
    }, [activeId, router]);

    const loadConversations = async () => {
        try {
            const data = await getConversations();
            if (data.length > 0 && !activeId && !searchParams.get('id')) {
                setActiveId(data[0].id);
            }
        } catch (error) {
            console.error("Failed to load conversations", error);
        }
    };

    const loadMessages = async (id: string) => {
        try {
            const data = await getMessages(id);
            setMessages(data);
        } catch (error) {
            console.error("Failed to load messages", error);
        }
    };

    const handleSendMessage = async (content: string) => {
        if (!content.trim()) return;
        let conversationId = activeId;
        if (!conversationId) {
            try {
                const newConv = await createConversation("New Chat");
                conversationId = newConv.id;
                setActiveId(conversationId);
                await loadConversations();
            } catch (error) {
                console.error("Failed to create conversation", error);
                return;
            }
        }

        setIsLoading(true);
        const currentActiveId = conversationId;
        const tempUserMsg: Message = {
            id: 'temp-user',
            conversation_id: currentActiveId,
            role: 'user',
            content,
            created_at: new Date().toISOString()
        };
        const tempAiMsg: Message = {
            id: 'temp-ai',
            conversation_id: currentActiveId,
            role: 'assistant',
            content: "",
            created_at: new Date().toISOString()
        };

        setMessages(prev => [...prev, tempUserMsg, tempAiMsg]);
        let hasError = false;

        try {
            let thinkingBuffer = '';
            let provider = "anthropic";
            let model_id: string | undefined = undefined;

            if (model && model.includes(':')) {
                const parts = model.split(':', 2);
                provider = parts[0];
                model_id = parts[1];
            } else if (model) {
                model_id = model;
            }

            await streamMessage(currentActiveId, content, provider, (event) => {
                setMessages(prev => {
                    const newMessages = [...prev];
                    const lastMsg = newMessages[newMessages.length - 1];
                    if (lastMsg.role === 'assistant') {
                        if (event.type === 'thinking_start') {
                            thinkingBuffer = '';
                        } else if (event.type === 'thinking' && event.content) {
                            thinkingBuffer += event.content;
                            lastMsg.thinking_steps = [thinkingBuffer];
                        } else if (event.type === 'content' && event.content) {
                            lastMsg.content += event.content;
                        } else if (event.type === 'error' && event.content) {
                            hasError = true;
                            lastMsg.content = `❌ **Error**: ${event.content}\n\n*Click the retry button to try again.*`;
                            lastMsg.thinking_steps = undefined;
                            setIsLoading(false);
                        }
                    }
                    return newMessages;
                });
            }, model_id);
        } catch (error) {
            console.error("Streaming failed", error);
            setMessages(prev => {
                const newMessages = [...prev];
                const lastMsg = newMessages[newMessages.length - 1];
                if (lastMsg.role === 'assistant') {
                    lastMsg.content = `❌ **Error**: ${error instanceof Error ? error.message : 'Failed to generate response'}\n\n*Click the retry button to try again.*`;
                    lastMsg.thinking_steps = undefined;
                }
                return newMessages;
            });
            hasError = true;
        } finally {
            if (!hasError) setIsLoading(false);
            loadMessages(currentActiveId);
        }
    };

    const handleSourceClick = (source: DocumentMetadata) => {
        setPreviewDocuments(prev => {
            const exists = prev.find(d => d.id === source.id);
            return exists ? prev : [...prev, source];
        });
        setActivePreviewId(source.id);
    };

    const onRemoveDocument = (id: string) => {
        setPreviewDocuments(prev => {
            const newDocs = prev.filter(d => d.id !== id);
            if (activePreviewId === id) {
                if (newDocs.length > 0) {
                    setActivePreviewId(newDocs[newDocs.length - 1].id);
                } else {
                    setActivePreviewId(null);
                }
            }
            return newDocs;
        });
    };

    const handleCloseAll = () => {
        setPreviewDocuments([]);
        setActivePreviewId(null);
        setIsPreviewFullscreen(false);
    };

    return (
        <div className="flex-1 w-full h-full overflow-hidden">
            {previewDocuments.length > 0 && isPreviewFullscreen ? (
                <div className="w-full h-full overflow-hidden">
                    <DocumentPreview
                        documents={previewDocuments}
                        activeId={activePreviewId || undefined}
                        onActiveChange={setActivePreviewId}
                        onClose={handleCloseAll}
                        onCloseDocument={onRemoveDocument}
                        isFullscreen={isPreviewFullscreen}
                        onToggleFullscreen={() => setIsPreviewFullscreen(!isPreviewFullscreen)}
                    />
                </div>
            ) : previewDocuments.length > 0 ? (
                <div className="w-full h-full overflow-hidden">
                    <ResizablePanelGroup orientation="horizontal" className="h-full w-full flex">
                        <ResizablePanel defaultSize={70} minSize={30} maxSize={70} className="min-w-0">
                            <ChatArea
                                messages={messages}
                                onSendMessage={handleSendMessage}
                                isLoading={isLoading}
                                onSourceClick={handleSourceClick}
                                model={model}
                                onModelChange={setModel}
                            />
                        </ResizablePanel>
                        <ResizableHandle withHandle className="w-1.5 hover:bg-secondary/50 transition-colors" />
                        <ResizablePanel defaultSize={30} minSize={30} maxSize={70}>
                            <DocumentPreview
                                documents={previewDocuments}
                                activeId={activePreviewId || undefined}
                                onActiveChange={setActivePreviewId}
                                onClose={handleCloseAll}
                                onCloseDocument={onRemoveDocument}
                                isFullscreen={isPreviewFullscreen}
                                onToggleFullscreen={() => setIsPreviewFullscreen(!isPreviewFullscreen)}
                            />
                        </ResizablePanel>
                    </ResizablePanelGroup>
                </div>
            ) : (
                <div className="w-full h-full flex justify-center overflow-hidden">
                    <div className="max-w-[95%] lg:max-w-[70%] h-full w-full">
                        <ChatArea
                            messages={messages}
                            onSendMessage={handleSendMessage}
                            isLoading={isLoading}
                            onSourceClick={handleSourceClick}
                            model={model}
                            onModelChange={setModel}
                        />
                    </div>
                </div>
            )}
        </div>
    );
}
