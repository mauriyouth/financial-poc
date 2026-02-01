import React from 'react';
import { Message } from '@/lib/api/chat';
import { DocumentMetadata } from '@/lib/api/documents';
import { cn } from '@/lib/utils';
import { UserMessage } from './UserMessage';
import { AssistantMessage } from './AssistantMessage';

interface MessageListProps {
    messages: Message[];
    onSourceClick?: (source: DocumentMetadata) => void;
}

export function MessageList({ messages, onSourceClick }: MessageListProps) {
    return (
        <>
            {messages.map((msg) => (
                <div
                    key={msg.id}
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
                                thinkingSteps={msg.thinking_steps}
                                sources={msg.sources}
                                onSourceClick={onSourceClick}
                            />
                        )}
                    </div>
                </div>
            ))}
        </>
    );
}
