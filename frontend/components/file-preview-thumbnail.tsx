"use client";

import React, { useState } from 'react';
import { DocumentMetadata } from '@/lib/api/documents';
import { FileText, File as FileIcon, FileSpreadsheet, X, Image as ImageIcon } from 'lucide-react';
import { Document, Page, pdfjs } from 'react-pdf';
import { cn } from '@/lib/utils';
import Image from 'next/image';

// Configure PDF.js worker
pdfjs.GlobalWorkerOptions.workerSrc = `https://unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;

interface FilePreviewThumbnailProps {
    file: File | DocumentMetadata;
    onRemove?: () => void;
    onClick?: () => void;
}

export function FilePreviewThumbnail({ file, onRemove, onClick }: FilePreviewThumbnailProps) {

    const isFileObject = (f: File | DocumentMetadata): f is File => {
        return f instanceof File;
    };

    const filename = isFileObject(file) ? file.name : file.filename;
    const fileType = isFileObject(file) ? file.type : file.file_type; // DocumentMetadata might need file_type mapping if not present

    // Heuristic for file type if content-type is missing or generic
    const ext = filename.split('.').pop()?.toLowerCase();

    const isImage = fileType?.startsWith('image/') || ['jpg', 'jpeg', 'png', 'gif', 'webp'].includes(ext || '');
    const isPdf = fileType === 'application/pdf' || ext === 'pdf';

    // Create source for preview
    const [previewSource, setPreviewSource] = useState<string | null>(null);

    React.useEffect(() => {
        let url: string | null = null;

        if (isFileObject(file)) {
            url = URL.createObjectURL(file);
            setPreviewSource(url);
        } else if (file.download_url) {
            setPreviewSource(file.download_url);
        } else {
            setPreviewSource(null);
        }

        return () => {
            if (url) {
                URL.revokeObjectURL(url);
            }
        };
    }, [file]);

    const renderPreview = () => {
        if (isImage && previewSource) {
            return (
                <div className="relative w-16 h-20 bg-muted/20 rounded-md overflow-hidden border border-border">
                    <Image
                        src={previewSource}
                        alt={filename}
                        fill
                        className="object-cover"
                        unoptimized
                    />
                </div>
            );
        }

        if (isPdf && previewSource) {
            return (
                <div className="relative w-16 h-20 bg-muted/20 rounded-md overflow-hidden border border-border">
                    <Document
                        file={previewSource}
                        loading={<div className="w-full h-full flex items-center justify-center"><div className="w-4 h-4 bg-primary/20 animate-pulse rounded-full" /></div>}
                        className="w-full h-full"
                    >
                        <Page
                            pageNumber={1}
                            width={64} // approx width of w-16
                            renderTextLayer={false}
                            renderAnnotationLayer={false}
                        />
                    </Document>
                </div>
            );
        }

        // Default / Office / Fallback preview
        let Icon = FileIcon;
        let colorClass = "text-gray-500";
        let bgClass = "bg-gray-50 dark:bg-gray-900";

        if (['xlsx', 'xls', 'csv'].includes(ext || '')) {
            Icon = FileSpreadsheet;
            colorClass = "text-green-600";
            bgClass = "bg-green-50 dark:bg-green-950/30";
        } else if (['doc', 'docx'].includes(ext || '')) {
            Icon = FileText;
            colorClass = "text-blue-600";
            bgClass = "bg-blue-50 dark:bg-blue-950/30";
        } else if (['ppt', 'pptx'].includes(ext || '')) {
            Icon = FileText; // Or a presentation icon if available
            colorClass = "text-orange-600";
            bgClass = "bg-orange-50 dark:bg-orange-950/30";
        } else if (isPdf) {
            Icon = FileText;
            colorClass = "text-red-600";
            bgClass = "bg-red-50 dark:bg-red-950/30";
        } else if (isImage) {
            Icon = ImageIcon;
            colorClass = "text-purple-600";
            bgClass = "bg-purple-50 dark:bg-purple-950/30";
        }

        return (
            <div className={`relative w-16 h-20 rounded-md overflow-hidden border border-border flex items-center justify-center ${bgClass}`}>
                <Icon className={`h-8 w-8 ${colorClass}`} />
            </div>
        );
    };

    return (
        <div
            className={cn("relative group shrink-0", onClick && "cursor-pointer transition-transform hover:scale-105")}
            onClick={onClick}
        >
            {renderPreview()}

            {onRemove && (
                <button
                    onClick={(e) => {
                        e.stopPropagation();
                        onRemove();
                    }}
                    className="absolute -top-1.5 -right-1.5 bg-destructive text-destructive-foreground rounded-full p-0.5 shadow-sm opacity-0 group-hover:opacity-100 transition-opacity"
                    aria-label="Remove file"
                >
                    <X className="h-3 w-3" />
                </button>
            )}

            <div className="absolute bottom-0 left-0 right-0 bg-black/60 p-0.5 text-[8px] text-white truncate text-center leading-tight">
                {filename}
            </div>
        </div>
    );
}
