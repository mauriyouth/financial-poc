'use client';

import React, { useState, useMemo } from 'react';
import { ArrowUp, ArrowDown, ArrowUpDown, Download, Columns3 } from 'lucide-react';
import { TableToolbar } from './table-toolbar';
import { ColumnVisibilityMenu } from './column-visibility-menu';
import { parseTableContent, sortTableData, exportToExcel, filterVisibleColumns, TableCell } from './utils';

interface InteractiveTableProps {
    children: React.ReactNode;
}

export function InteractiveTable({ children }: InteractiveTableProps) {
    const [sortColumn, setSortColumn] = useState<number | null>(null);
    const [sortDirection, setSortDirection] = useState<'asc' | 'desc' | null>(null);
    const [hiddenColumns, setHiddenColumns] = useState<Set<number>>(new Set());
    const [isHovered, setIsHovered] = useState(false);
    const [showColumnMenu, setShowColumnMenu] = useState(false);

    // Parse table content from children
    const { headers, rows } = useMemo(() => {
        const parsed = parseTableContent(children);
        return parsed;
    }, [children]);

    // Apply sorting
    const sortedRows = useMemo(() => {
        if (sortColumn === null || sortDirection === null) {
            return rows;
        }
        const dataForSorting = rows.map(row => row.map(cell => cell.text));
        const sortedIndices = sortTableData(dataForSorting, sortColumn, sortDirection)
            .map(sortedRow => rows.findIndex(originalRow => originalRow.every((cell, i) => cell.text === sortedRow[i])));

        // Simpler way: sort the actual objects based on their text property
        return [...rows].sort((a, b) => {
            const aVal = a[sortColumn]?.text || '';
            const bVal = b[sortColumn]?.text || '';

            const aNum = parseFloat(aVal.replace(/[^0-9.-]/g, ''));
            const bNum = parseFloat(bVal.replace(/[^0-9.-]/g, ''));

            if (!isNaN(aNum) && !isNaN(bNum)) {
                return sortDirection === 'asc' ? aNum - bNum : bNum - aNum;
            }

            const comp = aVal.toLowerCase().localeCompare(bVal.toLowerCase());
            return sortDirection === 'asc' ? comp : -comp;
        });
    }, [rows, sortColumn, sortDirection]);

    // Handle column header click for sorting
    const handleHeaderClick = (columnIndex: number) => {
        if (sortColumn === columnIndex) {
            // Cycle through: asc → desc → null
            if (sortDirection === 'asc') {
                setSortDirection('desc');
            } else if (sortDirection === 'desc') {
                setSortColumn(null);
                setSortDirection(null);
            }
        } else {
            setSortColumn(columnIndex);
            setSortDirection('asc');
        }
    };

    // Handle column visibility toggle
    const handleToggleColumn = (index: number) => {
        setHiddenColumns((prev) => {
            const newSet = new Set(prev);
            if (newSet.has(index)) {
                newSet.delete(index);
            } else {
                // Only hide if more than one column will remain visible
                if (headers.length - newSet.size > 1) {
                    newSet.add(index);
                }
            }
            return newSet;
        });
    };

    // Handle show all columns
    const handleShowAll = () => {
        setHiddenColumns(new Set());
    };

    // Handle hide all columns (leave one visible)
    const handleHideAll = () => {
        const newSet = new Set<number>();
        for (let i = 1; i < headers.length; i++) {
            newSet.add(i);
        }
        setHiddenColumns(newSet);
    };

    // Handle export to Excel
    const handleExportExcel = () => {
        const visibleHeaders = filterVisibleColumns([headers.map(h => h.text)], hiddenColumns)[0];
        const visibleRows = filterVisibleColumns(sortedRows.map(row => row.map(c => c.text)), hiddenColumns);
        exportToExcel(visibleHeaders as string[], visibleRows as string[][], 'table-export');
    };

    // Handle clear sort
    const handleClearSort = () => {
        setSortColumn(null);
        setSortDirection(null);
    };

    // Filter visible columns
    const visibleHeaders = headers.filter((_, index) => !hiddenColumns.has(index));
    const visibleRows = sortedRows.map((row) =>
        row.filter((_, index) => !hiddenColumns.has(index))
    );

    // Map visible index to original index
    const getOriginalIndex = (visibleIndex: number): number => {
        let count = 0;
        for (let i = 0; i < headers.length; i++) {
            if (!hiddenColumns.has(i)) {
                if (count === visibleIndex) {
                    return i;
                }
                count++;
            }
        }
        return visibleIndex;
    };

    // Render sort indicator
    const renderSortIndicator = (columnIndex: number) => {
        if (sortColumn === columnIndex) {
            if (sortDirection === 'asc') {
                return <ArrowUp className="inline h-3.5 w-3.5 ml-1 text-primary" />;
            } else if (sortDirection === 'desc') {
                return <ArrowDown className="inline h-3.5 w-3.5 ml-1 text-primary" />;
            }
        }
        return <ArrowUpDown className="inline h-3.5 w-3.5 ml-1 text-muted-foreground opacity-0 group-hover:opacity-100" />;
    };

    return (
        <div
            className="my-4 relative"
            onMouseEnter={() => setIsHovered(true)}
            onMouseLeave={() => setIsHovered(false)}
        >
            {/* Compact floating widget - appears on hover */}
            {isHovered && (
                <div className="absolute -top-7 right-2 z-20">
                    {/* Column Visibility Dropdown */}
                    <div className="relative inline-block">
                        <div className="flex gap-1.5 bg-background border border-primary rounded-lg p-1.5 shadow-lg">
                            {/* Column Visibility Button */}
                            <button
                                onClick={(e) => {
                                    e.stopPropagation();
                                    setShowColumnMenu(!showColumnMenu);
                                }}
                                className="p-1.5 hover:bg-muted rounded transition-colors group relative"
                                title="Show/hide columns"
                            >
                                <Columns3 className="h-4 w-4 text-foreground" />
                                <span className="absolute -bottom-8 left-1/2 -translate-x-1/2 px-2 py-1 bg-popover text-popover-foreground text-xs rounded whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50">
                                    Columns
                                </span>
                            </button>

                            {/* Clear Sort Button - only show if sorted */}
                            {sortColumn !== null && (
                                <button
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        handleClearSort();
                                    }}
                                    className="p-1.5 hover:bg-muted rounded transition-colors group relative"
                                    title="Clear sorting"
                                >
                                    <ArrowUpDown className="h-4 w-4 text-foreground" />
                                    <span className="absolute -bottom-8 left-1/2 -translate-x-1/2 px-2 py-1 bg-popover text-popover-foreground text-xs rounded whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50">
                                        Clear Sort
                                    </span>
                                </button>
                            )}

                            {/* Excel Export Button */}
                            <button
                                onClick={(e) => {
                                    e.stopPropagation();
                                    handleExportExcel();
                                }}
                                className="p-1.5 hover:bg-muted rounded transition-colors group relative"
                                title="Export to Excel"
                            >
                                <Download className="h-4 w-4 text-foreground" />
                                <span className="absolute -bottom-8 left-1/2 -translate-x-1/2 px-2 py-1 bg-popover text-popover-foreground text-xs rounded whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50">
                                    Export Excel
                                </span>
                            </button>
                        </div>

                        {/* Column Visibility Dropdown Menu */}
                        {showColumnMenu && (
                            <div className="absolute top-full right-0 mt-2 w-48 bg-background border border-border rounded-lg shadow-lg p-2 z-50">
                                {headers.map((header, index) => {
                                    const isVisible = !hiddenColumns.has(index);
                                    const canHide = headers.length - hiddenColumns.size > 1;
                                    const isDisabled = isVisible && !canHide;

                                    return (
                                        <label
                                            key={index}
                                            className={`flex items-center gap-2 px-2 py-1.5 rounded hover:bg-muted cursor-pointer ${isDisabled ? 'opacity-50 cursor-not-allowed' : ''
                                                }`}
                                        >
                                            <input
                                                type="checkbox"
                                                checked={isVisible}
                                                disabled={isDisabled}
                                                onChange={() => handleToggleColumn(index)}
                                                className="rounded"
                                            />
                                            <span className="text-sm">{header.text || `Column ${index + 1}`}</span>
                                        </label>
                                    );
                                })}
                                <div className="border-t border-border mt-2 pt-2 flex gap-1">
                                    <button
                                        onClick={handleShowAll}
                                        className="flex-1 px-2 py-1 text-xs hover:bg-muted rounded"
                                    >
                                        Show All
                                    </button>
                                    <button
                                        onClick={handleHideAll}
                                        disabled={headers.length - hiddenColumns.size <= 1}
                                        className="flex-1 px-2 py-1 text-xs hover:bg-muted rounded disabled:opacity-50"
                                    >
                                        Hide All
                                    </button>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            )}

            {/* Table with permanent blue border */}
            <div className="rounded-lg border border-primary shadow-md shadow-primary/30 overflow-hidden">
                <div className="overflow-x-auto max-h-[600px] overflow-y-auto">
                    <table className="min-w-full divide-y divide-border">
                        <thead className="bg-muted sticky top-0 z-10">
                            <tr>
                                {visibleHeaders.map((header, visibleIndex) => {
                                    const originalIndex = getOriginalIndex(visibleIndex);

                                    return (
                                        <th
                                            key={visibleIndex}
                                            className="px-4 py-3 text-left text-sm font-semibold text-foreground cursor-pointer hover:bg-muted/70 transition-colors group bg-muted"
                                            onClick={() => handleHeaderClick(originalIndex)}
                                        >
                                            {header.content}
                                            {renderSortIndicator(originalIndex)}
                                        </th>
                                    );
                                })}
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-border bg-card">
                            {visibleRows.map((row, rowIndex) => (
                                <tr key={rowIndex} className="hover:bg-muted/30 transition-colors">
                                    {row.map((cell, cellIndex) => (
                                        <td key={cellIndex} className="px-4 py-3 text-sm">
                                            {cell.content}
                                        </td>
                                    ))}
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
