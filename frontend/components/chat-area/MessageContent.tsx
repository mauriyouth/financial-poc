import React from 'react';
import ReactMarkdown from 'react-markdown';
import { Citation } from '@/lib/api/chat';
import { CitationBadge } from './CitationBadge';

interface MessageContentProps {
    content: string;
    citations?: Citation[];
    onCitationClick: (citation: Citation) => void;
}

export function MessageContent({ content, citations, onCitationClick }: MessageContentProps) {
    if (!citations || citations.length === 0) {
        return <ReactMarkdown>{content}</ReactMarkdown>;
    }

    // Parse content and replace [1], [2] etc. with citation badges
    const renderWithCitations = () => {
        const parts: React.ReactNode[] = [];
        const citationPattern = /\[(\d+)\]/g;
        let lastIndex = 0;
        let match;

        while ((match = citationPattern.exec(content)) !== null) {
            const citationNumber = parseInt(match[1]);
            const citation = citations[citationNumber - 1];

            // Add text before citation
            if (match.index > lastIndex) {
                const textBefore = content.substring(lastIndex, match.index);
                parts.push(
                    <ReactMarkdown key={`text-${lastIndex}`}>{textBefore}</ReactMarkdown>
                );
            }

            // Add citation badge
            if (citation) {
                parts.push(
                    <CitationBadge
                        key={`citation-${citationNumber}`}
                        citation={citation}
                        index={citationNumber}
                        onCitationClick={onCitationClick}
                    />
                );
            } else {
                // If citation not found, keep original text
                parts.push(<span key={`missing-${match.index}`}>{match[0]}</span>);
            }

            lastIndex = match.index + match[0].length;
        }

        // Add remaining text
        if (lastIndex < content.length) {
            const remainingText = content.substring(lastIndex);
            parts.push(
                <ReactMarkdown key={`text-${lastIndex}`}>{remainingText}</ReactMarkdown>
            );
        }

        return parts.length > 0 ? parts : <ReactMarkdown>{content}</ReactMarkdown>;
    };

    return <div className="inline">{renderWithCitations()}</div>;
}
