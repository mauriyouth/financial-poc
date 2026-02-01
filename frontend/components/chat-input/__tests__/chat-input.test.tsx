import { render, screen, fireEvent } from '@testing-library/react';
import { ChatInput } from '../index';
import * as ChatApi from '@/lib/api/chat';

jest.mock('@/lib/api/chat', () => ({
    getModels: jest.fn(),
    improvePrompt: jest.fn(),
}));

jest.mock('@/lib/api/documents', () => ({
    uploadDocument: jest.fn(),
}));

describe('ChatInput', () => {
    const mockOnSend = jest.fn();
    const mockOnChange = jest.fn();
    const mockOnDataSourceChange = jest.fn();
    const mockOnModelChange = jest.fn();

    const defaultProps = {
        value: '',
        onChange: mockOnChange,
        onSend: mockOnSend,
        onDataSourceChange: mockOnDataSourceChange,
        onModelChange: mockOnModelChange,
        showDataSourceSelector: true,
        model: 'anthropic'
    };

    beforeEach(() => {
        jest.clearAllMocks();
        (ChatApi.getModels as jest.Mock).mockResolvedValue([
            { id: 'anthropic', name: 'Claude' },
            { id: 'google', name: 'Gemini' }
        ]);
    });

    it('renders text area and buttons', () => {
        render(<ChatInput {...defaultProps} />);

        expect(screen.getByPlaceholderText(/message/i)).toBeInTheDocument();
        expect(screen.getByTitle(/attach/i)).toBeInTheDocument();
        expect(screen.getByTitle(/improve/i)).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /send/i })).toBeInTheDocument();
    });

    it('handles text input', () => {
        render(<ChatInput {...defaultProps} />);

        const textarea = screen.getByPlaceholderText(/message/i);
        fireEvent.change(textarea, { target: { value: 'Hello' } });

        expect(mockOnChange).toHaveBeenCalledWith('Hello');
    });

    it('submits on click send', () => {
        render(<ChatInput {...defaultProps} value="Hello world" />);

        const sendButton = screen.getByRole('button', { name: /send/i });
        expect(sendButton).not.toBeDisabled();

        fireEvent.click(sendButton);
        expect(mockOnSend).toHaveBeenCalledWith('Hello world', []);
        expect(mockOnChange).toHaveBeenCalledWith('');
    });

    it('renders ModelSelector when onModelChange is provided', () => {
        render(<ChatInput {...defaultProps} />);
        // ModelSelector will try to load, we just verify it's in the component tree
        expect(ChatApi.getModels).toHaveBeenCalled();
    });

    it('renders DataSourceSelector when showDataSourceSelector is true', () => {
        render(<ChatInput {...defaultProps} dataSource="knowledge" />);
        expect(screen.getByText('📚 Knowledge')).toBeInTheDocument();
    });

    it('does not render DataSourceSelector when showDataSourceSelector is false', () => {
        render(<ChatInput {...defaultProps} showDataSourceSelector={false} />);
        expect(screen.queryByText('📚 Knowledge')).not.toBeInTheDocument();
    });
});
