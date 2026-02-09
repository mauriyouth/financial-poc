import React from 'react';
import { MarkdownContent } from '@/components/markdown-content';
import { DocumentMetadata, getDocumentDownloadUrl } from '@/lib/api/documents';
import { parseAttachments } from './attachmentParser';
import dynamic from 'next/dynamic';

const FilePreviewThumbnail = dynamic(() => import('../file-preview-thumbnail').then(mod => mod.FilePreviewThumbnail), {
    ssr: false,
    loading: () => <div className="w-16 h-20 bg-muted/20 rounded-md animate-pulse" />
});

interface UserMessageProps {
    content: string;
    onSourceClick?: (source: DocumentMetadata) => void;
}

export function UserMessage({ content, onSourceClick }: UserMessageProps) {
    const { cleanText, attachments } = parseAttachments(content);

    return (
        <div className="flex-1 min-w-0 p-4 rounded-2xl shadow-sm bg-secondary text-primary-foreground rounded-tr-sm break-words overflow-hidden">
            <div className="space-y-2">
                {/* Render Attachments Grid */}
                {attachments.length > 0 && (
                    <div className="flex flex-wrap gap-2 mb-2">
                        {attachments.map((att) => (
                            <div key={att.id}>
                                <FilePreviewThumbnail
                                    file={{
                                        id: att.id,
                                        filename: att.filename,
                                        upload_date: '',
                                        status: 'completed',
                                        download_url: getDocumentDownloadUrl(att.id)
                                    }}
                                    onClick={() => {
                                        const docMeta: DocumentMetadata = {
                                            id: att.id,
                                            filename: att.filename,
                                            upload_date: new Date().toISOString(),
                                            status: 'completed',
                                            download_url: getDocumentDownloadUrl(att.id)
                                        };
                                        onSourceClick?.(docMeta);
                                    }}
                                />
                            </div>
                        ))}
                    </div>
                )}

                {/* Render Cleaned Text */}
                {cleanText && (
                    <div className="text-sm leading-relaxed text-primary break-words">
                        <MarkdownContent content={cleanText} />
                    </div>
                )}
            </div>
        </div>
    );
}
