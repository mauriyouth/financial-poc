import type { Meta, StoryObj } from '@storybook/react';
import { Checkbox } from './checkbox';

const meta = {
    title: 'UI/Checkbox',
    component: Checkbox,
    tags: ['autodocs'],
    argTypes: {
        checked: {
            control: 'boolean',
        },
        disabled: {
            control: 'boolean',
        },
    },
} satisfies Meta<typeof Checkbox>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
    args: {
    },
};

export const Checked: Story = {
    args: {
        checked: true,
    },
};

export const Disabled: Story = {
    args: {
        disabled: true,
    },
};

export const DisabledChecked: Story = {
    args: {
        disabled: true,
        checked: true,
    },
};

export const WithLabel: Story = {
    render: (args) => (
        <div className="flex items-center space-x-2">
            <Checkbox id="terms" {...args} />
            <label
                htmlFor="terms"
                className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
            >
                Accept terms and conditions
            </label>
        </div>
    ),
};
