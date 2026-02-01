"use client";

interface PDFPreviewProps {
    documentUrl: string;

}

export function PDFPreview({ documentUrl }: PDFPreviewProps) {
    return (
        <iframe
            src={`${documentUrl}#view=FitH`}
            className="w-full h-full"
            title="PDF Document Preview"
        />
    );
}
