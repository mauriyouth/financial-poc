"use client";

import * as React from "react";
import { Moon, Sun, Monitor } from "lucide-react";
import { useTheme } from "next-themes";
import { cn } from "@/lib/utils";

export function ThemeSwitcher() {
    const { theme, setTheme } = useTheme();
    const [mounted, setMounted] = React.useState(false);

    // Avoid hydration mismatch
    React.useEffect(() => {
        setMounted(true);
    }, []);

    if (!mounted) {
        return null;
    }

    const themes = [
        { value: "light", label: "Light", icon: Sun },
        { value: "dark", label: "Dark", icon: Moon },
        { value: "system", label: "System", icon: Monitor },
    ];

    return (
        <div className="space-y-3">
            <div className="space-y-1">
                <h4 className="font-medium text-sm">Theme</h4>
                <p className="text-xs text-muted-foreground">
                    Choose your preferred theme
                </p>
            </div>
            <div className="grid grid-cols-3 gap-2">
                {themes.map((t) => {
                    const Icon = t.icon;
                    const isActive = theme === t.value;

                    return (
                        <button
                            key={t.value}
                            onClick={() => setTheme(t.value)}
                            className={cn(
                                "flex flex-col items-center gap-2 p-3 rounded-lg border-2 transition-all",
                                "hover:bg-accent hover:border-primary/50",
                                isActive
                                    ? "border-primary bg-primary/5"
                                    : "border-border"
                            )}
                        >
                            <Icon className={cn(
                                "h-5 w-5",
                                isActive ? "text-primary" : "text-muted-foreground"
                            )} />
                            <span className={cn(
                                "text-xs font-medium",
                                isActive ? "text-primary" : "text-muted-foreground"
                            )}>
                                {t.label}
                            </span>
                        </button>
                    );
                })}
            </div>
        </div>
    );
}
