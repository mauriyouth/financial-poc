import { uploadDocument, getDocuments, DocumentMetadata } from '../documents';
import { api } from '../client';

// Mock the API client
jest.mock('../client', () => ({
    api: {
        post: jest.fn(),
        get: jest.fn(),
    },
    API_BASE_URL: 'http://localhost:8000',
}));

describe('Documents API', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    describe('uploadDocument', () => {
        it('uploads a file successfully', async () => {
            const mockFile = new File(['test'], 'test.txt', { type: 'text/plain' });
            const mockResponse: DocumentMetadata = {
                id: 'doc-123',
                filename: 'test.txt',
                upload_date: '2024-01-01',
                status: 'pending',
            };

            (api.post as jest.Mock).mockResolvedValue({ data: mockResponse });

            const result = await uploadDocument(mockFile);

            expect(api.post).toHaveBeenCalledWith(
                '/documents/',
                expect.any(FormData),
                expect.objectContaining({
                    headers: { 'Content-Type': 'multipart/form-data' },
                })
            );
            expect(result).toEqual(mockResponse);
        });
    });

    describe('getDocuments', () => {
        it('fetches all documents', async () => {
            const mockDocuments: DocumentMetadata[] = [
                { id: '1', filename: 'doc1.pdf', upload_date: '2024-01-01', status: 'completed' },
                { id: '2', filename: 'doc2.pdf', upload_date: '2024-01-02', status: 'pending' },
            ];

            (api.get as jest.Mock).mockResolvedValue({ data: mockDocuments });

            const result = await getDocuments();

            expect(api.get).toHaveBeenCalledWith('/documents/');
            expect(result).toEqual(mockDocuments);
            expect(result).toHaveLength(2);
        });
    });
});
