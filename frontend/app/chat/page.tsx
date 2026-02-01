"use client";

import { useState, useEffect, Suspense } from 'react';
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
import { Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

function ChatContent() {
    const searchParams = useSearchParams();
    const router = useRouter();
    // const [conversations, setConversations] = useState<Conversation[]>([]); // Future feature
    const [activeId, setActiveId] = useState<string | null>(null);
    const [messages, setMessages] = useState<Message[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [previewDocuments, setPreviewDocuments] = useState<DocumentMetadata[]>([]);
    const [activePreviewId, setActivePreviewId] = useState<string | null>(null);
    const [activeConversation, setActiveConversation] = useState<string | null>(null); // Added new state variable
    const [isPreviewFullscreen, setIsPreviewFullscreen] = useState(false);
    const [model, setModel] = useState<string>(''); // Changed default model to empty string

    useEffect(() => {
        // Load models and set default
        const loadModels = async () => {
            try {
                const models = await getModels();
                if (models && models.length > 0) {
                    // Check if there's a stored model first
                    const storedModel = localStorage.getItem('selectedModel');
                    if (storedModel) {
                        setModel(storedModel);
                    } else {
                        // Use first enabled model as default
                        setModel(models[0].id);
                    }
                }
            } catch (error) {
                console.error('Failed to load models:', error);
                // Fallback to a default model if API fails
                setModel('anthropic:claude-opus-4-5-20251101');
            }
        };
        loadModels();

        loadConversations();

        // Load conversation from URL if present
        const idFromUrl = searchParams.get('id');
        if (idFromUrl) {
            setActiveId(idFromUrl);
        }

        // Check for pending message from home page
        const pendingMessage = localStorage.getItem('pendingMessage');
        if (pendingMessage && idFromUrl) {
            try {
                const { content, model: pendingModel } = JSON.parse(pendingMessage);
                localStorage.removeItem('pendingMessage');

                if (pendingModel) {
                    setModel(pendingModel);
                }

                // Automatically send the message after a brief delay to ensure state is set
                setTimeout(() => {
                    handleSendMessage(content);
                }, 500);
            } catch (e) {
                console.error('Failed to parse pending message', e);
            }
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    // Load messages when active conversation changes
    useEffect(() => {
        if (activeId) {
            loadMessages(activeId);
            // Update URL when active conversation changes
            router.push(`/chat?id=${activeId}`, { scroll: false });
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [activeId]);

    const loadConversations = async () => {
        try {
            const data = await getConversations();
            // setConversations(data);

            // Only set first conversation as active if no conversation is selected
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

    const handleNewChat = async () => {
        try {
            const newConv = await createConversation("New Chat");
            await loadConversations();
            setActiveId(newConv.id); // This will trigger URL update via useEffect
            setMessages([]);
        } catch (error) {
            console.error("Failed to create conversation", error);
        }
    };

    const handleSendMessage = async (content: string) => {
        if (!content.trim()) return;

        // Auto-create conversation if none exists
        let conversationId = activeId;
        if (!conversationId) {
            try {
                const newConv = await createConversation("New Chat");
                conversationId = newConv.id;
                setActiveId(conversationId); // This will trigger URL update and reload conversations
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
            content: "", // Will fill via stream
            created_at: new Date().toISOString()
        };

        setMessages(prev => [...prev, tempUserMsg, tempAiMsg]);

        let hasError = false; // Moved hasError outside try block

        try {
            let thinkingBuffer = '';

            // Parse provider and model_id from model string (format: "provider:model_id")
            let provider = "anthropic"; // Default provider
            let model_id: string | undefined = undefined; // Default model_id

            if (model && model.includes(':')) {
                const parts = model.split(':', 2);
                provider = parts[0];
                model_id = parts[1];
            } else if (model) {
                // If no colon, treat the whole string as model_id
                model_id = model;
            }

            await streamMessage(currentActiveId, content, provider, (event) => {
                setMessages(prev => {
                    const newMessages = [...prev];
                    const lastMsg = newMessages[newMessages.length - 1];
                    if (lastMsg.role === 'assistant') {
                        if (event.type === 'thinking_start') {
                            // Reset thinking buffer when thinking starts
                            thinkingBuffer = '';
                        } else if (event.type === 'thinking' && event.content) {
                            // Accumulate thinking chunks into buffer
                            thinkingBuffer += event.content;
                            lastMsg.thinking_steps = [thinkingBuffer];
                        } else if (event.type === 'content' && event.content) {
                            // Stream content - just append the string
                            lastMsg.content += event.content;
                        } else if (event.type === 'error' && event.content) {
                            // Set error state
                            hasError = true;
                            lastMsg.content = `❌ **Error**: ${event.content}\n\n*Click the retry button to try again.*`;
                            lastMsg.thinking_steps = undefined; // Clear thinking on error
                            // Immediately stop loading when error occurs
                            setIsLoading(false);
                        }
                    }

                    return newMessages;
                });
            }, model_id);

            if (!hasError) {
                setIsLoading(false);
            }
        } catch (error) {
            console.error("Streaming failed", error);
            // Update the last message with error
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
            // Only set loading to false if no error occurred (error handler already sets it)
            if (!hasError) {
                setIsLoading(false);
            }
            // Optionally reload history to sync IDs
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

    // Future feature: individual document tab closing
    // const handleCloseDocument = (id: string) => {
    //     setPreviewDocuments(prev => prev.filter(d => d.id !== id));
    //     if (activePreviewId === id) setActivePreviewId(null);
    // };

    // Need to handle state update properly in one go to avoid race conditions or double renders
    // Refactoring handleCloseDocument slightly to be cleaner
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

    const handleToggleFullscreen = () => {
        setIsPreviewFullscreen(prev => !prev);
    };

    return (
        <div className="flex-1 w-full h-full overflow-hidden">
            {previewDocuments.length > 0 && isPreviewFullscreen ? (
                // Fullscreen preview - takes entire page
                <div className="w-full h-full overflow-hidden">
                    <DocumentPreview
                        documents={previewDocuments}
                        activeId={activePreviewId || undefined}
                        onActiveChange={setActivePreviewId}
                        onClose={handleCloseAll}
                        onCloseDocument={onRemoveDocument}
                        isFullscreen={isPreviewFullscreen}
                        onToggleFullscreen={handleToggleFullscreen}
                    />
                </div>
            ) : previewDocuments.length > 0 ? (
                // Split view with chat and preview
                <div className="w-full h-full overflow-hidden">
                    <ResizablePanelGroup orientation="horizontal" className="h-full w-full flex data-[panel-group-direction=vertical]:flex-col">
                        <ResizablePanel
                            defaultSize="70"
                            minSize="30"
                            maxSize="70"
                            className="min-w-0"
                        >
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

                        <ResizablePanel
                            defaultSize="30"
                            minSize="30"
                            maxSize="70"
                        >
                            <DocumentPreview
                                documents={previewDocuments}
                                activeId={activePreviewId || undefined}
                                onActiveChange={setActivePreviewId}
                                onClose={handleCloseAll}
                                onCloseDocument={onRemoveDocument}
                                isFullscreen={isPreviewFullscreen}
                                onToggleFullscreen={handleToggleFullscreen}
                            />
                        </ResizablePanel>
                    </ResizablePanelGroup>
                </div>
            ) : (
                // Centered chat with no preview
                <div className="w-full h-full flex justify-center overflow-hidden">
                    <div className="max-w-[95%] lg:max-w-[70%] h-full">
                        <div className="w-full h-full">
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
                </div>
            )}
        </div>
    );
}

export default function ChatPage() {
    return (
        <Suspense fallback={
            <div className="h-screen w-screen flex items-center justify-center bg-neutral-950 text-neutral-400">
                <Loader2 className="h-10 w-10 animate-spin" />
            </div>
        }>
            <ChatContent />
        </Suspense>
    );
}
