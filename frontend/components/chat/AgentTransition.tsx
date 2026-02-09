"use client";

import { motion } from "framer-motion";
import { ArrowRight } from "lucide-react";

interface AgentTransitionProps {
    fromAgent: string;
    toAgent: string;
    reason?: string;
}

export function AgentTransition({ fromAgent, toAgent, reason }: AgentTransitionProps) {
    return (
        <motion.div
            initial={{ opacity: 0, scale: 0.98 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.2 }}
            className="my-3 px-4"
        >
            <div className="flex items-center gap-3 py-2.5 px-4 rounded-lg bg-card border border-border">
                <span className="text-sm text-muted-foreground font-medium">
                    {fromAgent}
                </span>

                <ArrowRight className="w-4 h-4 text-muted-foreground flex-shrink-0" />

                <span className="text-sm text-foreground font-medium">
                    {toAgent}
                </span>

                {reason && (
                    <>
                        <span className="text-muted-foreground mx-1">•</span>
                        <span className="text-xs text-muted-foreground italic">{reason}</span>
                    </>
                )}
            </div>
        </motion.div>
    );
}
