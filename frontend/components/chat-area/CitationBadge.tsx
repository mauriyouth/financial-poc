import React from 'react';
import { Badge } from '@/components/ui/badge';
import { Citation } from '@/lib/api/chat';

interface CitationBadgeProps {
    citation: Citation;
    index: number;
    onCitationClick: (citation: Citation) => void;
}

export function CitationBadge({ citation, index, onCitationClick }: CitationBadgeProps) {
    return (
        <Badge
            variant="secondary"
            className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium cursor-pointer hover:bg-blue-100 dark:hover:bg-blue-900 ml-0.5 transition-colors"
            onClick={() => onCitationClick(citation)}
            title={`Source: ${citation.source_name}\n${citation.content.substring(0, 100)}...`}
        >
            [{index}]
        </Badge>
    );
}
