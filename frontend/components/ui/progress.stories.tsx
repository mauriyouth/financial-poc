import type { Meta, StoryObj } from '@storybook/react';
import { Progress } from './progress';

const meta = {
    title: 'UI/Progress',
    component: Progress,
    tags: ['autodocs'],
    argTypes: {
        value: {
            control: { type: 'range', min: 0, max: 100 },
        },
    },
} satisfies Meta<typeof Progress>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
    args: {
        value: 60,
    },
};

export const Zero: Story = {
    args: {
        value: 0,
    },
};

export const Complete: Story = {
    args: {
        value: 100,
    },
};
