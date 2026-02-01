import React from 'react';
import { Bot } from 'lucide-react';

export function LoadingIndicator() {
    return (
        <div className="flex justify-start">
            <div className="flex items-start space-x-2 max-w-[85%]">
                <div className="w-8 h-8 rounded-full flex items-center justify-center shrink-0 border shadow-sm bg-muted text-foreground">
                    <Bot size={16} />
                </div>
                <div className="bg-card border p-4 rounded-2xl rounded-bl-none shadow-sm flex items-center space-x-2">
                    <span className="flex space-x-1">
                        <span className="w-2 h-2 bg-muted-foreground/40 rounded-full animate-bounce [animation-delay:-0.3s]"></span>
                        <span className="w-2 h-2 bg-muted-foreground/40 rounded-full animate-bounce [animation-delay:-0.15s]"></span>
                        <span className="w-2 h-2 bg-muted-foreground/40 rounded-full animate-bounce"></span>
                    </span>
                </div>
            </div>
        </div>
    );
}
