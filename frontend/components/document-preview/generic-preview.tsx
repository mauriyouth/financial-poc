"use client";

import { Download, FileText } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface GenericPreviewProps {
    documentUrl: string;
}

export function GenericPreview({ documentUrl }: GenericPreviewProps) {
    return (
        <div className="flex flex-col items-center justify-center h-full p-6 text-center">
            <FileText className="h-16 w-16 mb-4 text-muted-foreground opacity-50" />
            <p className="text-sm font-medium mb-2">Preview not available</p>
            <p className="text-xs text-muted-foreground mb-4">
                This file type cannot be previewed
            </p>
            <Button
                variant="outline"
                size="sm"
                onClick={() => window.open(documentUrl, '_blank')}
            >
                <Download className="h-4 w-4 mr-2" />
                Download File
            </Button>
        </div>
    );
}
