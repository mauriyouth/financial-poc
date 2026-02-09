import type { Meta, StoryObj } from '@storybook/react';
import { Button } from './button';
import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from './tooltip';

const meta = {
    title: 'UI/Tooltip',
    component: Tooltip,
    tags: ['autodocs'],
    argTypes: {
    },
} satisfies Meta<typeof Tooltip>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
    render: (args) => (
        <TooltipProvider>
            <Tooltip {...args}>
                <TooltipTrigger asChild>
                    <Button variant="outline">Hover</Button>
                </TooltipTrigger>
                <TooltipContent>
                    <p>Add to library</p>
                </TooltipContent>
            </Tooltip>
        </TooltipProvider>
    ),
};
