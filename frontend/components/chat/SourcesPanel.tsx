"use client";

import { useEffect, useState, useCallback } from "react";
import { getWsBaseUrl } from "@/lib/config";
import { DocumentMetadata, getDocuments, deleteDocument } from "@/lib/api/documents";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2, CheckCircle2, AlertCircle, FileText, Info, Trash2 } from "lucide-react";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { Checkbox } from "@/components/ui/checkbox";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface SourcesPanelProps {
    onDocumentClick?: (doc: DocumentMetadata) => void;
    activeId?: string;
}

export function SourcesPanel({ onDocumentClick, activeId }: SourcesPanelProps) {
    const [documents, setDocuments] = useState<DocumentMetadata[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

    const fetchDocuments = useCallback(async () => {
        try {
            const docs = await getDocuments(activeId);
            // Sort by creation date desc
            docs.sort((a, b) => new Date(b.upload_date).getTime() - new Date(a.upload_date).getTime());
            setDocuments(docs);
        } catch (error) {
            console.error("Failed to fetch documents", error);
        } finally {
            setIsLoading(false);
        }
    }, [activeId]);

    const handleDelete = async (e: React.MouseEvent, id: string) => {
        e.stopPropagation();
        if (!confirm("Are you sure you want to delete this document?")) return;

        try {
            await deleteDocument(id);
            // Remove from local state immediately for responsiveness
            setDocuments(prev => prev.filter(d => d.id !== id));
            setSelectedIds(prev => {
                const next = new Set(prev);
                next.delete(id);
                return next;
            });
            // Trigger fetch to sync
            fetchDocuments();
        } catch (error) {
            console.error("Failed to delete document", error);
            alert("Failed to delete document");
        }
    };

    const handleBulkDelete = async () => {
        if (selectedIds.size === 0) return;
        if (!confirm(`Are you sure you want to delete ${selectedIds.size} documents?`)) return;

        try {
            await Promise.all(Array.from(selectedIds).map(id => deleteDocument(id)));
            setDocuments(prev => prev.filter(d => !selectedIds.has(d.id)));
            setSelectedIds(new Set());
            fetchDocuments();
        } catch (error) {
            console.error("Failed to delete documents", error);
            alert("Failed to delete selected documents");
        }
    };

    const toggleSelectAll = () => {
        if (selectedIds.size === documents.length && documents.length > 0) {
            setSelectedIds(new Set());
        } else {
            setSelectedIds(new Set(documents.map(d => d.id)));
        }
    };

    const toggleSelect = (id: string) => {
        setSelectedIds(prev => {
            const next = new Set(prev);
            if (next.has(id)) {
                next.delete(id);
            } else {
                next.add(id);
            }
            return next;
        });
    };

    useEffect(() => {
        fetchDocuments();

        // Connect to WebSocket for real-time updates
        let ws: WebSocket | null = null;
        try {
            // Dynamically import to avoid SSR issues if any, though "use client" handles it
            ws = new WebSocket(`${getWsBaseUrl()}/ws`);

            ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    if (data.type === 'document_status') {
                        setDocuments(prev => prev.map(doc => {
                            if (doc.id === data.document_id) {
                                return {
                                    ...doc,
                                    status: data.status,
                                    metadata: { ...doc.metadata, ...data.metadata }
                                };
                            }
                            return doc;
                        }));
                    }
                } catch (e) {
                    console.error("WS parse error", e);
                }
            };
        } catch (e) {
            console.error("WS connection error", e);
        }

        return () => {
            if (ws) ws.close();
        };
    }, [fetchDocuments]);

    const getStatusIcon = (status: string) => {
        switch (status) {
            case "processing":
            case "pending":
            case "queued":
                return <Loader2 className="h-4 w-4 animate-spin text-blue-500" />;
            case "completed":
                return <CheckCircle2 className="h-4 w-4 text-green-500" />;
            case "failed":
                return <AlertCircle className="h-4 w-4 text-red-500" />;
            default:
                return <FileText className="h-4 w-4 text-muted-foreground" />;
        }
    };

    const isAllSelected = documents.length > 0 && selectedIds.size === documents.length;

    return (
        <Card className="h-full border-l rounded-none border-y-0 border-r-0 bg-background/50 backdrop-blur-sm">
            <CardHeader className="py-4 px-4 border-b">
                <div className="flex items-center justify-between">
                    <CardTitle className="text-sm font-medium flex items-center gap-2">
                        <FileText className="h-4 w-4" />
                        Sources ({documents.length})
                    </CardTitle>
                    {selectedIds.size > 0 && (
                        <Button
                            variant="destructive"
                            size="sm"
                            className="h-6 px-2 text-xs"
                            onClick={handleBulkDelete}
                        >
                            Delete ({selectedIds.size})
                        </Button>
                    )}
                </div>
                <div className="flex items-center gap-2 mt-2">
                    <Checkbox
                        id="select-all"
                        checked={isAllSelected}
                        onCheckedChange={toggleSelectAll}
                        disabled={documents.length === 0}
                    />
                    <label
                        htmlFor="select-all"
                        className="text-xs text-muted-foreground cursor-pointer select-none"
                    >
                        Select all
                    </label>
                </div>
            </CardHeader>
            <ScrollArea className="h-[calc(100%-100px)]">
                <CardContent className="p-0">
                    {isLoading && documents.length === 0 ? (
                        <div className="flex items-center justify-center p-8 text-muted-foreground">
                            <Loader2 className="h-6 w-6 animate-spin" />
                        </div>
                    ) : documents.length === 0 ? (
                        <div className="p-8 text-center text-sm text-muted-foreground">
                            No documents uploaded yet.
                        </div>
                    ) : (
                        <div className="divide-y">
                            {documents.map((doc) => (
                                <div
                                    key={doc.id}
                                    className={cn(
                                        "p-3 hover:bg-accent/50 cursor-pointer transition-colors group flex items-start gap-3",
                                        activeId === doc.id && "bg-accent",
                                        selectedIds.has(doc.id) && "bg-accent/30"
                                    )}
                                    onClick={() => onDocumentClick?.(doc)}
                                >
                                    <div className="mt-0.5" onClick={(e) => e.stopPropagation()}>
                                        <Checkbox
                                            checked={selectedIds.has(doc.id)}
                                            onCheckedChange={() => toggleSelect(doc.id)}
                                        />
                                    </div>
                                    <div className="mt-0.5">
                                        {getStatusIcon(doc.status)}
                                    </div>
                                    <div className="flex-1 min-w-0 space-y-1">
                                        <div className="flex items-start justify-between gap-2">
                                            <p className="text-sm font-medium truncate leading-none">
                                                {doc.filename}
                                            </p>
                                            <button
                                                onClick={(e) => handleDelete(e, doc.id)}
                                                className="opacity-0 group-hover:opacity-100 p-1 hover:bg-destructive/10 text-muted-foreground hover:text-destructive rounded transition-all -mt-1 -mr-1"
                                                title="Delete document"
                                            >
                                                <Trash2 className="h-3.5 w-3.5" />
                                            </button>
                                        </div>
                                        <div className="flex items-center gap-2 text-xs text-muted-foreground">
                                            <span>{new Date(doc.upload_date).toLocaleDateString()}</span>
                                            {doc.metadata?.chunk_count && (
                                                <>
                                                    <span>•</span>
                                                    <span>{doc.metadata.chunk_count} chunks</span>
                                                </>
                                            )}
                                        </div>

                                        {/* Summary Preview / Tooltip */}
                                        {doc.metadata?.summary && (
                                            <TooltipProvider>
                                                <Tooltip delayDuration={300}>
                                                    <TooltipTrigger asChild>
                                                        <div className="flex items-start gap-1 mt-1.5 p-1.5 rounded bg-muted/40 text-[10px] text-muted-foreground hover:bg-muted/60 transition-colors">
                                                            <Info className="h-3 w-3 mt-0.5 shrink-0" />
                                                            <p className="line-clamp-2 leading-relaxed">
                                                                {doc.metadata.summary}
                                                            </p>
                                                        </div>
                                                    </TooltipTrigger>
                                                    <TooltipContent side="left" className="max-w-[300px] p-4 text-xs">
                                                        <p className="font-semibold mb-1">Summary</p>
                                                        <p>{doc.metadata.summary}</p>
                                                    </TooltipContent>
                                                </Tooltip>
                                            </TooltipProvider>
                                        )}

                                        {doc.status === 'processing' && (
                                            <p className="text-[10px] text-blue-500 mt-1 animate-pulse">
                                                Generating summary & embedding...
                                            </p>
                                        )}
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </CardContent>
            </ScrollArea>
        </Card>
    );
}
