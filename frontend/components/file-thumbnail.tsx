import { DocumentMetadata } from '@/lib/api/documents';
import { FileText, File, FileSpreadsheet, FileImage, X } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import Image from 'next/image';

interface FileThumbnailProps {
    file: DocumentMetadata;
    onRemove?: () => void;
    onClick?: () => void;
    showRemove?: boolean;
}

export function FileThumbnail({ file, onRemove, onClick, showRemove = false }: FileThumbnailProps) {
    const getFileIcon = (filename: string) => {
        const ext = filename.split('.').pop()?.toLowerCase();
        switch (ext) {
            case 'pdf':
                return <FileText className="h-4 w-4 text-red-500" aria-label="PDF file" role="img" />;
            case 'xlsx':
            case 'xls':
            case 'csv':
                return <FileSpreadsheet className="h-4 w-4 text-green-500" aria-label="Spreadsheet file" role="img" />;
            case 'png':
            case 'jpg':
            case 'jpeg':
            case 'gif':
                return <FileImage className="h-4 w-4 text-blue-500" aria-label="Image file" role="img" />;
            default:
                return <File className="h-4 w-4 text-gray-500" aria-label="File" role="img" />;
        }
    };

    return (
        <Badge
            variant="secondary"
            className={`gap-2 pr-1 pl-3 py-1.5 ${onClick ? 'cursor-pointer hover:bg-secondary/80' : ''}`}
            onClick={onClick}
        >
            {file.thumbnail_url ? (
                <div className="relative h-6 w-6 shrink-0">
                    <Image
                        src={file.thumbnail_url}
                        alt={file.filename}
                        fill
                        className="object-cover rounded-sm"
                        unoptimized
                    />
                </div>
            ) : (
                getFileIcon(file.filename)
            )}
            <span className="max-w-[200px] truncate">{file.filename}</span>
            {showRemove && onRemove && (
                <button
                    onClick={(e) => {
                        e.stopPropagation();
                        onRemove();
                    }}
                    className="ml-1 rounded-full hover:bg-destructive/20 p-0.5"
                    aria-label="Remove file"
                >
                    <X className="h-3 w-3" />
                </button>
            )}
        </Badge>
    );
}
