"use client";

import React, { useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Check, ChevronUp } from "lucide-react";
import { cn } from "@/lib/utils";
import { getModels, Model } from '@/lib/api/chat';

interface ModelSelectorProps {
    value?: string;
    onChange: (model: string) => void;
    className?: string;
}

const DEFAULT_MODELS = [
    { id: 'anthropic', name: 'Claude 3.5 Sonnet' },
    { id: 'google', name: 'Gemini 1.5 Pro' }
];

export function ModelSelector({ value, onChange, className }: ModelSelectorProps) {
    const [models, setModels] = useState<Model[]>(DEFAULT_MODELS);
    const [open, setOpen] = useState(false);

    useEffect(() => {
        getModels()
            .then(data => {
                setModels(data.length > 0 ? data : DEFAULT_MODELS);
            })
            .catch(error => {
                console.error('Failed to fetch models:', error);
                setModels(DEFAULT_MODELS);
            });
    }, []);

    return (
        <Popover open={open} onOpenChange={setOpen}>
            <PopoverTrigger asChild>
                <Button
                    variant="ghost"
                    className={cn("h-9 px-3 text-muted-foreground hover:text-foreground rounded-lg gap-1.5", className)}
                >
                    <span className="text-xs text-muted-foreground">
                        {models.find(m => m.id === value)?.name || 'Select Model'}
                    </span>
                    <ChevronUp className="h-3 w-3" />
                </Button>
            </PopoverTrigger>
            <PopoverContent className="w-56 p-2" align="end">
                <div className="flex flex-col gap-1">
                    <div className="px-2 py-1.5 text-xs font-semibold text-muted-foreground">
                        Select AI Model
                    </div>
                    {models.map(model => (
                        <button
                            key={model.id}
                            onClick={() => {
                                onChange(model.id);
                                setOpen(false);
                            }}
                            className={cn(
                                "flex items-center gap-2 px-2 py-1.5 text-sm rounded hover:bg-accent text-left",
                                value === model.id && "bg-accent"
                            )}
                        >
                            <Check className={cn(
                                "h-4 w-4",
                                value === model.id ? "opacity-100" : "opacity-0"
                            )} />
                            <span className="flex-1">{model.name}</span>
                        </button>
                    ))}
                </div>
            </PopoverContent>
        </Popover>
    );
}
