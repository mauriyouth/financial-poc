import React from 'react';
import { Message } from '@/lib/api/chat';
import { DocumentMetadata } from '@/lib/api/documents';
import { cn } from '@/lib/utils';
import { UserMessage } from './UserMessage';
import { AssistantMessage } from './AssistantMessage';
import { ReasoningPanel } from '@/components/chat/ReasoningPanel';

interface MessageListProps {
    messages: Message[];
    onSourceClick?: (source: DocumentMetadata) => void;
    onCitationClick?: (citationId: string) => void;
    citationStatus?: Record<string, 'valid' | 'invalid' | 'loading' | 'error'>;
}

export function MessageList({ messages, onSourceClick, onCitationClick, citationStatus }: MessageListProps) {
    return (
        <>
            {messages.map((msg) => (
                <React.Fragment key={msg.id}>


                    {/* Show reasoning panel (Top) */}
                    {msg.role === 'assistant' && msg.reasoning_events && msg.reasoning_events.length > 0 && (
                        <ReasoningPanel
                            events={msg.reasoning_events}
                        />
                    )}

                    <div
                        className={cn(
                            "flex w-full min-w-0",
                            msg.role === 'user' ? 'justify-end' : 'justify-start'
                        )}
                    >
                        <div className={cn(
                            "flex gap-3 max-w-[85%] min-w-0",
                            msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'
                        )}>
                            {msg.role === 'user' ? (
                                <UserMessage
                                    content={msg.content}
                                    onSourceClick={onSourceClick}
                                />
                            ) : (
                                <AssistantMessage
                                    content={msg.content}
                                    sources={msg.sources}
                                    citations={msg.citations}
                                    onSourceClick={onSourceClick}
                                    onCitationClick={onCitationClick}
                                    citationStatus={citationStatus}
                                />
                            )}
                        </div>
                    </div>


                </React.Fragment>
            ))}
        </>
    );
}
