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
}

export type DocumentContent = string | { content: string; metadata: Record<string, unknown> };

export const uploadDocument = async (file: File): Promise<DocumentMetadata> => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await api.post<DocumentMetadata>('/documents/', formData, {
        headers: {
            'Content-Type': 'multipart/form-data',
        },
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

export const getDocuments = async (): Promise<DocumentMetadata[]> => {
    const response = await api.get<DocumentMetadata[]>('/documents/');
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
