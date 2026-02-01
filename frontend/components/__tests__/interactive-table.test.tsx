import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { InteractiveTable } from '../interactive-table';
import * as utils from '../interactive-table/utils';

// Mock the xlsx library
jest.mock('xlsx', () => ({
    utils: {
        aoa_to_sheet: jest.fn(),
        book_new: jest.fn(() => ({})),
        book_append_sheet: jest.fn(),
    },
    writeFile: jest.fn(),
}));

describe('InteractiveTable', () => {
    const mockTableChildren = (
        <>
            <thead>
                <tr>
                    <th>Name</th>
                    <th>Age</th>
                    <th>City</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>Alice</td>
                    <td>30</td>
                    <td>New York</td>
                </tr>
                <tr>
                    <td>Bob</td>
                    <td>25</td>
                    <td>London</td>
                </tr>
                <tr>
                    <td>Charlie</td>
                    <td>35</td>
                    <td>Paris</td>
                </tr>
            </tbody>
        </>
    );

    describe('Rendering', () => {
        it('renders table with headers and data', () => {
            render(<InteractiveTable>{mockTableChildren}</InteractiveTable>);

            expect(screen.getByText('Name')).toBeInTheDocument();
            expect(screen.getByText('Age')).toBeInTheDocument();
            expect(screen.getByText('City')).toBeInTheDocument();
            expect(screen.getByText('Alice')).toBeInTheDocument();
            expect(screen.getByText('Bob')).toBeInTheDocument();
        });

        it('shows toolbar with correct row and column counts', () => {
            render(<InteractiveTable>{mockTableChildren}</InteractiveTable>);

            expect(screen.getByText(/3 columns × 3 rows/)).toBeInTheDocument();
        });

        it('displays column visibility button', () => {
            render(<InteractiveTable>{mockTableChildren}</InteractiveTable>);

            expect(screen.getByText('Columns')).toBeInTheDocument();
        });

        it('displays Excel export button', () => {
            render(<InteractiveTable>{mockTableChildren}</InteractiveTable>);

            expect(screen.getByText('Excel')).toBeInTheDocument();
        });
    });

    describe('Sorting', () => {
        it('sorts ascending when clicking header first time', () => {
            render(<InteractiveTable>{mockTableChildren}</InteractiveTable>);

            const nameHeader = screen.getByText('Name');
            fireEvent.click(nameHeader);

            // Check order: Alice, Bob, Charlie
            const cells = screen.getAllByRole('cell');
            expect(cells[0]).toHaveTextContent('Alice');
            expect(cells[3]).toHaveTextContent('Bob');
            expect(cells[6]).toHaveTextContent('Charlie');
        });

        it('shows clear sort button when sorted', () => {
            render(<InteractiveTable>{mockTableChildren}</InteractiveTable>);

            const nameHeader = screen.getByText('Name');
            fireEvent.click(nameHeader);

            expect(screen.getByText('Clear Sort')).toBeInTheDocument();
        });
    });

    describe('Column Visibility', () => {
        it('hides column when unchecked in menu', () => {
            render(<InteractiveTable>{mockTableChildren}</InteractiveTable>);

            const columnsButton = screen.getByText('Columns');
            fireEvent.click(columnsButton);

            // Find and click City checkbox to hide it
            const cityCheckbox = screen.getByRole('menuitemcheckbox', { name: /City/ });
            fireEvent.click(cityCheckbox);

            // City column should be hidden
            expect(screen.queryByText('Paris')).not.toBeInTheDocument();
            expect(screen.queryByText('London')).not.toBeInTheDocument();
        });

        it('updates visible column count after hiding columns', () => {
            render(<InteractiveTable>{mockTableChildren}</InteractiveTable>);

            const columnsButton = screen.getByText('Columns');
            fireEvent.click(columnsButton);

            const cityCheckbox = screen.getByRole('menuitemcheckbox', { name: /City/ });
            fireEvent.click(cityCheckbox);

            expect(screen.getByText(/2 columns × 3 rows/)).toBeInTheDocument();
        });
    });

    describe('Excel Export', () => {
        it('calls export function when Excel button clicked', () => {
            const exportSpy = jest.spyOn(utils, 'exportToExcel');

            render(<InteractiveTable>{mockTableChildren}</InteractiveTable>);

            const excelButton = screen.getByText('Excel');
            fireEvent.click(excelButton);

            expect(exportSpy).toHaveBeenCalled();
        });
    });
});

describe('Utility Functions', () => {
    describe('sortTableData', () => {
        it('sorts strings ascending', () => {
            const data = [['Charlie'], ['Alice'], ['Bob']];
            const sorted = utils.sortTableData(data, 0, 'asc');

            expect(sorted[0][0]).toBe('Alice');
            expect(sorted[1][0]).toBe('Bob');
            expect(sorted[2][0]).toBe('Charlie');
        });

        it('sorts strings descending', () => {
            const data = [['Alice'], ['Bob'], ['Charlie']];
            const sorted = utils.sortTableData(data, 0, 'desc');

            expect(sorted[0][0]).toBe('Charlie');
            expect(sorted[1][0]).toBe('Bob');
            expect(sorted[2][0]).toBe('Alice');
        });

        it('sorts numbers ascending', () => {
            const data = [['30'], ['10'], ['20']];
            const sorted = utils.sortTableData(data, 0, 'asc');

            expect(sorted[0][0]).toBe('10');
            expect(sorted[1][0]).toBe('20');
            expect(sorted[2][0]).toBe('30');
        });

        it('sorts numbers descending', () => {
            const data = [['10'], ['20'], ['30']];
            const sorted = utils.sortTableData(data, 0, 'desc');

            expect(sorted[0][0]).toBe('30');
            expect(sorted[1][0]).toBe('20');
            expect(sorted[2][0]).toBe('10');
        });
    });

    describe('filterVisibleColumns', () => {
        it('filters out hidden columns', () => {
            const data = [
                ['A', 'B', 'C'],
                ['1', '2', '3'],
            ];
            const hiddenColumns = new Set([1]); // Hide column B

            const filtered = utils.filterVisibleColumns(data, hiddenColumns);

            expect(filtered).toEqual([
                ['A', 'C'],
                ['1', '3'],
            ]);
        });

        it('returns all columns when none hidden', () => {
            const data = [
                ['A', 'B', 'C'],
                ['1', '2', '3'],
            ];
            const hiddenColumns = new Set<number>();

            const filtered = utils.filterVisibleColumns(data, hiddenColumns);

            expect(filtered).toEqual(data);
        });
    });
});
