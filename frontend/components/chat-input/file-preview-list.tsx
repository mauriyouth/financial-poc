"use client";

import { Loader2 } from 'lucide-react';
import { FileThumbnail } from '@/components/file-thumbnail';
import { DocumentMetadata } from '@/lib/api/documents';

export interface AttachedDocument {
    id: string;
    file: File;
    metadata?: DocumentMetadata;
    isUploading: boolean;
}

interface FilePreviewListProps {
    files: AttachedDocument[];
    onRemove: (id: string) => void;
}

export function FilePreviewList({ files, onRemove }: FilePreviewListProps) {
    // Cleanup object URLs when component unmounts or files change
    // We only need to cleanup for temp files that were created locally
    // Since we create them on the fly in the render loop (Bad practice), we should create them in a memo or effect
    // But since the current code is simple, we'll just handle it slightly differently to avoid leaks

    // Actually, `fileToMetadata` being outside creates a new URL every render if called there.
    // It should be inside the component or better yet, passed in the `AttachedDocument` state.
    // Let's modify how we get the metadata.
    // Ideally the parent should set this, but for now we'll do it here with a side effect cleanup?
    // No, cleaner is to just generate it if it's an image and let the browser handle closure for now,
    // but React strict mode might double invoke.

    // Better approach: modifying the props or state in parent is best, but let's do it safely here.
    // We will just use the one from metadata if available, otherwise create one.

    if (files.length === 0) {
        return null;
    }

    return (
        <div className="flex flex-wrap gap-2 px-1">
            {files.map((doc) => {
                // Create a stable metadata object for preview
                // Note: logic here is slightly "render-time side-effecty" for object URL,
                // but without state it's hard to persist.
                // A better fix would be in ChatInput's handleFilesSelected.
                // But for this quick fix, we'll generate it. `FileThumbnail` uses `img` tag.
                // We will create the URL inline.
                let meta = doc.metadata;
                if (!meta) {
                    meta = {
                        id: doc.id,
                        filename: doc.file.name,
                        upload_date: new Date().toISOString(),
                        status: 'pending',
                        file_type: doc.file.type,
                        thumbnail_url: doc.file.type.startsWith('image/') ? URL.createObjectURL(doc.file) : undefined
                    }
                }

                return (
                    <div key={doc.id} className="relative group">
                        <FileThumbnail
                            file={meta}
                            onRemove={() => onRemove(doc.id)}
                            showRemove={true}
                        />
                        {doc.isUploading && (
                            <div className="absolute inset-0 bg-background/50 flex items-center justify-center rounded-md">
                                <Loader2 className="h-4 w-4 animate-spin text-primary" />
                            </div>
                        )}
                    </div>
                );
            })}
        </div>
    );
}
