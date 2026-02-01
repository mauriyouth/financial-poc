import React from 'react';
import { Button } from '@/components/ui/button';
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuCheckboxItem,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Columns3 } from 'lucide-react';

interface ColumnVisibilityMenuProps {
    columns: string[];
    hiddenColumns: Set<number>;
    onToggleColumn: (index: number) => void;
    onShowAll: () => void;
    onHideAll: () => void;
}

export function ColumnVisibilityMenu({
    columns,
    hiddenColumns,
    onToggleColumn,
    onShowAll,
    onHideAll,
}: ColumnVisibilityMenuProps) {
    const visibleCount = columns.length - hiddenColumns.size;
    const canHideMore = visibleCount > 1;

    return (
        <DropdownMenu>
            <DropdownMenuTrigger asChild>
                <Button variant="outline" size="sm" className="h-8">
                    <Columns3 className="h-3.5 w-3.5 mr-1.5" />
                    Columns
                </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="center" className="w-48">
                {columns.map((column, index) => {
                    const isVisible = !hiddenColumns.has(index);
                    const isDisabled = isVisible && !canHideMore;

                    return (
                        <DropdownMenuCheckboxItem
                            key={index}
                            checked={isVisible}
                            onCheckedChange={() => onToggleColumn(index)}
                            disabled={isDisabled}
                        >
                            {column || `Column ${index + 1}`}
                        </DropdownMenuCheckboxItem>
                    );
                })}
                <DropdownMenuSeparator />
                <div className="flex gap-1 p-1">
                    <Button
                        variant="ghost"
                        size="sm"
                        className="h-7 flex-1 text-xs"
                        onClick={onShowAll}
                    >
                        Show All
                    </Button>
                    <Button
                        variant="ghost"
                        size="sm"
                        className="h-7 flex-1 text-xs"
                        onClick={onHideAll}
                        disabled={!canHideMore}
                    >
                        Hide All
                    </Button>
                </div>
            </DropdownMenuContent>
        </DropdownMenu>
    );
}
