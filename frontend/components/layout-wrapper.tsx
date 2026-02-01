"use client";

import { usePathname } from 'next/navigation';
import { ReactNode } from 'react';
import { AppSidebar } from './app-sidebar';

export function LayoutWrapper({ children }: { children: ReactNode }) {
    const pathname = usePathname();

    // Don't show sidebar on homepage
    const showSidebar = pathname !== '/';

    if (!showSidebar) {
        return <>{children}</>;
    }

    return (
        <div className="flex h-screen w-screen overflow-hidden bg-background">
            <AppSidebar />
            <main className="flex-1 min-w-0 h-full overflow-hidden relative">
                {children}
            </main>
        </div>
    );
}
