import type { Meta, StoryObj } from '@storybook/react';
import { Textarea } from './textarea';

const meta = {
    title: 'UI/Textarea',
    component: Textarea,
    tags: ['autodocs'],
    argTypes: {
        disabled: {
            control: 'boolean',
        },
        placeholder: {
            control: 'text',
        },
    },
} satisfies Meta<typeof Textarea>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
    args: {
        placeholder: 'Type your message here.',
    },
};

export const Disabled: Story = {
    args: {
        disabled: true,
        placeholder: 'Type your message here.',
    },
};

export const WithLabel: Story = {
    render: (args) => (
        <div className="grid w-full gap-1.5">
            <label htmlFor="message">Your message</label>
            <Textarea id="message" {...args} />
            <p className="text-sm text-muted-foreground">
                Your message will be copied to the support team.
            </p>
        </div>
    ),
    args: {
        placeholder: 'Type your message here.',
    },
};
