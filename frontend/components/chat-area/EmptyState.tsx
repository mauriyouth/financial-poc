import React from 'react';
import { Bot } from 'lucide-react';

export function EmptyState() {
    return (
        <div className="flex flex-col items-center justify-center h-[50vh] text-center space-y-4">
            <div className="bg-primary/10 p-4 rounded-full">
                <Bot size={48} className="text-primary" />
            </div>
            <div className="space-y-2">
                <h3 className="text-xl font-semibold">How can I help you today?</h3>
                <p className="text-muted-foreground max-w-sm">
                    I can analyze your financial documents, summarize reports, or answer questions about your data.
                </p>
            </div>
        </div>
    );
}
