"use client";

import React from 'react';
import { Citation } from '@/lib/api/chat';
import { ScrollArea } from "@/components/ui/scroll-area";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FileText, Map } from "lucide-react";
import { cn } from "@/lib/utils";

interface CitationsPanelProps {
    citations: Citation[];
    onCitationClick?: (chunkId: string) => void;
    activeChunkId?: string;
}

export function CitationsPanel({ citations, onCitationClick, activeChunkId }: CitationsPanelProps) {
    return (
        <Card className="h-full border-l rounded-none border-y-0 border-r-0 bg-background/50 backdrop-blur-sm">
            <CardHeader className="py-4 px-4 border-b">
                <CardTitle className="text-sm font-medium flex items-center gap-2">
                    <Map className="h-4 w-4" />
                    Citations ({citations.length})
                </CardTitle>
            </CardHeader>
            <ScrollArea className="h-[calc(100%-60px)]">
                <CardContent className="p-0">
                    {citations.length === 0 ? (
                        <div className="p-8 text-center text-sm text-muted-foreground">
                            No citations found in this conversation.
                        </div>
                    ) : (
                        <div className="divide-y">
                            {citations.map((citation, index) => (
                                <div
                                    key={`${citation.chunk_id}-${index}`}
                                    className={cn(
                                        "p-4 hover:bg-accent/50 cursor-pointer transition-colors group space-y-2",
                                        activeChunkId === citation.chunk_id && "bg-accent border-l-2 border-primary"
                                    )}
                                    onClick={() => onCitationClick?.(citation.chunk_id)}
                                >
                                    <div className="flex items-center justify-between gap-2">
                                        <div className="flex items-center gap-2 min-w-0">
                                            <span className="flex-shrink-0 flex items-center justify-center w-5 h-5 rounded-full bg-primary/10 text-primary text-[10px] font-bold">
                                                {index + 1}
                                            </span>
                                            <p className="text-xs font-medium truncate text-muted-foreground">
                                                {citation.source_name}
                                            </p>
                                        </div>
                                        {citation.metadata?.page_number && (
                                            <span className="text-[10px] bg-muted px-1.5 py-0.5 rounded text-muted-foreground whitespace-nowrap">
                                                Page {citation.metadata.page_number}
                                            </span>
                                        )}
                                    </div>
                                    <p className="text-xs leading-relaxed text-foreground line-clamp-3 italic">
                                        "{citation.content}"
                                    </p>
                                </div>
                            ))}
                        </div>
                    )}
                </CardContent>
            </ScrollArea>
        </Card>
    );
}
