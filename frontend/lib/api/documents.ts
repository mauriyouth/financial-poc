import { api, API_BASE_URL } from './client';

export interface DocumentMetadata {
    id: string;
    filename: string;
    upload_date: string;
    status: 'pending' | 'processing' | 'completed' | 'failed';
    file_type?: string;
    page_count?: number;
    error_message?: string;
    download_url?: string;
    thumbnail_url?: string;
    metadata?: {
        summary?: string;
        chunk_count?: number;
        [key: string]: unknown;
    };
}

export type DocumentContent = string | { content: string; metadata: Record<string, unknown> };

export const uploadDocument = async (file: File, threadId?: string): Promise<DocumentMetadata> => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await api.post<DocumentMetadata>('/documents/', formData, {
        headers: {
            'Content-Type': 'multipart/form-data',
        },
        params: {
            thread_id: threadId
        }
    });
    return response.data;
};

export const getDocument = async (id: string): Promise<DocumentMetadata> => {
    const response = await api.get<DocumentMetadata>(`/documents/${id}/status`);
    return response.data;
};

export const getDocumentContent = async (id: string, format: 'markdown' | 'html' | 'json'): Promise<DocumentContent> => {
    const response = await api.get(`/documents/${id}/content`, {
        params: { format }
    });
    return response.data;
};

export const getDocuments = async (threadId?: string): Promise<DocumentMetadata[]> => {
    const response = await api.get<DocumentMetadata[]>('/documents/', {
        params: {
            thread_id: threadId
        }
    });
    return response.data;
};

export const getDocumentDownloadUrl = (id: string): string => {
    return `${API_BASE_URL}/documents/${id}/download`;
};

export interface SlideTextElement {
    text: string;
    x: number;
    y: number;
    width: number;
    height: number;
}

export interface Slide {
    index: number;
    image_url: string;
    download_url: string;
    text_elements: SlideTextElement[];
}

export interface SlidesResponse {
    slide_count: number;
    slides: Slide[];
}

export const getDocumentSlides = async (documentId: string): Promise<SlidesResponse> => {
    const response = await api.get<SlidesResponse>(`/documents/${documentId}/slides`);
    return response.data;
};

export const updateDocument = async (id: string, file: File): Promise<DocumentMetadata> => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await api.put<DocumentMetadata>(`/documents/${id}/content`, formData, {
        headers: {
            'Content-Type': 'multipart/form-data',
        },
    });
    return response.data;
};

export const deleteDocument = async (id: string): Promise<void> => {
    await api.delete(`/documents/${id}`);
};

export interface Chunk {
    id: string;
    source_id: string;
    source_name: string;
    content: string;
    metadata: {
        page_number?: number;
        [key: string]: unknown;
    };
    bbox?: {
        page: number;
        x: number;
        y: number;
        width: number;
        height: number;
    };
}

export const getChunk = async (chunkId: string): Promise<Chunk | null> => {
    try {
        const response = await api.get<Chunk>(`/documents/chunks/${chunkId}`);
        return response.data;
    } catch (error) {
        console.warn(`Failed to fetch chunk ${chunkId}`, error);
        return null;
    }
};
