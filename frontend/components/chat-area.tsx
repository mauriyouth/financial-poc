import React, { useRef, useEffect, useState } from 'react';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Message } from '@/lib/api/chat';
import { DocumentMetadata } from '@/lib/api/documents';
import { ChatInput, DataSource } from '@/components/chat-input';
import { EmptyState } from './chat-area/EmptyState';
import { MessageList } from './chat-area/MessageList';
import { LoadingIndicator } from './chat-area/LoadingIndicator';
import { ArrowDown } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface ChatAreaProps {
    messages: Message[];
    onSendMessage: (content: string) => void;
    isLoading: boolean;
    onSourceClick?: (source: DocumentMetadata) => void;
    model?: string;
    onModelChange?: (model: string) => void;
    selectedAgent?: string | null;
    onAgentChange?: (agent: string | null) => void;
    onCitationClick?: (citationId: string) => void;
}

export function ChatArea({ messages, onSendMessage, isLoading, onSourceClick, model, onModelChange, selectedAgent, onAgentChange, onCitationClick }: ChatAreaProps) {

    const [input, setInput] = useState("");
    const [dataSource, setDataSource] = useState<DataSource>('knowledge');
    const scrollRef = useRef<HTMLDivElement>(null);
    const scrollAreaRef = useRef<HTMLDivElement>(null);
    const [showScrollButton, setShowScrollButton] = useState(false);

    useEffect(() => {
        if (!isLoading && scrollRef.current) {
            scrollRef.current.scrollIntoView({ behavior: 'smooth' });
        }
    }, [isLoading]);

    // Track scroll position to show/hide the scroll-to-bottom button
    useEffect(() => {
        const scrollArea = scrollAreaRef.current;
        if (!scrollArea) return;

        const handleScroll = () => {
            const viewport = scrollArea.querySelector('[data-radix-scroll-area-viewport]') as HTMLElement;
            if (!viewport) return;

            const scrollTop = viewport.scrollTop;
            const scrollHeight = viewport.scrollHeight;
            const clientHeight = viewport.clientHeight;

            // Show button if not at the bottom (with 10px buffer)
            const isAtBottom = scrollTop + clientHeight >= scrollHeight - 10;
            setShowScrollButton(!isAtBottom);
        };

        const viewport = scrollArea.querySelector('[data-radix-scroll-area-viewport]');
        if (viewport) {
            viewport.addEventListener('scroll', handleScroll);
            // Initial check
            handleScroll();
            return () => viewport.removeEventListener('scroll', handleScroll);
        }
    }, [messages.length]); // Use length instead of array to avoid size change warning

    const scrollToBottom = () => {
        const scrollArea = scrollAreaRef.current;
        if (!scrollArea) return;

        const viewport = scrollArea.querySelector('[data-radix-scroll-area-viewport]') as HTMLElement;
        if (viewport) {
            viewport.scrollTo({
                top: viewport.scrollHeight,
                behavior: 'smooth'
            });
        }
    };

    const handleSend = (message: string, attachments?: Array<{ id: string; filename: string }>) => {
        // If files are attached, prepend file context
        let finalMessage = message;
        if (attachments && attachments.length > 0) {
            const fileContext = attachments.map(f => `[Attached File: ${f.filename} (ID: ${f.id})]`).join('\n');
            finalMessage = `${fileContext}\n\n${message}`;
        }
        onSendMessage(finalMessage);
    };

    return (
        <div className="flex flex-col h-full w-full bg-background overflow-hidden min-w-0 relative">
            {/* Messages Area */}
            <ScrollArea
                ref={scrollAreaRef}
                className="flex-1 min-h-0 w-full px-4 py-6 overflow-hidden min-w-0 [&>[data-radix-scroll-area-viewport]]:min-w-0 [&>[data-radix-scroll-area-viewport]>div]:min-w-0"
            >
                <div className="space-y-6 w-full min-w-0">
                    {messages.length === 0 && <EmptyState />}

                    <MessageList
                        messages={messages}
                        onSourceClick={onSourceClick}
                        onCitationClick={onCitationClick}
                    />

                    {isLoading && <LoadingIndicator />}

                    <div ref={scrollRef} />
                </div>
            </ScrollArea>

            {/* Floating Scroll to Bottom Button */}
            {showScrollButton && (
                <div className="flex justify-center py-2">
                    <Button
                        onClick={scrollToBottom}
                        size="sm"
                        className="rounded-full shadow-lg hover:shadow-xl transition-shadow"
                        variant="secondary"
                    >
                        <ArrowDown className="h-4 w-4" />
                    </Button>
                </div>
            )}

            {/* Input Area */}
            <div className="p-4">
                <div className="w-full mx-auto">
                    <ChatInput
                        value={input}
                        onChange={setInput}
                        onSend={handleSend}
                        isLoading={isLoading}
                        placeholder="Message..."
                        showDataSourceSelector={true}
                        dataSource={dataSource}
                        onDataSourceChange={setDataSource}
                        model={model}
                        onModelChange={onModelChange}
                        selectedAgent={selectedAgent}
                        onAgentChange={onAgentChange}
                    />
                </div>
            </div>
        </div>
    );
}