import { render, screen } from '@testing-library/react';
import { FilePreviewList, AttachedDocument } from '../file-preview-list';

describe('FilePreviewList', () => {
    const mockOnRemove = jest.fn();

    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('renders null when no files', () => {
        const { container } = render(<FilePreviewList files={[]} onRemove={mockOnRemove} />);
        expect(container.firstChild).toBeNull();
    });

    it('renders file list', () => {
        const files: AttachedDocument[] = [
            {
                id: '1',
                file: new File(['content'], 'test.pdf', { type: 'application/pdf' }),
                isUploading: false
            }
        ];

        render(<FilePreviewList files={files} onRemove={mockOnRemove} />);
        expect(screen.getByText('test.pdf')).toBeInTheDocument();
    });

    it('shows loading indicator for uploading files', () => {
        const files: AttachedDocument[] = [
            {
                id: '1',
                file: new File(['content'], 'test.pdf', { type: 'application/pdf' }),
                isUploading: true
            }
        ];

        render(<FilePreviewList files={files} onRemove={mockOnRemove} />);

        // Look for the Loader2 SVG
        const loader = document.querySelector('.lucide-loader-2');
        expect(loader).toBeInTheDocument();
    });
});
