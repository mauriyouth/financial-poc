"use client";

import { useState } from 'react';
import { ScrollArea } from '@/components/ui/scroll-area';
import { X, FileText, Download, FileSpreadsheet, FileImage, File, Maximize, Minimize } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { DocumentMetadata, getDocumentDownloadUrl } from '@/lib/api/documents';
import { cn } from '@/lib/utils';
import { PDFPreview } from './pdf-preview';
import { ExcelPreview } from './excel-preview';
import { ImagePreview } from './image-preview';
import { GenericPreview } from './generic-preview';

export interface DocumentPreviewProps {
    documents: DocumentMetadata[];
    activeId?: string;
    onActiveChange: (id: string) => void;
    onClose: () => void;
    onCloseDocument: (id: string) => void;
    isFullscreen?: boolean;
    onToggleFullscreen?: () => void;
}

export function DocumentPreview({
    documents,
    activeId,
    onActiveChange,
    onClose,
    onCloseDocument,
    isFullscreen = false,
    onToggleFullscreen
}: DocumentPreviewProps) {
    const currentId = activeId || documents[0]?.id;

    // Move useState before any conditional returns (React Hooks rule)
    const [activeTab, setActiveTab] = useState<string>("preview");

    if (!documents.length) {
        return null;
    }

    const currentDocument = documents.find(doc => doc.id === currentId) || documents[0];

    const documentId = currentDocument.id;
    const documentName = currentDocument.filename;

    const getFileIcon = (filename: string) => {
        const ext = filename.split('.').pop()?.toLowerCase();
        switch (ext) {
            case 'pdf':
                return <FileText className="h-3 w-3 shrink-0 text-red-500" />;
            case 'xlsx':
            case 'xls':
            case 'csv':
                return <FileSpreadsheet className="h-3 w-3 shrink-0 text-green-500" />;
            case 'png':
            case 'jpg':
            case 'jpeg':
            case 'gif':
            case 'webp':
                return <FileImage className="h-3 w-3 shrink-0 text-blue-500" />;
            case 'pptx':
            case 'ppt':
                return <FileText className="h-3 w-3 shrink-0 text-orange-500" />;
            default:
                return <File className="h-3 w-3 shrink-0 text-muted-foreground" />;
        }
    };

    // Determine file type from extension
    const fileExt = documentName?.split('.').pop()?.toLowerCase();
    const isPDF = fileExt === 'pdf';
    const isExcel = ['xlsx', 'xls', 'csv'].includes(fileExt || '');
    const isPowerPoint = ['pptx', 'ppt'].includes(fileExt || '');
    const isOfficeDoc = ['docx', 'doc'].includes(fileExt || '');
    const isImage = ['jpg', 'jpeg', 'png', 'gif', 'webp'].includes(fileExt || '');

    const documentUrl = currentDocument.download_url || getDocumentDownloadUrl(documentId);

    // Render appropriate preview component
    const renderPreview = () => {
        // PowerPoint files are auto-converted to PDF on upload, so use PDF preview
        if (isPDF || isPowerPoint) {
            return <PDFPreview documentUrl={documentUrl} />;
        }
        if (isExcel) {
            return <ExcelPreview documentId={documentId} documentUrl={documentUrl} documentName={documentName} />;
        }
        if (isImage) {
            return <ImagePreview documentUrl={documentUrl} documentName={documentName} />;
        }
        if (isOfficeDoc) {
            // Word documents - could add docx-preview.tsx later
            return <GenericPreview documentUrl={documentUrl} />;
        }
        return <GenericPreview documentUrl={documentUrl} />;
    };

    return (
        <div className="flex flex-col h-full bg-card">
            {/* Document Tabs with Action Buttons */}
            <div className="flex items-center justify-between bg-muted/30 border-b">
                <div className="flex items-center overflow-x-auto no-scrollbar flex-1">
                    {documents.map((doc) => (
                        <div
                            key={doc.id}
                            className={cn(
                                "flex items-center gap-2 px-3 py-2 text-sm border-r cursor-pointer select-none hover:bg-muted/50 transition-colors min-w-[120px] max-w-[200px]",
                                doc.id === currentId ? "bg-background font-medium text-foreground" : "text-muted-foreground bg-muted/10"
                            )}
                            onClick={() => onActiveChange(doc.id)}
                        >
                            {getFileIcon(doc.filename)}
                            <span className="truncate flex-1">{doc.filename}</span>
                            <div
                                role="button"
                                className="p-0.5 hover:bg-muted-foreground/20 rounded-sm"
                                onClick={(e) => {
                                    e.stopPropagation();
                                    onCloseDocument(doc.id);
                                }}
                            >
                                <X className="h-3 w-3" />
                            </div>
                        </div>
                    ))}
                </div>

                {/* Action Buttons */}
                <div className="flex items-center gap-1 px-2 border-l bg-background/50">
                    {onToggleFullscreen && (
                        <Button
                            variant="ghost"
                            size="sm"
                            onClick={onToggleFullscreen}
                            title={isFullscreen ? "Exit Fullscreen" : "Fullscreen"}
                            className="h-8 w-8 p-0"
                        >
                            {isFullscreen ? <Minimize className="h-4 w-4" /> : <Maximize className="h-4 w-4" />}
                        </Button>
                    )}
                    <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => window.open(documentUrl, '_blank')}
                        title="Download"
                        className="h-8 w-8 p-0"
                    >
                        <Download className="h-4 w-4" />
                    </Button>
                    <Button
                        variant="ghost"
                        size="sm"
                        onClick={onClose}
                        title="Close"
                        className="h-8 w-8 p-0"
                    >
                        <X className="h-4 w-4" />
                    </Button>
                </div>
            </div>

            {/* Content */}
            <Tabs key={documentId} value={activeTab} onValueChange={setActiveTab} className="flex-1 flex flex-col min-h-0">
                <TabsList className="mx-4 mt-4 shrink-0">
                    <TabsTrigger value="preview">Preview</TabsTrigger>
                    <TabsTrigger value="details">Details</TabsTrigger>
                </TabsList>

                <TabsContent value="preview" className="flex-1 mt-0 p-4 min-h-0 overflow-hidden">
                    <div className="h-full bg-muted/5 rounded-lg border overflow-hidden relative">
                        {renderPreview()}
                    </div>
                </TabsContent>

                <TabsContent value="details" className="flex-1 mt-0 p-4 min-h-0 overflow-hidden">
                    <ScrollArea className="h-full">
                        <div className="space-y-4 pr-4">
                            <div>
                                <label className="text-xs font-semibold text-muted-foreground uppercase">File Name</label>
                                <p className="mt-1 text-sm">{documentName}</p>
                            </div>
                            <div>
                                <label className="text-xs font-semibold text-muted-foreground uppercase">Document ID</label>
                                <p className="mt-1 text-sm font-mono text-xs">{documentId}</p>
                            </div>
                            <div>
                                <label className="text-xs font-semibold text-muted-foreground uppercase">File Type</label>
                                <p className="mt-1 text-sm">{fileExt?.toUpperCase()} - {
                                    isPDF ? 'PDF Document' :
                                        isExcel ? 'Excel Spreadsheet' :
                                            isPowerPoint ? 'PowerPoint Presentation' :
                                                isOfficeDoc ? 'Word Document' :
                                                    'Unknown Type'
                                }</p>
                            </div>
                            <div>
                                <label className="text-xs font-semibold text-muted-foreground uppercase">Actions</label>
                                <div className="mt-2 space-y-2">
                                    <Button
                                        variant="outline"
                                        size="sm"
                                        className="w-full justify-start"
                                        onClick={() => window.open(documentUrl, '_blank')}
                                    >
                                        <Download className="h-4 w-4 mr-2" />
                                        Download Document
                                    </Button>
                                </div>
                            </div>
                        </div>
                    </ScrollArea>
                </TabsContent>
            </Tabs>
        </div>
    );
}
