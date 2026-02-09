"use client";

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Plus, UploadCloud } from 'lucide-react';
import { useDropzone } from 'react-dropzone';
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Input } from '@/components/ui/input';
import { Checkbox } from '@/components/ui/checkbox';
import { Separator } from '@/components/ui/separator';
import { cn } from '@/lib/utils';

export type DataSource = 'web' | 'knowledge' | 'uploaded';

interface DataSourceOption {
    value: DataSource;
    label: string;
    description: string;
}

const DATA_SOURCES: DataSourceOption[] = [
    { value: 'web', label: 'Web Search', description: 'Search the internet' },
    { value: 'knowledge', label: 'Knowledge Base', description: 'Use uploaded documents' },
    { value: 'uploaded', label: 'Uploads Only', description: 'Current session files' }
];

interface FileUploadButtonProps {
    onFilesSelected: (files: File[]) => void;
    disabled?: boolean;
    // Data source props
    showDataSourceSelector?: boolean;
    dataSource?: DataSource;
    onDataSourceChange?: (source: DataSource) => void;
}

export function FileUploadButton({
    onFilesSelected,
    disabled = false,
    showDataSourceSelector = false,
    dataSource = 'knowledge',
    onDataSourceChange
}: FileUploadButtonProps) {
    const [uploadOpen, setUploadOpen] = useState(false);
    const [selectedSources, setSelectedSources] = useState<Set<DataSource>>(new Set([dataSource]));

    const onDrop = (acceptedFiles: File[]) => {
        if (acceptedFiles.length > 0) {
            onFilesSelected(acceptedFiles);
            setUploadOpen(false);
        }
    };

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        noClick: false,
        noKeyboard: true
    });

    const handleToggle = (source: DataSource) => {
        const newSelected = new Set(selectedSources);
        if (newSelected.has(source)) {
            newSelected.delete(source);
        } else {
            newSelected.add(source);
        }

        // Ensure at least one is selected
        if (newSelected.size === 0) {
            newSelected.add(source);
        }

        setSelectedSources(newSelected);
        // Set the first selected as primary
        if (onDataSourceChange) {
            onDataSourceChange(Array.from(newSelected)[0]);
        }
    };

    return (
        <Popover open={uploadOpen} onOpenChange={setUploadOpen}>
            <PopoverTrigger asChild>
                <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8 ml-1 text-muted-foreground hover:text-foreground rounded-full hover:bg-accent/50"
                    disabled={disabled}
                    title="Add files and sources"
                >
                    <Plus className="h-4 w-4" />
                </Button>
            </PopoverTrigger>
            <PopoverContent className="w-[280px] p-0" side="top" align="start">
                {/* Upload Document Section */}
                <div className="p-3 space-y-2">
                    <div className="space-y-0.5">
                        <h4 className="font-medium text-sm">Upload Document</h4>
                        <p className="text-[11px] text-muted-foreground">Drag & drop or click to browse</p>
                    </div>
                    <div
                        {...getRootProps()}
                        className={cn(
                            "border-2 border-dashed rounded-lg p-4 text-center cursor-pointer transition-colors hover:bg-accent/50",
                            isDragActive ? "border-primary bg-accent" : "border-muted-foreground/25"
                        )}
                    >
                        <Input {...getInputProps()} className="hidden" />
                        <div className="flex flex-col items-center gap-1.5">
                            <UploadCloud className="h-6 w-6 text-muted-foreground" />
                            <p className="text-xs font-medium text-muted-foreground">
                                {isDragActive ? "Drop here" : "Click or drag"}
                            </p>
                        </div>
                    </div>
                    <p className="text-[10px] text-center text-muted-foreground/70">
                        PDF, Images, Excel, Word, PPT
                    </p>
                </div>

                {/* Separator Line */}
                {showDataSourceSelector && onDataSourceChange && (
                    <>
                        <Separator className="my-0" />

                        {/* Data Sources Section */}
                        <div className="p-3 space-y-1.5">
                            <div className="space-y-0.5">
                                <h4 className="font-medium text-sm">Data Sources</h4>
                                <p className="text-[11px] text-muted-foreground">Multi-select sources</p>
                            </div>
                            <div className="flex flex-col gap-0.5 pt-1">
                                {DATA_SOURCES.map(source => (
                                    <label
                                        key={source.value}
                                        className="flex items-start gap-2 px-1.5 py-1.5 rounded-md hover:bg-accent cursor-pointer transition-colors"
                                    >
                                        <Checkbox
                                            checked={selectedSources.has(source.value)}
                                            onCheckedChange={() => handleToggle(source.value)}
                                            className="mt-0.5"
                                        />
                                        <div className="flex-1 min-w-0">
                                            <div className="text-xs font-medium leading-tight">{source.label}</div>
                                            <div className="text-[11px] text-muted-foreground leading-tight">{source.description}</div>
                                        </div>
                                    </label>
                                ))}
                            </div>
                        </div>
                    </>
                )}
            </PopoverContent>
        </Popover>
    );
}
