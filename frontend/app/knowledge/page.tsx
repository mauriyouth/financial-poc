"use client";

import { useEffect, useState } from 'react';
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogTrigger
} from "@/components/ui/dialog";
import {
    getDocuments,
    uploadDocument,
    DocumentMetadata
} from '@/lib/api/documents';
import { Plus, FileText, Search, Loader2 } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Label } from '@/components/ui/label';
import { DocumentPreview } from '@/components/document-preview';
import { ResizableHandle, ResizablePanel, ResizablePanelGroup } from '@/components/ui/resizable';

export default function KnowledgeBasePage() {
    // const router = useRouter();  // Future feature
    const [documents, setDocuments] = useState<DocumentMetadata[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState("");
    const [uploading, setUploading] = useState(false);
    const [uploadOpen, setUploadOpen] = useState(false);
    const [previewDocuments, setPreviewDocuments] = useState<DocumentMetadata[]>([]);
    const [activePreviewId, setActivePreviewId] = useState<string | null>(null);
    const [isPreviewFullscreen, setIsPreviewFullscreen] = useState(false);

    useEffect(() => {
        loadDocuments();
    }, []);

    const loadDocuments = async () => {
        try {
            setLoading(true);
            const data = await getDocuments();
            setDocuments(data);
        } catch (error) {
            console.error("Failed to load documents", error);
        } finally {
            setLoading(false);
        }
    };

    const handleUpload = async (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        const formData = new FormData(e.currentTarget);
        const file = formData.get('file') as File;

        if (!file) return;

        try {
            setUploading(true);
            await uploadDocument(file);
            setUploadOpen(false);
            loadDocuments(); // Reload list
        } catch (error) {
            console.error("Failed to upload", error);
        } finally {
            setUploading(false);
        }
    };

    const filteredDocs = documents.filter(doc =>
        doc.filename.toLowerCase().includes(searchTerm.toLowerCase())
    );

    const handleDocumentClick = (doc: DocumentMetadata) => {
        setPreviewDocuments(prev => {
            const exists = prev.find(d => d.id === doc.id);
            return exists ? prev : [...prev, doc];
        });
        setActivePreviewId(doc.id);
    };

    const handleCloseDocument = (id: string) => {
        setPreviewDocuments(prev => {
            const newDocs = prev.filter(d => d.id !== id);
            if (activePreviewId === id) {
                if (newDocs.length > 0) {
                    setActivePreviewId(newDocs[newDocs.length - 1].id);
                } else {
                    setActivePreviewId(null);
                }
            }
            return newDocs;
        });
    };

    const handleCloseAll = () => {
        setPreviewDocuments([]);
        setActivePreviewId(null);
        setIsPreviewFullscreen(false);
    };

    const handleToggleFullscreen = () => {
        setIsPreviewFullscreen(prev => !prev);
    };

    return (
        <div className="flex h-full w-full overflow-hidden">
            {previewDocuments.length > 0 ? (
                <ResizablePanelGroup orientation="horizontal" className="h-full w-full flex">
                    <ResizablePanel defaultSize={isPreviewFullscreen ? 0 : 70} minSize={isPreviewFullscreen ? 0 : 30} maxSize={isPreviewFullscreen ? 0 : 80} collapsible={true}>
                        <div className="container mx-auto py-10 space-y-8 animate-in fade-in duration-500 h-full overflow-auto">
                            <div className="flex justify-between items-center">
                                <div>
                                    <h1 className="text-3xl font-bold tracking-tight">Knowledge Base</h1>
                                    <p className="text-muted-foreground">Manage your documents and data sources.</p>
                                </div>
                                <Dialog open={uploadOpen} onOpenChange={setUploadOpen}>
                                    <DialogTrigger asChild>
                                        <Button className="gap-2">
                                            <Plus className="h-4 w-4" />
                                            Upload Document
                                        </Button>
                                    </DialogTrigger>
                                    <DialogContent>
                                        <DialogHeader>
                                            <DialogTitle>Upload Document</DialogTitle>
                                        </DialogHeader>
                                        <form onSubmit={handleUpload} className="space-y-4">
                                            <div className="space-y-2">
                                                <Label htmlFor="file">File</Label>
                                                <Input id="file" name="file" type="file" required />
                                            </div>
                                            <Button type="submit" disabled={uploading} className="w-full">
                                                {uploading ? <Loader2 className="h-4 w-4 animate-spin" /> : "Upload"}
                                            </Button>
                                        </form>
                                    </DialogContent>
                                </Dialog>
                            </div>

                            <div className="flex items-center space-x-2 bg-muted/30 p-2 rounded-lg border">
                                <Search className="h-4 w-4 text-muted-foreground ml-2" />
                                <Input
                                    placeholder="Search documents..."
                                    value={searchTerm}
                                    onChange={(e) => setSearchTerm(e.target.value)}
                                    className="border-0 bg-transparent focus-visible:ring-0 focus-visible:ring-offset-0"
                                />
                            </div>

                            <div className="border rounded-lg bg-card">
                                <Table>
                                    <TableHeader>
                                        <TableRow>
                                            <TableHead>No.</TableHead>
                                            <TableHead>Filename</TableHead>
                                            <TableHead>Status</TableHead>
                                            <TableHead>Upload Date</TableHead>
                                            <TableHead className="text-right">Actions</TableHead>
                                        </TableRow>
                                    </TableHeader>
                                    <TableBody>
                                        {loading ? (
                                            <TableRow>
                                                <TableCell colSpan={5} className="h-24 text-center">
                                                    <Loader2 className="h-6 w-6 animate-spin mx-auto text-muted-foreground" />
                                                </TableCell>
                                            </TableRow>
                                        ) : filteredDocs.length === 0 ? (
                                            <TableRow>
                                                <TableCell colSpan={5} className="h-24 text-center text-muted-foreground">
                                                    No documents found. Upload one to get started.
                                                </TableCell>
                                            </TableRow>
                                        ) : (
                                            filteredDocs.map((doc, index) => (
                                                <TableRow key={doc.id} className="group cursor-pointer hover:bg-muted/50" onClick={() => handleDocumentClick(doc)}>
                                                    <TableCell className="font-mono text-xs text-muted-foreground">
                                                        {(index + 1).toString().padStart(2, '0')}
                                                    </TableCell>
                                                    <TableCell>
                                                        <div className="flex items-center gap-2 font-medium">
                                                            <FileText className="h-4 w-4 text-blue-500" />
                                                            {doc.filename}
                                                        </div>
                                                    </TableCell>
                                                    <TableCell>
                                                        <Badge variant="outline" className={`
                                                            ${doc.status === 'completed' ? 'border-green-500 text-green-500' : ''}
                                                            ${doc.status === 'processing' ? 'border-blue-500 text-blue-500' : ''}
                                                            ${doc.status === 'failed' ? 'border-red-500 text-red-500' : ''}
                                                            capitalize
                                                        `}>
                                                            {doc.status}
                                                        </Badge>
                                                    </TableCell>
                                                    <TableCell className="text-muted-foreground text-sm">
                                                        {new Date(doc.upload_date).toLocaleDateString()}
                                                    </TableCell>
                                                    <TableCell className="text-right">
                                                        <Button variant="ghost" size="sm" onClick={(e) => { e.stopPropagation(); handleDocumentClick(doc); }}>
                                                            View
                                                        </Button>
                                                    </TableCell>
                                                </TableRow>
                                            ))
                                        )}
                                    </TableBody>
                                </Table>
                            </div>
                        </div>
                    </ResizablePanel>
                    <ResizableHandle withHandle className="w-1.5 hover:bg-secondary/50 transition-colors" style={{ display: isPreviewFullscreen ? 'none' : 'block' }} />
                    <ResizablePanel defaultSize={isPreviewFullscreen ? 100 : 30} minSize={isPreviewFullscreen ? 100 : 25} maxSize={isPreviewFullscreen ? 100 : 70}>
                        <DocumentPreview
                            documents={previewDocuments}
                            activeId={activePreviewId || undefined}
                            onActiveChange={setActivePreviewId}
                            onClose={handleCloseAll}
                            onCloseDocument={handleCloseDocument}
                            isFullscreen={isPreviewFullscreen}
                            onToggleFullscreen={handleToggleFullscreen}
                        />
                    </ResizablePanel>
                </ResizablePanelGroup>
            ) : (
                <div className="container mx-auto py-10 space-y-8 animate-in fade-in duration-500">
                    <div className="flex justify-between items-center">
                        <div>
                            <h1 className="text-3xl font-bold tracking-tight">Knowledge Base</h1>
                            <p className="text-muted-foreground">Manage your documents and data sources.</p>
                        </div>
                        <Dialog open={uploadOpen} onOpenChange={setUploadOpen}>
                            <DialogTrigger asChild>
                                <Button className="gap-2">
                                    <Plus className="h-4 w-4" />
                                    Upload Document
                                </Button>
                            </DialogTrigger>
                            <DialogContent>
                                <DialogHeader>
                                    <DialogTitle>Upload Document</DialogTitle>
                                </DialogHeader>
                                <form onSubmit={handleUpload} className="space-y-4">
                                    <div className="space-y-2">
                                        <Label htmlFor="file">File</Label>
                                        <Input id="file" name="file" type="file" required />
                                    </div>
                                    <Button type="submit" disabled={uploading} className="w-full">
                                        {uploading ? <Loader2 className="h-4 w-4 animate-spin" /> : "Upload"}
                                    </Button>
                                </form>
                            </DialogContent>
                        </Dialog>
                    </div>

                    <div className="flex items-center space-x-2 bg-muted/30 p-2 rounded-lg border">
                        <Search className="h-4 w-4 text-muted-foreground ml-2" />
                        <Input
                            placeholder="Search documents..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            className="border-0 bg-transparent focus-visible:ring-0 focus-visible:ring-offset-0"
                        />
                    </div>

                    <div className="border rounded-lg bg-card">
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead>No.</TableHead>
                                    <TableHead>Filename</TableHead>
                                    <TableHead>Status</TableHead>
                                    <TableHead>Upload Date</TableHead>
                                    <TableHead className="text-right">Actions</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {loading ? (
                                    <TableRow>
                                        <TableCell colSpan={5} className="h-24 text-center">
                                            <Loader2 className="h-6 w-6 animate-spin mx-auto text-muted-foreground" />
                                        </TableCell>
                                    </TableRow>
                                ) : filteredDocs.length === 0 ? (
                                    <TableRow>
                                        <TableCell colSpan={5} className="h-24 text-center text-muted-foreground">
                                            No documents found. Upload one to get started.
                                        </TableCell>
                                    </TableRow>
                                ) : (
                                    filteredDocs.map((doc, index) => (
                                        <TableRow key={doc.id} className="group cursor-pointer hover:bg-muted/50" onClick={() => handleDocumentClick(doc)}>
                                            <TableCell className="font-mono text-xs text-muted-foreground">
                                                {(index + 1).toString().padStart(2, '0')}
                                            </TableCell>
                                            <TableCell>
                                                <div className="flex items-center gap-2 font-medium">
                                                    <FileText className="h-4 w-4 text-blue-500" />
                                                    {doc.filename}
                                                </div>
                                            </TableCell>
                                            <TableCell>
                                                <Badge variant="outline" className={`
                                                    ${doc.status === 'completed' ? 'border-green-500 text-green-500' : ''}
                                                    ${doc.status === 'processing' ? 'border-blue-500 text-blue-500' : ''}
                                                    ${doc.status === 'failed' ? 'border-red-500 text-red-500' : ''}
                                                    capitalize
                                                `}>
                                                    {doc.status}
                                                </Badge>
                                            </TableCell>
                                            <TableCell className="text-muted-foreground text-sm">
                                                {new Date(doc.upload_date).toLocaleDateString()}
                                            </TableCell>
                                            <TableCell className="text-right">
                                                <Button variant="ghost" size="sm" onClick={(e) => { e.stopPropagation(); handleDocumentClick(doc); }}>
                                                    View
                                                </Button>
                                            </TableCell>
                                        </TableRow>
                                    ))
                                )}
                            </TableBody>
                        </Table>
                    </div>
                </div>
            )}
        </div>
    );
}
