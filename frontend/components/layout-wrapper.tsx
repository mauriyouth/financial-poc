"use client";

import { usePathname } from 'next/navigation';
import { ReactNode, Suspense } from 'react';
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
            <Suspense fallback={<div className="w-16 flex-shrink-0 border-r bg-card" />}>
                <AppSidebar />
            </Suspense>
            <main className="flex-1 min-w-0 h-full overflow-hidden relative">
                {children}
            </main>
        </div>
    );
}
