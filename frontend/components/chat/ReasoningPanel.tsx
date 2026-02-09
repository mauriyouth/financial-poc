"use client";

import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown, ChevronUp } from "lucide-react";
import { useState } from "react";

import { StreamEvent } from "@/lib/api/chat";

interface ReasoningPanelProps {
    events: StreamEvent[];
}

export function ReasoningPanel({ events }: ReasoningPanelProps) {
    const [isExpanded, setIsExpanded] = useState(true);

    if (events.length === 0) return null;

    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="my-3"
        >
            <div className="rounded-lg border border-border bg-card overflow-hidden">
                <button
                    onClick={() => setIsExpanded(!isExpanded)}
                    className="w-full px-4 py-2.5 flex items-center justify-between hover:bg-muted/50 transition-colors"
                >
                    <div className="flex items-center gap-2">
                        <span className="text-sm font-medium text-foreground">
                            Agent Reasoning
                        </span>
                        <span className="text-xs text-muted-foreground">
                            {events.length} {events.length === 1 ? 'step' : 'steps'}
                        </span>
                    </div>
                    {isExpanded ? (
                        <ChevronUp className="w-4 h-4 text-muted-foreground" />
                    ) : (
                        <ChevronDown className="w-4 h-4 text-muted-foreground" />
                    )}
                </button>

                <AnimatePresence>
                    {isExpanded && (
                        <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: "auto", opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            transition={{ duration: 0.2 }}
                            className="border-t border-border"
                        >
                            <div className="p-4">
                                {/* Metro timeline */}
                                <div className="relative">
                                    {/* Vertical line */}
                                    <div className="absolute left-[7px] top-2 bottom-2 w-[2px] bg-border" />

                                    {/* Events */}
                                    <div className="space-y-4">
                                        {events.map((event, index) => (
                                            <ReasoningStep key={index} event={event} index={index} />
                                        ))}
                                    </div>
                                </div>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
        </motion.div>
    );
}

function ReasoningStep({ event, index }: { event: StreamEvent; index: number }) {
    const getStepInfo = () => {
        switch (event.type) {
            case "thinking":
                return {
                    title: "Thinking",
                    subtitle: (event.arguments?.thought as string) || (event.result?.thought as string) || event.content || "Processing...",
                    dotColor: "bg-blue-500",
                };
            case "tool_call":
                return {
                    title: `Calling: ${event.tool_name}`,
                    subtitle: "Tool invocation",
                    dotColor: "bg-purple-500",
                };
            case "tool_result":
                return {
                    title: `Result: ${event.tool_name}`,
                    subtitle: "Tool completed",
                    dotColor: "bg-green-500",
                };
            case "llm_error":
                return {
                    title: "Error",
                    subtitle: event.error_message || "An error occurred",
                    dotColor: "bg-red-500",
                };
            case "agent_start":
                return {
                    title: `Agent: ${event.agent_name || 'Unknown'}`,
                    subtitle: (event.arguments?.reason as string) || "Orchestrating task...",
                    dotColor: "bg-orange-500",
                };
            // agent_info is not in StreamEvent, maybe I should add it or handle it?
            // "agent_info" was in local interface but StreamEvent has "agent_start" | "agent_end".
            // I'll stick to what StreamEvent has.
            default:
                return {
                    title: event.type,
                    subtitle: "",
                    dotColor: "bg-gray-500",
                };
        }
    };

    const info = getStepInfo();

    return (
        <motion.div
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.05 }}
            className="relative pl-6"
        >
            {/* Timeline dot */}
            <div className={`absolute left-0 top-1.5 w-4 h-4 rounded-full ${info.dotColor} border-2 border-background`} />

            {/* Content */}
            <div className="space-y-1">
                <div className="text-sm font-medium text-foreground">{info.title}</div>
                {info.subtitle && (
                    <div className="text-xs text-muted-foreground">{info.subtitle}</div>
                )}

                {/* Tool arguments */}
                {event.type === "tool_call" && event.arguments && Object.keys(event.arguments).length > 0 && (
                    <div className="mt-2 text-xs">
                        <div className="font-mono bg-muted p-2 rounded text-muted-foreground overflow-x-auto max-h-32 overflow-y-auto">
                            {JSON.stringify(event.arguments, null, 2)}
                        </div>
                    </div>
                )}

                {/* Tool results */}
                {event.type === "tool_result" && event.result && (
                    <div className="mt-2 text-xs">
                        <div className="font-mono bg-muted p-2 rounded text-muted-foreground overflow-x-auto max-h-32 overflow-y-auto">
                            {JSON.stringify(event.result, null, 2)}
                        </div>
                    </div>
                )}
            </div>
        </motion.div>
    );
}
