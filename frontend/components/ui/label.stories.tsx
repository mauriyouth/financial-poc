import type { Meta, StoryObj } from '@storybook/react';
import { Label } from './label';

const meta = {
    title: 'UI/Label',
    component: Label,
    tags: ['autodocs'],
} satisfies Meta<typeof Label>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
    args: {
        children: 'Accept terms and conditions',
    },
};
