import { useState, useCallback } from 'react';
import { Citation, BBox } from '@/lib/api/chat';

export interface DocumentHighlight {
    documentId: string;
    bbox: BBox;
    citation: Citation;
}

export function useCitationNavigation() {
    const [activeHighlight, setActiveHighlight] = useState<DocumentHighlight | null>(null);

    const handleCitationClick = useCallback(async (citation: Citation) => {
        if (!citation.bbox) {
            console.warn('Citation has no bbox information:', citation);
            return;
        }

        // Extract document ID from chunk metadata or source name
        const documentId = citation.metadata?.document_id || citation.chunk_id;

        const highlight: DocumentHighlight = {
            documentId,
            bbox: citation.bbox,
            citation,
        };

        setActiveHighlight(highlight);

        // Trigger document viewer to open and highlight
        // This will be handled by the parent component
        return highlight;
    }, []);

    const clearHighlight = useCallback(() => {
        setActiveHighlight(null);
    }, []);

    return {
        activeHighlight,
        handleCitationClick,
        clearHighlight,
    };
}
