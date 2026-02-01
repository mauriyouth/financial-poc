"use client";

import React, { useRef, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Sparkles, Send, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { DocumentMetadata, uploadDocument } from '@/lib/api/documents';
import { improvePrompt } from '@/lib/api/chat';

import { ModelSelector } from './model-selector';
import { FileUploadButton, DataSource } from './file-upload-button';
import { FilePreviewList, AttachedDocument } from './file-preview-list';

export type { DataSource };

interface ChatInputProps {
    value: string;
    onChange: (value: string) => void;
    onSend: (message: string, attachments?: DocumentMetadata[]) => void;
    isLoading?: boolean;
    placeholder?: string;
    showDataSourceSelector?: boolean;
    dataSource?: DataSource;
    onDataSourceChange?: (source: DataSource) => void;
    model?: string;
    onModelChange?: (model: string) => void;
    className?: string;
}

export function ChatInput({
    value,
    onChange,
    onSend,
    isLoading = false,
    placeholder = "Message...",
    showDataSourceSelector = false,
    dataSource = 'knowledge',
    onDataSourceChange,
    model,
    onModelChange,
    className
}: ChatInputProps) {
    const [attachedDocs, setAttachedDocs] = useState<AttachedDocument[]>([]);
    const [isImproving, setIsImproving] = useState(false);
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    const handleFilesSelected = async (files: File[]) => {
        const newDocs: AttachedDocument[] = files.map(file => ({
            id: Math.random().toString(36).substring(7),
            file,
            isUploading: true
        }));

        setAttachedDocs(prev => [...prev, ...newDocs]);

        for (const doc of newDocs) {
            try {
                const metadata = await uploadDocument(doc.file);
                setAttachedDocs(prev => prev.map(d =>
                    d.id === doc.id ? { ...d, metadata, isUploading: false } : d
                ));
            } catch (error) {
                console.error("Upload failed for", doc.file.name, error);
                setAttachedDocs(prev => prev.filter(d => d.id !== doc.id));
            }
        }
    };

    const handleSend = () => {
        const validAttachments = attachedDocs
            .filter(d => !d.isUploading && d.metadata)
            .map(d => d.metadata!);

        if ((!value.trim() && validAttachments.length === 0) || isLoading) return;

        onSend(value, validAttachments);
        onChange('');
        setAttachedDocs([]);

        if (textareaRef.current) {
            textareaRef.current.style.height = 'auto';
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
        onChange(e.target.value);
        e.target.style.height = 'auto';
        e.target.style.height = `${e.target.scrollHeight}px`;
    };

    const handleImprovePrompt = async () => {
        if (!value.trim() || isImproving) return;

        setIsImproving(true);
        try {
            // Parse provider and model_id from model string (format: "provider:model_id")
            let provider = "anthropic";
            let model_id = model;

            if (model && model.includes(':')) {
                const parts = model.split(':', 2);
                provider = parts[0];
                model_id = parts[1];
            }

            const improved = await improvePrompt(value, provider, model_id);
            onChange(improved);

            if (textareaRef.current) {
                textareaRef.current.style.height = 'auto';
                textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
            }
        } catch (error) {
            console.error("Failed to improve prompt", error);
        } finally {
            setIsImproving(false);
        }
    };

    const removeDoc = (id: string) => {
        setAttachedDocs(prev => prev.filter(d => d.id !== id));
    };

    const isUploading = attachedDocs.some(d => d.isUploading);

    return (
        <div className={cn("space-y-2", className)}>
            {/* Attached Files Previews */}
            <FilePreviewList files={attachedDocs} onRemove={removeDoc} />

            {/* Input Container */}
            <div className="rounded-3xl shadow-lg focus-within:shadow-xl transition-all overflow-hidden flex flex-col bg-card border border-border">
                <Textarea
                    ref={textareaRef}
                    value={value}
                    onChange={handleInput}
                    onKeyDown={handleKeyDown}
                    placeholder={placeholder}
                    className="min-h-[70px] max-h-[240px] border-none shadow-none focus-visible:ring-0 resize-none text-base px-4 py-3 w-full bg-transparent"
                    disabled={isLoading}
                    rows={1}
                />

                {/* Actions Bar */}
                <div className="flex items-center justify-between p-2 bg-transparent">
                    {/* Left Side Icons: Upload & Data Source Combined */}
                    <div className="flex items-center gap-2">
                        {/* Combined Upload & Data Source Button */}
                        <div className="relative group">
                            <FileUploadButton
                                onFilesSelected={handleFilesSelected}
                                disabled={isLoading}
                                showDataSourceSelector={showDataSourceSelector}
                                dataSource={dataSource}
                                onDataSourceChange={onDataSourceChange}
                            />
                            <span className="absolute bottom-full left-0 mb-2 px-2 py-1 bg-popover text-popover-foreground text-xs rounded whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50">
                                Add Files & Sources
                            </span>
                        </div>
                        <div className="relative group">
                            <Button
                                variant="ghost"
                                size="icon"
                                className="h-9 w-9 text-muted-foreground hover:text-foreground rounded-lg hover:bg-accent/50"
                                onClick={handleImprovePrompt}
                                disabled={isLoading || !value.trim() || isImproving}
                            >
                                {isImproving ? (
                                    <Loader2 className="h-4 w-4 animate-spin" />
                                ) : (
                                    <Sparkles className="h-4 w-4" />
                                )}
                            </Button>
                            <span className="absolute bottom-full left-0 mb-2 px-2 py-1 bg-popover text-popover-foreground text-xs rounded whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50">
                                Improve Prompt
                            </span>
                        </div>
                    </div>

                    {/* Right Side Icons: Model, Improve, Send */}
                    <div className="flex items-center gap-2">
                        {/* Model Selector */}
                        {onModelChange && (
                            <div className="relative group">
                                <ModelSelector value={model} onChange={onModelChange} />
                                <span className="absolute rounded-lg bottom-full right-0 mb-2 px-2 py-1 bg-popover text-popover-foreground text-xs whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50">
                                    Select AI Model
                                </span>
                            </div>
                        )}

                        {/* Send Button */}
                        <div className="relative group">
                            <Button
                                onClick={handleSend}
                                disabled={isLoading || (!value.trim() && attachedDocs.length === 0) || isUploading}
                                size="icon"
                                className="h-9 w-9 rounded-full"
                            >
                                <Send className="h-4 w-4" />
                            </Button>
                            <span className="absolute rounded-lg bottom-full right-0 mb-2 px-2 py-1 bg-popover text-popover-foreground text-xs whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50">
                                Send (Enter)
                            </span>
                        </div>
                    </div>
                </div>
            </div>

            {/* Helper Text */}
            <div className="text-center text-xs text-muted-foreground/50">
                AI available tools: Python Code Interpreter, Web Search, Knowledge Base Retrieval
            </div>
        </div>
    );
}
