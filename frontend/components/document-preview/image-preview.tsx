"use client";

import Image from 'next/image';

interface ImagePreviewProps {
    documentUrl: string;
    documentName: string;
}

export function ImagePreview({ documentUrl, documentName }: ImagePreviewProps) {
    return (
        <div className="w-full h-full flex items-center justify-center bg-black/5">
            <div className="relative w-full h-full">
                <Image
                    src={documentUrl}
                    alt={documentName}
                    fill
                    className="object-contain shadow-lg"
                    unoptimized
                />
            </div>
        </div>
    );
}
