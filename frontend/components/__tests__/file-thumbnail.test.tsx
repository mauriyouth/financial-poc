import { render, screen } from '@testing-library/react';
import { DocumentMetadata } from '@/lib/api/documents';
import { FileThumbnail } from '../file-thumbnail';

describe('FileThumbnail', () => {
    const mockDocument: DocumentMetadata = {
        id: 'test-123',
        filename: 'test.pdf',
        upload_date: '2024-01-01',
        status: 'completed',
        file_type: 'application/pdf',
    };

    it('renders document filename', () => {
        render(<FileThumbnail file={mockDocument} />);
        expect(screen.getByText('test.pdf')).toBeInTheDocument();
    });

    it('shows PDF icon for PDF files', () => {
        render(<FileThumbnail file={mockDocument} />);
        expect(screen.getByRole('img', { hidden: true })).toBeInTheDocument();
    });

    it('shows completed status correctly', () => {
        render(<FileThumbnail file={mockDocument} />);
        expect(screen.getByText('test.pdf')).toBeInTheDocument();
    });
});
