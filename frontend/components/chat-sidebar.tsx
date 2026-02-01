import React from 'react';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Plus, MessageSquare } from 'lucide-react';
import { Conversation } from '@/lib/api/chat';

interface ChatSidebarProps {
    conversations: Conversation[];
    activeId: string | null;
    onSelect: (id: string) => void;
    onNewChat: () => void;
}

export function ChatSidebar({ conversations, activeId, onSelect, onNewChat }: ChatSidebarProps) {
    return (
        <div className="w-64 border-r h-full flex flex-col bg-muted/10">
            <div className="p-4 border-b">
                <Button onClick={onNewChat} className="w-full justify-start" variant="outline">
                    <Plus className="mr-2 h-4 w-4" />
                    New Chat
                </Button>
            </div>
            <ScrollArea className="flex-1">
                <div className="p-2 space-y-2">
                    {conversations.length === 0 && (
                        <div className="text-center text-sm text-muted-foreground p-4">
                            No conversations yet.
                        </div>
                    )}
                    {conversations.map((conv) => (
                        <Button
                            key={conv.id}
                            variant={activeId === conv.id ? "secondary" : "ghost"}
                            className="w-full justify-start text-left font-normal"
                            onClick={() => onSelect(conv.id)}
                        >
                            <MessageSquare className="mr-2 h-4 w-4" />
                            <span className="truncate">
                                {conv.title || "Untitled Conversation"}
                            </span>
                        </Button>
                    ))}
                </div>
            </ScrollArea>
        </div>
    );
}
