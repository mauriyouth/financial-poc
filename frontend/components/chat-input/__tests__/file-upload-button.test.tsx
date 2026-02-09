import { render, screen, fireEvent } from '@testing-library/react';
import { FileUploadButton } from '../file-upload-button';

describe('FileUploadButton', () => {
    const mockOnFilesSelected = jest.fn();

    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('renders upload button', () => {
        render(<FileUploadButton onFilesSelected={mockOnFilesSelected} />);
        expect(screen.getByTitle(/attach/i)).toBeInTheDocument();
    });

    it('opens popover on click', () => {
        render(<FileUploadButton onFilesSelected={mockOnFilesSelected} />);

        const button = screen.getByTitle(/attach/i);
        fireEvent.click(button);

        expect(screen.getByText('Upload Document')).toBeInTheDocument();
        expect(screen.getByText(/drag & drop/i)).toBeInTheDocument();
    });

    it('disables button when disabled prop is true', () => {
        render(<FileUploadButton onFilesSelected={mockOnFilesSelected} disabled={true} />);

        const button = screen.getByTitle(/attach/i);
        expect(button).toBeDisabled();
    });
});
