import { useEffect, useState, useRef } from 'react';

export interface DocumentStatusUpdate {
    type: 'document_status';
    document_id: string;
    status: 'pending' | 'queued' | 'processing' | 'completed' | 'failed';
    metadata?: {
        chunk_count?: number;
        error?: string;
    };
    timestamp: string;
}

export function useDocumentStatus(documentId: string | null) {
    const [status, setStatus] = useState<string>('pending');
    const [metadata, setMetadata] = useState<Record<string, any>>({});
    const wsRef = useRef<WebSocket | null>(null);

    useEffect(() => {
        if (!documentId) return;

        // Connect to WebSocket
        const ws = new WebSocket(`ws://localhost:8000/ws`);
        wsRef.current = ws;

        ws.onopen = () => {
            console.log('WebSocket connected');
        };

        ws.onmessage = (event) => {
            try {
                const data: DocumentStatusUpdate = JSON.parse(event.data);

                // Update state if message is for this document
                if (data.type === 'document_status' && data.document_id === documentId) {
                    setStatus(data.status);
                    if (data.metadata) {
                        setMetadata(data.metadata);
                    }
                    console.log(`Document ${documentId} status:`, data.status);
                }
            } catch (error) {
                console.error('Error parsing WebSocket message:', error);
            }
        };

        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };

        ws.onclose = () => {
            console.log('WebSocket disconnected');
        };

        // Cleanup on unmount
        return () => {
            ws.close();
        };
    }, [documentId]);

    return { status, metadata };
}
