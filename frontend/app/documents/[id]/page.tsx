'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import {
    ResizableHandle,
    ResizablePanel,
    ResizablePanelGroup
} from "@/components/ui/resizable";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import { getDocument, getDocumentContent, DocumentMetadata } from '@/lib/api/documents';
import { Loader2, FileText, Code, Braces } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

export default function DocumentViewer() {
    const { id } = useParams() as { id: string };
    const [doc, setDoc] = useState<DocumentMetadata | null>(null);
    const [loading, setLoading] = useState(true);

    const [contentMarkdown, setContentMarkdown] = useState<string>('');
    const [contentHtml, setContentHtml] = useState<string>('');
    const [contentJson, setContentJson] = useState<string>('');

    const extractString = (data: DocumentMetadata | string | { content: string } | any): string => {
        if (typeof data === 'string') return data;
        if (data && typeof data === 'object' && 'content' in data) return data.content;
        return '';
    };

    useEffect(() => {
        const fetchData = async () => {
            try {
                const docData = await getDocument(id);
                setDoc(docData);

                // Fetch mock content parallel
                const [mk, ht, js] = await Promise.all([
                    getDocumentContent(id, 'markdown'),
                    getDocumentContent(id, 'html'),
                    getDocumentContent(id, 'json')
                ]);

                setContentMarkdown(extractString(mk));
                setContentHtml(extractString(ht));
                setContentJson(JSON.stringify(js, null, 2));

            } catch (error) {
                console.error("Failed to fetch document", error);
            } finally {
                setLoading(false);
            }
        };

        if (id) fetchData();
    }, [id]);

    if (loading) {
        return (
            <div className="h-screen w-screen flex items-center justify-center bg-neutral-950 text-neutral-400">
                <Loader2 className="h-10 w-10 animate-spin" />
            </div>
        );
    }

    if (!doc) return <div className="p-10 text-white">Document not found</div>;

    return (
        <div className="h-screen flex flex-col bg-neutral-950 text-neutral-200 overflow-hidden font-sans">
            {/* Header */}
            <div className="h-14 border-b border-neutral-800 flex items-center px-6 justify-between shrink-0 bg-neutral-900/50">
                <div className="flex items-center gap-3">
                    <div className="bg-blue-500/10 p-2 rounded-md">
                        <FileText className="h-5 w-5 text-blue-400" />
                    </div>
                    <span className="font-semibold text-lg">{doc.filename}</span>
                    <Badge variant="outline" className="ml-2 border-neutral-700 text-neutral-400">
                        {doc.status}
                    </Badge>
                </div>
                <div className="text-sm text-neutral-500 font-mono">
                    ID: {doc.id.substring(0, 8)}
                </div>
            </div>

            {/* Main Split View */}
            <ResizablePanelGroup orientation="horizontal" className="flex-1 flex h-full w-full data-[panel-group-direction=vertical]:flex-col">

                {/* Left Panel: Original Document (Preview) */}
                <ResizablePanel defaultSize="40" minSize="20" className="bg-neutral-900/30">
                    <div className="h-full flex flex-col">
                        <div className="p-3 border-b border-neutral-800 text-xs font-semibold text-neutral-500 uppercase tracking-wider flex justify-between items-center">
                            <span>Original Document</span>
                            {/* Visual placeholder for zoom controls */}
                            <div className="flex gap-1">
                                <div className="px-2 py-0.5 bg-neutral-800 rounded text-neutral-400 hover:text-white cursor-pointer transition-colors">-</div>
                                <div className="px-2 py-0.5 bg-neutral-800 rounded text-neutral-400 hover:text-white cursor-pointer transition-colors">+</div>
                            </div>
                        </div>
                        <div className="flex-1 flex items-center justify-center bg-neutral-950 relative">
                            {/* 
                  Real PDF rendering would go here (e.g., using iframe or react-pdf).
                  For now, a placeholder.
               */}
                            <div className="text-center space-y-4">
                                <div className="inline-flex items-center justify-center w-20 h-28 border-2 border-dashed border-neutral-700 rounded bg-neutral-900">
                                    <FileText className="text-neutral-600 h-8 w-8" />
                                </div>
                                <p className="text-neutral-500 text-sm">Document Preview Placeholder</p>
                                <p className="text-xs text-neutral-600 max-w-[200px] mx-auto">
                                    (In a real implementation, the PDF/Image from MinIO would be rendered here)
                                </p>
                            </div>
                        </div>
                    </div>
                </ResizablePanel>

                <ResizableHandle withHandle className="bg-neutral-800 hover:bg-blue-500 transition-colors" />

                {/* Right Panel: Analyzed Content */}
                <ResizablePanel defaultSize="60" minSize="30" className="bg-neutral-950">
                    <Tabs defaultValue="html" className="h-full flex flex-col">
                        <div className="border-b border-neutral-800 px-4 bg-neutral-900/50">
                            <TabsList className="h-12 bg-transparent p-0 gap-6">
                                <TabsTrigger value="markdown" className="data-[state=active]:bg-transparent data-[state=active]:text-blue-400 data-[state=active]:shadow-none rounded-none h-12 border-b-2 border-transparent data-[state=active]:border-blue-500 px-0 transition-all text-neutral-500 hover:text-neutral-300">
                                    <div className="flex items-center gap-2">
                                        <FileText className="w-4 h-4" />
                                        <span className="font-medium">Markdown</span>
                                    </div>
                                </TabsTrigger>
                                <TabsTrigger value="html" className="data-[state=active]:bg-transparent data-[state=active]:text-orange-400 data-[state=active]:shadow-none rounded-none h-12 border-b-2 border-transparent data-[state=active]:border-orange-500 px-0 transition-all text-neutral-500 hover:text-neutral-300">
                                    <div className="flex items-center gap-2">
                                        <Code className="w-4 h-4" />
                                        <span className="font-medium">HTML</span>
                                    </div>
                                </TabsTrigger>
                                <TabsTrigger value="json" className="data-[state=active]:bg-transparent data-[state=active]:text-green-400 data-[state=active]:shadow-none rounded-none h-12 border-b-2 border-transparent data-[state=active]:border-green-500 px-0 transition-all text-neutral-500 hover:text-neutral-300">
                                    <div className="flex items-center gap-2">
                                        <Braces className="w-4 h-4" />
                                        <span className="font-medium">JSON Data</span>
                                    </div>
                                </TabsTrigger>
                            </TabsList>
                        </div>
                        <div className="flex-1 overflow-hidden relative group">
                            {/* Markdown View */}
                            <TabsContent value="markdown" className="h-full m-0 p-0 border-0 outline-none">
                                <ScrollArea className="h-full w-full">
                                    <div className="p-6 max-w-3xl mx-auto prose prose-invert prose-blue">
                                        <pre className="whitespace-pre-wrap font-mono text-sm text-neutral-300 bg-transparent p-0">
                                            {contentMarkdown}
                                        </pre>
                                    </div>
                                </ScrollArea>
                            </TabsContent>

                            {/* HTML View (Rendered) */}
                            <TabsContent value="html" className="h-full m-0 p-0 border-0 outline-none bg-white text-black">
                                <iframe
                                    srcDoc={contentHtml}
                                    className="w-full h-full border-none"
                                    sandbox="allow-scripts"
                                />
                            </TabsContent>

                            {/* JSON View */}
                            <TabsContent value="json" className="h-full m-0 p-0 border-0 outline-none">
                                <ScrollArea className="h-full w-full">
                                    <div className="p-4">
                                        <pre className="font-mono text-xs text-green-300 bg-neutral-900/50 p-4 rounded-lg border border-neutral-800 overflow-x-auto">
                                            {contentJson}
                                        </pre>
                                    </div>
                                </ScrollArea>
                            </TabsContent>
                        </div>
                    </Tabs>
                </ResizablePanel>

            </ResizablePanelGroup>
        </div>
    );
}
