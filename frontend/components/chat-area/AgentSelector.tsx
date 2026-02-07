"use client";

import { useState, useEffect } from 'react';
import { Agent, getAgents } from '@/lib/api/chat';
import * as SelectPrimitive from "@radix-ui/react-select";

import {
    Select,
    SelectContent,
    SelectItem,
    SelectValue,
} from "@/components/ui/select";
import { Bot } from 'lucide-react';

interface AgentSelectorProps {
    selectedAgent: string | null;
    onAgentChange: (agent: string | null) => void;
}

export function AgentSelector({ selectedAgent, onAgentChange }: AgentSelectorProps) {
    const [agents, setAgents] = useState<Agent[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const loadAgents = async () => {
            try {
                const data = await getAgents();
                setAgents(data);
            } catch (error) {
                console.error('Failed to load agents:', error);
            } finally {
                setLoading(false);
            }
        };
        loadAgents();
    }, []);

    if (loading) {
        return null;
    }

    return (
        <Select value={selectedAgent || 'auto'} onValueChange={(value) => onAgentChange(value === 'auto' ? null : value)}>
            <SelectPrimitive.Trigger className="inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 h-9 w-9 p-0 border-none shadow-none bg-transparent text-muted-foreground hover:text-foreground hover:bg-accent/50">
                <Bot className="h-4 w-4" />
                <span className="sr-only">
                    <SelectValue />
                </span>
            </SelectPrimitive.Trigger>
            <SelectContent>
                <SelectItem value="auto">
                    <div className="flex flex-col">
                        <span className="font-medium">Orchestrator (Auto)</span>
                        <span className="text-xs text-muted-foreground">Routes to best agent</span>
                    </div>
                </SelectItem>
                {agents.map((agent) => (
                    <SelectItem key={agent.name} value={agent.name}>
                        <div className="flex flex-col">
                            <span className="font-medium">{agent.name.replace(/_/g, ' ')}</span>
                            <span className="text-xs text-muted-foreground">{agent.description}</span>
                        </div>
                    </SelectItem>
                ))}
            </SelectContent>
        </Select>
    );
}
