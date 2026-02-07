"use client";

interface PDFPreviewProps {
    documentUrl: string;

}

export function PDFPreview({ documentUrl, page }: PDFPreviewProps & { page?: number }) {
    const src = page ? `${documentUrl}#page=${page}&view=FitH` : `${documentUrl}#view=FitH`;
    return (
        <iframe
            src={src}
            className="w-full h-full"
            title="PDF Document Preview"
        />
    );
}
