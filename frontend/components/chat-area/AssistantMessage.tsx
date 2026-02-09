import React from 'react';
import { FileText } from 'lucide-react';
import { MarkdownContent } from '@/components/markdown-content';
import { DocumentMetadata } from '@/lib/api/documents';
import { Citation } from '@/lib/api/chat';
import { Badge } from '@/components/ui/badge';

interface AssistantMessageProps {
    content: string;
    thinkingSteps?: string[];
    sources?: DocumentMetadata[];
    citations?: Citation[];  // NEW: Citations with bbox
    onSourceClick?: (source: DocumentMetadata) => void;
    onCitationClick?: (citationId: string) => void;
    citationStatus?: Record<string, 'valid' | 'invalid' | 'loading' | 'error'>;
}

export function AssistantMessage({
    content,
    thinkingSteps,
    sources,
    citations,
    onSourceClick,
    onCitationClick,
    citationStatus
}: AssistantMessageProps) {
    return (
        <div className="flex-1 min-w-0">
            {thinkingSteps && thinkingSteps.length > 0 && (
                <details className="mb-3 bg-muted/30 rounded-lg border border-muted" open>
                    <summary className="cursor-pointer px-4 py-2 text-sm font-medium text-muted-foreground hover:text-foreground transition-colors flex items-center gap-2">
                        <div className="flex items-center gap-2 flex-1">
                            <div className="w-2 h-2 rounded-full bg-gradient-to-r from-purple-500 to-blue-500 animate-pulse" />
                            <span>Thinking Process</span>
                            <span className="text-xs opacity-60">
                                ({thinkingSteps[0]?.length || 0} chars)
                            </span>
                        </div>
                    </summary>
                    <div className="px-4 py-3 border-t border-muted">
                        <div className="text-sm text-muted-foreground whitespace-pre-wrap font-mono bg-muted/20 p-3 rounded">
                            {thinkingSteps[0]}
                        </div>
                    </div>
                </details>
            )}

            {/* Message Text*/}
            <div className="text-sm leading-relaxed max-w-full overflow-hidden">
                <MarkdownContent
                    content={content}
                    citations={citations}
                    onCitationClick={onCitationClick}
                    citationStatus={citationStatus}
                />
            </div>

            {/* Source Citations */}
            {sources && sources.length > 0 && (
                <div className="mt-3 pt-3 border-t border-muted">
                    <p className="text-xs text-muted-foreground mb-2">Sources:</p>
                    <div className="flex flex-wrap gap-2">
                        {sources.map((source) => (
                            <Badge
                                key={source.id}
                                variant="outline"
                                className="cursor-pointer hover:bg-accent"
                                onClick={() => onSourceClick?.(source)}
                            >
                                <FileText className="h-3 w-3 mr-1" />
                                {source.filename}
                            </Badge>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}
