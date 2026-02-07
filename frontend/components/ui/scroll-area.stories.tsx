import type { Meta, StoryObj } from '@storybook/react';
import { ScrollArea } from './scroll-area';
import { Separator } from './separator';

const meta = {
    title: 'UI/ScrollArea',
    component: ScrollArea,
    tags: ['autodocs'],
    argTypes: {
    },
} satisfies Meta<typeof ScrollArea>;

export default meta;
type Story = StoryObj<typeof meta>;

const tags = Array.from({ length: 50 }).map(
    (_, i, a) => `v1.2.0-beta.${a.length - i}`
);

export const Default: Story = {
    render: (args) => (
        <ScrollArea className="h-72 w-48 rounded-md border" {...args}>
            <div className="p-4">
                <h4 className="mb-4 text-sm font-medium leading-none">Tags</h4>
                {tags.map((tag) => (
                    <div key={tag}>
                        <div className="text-sm">
                            {tag}
                        </div>
                        <Separator className="my-2" />
                    </div>
                ))}
            </div>
        </ScrollArea>
    ),
};

export const Horizontal: Story = {
    render: (args) => (
        <ScrollArea className="w-96 whitespace-nowrap rounded-md border" {...args}>
            <div className="flex w-max space-x-4 p-4">
                {
                    [1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((artwork) => (
                        <div key={artwork} className="shrink-0">
                            <div className="overflow-hidden rounded-md">
                                <div
                                    className="aspect-[3/4] h-fit w-fit object-cover bg-gray-100 dark:bg-gray-800 flex items-center justify-center text-4xl"
                                    style={{ width: 150, height: 200 }}
                                >
                                    {artwork}
                                </div>
                            </div>
                        </div>
                    ))
                }
            </div>
        </ScrollArea>
    ),
};
