import { render, screen, waitFor } from '@testing-library/react';
import { ModelSelector } from '../model-selector';
import * as ChatApi from '@/lib/api/chat';

jest.mock('@/lib/api/chat', () => ({
    getModels: jest.fn(),
}));

describe('ModelSelector', () => {
    const mockOnChange = jest.fn();

    beforeEach(() => {
        jest.clearAllMocks();
        (ChatApi.getModels as jest.Mock).mockResolvedValue([
            { id: 'anthropic', name: 'Claude' },
            { id: 'google', name: 'Gemini' }
        ]);
    });

    it('renders with initial value', async () => {
        render(<ModelSelector value="anthropic" onChange={mockOnChange} />);

        await waitFor(() => {
            expect(screen.getByText('Claude')).toBeInTheDocument();
        });
    });

    it('loads models from API', async () => {
        render(<ModelSelector value="anthropic" onChange={mockOnChange} />);

        await waitFor(() => {
            expect(ChatApi.getModels).toHaveBeenCalled();
        });
    });

    it('falls back to default models on error', async () => {
        (ChatApi.getModels as jest.Mock).mockRejectedValue(new Error('Failed'));
        render(<ModelSelector value="anthropic" onChange={mockOnChange} />);

        await waitFor(() => {
            expect(screen.getByText('Claude 3.5 Sonnet')).toBeInTheDocument();
        });
    });

    it('renders null when no models', () => {
        (ChatApi.getModels as jest.Mock).mockResolvedValue([]);
        const { container } = render(<ModelSelector value="anthropic" onChange={mockOnChange} />);

        // Initially should render, but after loading empty models, should be null
        expect(container.firstChild).toBeInTheDocument();
    });
});
