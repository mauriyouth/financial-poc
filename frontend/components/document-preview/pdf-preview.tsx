"use client";

import { useState, useEffect, useRef } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import { ZoomIn, ZoomOut, RotateCw, PanelLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { useTheme } from 'next-themes';
import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';

// Set worker source
pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;

interface PDFPreviewProps {
    documentUrl: string;
    page?: number;
    highlight?: {
        page: number;
        x: number;
        y: number;
        width: number;
        height: number;
    };
}

export function PDFPreview({ documentUrl, page, highlight }: PDFPreviewProps) {
    const [numPages, setNumPages] = useState<number>(0);
    const [scale, setScale] = useState<number>(1.0);
    const [rotation, setRotation] = useState<number>(0);
    const [showSidebar, setShowSidebar] = useState(true);
    const { theme } = useTheme();

    // Refs for scrolling
    const pageRefs = useRef<{ [key: number]: HTMLDivElement | null }>({});
    const mainContainerRef = useRef<HTMLDivElement>(null);

    // Scroll to page when 'page' prop changes
    useEffect(() => {
        if (page && pageRefs.current[page]) {
            pageRefs.current[page]?.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }, [page]);

    // Scroll to highlight
    useEffect(() => {
        if (highlight?.page && pageRefs.current[highlight.page]) {
            pageRefs.current[highlight.page]?.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }, [highlight]);

    function onDocumentLoadSuccess({ numPages }: { numPages: number }) {
        setNumPages(numPages);
    }

    const zoomIn = () => setScale(prev => Math.min(prev + 0.2, 3));
    const zoomOut = () => setScale(prev => Math.max(prev - 0.2, 0.5));
    const rotate = () => setRotation(prev => (prev + 90) % 360);

    const isDark = theme === 'dark';

    return (
        <div className="flex flex-col h-full bg-background relative border rounded-md overflow-hidden">
            {/* Toolbar */}
            <div className="flex items-center justify-between p-2 border-b bg-muted/40 z-10 shrink-0">
                <div className="flex items-center gap-1">
                    <Button variant={showSidebar ? "secondary" : "ghost"} size="icon" onClick={() => setShowSidebar(!showSidebar)} title="Toggle Sidebar">
                        <PanelLeft className="h-4 w-4" />
                    </Button>
                    <div className="w-px h-4 bg-border mx-1" />
                    <span className="text-xs text-muted-foreground font-medium px-2">
                        {numPages} Pages
                    </span>
                </div>

                <div className="flex items-center gap-1">
                    <Button variant="ghost" size="icon" onClick={zoomOut}>
                        <ZoomOut className="h-4 w-4" />
                    </Button>
                    <span className="text-xs font-medium w-12 text-center select-none">{Math.round(scale * 100)}%</span>
                    <Button variant="ghost" size="icon" onClick={zoomIn}>
                        <ZoomIn className="h-4 w-4" />
                    </Button>
                    <div className="w-px h-4 bg-border mx-1" />
                    <Button variant="ghost" size="icon" onClick={rotate}>
                        <RotateCw className="h-4 w-4" />
                    </Button>
                </div>
            </div>

            {/* Main Area */}
            <div className="flex-1 flex min-h-0 relative">
                <Document
                    file={documentUrl}
                    onLoadSuccess={onDocumentLoadSuccess}
                    className="flex flex-1 min-h-0"
                    loading={
                        <div className="flex items-center justify-center w-full h-full">
                            <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
                        </div>
                    }
                    error={
                        <div className="flex flex-col items-center justify-center w-full h-full text-red-500 gap-2 p-4">
                            <p className="font-medium">Failed to load PDF</p>
                        </div>
                    }
                >
                    {/* Sidebar Thumbnails */}
                    {showSidebar && (
                        <div className="w-[180px] bg-muted/10 border-r overflow-y-auto shrink-0 flex flex-col gap-4 p-4 text-center">
                            {Array.from(new Array(numPages), (_, index) => (
                                <div
                                    key={`thumb_${index + 1}`}
                                    className="cursor-pointer hover:opacity-80 transition-opacity relative group"
                                    onClick={() => pageRefs.current[index + 1]?.scrollIntoView({ behavior: 'smooth', block: 'start' })}
                                >
                                    <div className={cn("border rounded overflow-hidden shadow-sm transition-ring group-hover:ring-2 ring-primary/50", isDark && "invert-[0.9] hue-rotate-180")}>
                                        <Page
                                            pageNumber={index + 1}
                                            width={150}
                                            renderTextLayer={false}
                                            renderAnnotationLayer={false}
                                        />
                                    </div>
                                    <span className="text-[10px] text-muted-foreground mt-1 block">{index + 1}</span>
                                </div>
                            ))}
                        </div>
                    )}

                    {/* Main Scroll Content */}
                    <div className="flex-1 bg-muted/20 overflow-y-auto p-8 relative" ref={mainContainerRef}>
                        <div className="flex flex-col items-center gap-8">
                            {Array.from(new Array(numPages), (_, index) => (
                                <div
                                    key={`page_${index + 1}`}
                                    ref={(el) => { pageRefs.current[index + 1] = el; }}
                                    className="relative transition-all"
                                >
                                    <div className={cn("shadow-lg transition-all", isDark && "invert-[0.9] hue-rotate-180")}>
                                        <Page
                                            pageNumber={index + 1}
                                            scale={scale}
                                            rotate={rotation}
                                            className="bg-white"
                                            renderTextLayer={true}
                                            renderAnnotationLayer={true}
                                            loading={
                                                <div className="bg-white/50 animate-pulse aspect-[1/1.4] w-[600px]" />
                                            }
                                        />
                                    </div>

                                    {/* Highlight Overlay - Rendered OUTSIDE the inverted container so the yellow highlight stays yellow */}
                                    {highlight && highlight.page === (index + 1) && (
                                        <div
                                            className="absolute top-0 left-0 pointer-events-none z-10"
                                            style={{
                                                left: highlight.x * scale,
                                                top: highlight.y * scale,
                                                width: highlight.width * scale,
                                                height: highlight.height * scale,
                                                backgroundColor: 'rgba(255, 235, 59, 0.4)', // Stronger yellow
                                                border: '2px solid rgba(255, 193, 7, 0.8)',
                                                boxShadow: '0 0 10px rgba(255, 193, 7, 0.5)'
                                            }}
                                        />
                                    )}
                                </div>
                            ))}
                        </div>
                    </div>
                </Document>
            </div>
        </div>
    );
}
