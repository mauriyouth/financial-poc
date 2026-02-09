"use client";

import { useState, useEffect, useRef, useCallback } from 'react';
import { Download, FileSpreadsheet, Loader2, FunctionSquare, Table as TableIcon, Save } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ScrollArea, ScrollBar } from '@/components/ui/scroll-area';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { cn } from '@/lib/utils';
import * as XLSX from 'xlsx';
import { updateDocument } from '@/lib/api/documents';

interface ExcelPreviewProps {
    documentId?: string; // Add optional ID
    documentUrl: string;
    documentName: string;
}

interface CellData {
    value: string;
    formula?: string;
    address: string; // A1, B2, etc.
}

interface SheetData {
    name: string;
    rows: CellData[][];
    colHeaders: string[]; // A, B, C...
}

// A range is inclusive of start and end coordinates
interface SelectionRange {
    startRow: number;
    startCol: number;
    endRow: number;
    endCol: number;
}

export function ExcelPreview({ documentId, documentUrl, documentName }: ExcelPreviewProps) {
    const [sheets, setSheets] = useState<SheetData[]>([]);
    const [activeSheetIndex, setActiveSheetIndex] = useState(0);
    const [loading, setLoading] = useState(false);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Active cell is the "cursor" / focus point
    const [activeCell, setActiveCell] = useState<{ row: number, col: number } | null>(null);

    // Editing State
    const [isEditing, setIsEditing] = useState(false);
    const [editValue, setEditValue] = useState('');

    // Selection range defines the full selected area (including the active cell)
    const [selectionRange, setSelectionRange] = useState<SelectionRange | null>(null);

    const containerRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        let isMounted = true;

        const loadExcel = async () => {
            try {
                setLoading(true);
                setError(null);

                const response = await fetch(documentUrl);
                if (!response.ok) throw new Error('Failed to fetch file');

                const blob = await response.blob();
                const arrayBuffer = await blob.arrayBuffer();

                const workbook = XLSX.read(arrayBuffer, { type: 'array' });
                const parsedSheets: SheetData[] = [];

                // Parse each sheet
                workbook.SheetNames.forEach(name => {
                    const sheet = workbook.Sheets[name];
                    const range = XLSX.utils.decode_range(sheet['!ref'] || 'A1');
                    const rows: CellData[][] = [];
                    const colHeaders: string[] = [];

                    // Generate column headers (A, B, C...)
                    for (let C = range.s.c; C <= range.e.c; ++C) {
                        colHeaders.push(XLSX.utils.encode_col(C));
                    }

                    for (let R = range.s.r; R <= range.e.r; ++R) {
                        const row: CellData[] = [];
                        for (let C = range.s.c; C <= range.e.c; ++C) {
                            const cellAddress = XLSX.utils.encode_cell({ r: R, c: C });
                            const cell = sheet[cellAddress];

                            row.push({
                                value: cell ? (cell.w || cell.v || '') : '', // Prefer formatted text, then value
                                formula: cell && cell.f ? `=${cell.f}` : undefined,
                                address: cellAddress
                            });
                        }
                        rows.push(row);
                    }
                    parsedSheets.push({ name, rows, colHeaders });
                });

                if (isMounted) {
                    setSheets(parsedSheets);
                    if (parsedSheets.length > 0) {
                        setActiveSheetIndex(0);
                        if (parsedSheets[0].rows.length > 0 && parsedSheets[0].rows[0].length > 0) {
                            const initial = { row: 0, col: 0 };
                            setActiveCell(initial);
                            setSelectionRange({ startRow: 0, startCol: 0, endRow: 0, endCol: 0 });
                        }
                    }
                }
            } catch (err) {
                console.error('Error loading Excel file:', err);
                if (isMounted) {
                    setError('Failed to load preview');
                }
            } finally {
                if (isMounted) {
                    setLoading(false);
                }
            }
        };

        loadExcel();

        return () => {
            isMounted = false;
        };
    }, [documentUrl]);

    // Reset selection when switching sheets
    useEffect(() => {
        if (sheets.length > 0 && sheets[activeSheetIndex].rows.length > 0) {
            setActiveCell({ row: 0, col: 0 });
            setSelectionRange({ startRow: 0, startCol: 0, endRow: 0, endCol: 0 });
        } else {
            setActiveCell(null);
            setSelectionRange(null);
        }
    },
        [activeSheetIndex, sheets]);


    // Save Document
    const handleSave = async () => {
        if (!documentId || sheets.length === 0) return;

        try {
            setSaving(true);

            // Reconstruct workbook from sheets
            const wb = XLSX.utils.book_new();
            sheets.forEach(sheet => {
                const ws_data: (string | number | boolean)[][] = [];
                // First pass: Values
                sheet.rows.forEach(row => {
                    const rowData = row.map(cell => cell.value);
                    ws_data.push(rowData);
                });

                const ws = XLSX.utils.aoa_to_sheet(ws_data);

                // Second pass: Apply formulas if present
                sheet.rows.forEach((row, R) => {
                    row.forEach((cell, C) => {
                        if (cell.formula) {
                            const cellRef = XLSX.utils.encode_cell({ c: C, r: R });
                            if (!ws[cellRef]) ws[cellRef] = { v: cell.value, t: 'n' }; // Ensure cell exists
                            ws[cellRef].f = cell.formula;
                            // SheetJS will use .v as the cached value. 
                            // If we just edited it, .v might be the formula string or empty.
                            // Ideally, we'd recalculate, but that requires a calc engine.
                            // We'll set .v to undefined to force Excel to calc on load? 
                            // Or keep it as is.
                        }
                    });
                });

                XLSX.utils.book_append_sheet(wb, ws, sheet.name);
            });

            // Write to buffer
            const wbout = XLSX.write(wb, { bookType: 'xlsx', type: 'array' });

            // Create File object
            const file = new File([wbout], documentName, {
                type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            });

            // Upload
            await updateDocument(documentId, file);

            // Just simple feedback
            // console.log("Saved successfully");
            setSaving(false);

            // Re-fetch to ensure sync (optional but good)
            window.location.reload(); // Hard reload to see changes or we could just refetch doc url. 
            // Better: just stay here, we updated state.

        } catch (err) {
            console.error("Failed to save:", err);
            setSaving(false);
            setError("Failed to save changes");
        }
    };

    // Commit Cell Edit
    const commitEdit = useCallback((row: number, col: number, newValue: string) => {
        const newSheets = [...sheets];
        const currentSheet = newSheets[activeSheetIndex];

        // Ensure row exists
        if (!currentSheet.rows[row]) return; // Should not happen if clicking existing cell

        const cell = currentSheet.rows[row][col];
        if (cell) {
            cell.value = newValue;
            cell.formula = newValue.startsWith('=') ? newValue.substring(1) : undefined;
        } else {
            currentSheet.rows[row][col] = {
                value: newValue,
                address: XLSX.utils.encode_cell({ r: row, c: col }),
                formula: newValue.startsWith('=') ? newValue.substring(1) : undefined
            };
        }

        setSheets(newSheets);
        setIsEditing(false);
        setEditValue('');
        // Restore focus to container
        containerRef.current?.focus();
    }, [sheets, activeSheetIndex]);


    // Keyboard navigation
    const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
        // If editing, don't hijack nav keys unless Enter/Escape
        if (isEditing) {
            if (e.key === 'Enter') {
                e.preventDefault();
                if (activeCell) commitEdit(activeCell.row, activeCell.col, editValue);
            }
            return;
        }

        if (!activeCell || sheets.length === 0) return;

        const currentSheet = sheets[activeSheetIndex];
        const maxRow = currentSheet.rows.length - 1;
        const maxCol = currentSheet.colHeaders.length - 1;

        // Enter to Edit
        if (e.key === 'Enter' && !e.ctrlKey && !e.metaKey) {
            e.preventDefault();
            setIsEditing(true);
            const cell = currentSheet.rows[activeCell.row][activeCell.col];
            setEditValue(cell ? (cell.formula ? `=${cell.formula}` : cell.value) : '');
            return;
        }

        // Start typing to edit (alphanumeric)
        // Check if key is single char and not modifier
        if (e.key.length === 1 && !e.ctrlKey && !e.metaKey && !e.altKey) {
            // setIsEditing(true);
            // setEditValue(e.key);
            // Actually, usually users expect to overwrite immediately. 
            // Implementing "F2" behavior (Enter/Doubleclick) vs "Type over" behavior
            // For simplicity, let's stick to Enter/Double Click for now, or users get frustrated by accidental edits.
        }


        // Select All (Ctrl+A or Cmd+A)
        if ((e.ctrlKey || e.metaKey) && e.key === 'a') {
            e.preventDefault();
            setSelectionRange({
                startRow: 0,
                startCol: 0,
                endRow: maxRow,
                endCol: maxCol
            });
            return;
        }

        if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(e.key)) {
            e.preventDefault();
            // ... (rest of nav code same)
            // Copy logic from before...
            setActiveCell(prev => {
                if (!prev) return { row: 0, col: 0 };
                let { row, col } = prev;

                switch (e.key) {
                    case 'ArrowUp': row = Math.max(0, row - 1); break;
                    case 'ArrowDown': row = Math.min(maxRow, row + 1); break;
                    case 'ArrowLeft': col = Math.max(0, col - 1); break;
                    case 'ArrowRight': col = Math.min(maxCol, col + 1); break;
                }

                setSelectionRange({
                    startRow: row,
                    startCol: col,
                    endRow: row,
                    endCol: col
                });

                return { row, col };
            });
        }
    }, [activeCell, sheets, activeSheetIndex, isEditing, editValue, commitEdit]);


    if (loading) {
        return (
            <div className="flex flex-col items-center justify-center h-full text-muted-foreground">
                <Loader2 className="h-8 w-8 animate-spin mb-2" />
                <p>Loading spreadsheet...</p>
            </div>
        );
    }

    if (error || sheets.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center h-full p-6 text-center">
                <FileSpreadsheet className="h-16 w-16 mb-4 text-muted-foreground opacity-50" />
                <p className="text-sm font-medium mb-2">{error || "Preview not available"}</p>
                {error === "Failed to save changes" && (
                    <Button variant="outline" size="sm" onClick={() => window.location.reload()} className="mt-2">
                        Reload
                    </Button>
                )}
                {!error?.includes("save") && (
                    <>
                        <p className="text-xs text-muted-foreground mb-4">
                            This file cannot be previewed in the browser.
                        </p>
                        <Button
                            variant="outline"
                            size="sm"
                            onClick={() => window.open(documentUrl, '_blank')}
                        >
                            <Download className="h-4 w-4 mr-2" />
                            Download to View
                        </Button>
                    </>
                )}
            </div>
        );
    }

    const currentSheet = sheets[activeSheetIndex];
    const rows = currentSheet.rows;

    // Formula bar logic
    let activeCellData: CellData | null = null;
    if (activeCell && rows[activeCell.row] && rows[activeCell.row][activeCell.col]) {
        activeCellData = rows[activeCell.row][activeCell.col];
    }

    // If editing, show edit value in formula bar ?? or bind active cell
    const formulaBarValue = isEditing
        ? editValue
        : (activeCellData ? (activeCellData.formula ? `=${activeCellData.formula}` : activeCellData.value) : '');

    const addressBarValue = activeCellData ? activeCellData.address : '';

    // Helper to check overlap
    const isSelected = (r: number, c: number) => {
        if (!selectionRange) return false;
        return (
            r >= Math.min(selectionRange.startRow, selectionRange.endRow) &&
            r <= Math.max(selectionRange.startRow, selectionRange.endRow) &&
            c >= Math.min(selectionRange.startCol, selectionRange.endCol) &&
            c <= Math.max(selectionRange.startCol, selectionRange.endCol)
        );
    };

    const isColSelected = (c: number) => {
        if (!selectionRange) return false;
        return (
            selectionRange.startRow === 0 &&
            selectionRange.endRow === rows.length - 1 &&
            c >= Math.min(selectionRange.startCol, selectionRange.endCol) &&
            c <= Math.max(selectionRange.startCol, selectionRange.endCol)
        );
    };

    const isRowSelected = (r: number) => {
        if (!selectionRange) return false;
        return (
            selectionRange.startCol === 0 &&
            selectionRange.endCol === currentSheet.colHeaders.length - 1 &&
            r >= Math.min(selectionRange.startRow, selectionRange.endRow) &&
            r <= Math.max(selectionRange.startRow, selectionRange.endRow)
        );
    };

    return (
        <div
            className="h-full flex flex-col outline-none group"
            tabIndex={0}
            onKeyDown={handleKeyDown}
            ref={containerRef}
            onClick={() => {
                if (!isEditing) containerRef.current?.focus();
            }}
        >
            {/* Toolbar & Formula Bar */}
            <div className="flex flex-col border-b bg-muted/20 shrink-0">
                {/* Actions Row */}
                <div className="flex items-center justify-between p-2 pb-1 gap-4">
                    <div className="flex items-center gap-2">
                        <div className="flex items-center px-2 py-1 bg-white dark:bg-neutral-800 border rounded text-xs font-medium w-[60px] justify-center text-muted-foreground shadow-sm">
                            {addressBarValue || ""}
                        </div>
                        <div className="flex-1 flex items-center bg-white dark:bg-neutral-800 border rounded px-2 py-1 h-7 min-w-[300px] shadow-sm">
                            <FunctionSquare className="h-3 w-3 text-muted-foreground mr-2 shrink-0" />
                            <input
                                type="text"
                                value={formulaBarValue || ''}
                                onChange={(e) => {
                                    if (activeCell) {
                                        setIsEditing(true);
                                        setEditValue(e.target.value);
                                    }
                                }}
                                onKeyDown={(e) => {
                                    if (e.key === 'Enter' && activeCell) {
                                        commitEdit(activeCell.row, activeCell.col, editValue);
                                    }
                                }}
                                className="bg-transparent border-none outline-none text-xs w-full font-mono text-foreground"
                                placeholder=""
                            />
                        </div>
                    </div>

                    <div className="flex items-center gap-2">
                        {documentId && (
                            <Button
                                variant={saving ? "secondary" : "default"}
                                size="sm"
                                className="h-7 text-xs bg-green-600 hover:bg-green-700 text-white"
                                onClick={handleSave}
                                disabled={saving}
                            >
                                {saving ? <Loader2 className="h-3 w-3 animate-spin mr-2" /> : <Save className="h-3 w-3 mr-2" />}
                                {saving ? "Saving..." : "Save"}
                            </Button>
                        )}
                        <Button
                            variant="ghost"
                            size="sm"
                            className="h-7 text-xs"
                            onClick={() => window.open(documentUrl, '_blank')}
                        >
                            <Download className="h-3 w-3 mr-2" />
                            Download
                        </Button>
                    </div>
                </div>
            </div>

            {/* Table Content */}
            <ScrollArea className="flex-1 w-full bg-white dark:bg-neutral-900 border-b">
                <div className="p-0">
                    <div className="border-b">
                        <Table>
                            <TableHeader>
                                <TableRow className="hover:bg-transparent">
                                    <TableHead
                                        className="w-[40px] bg-muted/20 text-center border-r border-b font-mono text-[10px] p-0 h-6 cursor-pointer hover:bg-muted/40"
                                        onClick={() => {
                                            const maxRow = rows.length - 1;
                                            const maxCol = currentSheet.colHeaders.length - 1;
                                            setSelectionRange({
                                                startRow: 0,
                                                startCol: 0,
                                                endRow: maxRow,
                                                endCol: maxCol
                                            });
                                        }}
                                    ></TableHead>

                                    {currentSheet.colHeaders.map((header, colIndex) => {
                                        const selected = isColSelected(colIndex);
                                        return (
                                            <TableHead
                                                key={colIndex}
                                                className={cn(
                                                    "whitespace-nowrap h-6 px-1 text-center font-semibold text-[11px] border-r border-b min-w-[80px] select-none text-foreground cursor-pointer transition-colors",
                                                    selected ? "bg-green-100 dark:bg-green-900/40 text-green-700" : "bg-muted/20 hover:bg-muted/30"
                                                )}
                                                onClick={(e) => {
                                                    const maxRow = rows.length - 1;
                                                    if (e.shiftKey && selectionRange && selectionRange.startRow === 0 && selectionRange.endRow === maxRow) {
                                                        setSelectionRange(prev => ({ ...prev!, endCol: colIndex }));
                                                    } else {
                                                        setActiveCell({ row: 0, col: colIndex });
                                                        setSelectionRange({ startRow: 0, startCol: colIndex, endRow: maxRow, endCol: colIndex });
                                                    }
                                                }}
                                            >
                                                {header}
                                                {selected && <div className="absolute inset-x-0 bottom-0 h-[2px] bg-green-500" />}
                                            </TableHead>
                                        );
                                    })}
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {rows.map((row, rowIndex) => {
                                    const selected = isRowSelected(rowIndex);
                                    return (
                                        <TableRow key={rowIndex} className="hover:bg-transparent">
                                            <TableCell
                                                className={cn(
                                                    "text-center border-r border-b font-semibold text-[11px] text-muted-foreground w-[40px] p-0 h-7 select-none cursor-pointer transition-colors",
                                                    selected ? "bg-green-100 dark:bg-green-900/40 text-green-700" : "bg-muted/20 hover:bg-muted/30"
                                                )}
                                                onClick={(e) => {
                                                    const maxCol = currentSheet.colHeaders.length - 1;
                                                    if (e.shiftKey && selectionRange && selectionRange.startCol === 0 && selectionRange.endCol === maxCol) {
                                                        setSelectionRange(prev => ({ ...prev!, endRow: rowIndex }));
                                                    } else {
                                                        setActiveCell({ row: rowIndex, col: 0 });
                                                        setSelectionRange({ startRow: rowIndex, startCol: 0, endRow: rowIndex, endCol: maxCol });
                                                    }
                                                }}
                                            >
                                                {rowIndex + 1}
                                                {selected && <div className="absolute inset-y-0 right-0 w-[2px] bg-green-500" />}
                                            </TableCell>

                                            {row.map((cell, colIndex) => {
                                                const isActive = activeCell?.row === rowIndex && activeCell?.col === colIndex;
                                                const isRangeSelected = isSelected(rowIndex, colIndex);
                                                const isCellEditing = isActive && isEditing;

                                                return (
                                                    <TableCell
                                                        key={colIndex}
                                                        onMouseDown={(e) => {
                                                            if (e.shiftKey && activeCell) {
                                                                setSelectionRange({
                                                                    startRow: activeCell.row,
                                                                    startCol: activeCell.col,
                                                                    endRow: rowIndex,
                                                                    endCol: colIndex
                                                                });
                                                            } else {
                                                                setActiveCell({ row: rowIndex, col: colIndex });
                                                                setSelectionRange({
                                                                    startRow: rowIndex,
                                                                    startCol: colIndex,
                                                                    endRow: rowIndex,
                                                                    endCol: colIndex
                                                                });
                                                            }
                                                        }}
                                                        onDoubleClick={() => {
                                                            setIsEditing(true);
                                                            setActiveCell({ row: rowIndex, col: colIndex });
                                                            // Set raw value or formula
                                                            setEditValue(cell.formula ? `=${cell.formula}` : cell.value);
                                                        }}
                                                        className={cn(
                                                            "whitespace-nowrap p-0 px-2 h-7 border-r border-b last:border-r-0 font-normal text-xs cursor-default relative select-none",
                                                            isRangeSelected && !isActive ? "bg-green-50/50 dark:bg-green-400/10" : "",
                                                            isActive && isRangeSelected && !isCellEditing ? "bg-green-50/50 dark:bg-green-400/10" : "",
                                                            isActive && !isCellEditing ? "ring-2 ring-green-600 ring-inset z-10" : ""
                                                        )}
                                                    >
                                                        {isCellEditing ? (
                                                            <input
                                                                autoFocus
                                                                value={editValue}
                                                                onChange={(e) => setEditValue(e.target.value)}
                                                                onBlur={() => commitEdit(rowIndex, colIndex, editValue)}
                                                                onKeyDown={(e) => {
                                                                    if (e.key === 'Enter') { // Don't allow new lines in simple cell
                                                                        e.preventDefault();
                                                                        commitEdit(rowIndex, colIndex, editValue);
                                                                    }
                                                                }}
                                                                className="absolute inset-0 w-full h-full px-2 bg-background text-foreground border-2 border-green-600 z-20 outline-none"
                                                            />
                                                        ) : (
                                                            String(cell.value)
                                                        )}
                                                    </TableCell>
                                                );
                                            })}
                                        </TableRow>
                                    );
                                })}
                            </TableBody>
                        </Table>
                    </div>
                </div>
                <ScrollBar orientation="horizontal" />
                <ScrollBar orientation="vertical" />
            </ScrollArea>

            {/* Sheet Tabs */}
            <div className="flex items-center bg-muted/10 border-t overflow-x-auto h-8 shrink-0">
                {sheets.map((sheet, index) => (
                    <button
                        key={index}
                        onClick={() => setActiveSheetIndex(index)}
                        className={cn(
                            "flex items-center gap-2 px-4 h-full text-[11px] font-medium border-r transition-colors select-none whitespace-nowrap",
                            activeSheetIndex === index
                                ? "bg-background text-green-700 font-semibold border-b-2 border-b-green-600"
                                : "text-muted-foreground hover:bg-muted/30"
                        )}
                    >
                        {activeSheetIndex === index && <TableIcon className="h-3 w-3" />}
                        {sheet.name}
                    </button>
                ))}
            </div>
        </div>
    );
}
