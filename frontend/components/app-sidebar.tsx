import { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { usePathname, useRouter, useSearchParams } from 'next/navigation';
import { MessageSquare, Database, Home, Plus, Settings } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { getConversations, Conversation, createConversation } from '@/lib/api/chat';
import { ThemeSwitcher } from './theme-switcher';

const navItems = [
    {
        href: '/',
        label: 'Home',
        icon: Home
    },
    {
        href: '/chat',
        label: 'Chat',
        icon: MessageSquare
    },
    {
        href: '/knowledge',
        label: 'Knowledge Base',
        icon: Database
    }
];

interface AppSidebarProps {
    activeConversationId?: string | null;
    onConversationSelect?: (id: string) => void;
    onNewChat?: () => void;
}

export function AppSidebar({ activeConversationId: propsActiveId, onConversationSelect, onNewChat }: AppSidebarProps) {
    const pathname = usePathname();
    const router = useRouter();
    const searchParams = useSearchParams();

    // Use prop if provided, otherwise check search params
    const activeConversationId = propsActiveId !== undefined ? propsActiveId : searchParams.get('id');

    const [isHovered, setIsHovered] = useState(false);
    const [conversations, setConversations] = useState<Conversation[]>([]);
    const [settingsOpen, setSettingsOpen] = useState(false);
    const isChatPage = pathname === '/chat';

    const loadConversations = useCallback(async () => {
        try {
            const data = await getConversations();
            setConversations(data);
        } catch (error) {
            console.error("Failed to load conversations", error);
        }
    }, []);

    useEffect(() => {
        // Fetch conversations regardless of page to keep sidebar updated if needed, 
        // but especially on chat page.
        getConversations().then(data => {
            setConversations(data);
        }).catch(err => {
            console.error("Failed to load conversations", err);
        });
    }, []);

    const handleNewChat = async () => {
        if (onNewChat) {
            onNewChat();
        } else {
            try {
                const newConv = await createConversation("New Chat");
                router.push(`/chat?id=${newConv.id}`);
                await loadConversations();
            } catch (error) {
                console.error("Failed to create conversation", error);
            }
        }
    };

    const handleSelectConversation = (id: string) => {
        if (onConversationSelect) {
            onConversationSelect(id);
        } else {
            router.push(`/chat?id=${id}`);
        }
    };

    // Auto-collapse: expanded only when hovered
    const isExpanded = isHovered;

    return (
        <div
            className={cn(
                "flex flex-col h-full bg-card border-r transition-all duration-300 ease-in-out z-30 shrink-0",
                isExpanded ? "w-64" : "w-16"
            )}
            onMouseEnter={() => setIsHovered(true)}
            onMouseLeave={() => setIsHovered(false)}
        >
            {/* Header */}
            <div className="p-4 border-b flex items-center justify-center overflow-hidden">
                {isExpanded ? (
                    <div className="w-full">
                        <h2 className="text-lg font-bold bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent truncate">
                            Financial AI
                        </h2>
                        <p className="text-xs text-muted-foreground truncate">Enterprise Platform</p>
                    </div>
                ) : (
                    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-600 to-blue-600 flex items-center justify-center text-white font-bold text-sm">
                        F
                    </div>
                )}
            </div>

            {/* Navigation */}
            <nav className={cn("p-2 space-y-1", (!isChatPage || !isExpanded) && "flex-1")}>
                {navItems.map((item) => {
                    const Icon = item.icon;
                    const isActive = pathname === item.href;

                    return (
                        <Link
                            key={item.href}
                            href={item.href}
                            className={cn(
                                "flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all",
                                "hover:bg-accent hover:text-accent-foreground",
                                isActive && "bg-primary text-primary-foreground hover:bg-primary/90",
                                !isExpanded && "justify-center"
                            )}
                            title={!isExpanded ? item.label : undefined}
                        >
                            <Icon className="h-5 w-5 shrink-0" />
                            {isExpanded && <span className="font-medium text-sm truncate">{item.label}</span>}
                        </Link>
                    );
                })}
            </nav>

            {/* Chat History (only on chat page and when expanded) */}
            {isChatPage && isExpanded && (
                <div className="flex-1 border-t p-3 overflow-hidden flex flex-col">
                    <div className="flex items-center justify-between mb-2">
                        <h3 className="text-xs font-semibold text-muted-foreground uppercase">Recent</h3>
                        <Button
                            variant="ghost"
                            size="sm"
                            onClick={handleNewChat}
                            className="h-7 w-7 p-0"
                        >
                            <Plus className="h-4 w-4" />
                        </Button>
                    </div>
                    <div className="space-y-1 overflow-y-auto flex-1">
                        {conversations.length === 0 ? (
                            <p className="text-xs text-muted-foreground text-center py-4">No chats yet</p>
                        ) : (
                            conversations.map((conv) => (
                                <button
                                    key={conv.id}
                                    onClick={() => handleSelectConversation(conv.id)}
                                    className={cn(
                                        "w-full text-left px-2 py-2 rounded-md text-xs transition-colors",
                                        "hover:bg-accent hover:text-accent-foreground",
                                        activeConversationId === conv.id && "bg-accent"
                                    )}
                                >
                                    <div className="font-medium truncate">
                                        {conv.title || 'New Chat'}
                                    </div>
                                    <div className="text-xs text-muted-foreground">
                                        {new Date(conv.created_at).toLocaleDateString()}
                                    </div>
                                </button>
                            ))
                        )}
                    </div>
                </div>
            )}

            {/* Settings Button */}
            <div className="border-t p-2">
                <Popover open={settingsOpen} onOpenChange={setSettingsOpen}>
                    <PopoverTrigger asChild>
                        <Button
                            variant="ghost"
                            className={cn(
                                "w-full gap-3 transition-all",
                                "hover:bg-accent hover:text-accent-foreground",
                                !isExpanded && "justify-center px-0"
                            )}
                            title={!isExpanded ? "Settings" : undefined}
                        >
                            <Settings className="h-5 w-5 shrink-0" />
                            {isExpanded && <span className="font-medium text-sm">Settings</span>}
                        </Button>
                    </PopoverTrigger>
                    <PopoverContent className="w-80 p-4" side="right" align="end">
                        <ThemeSwitcher />
                    </PopoverContent>
                </Popover>
            </div>

            {/* Footer */}
            {isExpanded && (
                <div className="p-3 border-t text-xs text-muted-foreground">
                    <p>© 2026 Financial AI</p>
                </div>
            )}
        </div>
    );
}
