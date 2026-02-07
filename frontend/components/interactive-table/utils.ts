import * as XLSX from 'xlsx';
import React from 'react';

/**
 * Utility functions for interactive table operations
 */

/**
 * Parses table content from React children (ReactMarkdown output)
 * Extracts headers and data rows from table structure
 */
export interface TableCell {
    content: React.ReactNode;
    text: string;
}

/**
 * Parses table content from React children (ReactMarkdown output)
 * Extracts headers and data rows from table structure, preserving React elements
 */
export function parseTableContent(children: React.ReactNode): {
    headers: TableCell[];
    rows: TableCell[][];
} {
    const headers: TableCell[] = [];
    const rows: TableCell[][] = [];

    // Helper to extract text from React nodes recursively
    const extractText = (node: any): string => {
        if (typeof node === 'string') return node;
        if (typeof node === 'number') return String(node);
        if (node === null || node === undefined) return '';

        if (Array.isArray(node)) {
            return node.map(extractText).join('');
        }

        if (React.isValidElement(node)) {
            return extractText((node.props as any).children);
        }

        if (node.props?.children) {
            return extractText(node.props.children);
        }

        return '';
    };

    // Parse table structure
    const processChildren = (elements: any) => {
        const elementArray = Array.isArray(elements) ? elements : [elements];

        elementArray.forEach((element: any) => {
            if (!React.isValidElement(element)) return;

            const key = String(element.key || '');
            const elementProps = (element.props as any);

            // Handle thead
            if (key.startsWith('thead')) {
                const theadChildren = React.Children.toArray(elementProps.children);
                theadChildren.forEach((tr: any) => {
                    if (React.isValidElement(tr)) {
                        const trProps = (tr.props as any);
                        const thElements = React.Children.toArray(trProps.children);
                        thElements.forEach((th: any) => {
                            if (React.isValidElement(th)) {
                                const thProps = (th.props as any);
                                headers.push({
                                    content: thProps.children,
                                    text: extractText(thProps.children).trim()
                                });
                            }
                        });
                    }
                });
            }

            // Handle tbody
            if (key.startsWith('tbody')) {
                const tbodyChildren = React.Children.toArray(elementProps.children);
                tbodyChildren.forEach((tr: any) => {
                    if (React.isValidElement(tr)) {
                        const trProps = (tr.props as any);
                        const row: TableCell[] = [];
                        const tdElements = React.Children.toArray(trProps.children);
                        tdElements.forEach((td: any) => {
                            if (React.isValidElement(td)) {
                                const tdProps = (td.props as any);
                                row.push({
                                    content: tdProps.children,
                                    text: extractText(tdProps.children).trim()
                                });
                            }
                        });
                        if (row.length > 0) {
                            rows.push(row);
                        }
                    }
                });
            }
        });
    };

    processChildren(children);

    return { headers, rows };
}

/**
 * Sorts table data by specified column
 * @param data - Array of rows (each row is an array of strings)
 * @param columnIndex - Index of column to sort by
 * @param direction - Sort direction ('asc' or 'desc')
 * @returns Sorted copy of data
 */
export function sortTableData(
    data: string[][],
    columnIndex: number,
    direction: 'asc' | 'desc'
): string[][] {
    const sortedData = [...data];

    sortedData.sort((a, b) => {
        const aVal = a[columnIndex] || '';
        const bVal = b[columnIndex] || '';

        // Try numeric comparison first
        const aNum = parseFloat(aVal.replace(/[^0-9.-]/g, ''));
        const bNum = parseFloat(bVal.replace(/[^0-9.-]/g, ''));

        if (!isNaN(aNum) && !isNaN(bNum)) {
            // Numeric comparison
            return direction === 'asc' ? aNum - bNum : bNum - aNum;
        }

        // String comparison (case-insensitive)
        const comparison = aVal.toLowerCase().localeCompare(bVal.toLowerCase());
        return direction === 'asc' ? comparison : -comparison;
    });

    return sortedData;
}

/**
 * Exports table data to Excel format
 * @param headers - Array of column headers
 * @param data - Array of data rows
 * @param filename - Name for the downloaded file
 */
export function exportToExcel(
    headers: string[],
    data: string[][],
    filename: string = 'table-export'
): void {
    // Create worksheet data (headers + rows)
    const wsData = [headers, ...data];

    // Create worksheet
    const ws = XLSX.utils.aoa_to_sheet(wsData);

    // Set column widths based on content
    const colWidths = headers.map((header, i) => {
        const maxLength = Math.max(
            header.length,
            ...data.map(row => (row[i] || '').length)
        );
        return { wch: Math.min(maxLength + 2, 50) }; // Max width 50
    });
    ws['!cols'] = colWidths;

    // Create workbook
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, 'Table Data');

    // Generate timestamp for filename
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
    const fullFilename = `${filename}-${timestamp}.xlsx`;

    // Trigger download
    XLSX.writeFile(wb, fullFilename);
}

/**
 * Filters columns from data based on hidden columns set
 */
export function filterVisibleColumns<T>(
    data: T[],
    hiddenColumns: Set<number>
): T[] {
    return data.map((row) => {
        if (Array.isArray(row)) {
            return row.filter((_, index) => !hiddenColumns.has(index)) as T;
        }
        return row;
    });
}
