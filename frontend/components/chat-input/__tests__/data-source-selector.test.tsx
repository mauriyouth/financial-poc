import { render, screen } from '@testing-library/react';
import { DataSourceSelector } from '../data-source-selector';

describe('DataSourceSelector', () => {
    const mockOnChange = jest.fn();

    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('renders with initial value - knowledge', () => {
        render(<DataSourceSelector value="knowledge" onChange={mockOnChange} />);
        expect(screen.getByText('📚 Knowledge')).toBeInTheDocument();
    });

    it('renders with initial value - web', () => {
        render(<DataSourceSelector value="web" onChange={mockOnChange} />);
        expect(screen.getByText('🌐 Web Search')).toBeInTheDocument();
    });

    it('renders with initial value - uploaded', () => {
        render(<DataSourceSelector value="uploaded" onChange={mockOnChange} />);
        expect(screen.getByText('📎 Uploads Only')).toBeInTheDocument();
    });
});
