"use client";

import { useEffect, useState } from 'react';
import { ChevronLeft, ChevronRight, Copy, Download, FileText } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { getDocumentSlides, Slide } from '@/lib/api/documents';
import Image from 'next/image';

interface PPTXPreviewProps {
    documentId: string;
    documentUrl: string;
    documentName?: string;
}

export function PPTXPreview({ documentId, documentUrl }: PPTXPreviewProps) {
    const [slides, setSlides] = useState<Slide[]>([]);
    const [currentSlideIndex, setCurrentSlideIndex] = useState(0);
    const [slidesLoading, setSlidesLoading] = useState(false);

    useEffect(() => {
        let cancelled = false;

        const loadSlides = async () => {
            if (cancelled) return;

            setSlides([]);
            setCurrentSlideIndex(0);
            setSlidesLoading(true);

            try {
                const data = await getDocumentSlides(documentId);
                if (!cancelled) {
                    setSlides(data.slides);
                }
            } catch (err) {
                console.error('Failed to load slides:', err);
                if (!cancelled) {
                    setSlides([]);
                }
            } finally {
                if (!cancelled) {
                    setSlidesLoading(false);
                }
            }
        };

        loadSlides();

        return () => {
            cancelled = true;
        };
    }, [documentId]);

    const handlePreviousSlide = () => {
        setCurrentSlideIndex(prev => Math.max(0, prev - 1));
    };

    const handleNextSlide = () => {
        setCurrentSlideIndex(prev => Math.min(slides.length - 1, prev + 1));
    };

    const handleCopySlideImage = async () => {
        if (!slides[currentSlideIndex]) return;

        try {
            const response = await fetch(slides[currentSlideIndex].image_url);
            const blob = await response.blob();
            await navigator.clipboard.write([
                new ClipboardItem({ 'image/png': blob })
            ]);
            console.log('Slide copied successfully');
        } catch (error) {
            console.error('Failed to copy:', error);
            alert('Failed to copy slide image');
        }
    };

    const handleDownloadSlide = () => {
        if (!slides[currentSlideIndex]) return;
        window.open(slides[currentSlideIndex].download_url, '_blank');
    };

    if (slidesLoading) {
        return (
            <div className="flex-1 flex items-center justify-center">
                <div className="text-muted-foreground">Loading slides...</div>
            </div>
        );
    }

    if (slides.length === 0) {
        return (
            <div className="flex-1 flex flex-col items-center justify-center p-6 text-center">
                <FileText className="h-16 w-16 mb-4 text-muted-foreground opacity-50" />
                <p className="text-sm font-medium mb-2">No slides available</p>
                <p className="text-xs text-muted-foreground mb-4">
                    Slides may still be processing or failed to extract
                </p>
                <Button
                    variant="outline"
                    size="sm"
                    onClick={() => window.open(documentUrl, '_blank')}
                >
                    <Download className="h-4 w-4 mr-2" />
                    Download Original
                </Button>
            </div>
        );
    }

    return (
        <div className="w-full h-full flex flex-col">
            {/* Slide Navigation Header */}
            <div className="flex items-center justify-between p-3 border-b bg-muted/30 shrink-0">
                <div className="flex items-center gap-2">
                    <Button
                        variant="ghost"
                        size="sm"
                        onClick={handlePreviousSlide}
                        disabled={currentSlideIndex === 0}
                    >
                        <ChevronLeft className="h-4 w-4" />
                    </Button>
                    <span className="text-sm font-medium min-w-[80px] text-center">
                        Slide {currentSlideIndex + 1} / {slides.length}
                    </span>
                    <Button
                        variant="ghost"
                        size="sm"
                        onClick={handleNextSlide}
                        disabled={currentSlideIndex === slides.length - 1}
                    >
                        <ChevronRight className="h-4 w-4" />
                    </Button>
                </div>

                <div className="flex items-center gap-2">
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={handleCopySlideImage}
                    >
                        <Copy className="h-4 w-4 mr-2" />
                        Quick Copy
                    </Button>
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={handleDownloadSlide}
                    >
                        <Download className="h-4 w-4 mr-2" />
                        Download .pptx
                    </Button>
                </div>
            </div>

            {/* Slide Display Area */}
            <div className="flex-1 relative overflow-auto bg-neutral-100 dark:bg-neutral-900 p-4">
                {slides[currentSlideIndex] && (
                    <div className="relative w-full h-full flex items-center justify-center">
                        <div className="relative max-w-full max-h-full">
                            <Image
                                src={slides[currentSlideIndex].image_url}
                                alt={`Slide ${currentSlideIndex + 1}`}
                                width={1200}
                                height={800}
                                className="object-contain shadow-2xl"
                                unoptimized
                                priority
                            />
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
