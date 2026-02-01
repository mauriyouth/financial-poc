import type { Meta, StoryObj } from '@storybook/react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from './card';

const meta = {
    title: 'UI/Card',
    component: Card,
    tags: ['autodocs'],
} satisfies Meta<typeof Card>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
    render: () => (
        <Card className="w-[350px]">
            <CardHeader>
                <CardTitle>Create project</CardTitle>
                <CardDescription>Deploy your new project in one-click.</CardDescription>
            </CardHeader>
            <CardContent>
                <p>Your project content goes here.</p>
            </CardContent>
            <CardFooter className="flex justify-between">
                <button className="text-sm font-medium">Cancel</button>
                <button className="text-sm font-medium bg-primary text-primary-foreground px-4 py-2 rounded">Deploy</button>
            </CardFooter>
        </Card>
    ),
};
