import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { InteractiveTable } from './interactive-table';

interface MarkdownContentProps {
    content: string;
    className?: string;
}

/**
 * Styled markdown renderer with custom components for better formatting.
 * Provides professional styling for headers, tables, lists, code blocks, etc.
 * Uses remark-gfm for GitHub Flavored Markdown support (tables, strikethrough, etc.)
 */
export function MarkdownContent({ content, className = '' }: MarkdownContentProps) {
    return (
        <div className={`prose dark:prose-invert prose-sm max-w-none 
            prose-headings:font-semibold prose-headings:text-foreground
            prose-h2:text-lg prose-h2:mt-6 prose-h2:mb-3 prose-h2:border-b prose-h2:border-border prose-h2:pb-2
            prose-h3:text-base prose-h3:mt-4 prose-h3:mb-2
            prose-p:my-3 prose-p:leading-7
            prose-ul:my-3 prose-ul:space-y-1
            prose-ol:my-3 prose-ol:space-y-1
            prose-li:my-1
            prose-table:my-4 prose-table:border-collapse
            prose-th:border prose-th:border-border prose-th:bg-muted prose-th:px-4 prose-th:py-2 prose-th:font-semibold
            prose-td:border prose-td:border-border prose-td:px-4 prose-td:py-2
            prose-strong:font-semibold prose-strong:text-foreground
            prose-strong:font-semibold prose-strong:text-foreground
            prose-code:bg-muted prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded prose-code:text-sm
            prose-pre:bg-muted prose-pre:border prose-pre:border-border prose-pre:p-4 prose-pre:rounded-lg prose-pre:my-4
            prose-blockquote:border-l-4 prose-blockquote:border-primary prose-blockquote:pl-4 prose-blockquote:italic prose-blockquote:my-4
            break-words min-w-0
            ${className}`}
        >
            <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                    // Headers with custom styling and spacing
                    h2: ({ node, ...props }) => (
                        <h2 className="text-lg font-semibold mt-6 mb-3 pb-2 border-b border-border" {...props} />
                    ),
                    h3: ({ node, ...props }) => (
                        <h3 className="text-base font-semibold mt-4 mb-2" {...props} />
                    ),

                    // Paragraphs with proper spacing
                    p: ({ node, ...props }) => (
                        <p className="my-3 leading-7" {...props} />
                    ),

                    // Lists with better spacing and markers
                    ul: ({ node, ...props }) => (
                        <ul className="my-3 space-y-1 list-disc list-inside" {...props} />
                    ),
                    ol: ({ node, ...props }) => (
                        <ol className="my-3 space-y-1 list-decimal list-inside" {...props} />
                    ),
                    li: ({ node, ...props }) => (
                        <li className="my-1 leading-relaxed" {...props} />
                    ),

                    // Interactive tables with sorting and export
                    table: ({ node, children, ...props }) => (
                        <InteractiveTable>{children}</InteractiveTable>
                    ),

                    // These are handled by InteractiveTable, but keep for fallback
                    thead: ({ node, ...props }) => (
                        <thead className="bg-muted/50" {...props} />
                    ),
                    tbody: ({ node, ...props }) => (
                        <tbody className="divide-y divide-border bg-card" {...props} />
                    ),
                    tr: ({ node, ...props }) => (
                        <tr className="hover:bg-muted/30 transition-colors" {...props} />
                    ),
                    th: ({ node, ...props }) => (
                        <th className="px-4 py-3 text-left text-sm font-semibold text-foreground" {...props} />
                    ),
                    td: ({ node, ...props }) => (
                        <td className="px-4 py-3 text-sm" {...props} />
                    ),

                    // Inline elements
                    strong: ({ node, ...props }) => (
                        <strong className="font-semibold text-foreground" {...props} />
                    ),
                    code: ({ node, inline, ...props }: any) =>
                        inline ? (
                            <code className="bg-muted px-1.5 py-0.5 rounded text-sm font-mono" {...props} />
                        ) : (
                            <code className="block" {...props} />
                        ),
                    pre: ({ node, ...props }) => (
                        <pre className="bg-muted border border-border p-4 rounded-lg my-4 overflow-x-auto" {...props} />
                    ),

                    // Blockquotes
                    blockquote: ({ node, ...props }) => (
                        <blockquote className="border-l-4 border-primary pl-4 italic my-4 text-muted-foreground" {...props} />
                    ),
                }}
            >
                {content}
            </ReactMarkdown>
        </div>
    );
}
