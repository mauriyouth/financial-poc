"use client";

import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Database, Check, ChevronDown } from 'lucide-react';
import { Checkbox } from '@/components/ui/checkbox';
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

interface DataSourceSelectorProps {
    value: DataSource;
    onChange: (source: DataSource) => void;
    className?: string;
}

export function DataSourceSelector({ value, onChange, className }: DataSourceSelectorProps) {
    const [open, setOpen] = useState(false);
    const [selectedSources, setSelectedSources] = useState<Set<DataSource>>(new Set([value]));

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
        onChange(Array.from(newSelected)[0]);
    };

    const getLabel = () => {
        const count = selectedSources.size;
        if (count === 1) {
            return DATA_SOURCES.find(s => s.value === value)?.label || 'Data Source';
        }
        return `${count} Sources`;
    };

    return (
        <Popover open={open} onOpenChange={setOpen}>
            <PopoverTrigger asChild>
                <Button
                    variant="ghost"
                    className={cn("h-9 px-3 text-muted-foreground hover:text-foreground rounded-lg gap-1.5", className)}
                >
                    <span className="text-xs text-muted-foreground">{getLabel()}</span>
                    <ChevronDown className="h-3 w-3" />
                </Button>
            </PopoverTrigger>
            <PopoverContent className="w-64 p-2" align="start">
                <div className="flex flex-col gap-1">
                    <div className="px-2 py-1.5 text-xs font-semibold text-muted-foreground">
                        Data Sources (Multi-select)
                    </div>
                    {DATA_SOURCES.map(source => (
                        <label
                            key={source.value}
                            className="flex items-start gap-2 px-2 py-2 rounded hover:bg-accent cursor-pointer"
                        >
                            <Checkbox
                                checked={selectedSources.has(source.value)}
                                onCheckedChange={() => handleToggle(source.value)}
                                className="mt-0.5"
                            />
                            <div className="flex-1 min-w-0">
                                <div className="text-sm font-medium">{source.label}</div>
                                <div className="text-xs text-muted-foreground">{source.description}</div>
                            </div>
                        </label>
                    ))}
                </div>
            </PopoverContent>
        </Popover>
    );
}
