import React from 'react';
import { FileText } from 'lucide-react';
import { Citation } from '@/lib/api/chat';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';

interface CitationListProps {
    citations: Citation[];
    onCitationClick: (citation: Citation) => void;
}

export function CitationList({ citations, onCitationClick }: CitationListProps) {
    if (!citations || citations.length === 0) {
        return null;
    }

    return (
        <Card className="p-4 mt-4">
            <div className="flex items-center gap-2 mb-3">
                <FileText className="h-4 w-4 text-muted-foreground" />
                <h3 className="text-sm font-medium">Citations ({citations.length})</h3>
            </div>

            <ScrollArea className="max-h-64">
                <div className="space-y-2">
                    {citations.map((citation, index) => (
                        <div
                            key={citation.id}
                            className="p-3 rounded-lg border border-muted hover:bg-accent cursor-pointer transition-colors"
                            onClick={() => onCitationClick(citation)}
                        >
                            <div className="flex items-start gap-2">
                                <Badge variant="secondary" className="mt-0.5">
                                    [{index + 1}]
                                </Badge>
                                <div className="flex-1 min-w-0">
                                    <p className="text-sm font-medium text-foreground mb-1">
                                        {citation.source_name}
                                    </p>
                                    <p className="text-xs text-muted-foreground line-clamp-2">
                                        {citation.content}
                                    </p>
                                    <div className="flex gap-2 mt-2">
                                        <span className="text-xs text-muted-foreground px-2 py-0.5 rounded bg-muted">
                                            {citation.source_type}
                                        </span>
                                        {citation.bbox?.page && (
                                            <span className="text-xs text-muted-foreground px-2 py-0.5 rounded bg-muted">
                                                Page {citation.bbox.page}
                                            </span>
                                        )}
                                    </div>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </ScrollArea>
        </Card>
    );
}
