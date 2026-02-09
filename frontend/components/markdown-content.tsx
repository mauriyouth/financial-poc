import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { InteractiveTable } from './interactive-table';
import { Citation } from '@/lib/api/chat';
import { AlertTriangle } from 'lucide-react';
import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from "@/components/ui/tooltip";

interface MarkdownContentProps {
    content: string;
    className?: string;
    citations?: Citation[];
    onCitationClick?: (id: string) => void;
    citationStatus?: Record<string, 'valid' | 'invalid' | 'loading' | 'error'>;
}


/**
 * Styled markdown renderer with custom components for better formatting.
 * Provides professional styling for headers, tables, lists, code blocks, etc.
 * Uses remark-gfm for GitHub Flavored Markdown support (tables, strikethrough, etc.)
 */
export function MarkdownContent({ content, className = '', citations, onCitationClick, citationStatus }: MarkdownContentProps) {
    // Process content to replace citations {{cite:id}} with links or error icons
    const citationMap = new Map<string, number>();

    // If citations are provided, initialize the map from them
    // Note: This aligns with backend provided citations, but we might rely on dynamic hydration map now
    if (citations && citations.length > 0) {
        citations.forEach((c, idx) => {
            citationMap.set(c.chunk_id, idx + 1);
        });
    }

    let nextCitationIndex = citationMap.size + 1;

    // First pass: Assign numbers to all VALID citations encountered
    // We need consistency, so maybe we just rely on order of appearance if not in backend list?
    // Actually, let's process them and build the tokens.

    // Split content by regex to interleave components (ReactMarkdown can't easily handle custom component injection via simple replace string)
    // BUT ReactMarkdown expects string input.
    // If we want to render a React Component (Tooltip) inside the markdown, we need a custom plugin or directive.
    // OR we convert {{cite:id}} to a special link format `[error:id](#error)` and handle it in the `a` tag renderer.

    const processedContent = content.replace(/{{cite:([^}]+)}}/g, (match, id) => {
        const status = citationStatus?.[id];

        if (status === 'error') {
            // Mark as error link
            return `[FAILED_CITATION:${id}](#citation-error-${id})`;
        }

        if (!citationMap.has(id)) {
            citationMap.set(id, nextCitationIndex++);
        }
        const num = citationMap.get(id);
        return `[${num}](#citation-${id})`;
    });
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
                    h2: ({ ...props }) => (
                        <h2 className="text-lg font-semibold mt-6 mb-3 pb-2 border-b border-border" {...props} />
                    ),
                    h3: ({ ...props }) => (
                        <h3 className="text-base font-semibold mt-4 mb-2" {...props} />
                    ),

                    // Paragraphs with proper spacing
                    p: ({ ...props }) => (
                        <p className="my-3 leading-7" {...props} />
                    ),

                    // Lists with better spacing and markers
                    ul: ({ ...props }) => (
                        <ul className="my-3 space-y-1 list-disc list-inside" {...props} />
                    ),
                    ol: ({ ...props }) => (
                        <ol className="my-3 space-y-1 list-decimal list-inside" {...props} />
                    ),
                    li: ({ ...props }) => (
                        <li className="my-1 leading-relaxed" {...props} />
                    ),

                    // Interactive tables with sorting and export
                    table: ({ children }) => (
                        <InteractiveTable>{children}</InteractiveTable>
                    ),

                    // These are handled by InteractiveTable, but keep for fallback
                    thead: ({ ...props }) => (
                        <thead className="bg-muted/50" {...props} />
                    ),
                    tbody: ({ ...props }) => (
                        <tbody className="divide-y divide-border bg-card" {...props} />
                    ),
                    tr: ({ ...props }) => (
                        <tr className="hover:bg-muted/30 transition-colors" {...props} />
                    ),
                    th: ({ ...props }) => (
                        <th className="px-4 py-3 text-left text-sm font-semibold text-foreground" {...props} />
                    ),
                    td: ({ ...props }) => (
                        <td className="px-4 py-3 text-sm" {...props} />
                    ),

                    // Inline elements
                    strong: ({ ...props }) => (
                        <strong className="font-semibold text-foreground" {...props} />
                    ),
                    code: ({ inline, ...props }: React.DetailedHTMLProps<React.HTMLAttributes<HTMLElement>, HTMLElement> & { inline?: boolean; node?: unknown }) =>
                        inline ? (
                            <code className="bg-muted px-1.5 py-0.5 rounded text-sm font-mono" {...props} />
                        ) : (
                            <code className="block" {...props} />
                        ),
                    pre: ({ ...props }) => (
                        <pre className="bg-muted border border-border p-4 rounded-lg my-4 overflow-x-auto" {...props} />
                    ),

                    blockquote: ({ ...props }) => (
                        <blockquote className="border-l-4 border-primary pl-4 italic my-4 text-muted-foreground" {...props} />
                    ),

                    // Custom renderer for links to handle citations
                    a: ({ href, children, ...props }) => {
                        if (href?.startsWith('#citation-error-')) {
                            const id = href.replace('#citation-error-', '');
                            return (
                                <TooltipProvider delayDuration={0}>
                                    <Tooltip>
                                        <TooltipTrigger asChild>
                                            <span className="inline-flex items-center justify-center ml-1 text-destructive cursor-help align-text-top">
                                                <AlertTriangle className="h-4 w-4" />
                                            </span>
                                        </TooltipTrigger>
                                        <TooltipContent className="bg-destructive text-destructive-foreground border-destructive">
                                            <p className="font-semibold">Citation Source Not Found</p>
                                            <p className="text-xs">The AI cited a chunk ID ({id.slice(0, 8)}...) that does not exist.</p>
                                        </TooltipContent>
                                    </Tooltip>
                                </TooltipProvider>
                            );
                        }
                        if (href?.startsWith('#citation-')) {
                            const id = href.replace('#citation-', '');
                            const num = children;
                            return (
                                <button
                                    className="inline-flex items-center justify-center w-5 h-5 ml-1 -mt-2 text-[10px] font-bold text-primary bg-primary/10 hover:bg-primary/20 rounded-full cursor-pointer transition-colors align-super"
                                    onClick={(e) => {
                                        e.preventDefault();
                                        if (onCitationClick) onCitationClick(id);
                                    }}
                                    title="View Source"
                                >
                                    {num}
                                </button>
                            );
                        }
                        return <a className="text-primary underline hover:text-primary/80" href={href} {...props}>{children}</a>;
                    },
                }}
            >
                {processedContent}
            </ReactMarkdown>
        </div>
    );
}
