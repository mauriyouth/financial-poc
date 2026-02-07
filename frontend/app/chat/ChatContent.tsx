"use client";

import { useState, useEffect } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { ChatArea } from '@/components/chat-area';
import { DocumentPreview } from '@/components/document-preview';
import { ResizableHandle, ResizablePanel, ResizablePanelGroup } from '@/components/ui/resizable';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
    Message,
    getConversations,
    createConversation,
    getMessages,
    streamMessage,
    getModels,
    Agent,
    getAgents,
} from '@/lib/api/chat';
import { DocumentMetadata, getChunk } from '@/lib/api/documents';
import { useToast } from '@/hooks/use-toast';
import { ToastAction } from '@/components/ui/toast';
import { SourcesPanel } from '@/components/chat/SourcesPanel';
import { CitationsPanel } from '@/components/chat/CitationsPanel';

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
    const [selectedAgent, setSelectedAgent] = useState<string | null>(null);
    const [isRightPanelOpen, setIsRightPanelOpen] = useState(true);
    const [activeRightTab, setActiveRightTab] = useState<string>('sources');
    const [activePage, setActivePage] = useState<number | undefined>(undefined);

    const { toast } = useToast();

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
                const { content, files, model: pendingModel, agent: pendingAgent } = JSON.parse(pendingMessage);
                localStorage.removeItem('pendingMessage');
                if (pendingModel) setModel(pendingModel);
                if (pendingAgent) setSelectedAgent(pendingAgent);

                let finalContent = content;
                if (files && files.length > 0) {
                    const fileContext = files.map((f: any) => `[Attached File: ${f.filename} (ID: ${f.id})]`).join('\n');
                    finalContent = `${fileContext}\n\n${content}`;
                }

                setTimeout(() => {
                    handleSendMessage(finalContent);
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

    const processMessageStream = async (conversationId: string, content: string, modelId?: string) => {
        setIsLoading(true);
        let hasError = false;

        try {
            let thinkingBuffer = '';
            let reasoningEvents: any[] = [];
            let currentAgent = '';
            let previousAgent = '';
            let provider = "anthropic";
            let actualModelId: string | undefined = undefined;

            if (modelId && modelId.includes(':')) {
                const parts = modelId.split(':', 2);
                provider = parts[0];
                actualModelId = parts[1];
            } else if (modelId) {
                actualModelId = modelId;
            }

            setMessages(prev => {
                const lastMsg = prev[prev.length - 1];
                if (lastMsg.role === 'user') {
                    const tempAiMsg: Message = {
                        id: 'temp-ai-' + Date.now(),
                        conversation_id: conversationId,
                        role: 'assistant',
                        content: "",
                        created_at: new Date().toISOString()
                    };
                    return [...prev, tempAiMsg];
                }
                return prev;
            });

            await streamMessage(conversationId, content, provider, (event: any) => {
                setMessages(prev => {
                    const newMessages = [...prev];
                    const lastMsg = newMessages[newMessages.length - 1];
                    if (lastMsg.role === 'assistant') {
                        if (event.type === 'thinking' || event.type === 'tool_call' || event.type === 'tool_result' || event.type === 'llm_error') {
                            if (!lastMsg.reasoning_events) {
                                lastMsg.reasoning_events = [];
                            }
                            lastMsg.reasoning_events.push(event);
                        } else if (event.type === 'agent_start') {
                            previousAgent = currentAgent;
                            currentAgent = event.agent_name || '';
                            if (previousAgent && previousAgent !== currentAgent) {
                                if (!lastMsg.agent_transitions) {
                                    lastMsg.agent_transitions = [];
                                }
                                lastMsg.agent_transitions.push({
                                    from: previousAgent,
                                    to: currentAgent,
                                    reason: 'Routing to specialized agent'
                                });
                            }
                        } else if (event.type === 'thinking_start') {
                            thinkingBuffer = '';
                        } else if (event.type === 'thinking' && event.content) {
                            thinkingBuffer += event.content;
                            lastMsg.thinking_steps = [thinkingBuffer];
                        } else if (event.type === 'content' && event.content) {
                            lastMsg.content += event.content;
                        } else if (event.type === 'error' && event.content) {
                            hasError = true;
                            lastMsg.content = `❌ **Error**: ${event.content}`;
                            lastMsg.thinking_steps = undefined;
                            setIsLoading(false);

                            toast({
                                variant: "destructive",
                                title: "Error generating response",
                                description: event.content,
                                action: (
                                    <ToastAction altText="Try again" onClick={() => handleRetry(content, modelId)}>
                                        Try again
                                    </ToastAction>
                                ),
                            });
                        }
                    }
                    return newMessages;
                });
            }, actualModelId, selectedAgent || undefined);
        } catch (error) {
            console.error("Streaming failed", error);
            const errorMessage = error instanceof Error ? error.message : 'Failed to generate response';

            setMessages(prev => {
                const newMessages = [...prev];
                const lastMsg = newMessages[newMessages.length - 1];
                if (lastMsg.role === 'assistant') {
                    lastMsg.content = `❌ **Error**: ${errorMessage}`;
                    lastMsg.thinking_steps = undefined;
                }
                return newMessages;
            });
            hasError = true;

            toast({
                variant: "destructive",
                title: "Connection Error",
                description: errorMessage,
                action: (
                    <ToastAction altText="Try again" onClick={() => handleRetry(content, modelId)}>
                        Try again
                    </ToastAction>
                ),
            });

        } finally {
            if (!hasError) setIsLoading(false);
            loadMessages(conversationId);
        }
    };

    const handleRetry = (content: string, modelId?: string) => {
        setMessages(prev => {
            const lastMsg = prev[prev.length - 1];
            if (lastMsg.role === 'assistant' && lastMsg.content.includes('❌ **Error**')) {
                return prev.slice(0, -1);
            }
            return prev;
        });

        if (activeId) {
            processMessageStream(activeId, content, modelId);
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
                toast({
                    variant: "destructive",
                    title: "Failed to start chat",
                    description: "Could not create a new conversation. Please try again.",
                });
                return;
            }
        }

        const currentActiveId = conversationId;

        const tempUserMsg: Message = {
            id: 'temp-user-' + Date.now(),
            conversation_id: currentActiveId,
            role: 'user',
            content,
            created_at: new Date().toISOString()
        };

        setMessages(prev => [...prev, tempUserMsg]);
        await processMessageStream(currentActiveId, content, model);
    };

    const handleSourceClick = (source: DocumentMetadata) => {
        setPreviewDocuments(prev => {
            const exists = prev.find(d => d.id === source.id);
            return exists ? prev : [...prev, source];
        });
        setActivePreviewId(source.id);
        setIsRightPanelOpen(true);
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
        setActivePage(undefined);
        setIsPreviewFullscreen(false);
        setActiveRightTab('sources');
    };

    const handleCitationClick = async (chunkId: string) => {
        try {
            const chunk = await getChunk(chunkId);
            if (!chunk) {
                console.warn(`Chunk ${chunkId} not found`);
                return;
            }

            const docId = chunk.source_id;
            const page = chunk.metadata.page_number;

            // Check if document is already in preview list
            const existingDoc = previewDocuments.find(d => d.id === docId);
            if (!existingDoc) {
                // If we don't have full metadata, create a minimal object
                // Ideally we should fetch document metadata but this is faster
                const newDoc: DocumentMetadata = {
                    id: docId,
                    filename: chunk.source_name,
                    status: 'completed',
                    upload_date: new Date().toISOString(),
                    file_type: chunk.source_name.split('.').pop()
                };
                setPreviewDocuments(prev => [...prev, newDoc]);
            }

            setActivePreviewId(docId);
            setActivePage(page);
            setIsRightPanelOpen(true);
            setActiveRightTab('preview');
        } catch (e) {
            console.error("Failed to handle citation click", e);
            toast({
                variant: "destructive",
                title: "Error",
                description: "Failed to locate citation source.",
            });
        }
    };

    const allCitations = messages
        .filter(m => m.role === 'assistant' && m.citations)
        .flatMap(m => m.citations || []);

    return (
        <div className="flex-1 w-full h-full overflow-hidden">
            {isRightPanelOpen ? (
                <div className="w-full h-full overflow-hidden">
                    <ResizablePanelGroup orientation="horizontal" className="h-full w-full flex">
                        <ResizablePanel defaultSize="70" minSize="30" maxSize="85" className="min-w-0">
                            <ChatArea
                                messages={messages}
                                onSendMessage={handleSendMessage}
                                isLoading={isLoading}
                                onSourceClick={handleSourceClick}
                                onModelChange={setModel}
                                selectedAgent={selectedAgent}
                                onAgentChange={setSelectedAgent}
                                onCitationClick={handleCitationClick}
                            />
                        </ResizablePanel>

                        <ResizableHandle withHandle className="w-1.5 hover:bg-secondary/50 transition-colors" />

                        <ResizablePanel defaultSize="30" minSize="15" maxSize="70" collapsible={true} onResize={(size: any) => { if (size === 0) setIsRightPanelOpen(false); }}>
                            <div className="h-full flex flex-col bg-card">
                                <Tabs value={activeRightTab} onValueChange={setActiveRightTab} className="flex-1 flex flex-col min-h-0">
                                    <div className="px-4 pt-4 border-b bg-muted/30">
                                        <TabsList className="grid w-full grid-cols-3">
                                            <TabsTrigger value="sources">Sources</TabsTrigger>
                                            <TabsTrigger value="citations" disabled={allCitations.length === 0}>Citations</TabsTrigger>
                                            <TabsTrigger value="preview">Preview</TabsTrigger>
                                        </TabsList>
                                    </div>

                                    <div className="flex-1 overflow-hidden relative">
                                        <TabsContent value="sources" className="h-full m-0 border-0">
                                            <SourcesPanel
                                                onDocumentClick={(doc) => {
                                                    handleSourceClick(doc);
                                                    setActiveRightTab('preview');
                                                }}
                                                activeId={activePreviewId || undefined}
                                            />
                                        </TabsContent>

                                        <TabsContent value="citations" className="h-full m-0 border-0">
                                            <CitationsPanel
                                                citations={allCitations}
                                                onCitationClick={handleCitationClick}
                                            />
                                        </TabsContent>

                                        <TabsContent value="preview" className="h-full m-0 border-0">
                                            {previewDocuments.length > 0 ? (
                                                <DocumentPreview
                                                    documents={previewDocuments}
                                                    activeId={activePreviewId || undefined}
                                                    onActiveChange={(id) => {
                                                        setActivePreviewId(id);
                                                        setActivePage(undefined);
                                                    }}
                                                    onClose={handleCloseAll}
                                                    onCloseDocument={onRemoveDocument}
                                                    isFullscreen={isPreviewFullscreen}
                                                    onToggleFullscreen={() => setIsPreviewFullscreen(!isPreviewFullscreen)}
                                                    activePage={activePage}
                                                />
                                            ) : (
                                                <div className="flex items-center justify-center h-full text-muted-foreground text-sm p-8 text-center">
                                                    Select a document from the Sources tab to preview it.
                                                </div>
                                            )}
                                        </TabsContent>
                                    </div>
                                </Tabs>
                            </div>
                        </ResizablePanel>
                    </ResizablePanelGroup>
                </div>
            ) : (
                <div className="w-full h-full flex overflow-hidden relative">
                    <div className="flex-1 min-w-0">
                        <ChatArea
                            messages={messages}
                            onSendMessage={handleSendMessage}
                            isLoading={isLoading}
                            onSourceClick={handleSourceClick}
                            model={model}
                            onModelChange={setModel}
                            selectedAgent={selectedAgent}
                            onAgentChange={setSelectedAgent}
                            onCitationClick={handleCitationClick}
                        />
                    </div>
                    <div className="absolute right-4 top-4 z-50">
                        <button
                            onClick={() => setIsRightPanelOpen(true)}
                            className="p-2 bg-background border rounded-full shadow-sm hover:bg-accent opacity-50 hover:opacity-100 transition-all"
                            title="Open Sources"
                        >
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect width="18" height="18" x="3" y="3" rx="2" ry="2" /><line x1="15" x2="15" y1="3" y2="21" /></svg>
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}
