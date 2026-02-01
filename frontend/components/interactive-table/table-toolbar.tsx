import React from 'react';
import { Button } from '@/components/ui/button';
import { Download, ArrowUpDown } from 'lucide-react';
import { ColumnVisibilityMenu } from './column-visibility-menu';

interface TableToolbarProps {
    columnHeaders: string[];
    hiddenColumns: Set<number>;
    onToggleColumn: (index: number) => void;
    onShowAll: () => void;
    onHideAll: () => void;
    onExportExcel: () => void;
    onClearSort?: () => void;
    rowCount: number;
    isSorted: boolean;
}

export function TableToolbar({
    columnHeaders,
    hiddenColumns,
    onToggleColumn,
    onShowAll,
    onHideAll,
    onExportExcel,
    onClearSort,
    rowCount,
    isSorted,
}: TableToolbarProps) {
    const visibleColumnCount = columnHeaders.length - hiddenColumns.size;

    return (
        <div className="flex items-center justify-between px-0 py-2 bg-muted/30 border border-border rounded-t-lg">
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <span className="font-mono">
                    📊 {visibleColumnCount} column{visibleColumnCount !== 1 ? 's' : ''} × {rowCount} row{rowCount !== 1 ? 's' : ''}
                </span>
            </div>

            <div className="flex items-center gap-2">
                {/* Column Visibility */}
                <ColumnVisibilityMenu
                    columns={columnHeaders}
                    hiddenColumns={hiddenColumns}
                    onToggleColumn={onToggleColumn}
                    onShowAll={onShowAll}
                    onHideAll={onHideAll}
                />

                {/* Clear Sort */}
                {isSorted && onClearSort && (
                    <Button
                        variant="outline"
                        size="sm"
                        className="h-8"
                        onClick={onClearSort}
                    >
                        <ArrowUpDown className="h-3.5 w-3.5 mr-1.5" />
                        Clear Sort
                    </Button>
                )}

                {/* Export to Excel */}
                <Button
                    variant="outline"
                    size="sm"
                    className="h-8"
                    onClick={onExportExcel}
                >
                    <Download className="h-3.5 w-3.5 mr-1.5" />
                    Excel
                </Button>
            </div>
        </div>
    );
}
