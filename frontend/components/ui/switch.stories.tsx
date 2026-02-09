import type { Meta, StoryObj } from '@storybook/react';
import { Switch } from './switch';

const meta = {
    title: 'UI/Switch',
    component: Switch,
    tags: ['autodocs'],
    argTypes: {
        checked: {
            control: 'boolean',
        },
        disabled: {
            control: 'boolean',
        },
    },
} satisfies Meta<typeof Switch>;

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
            <Switch id="airplane-mode" {...args} />
            <label htmlFor="airplane-mode">Airplane Mode</label>
        </div>
    ),
}
