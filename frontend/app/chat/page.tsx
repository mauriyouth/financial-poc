import { Suspense } from 'react';
import { ChatContent } from './ChatContent';
import { Loader2 } from 'lucide-react';

export default function ChatPage() {
    return (
        <Suspense fallback={
            <div className="h-screen w-screen flex items-center justify-center bg-neutral-950 text-neutral-400">
                <Loader2 className="h-10 w-10 animate-spin" />
            </div>
        }>
            <ChatContent />
        </Suspense>
    );
}
