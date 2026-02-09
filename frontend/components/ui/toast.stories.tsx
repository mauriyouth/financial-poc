import type { Meta, StoryObj } from '@storybook/react';
import { Button } from './button';
import { ToastAction } from './toast';
import { Toaster } from './toaster';
import { useToast } from '@/hooks/use-toast';

const ToastDemo = () => {
    const { toast } = useToast();

    return (
        <div className="flex gap-4">
            <Button
                variant="outline"
                onClick={() => {
                    toast({
                        title: "Scheduled: Catch up ",
                        description: "Friday, February 10, 2023 at 5:57 PM",
                    });
                }}
            >
                Show Toast
            </Button>
            <Button
                variant="outline"
                onClick={() => {
                    toast({
                        title: "Uh oh! Something went wrong.",
                        description: "There was a problem with your request.",
                        action: <ToastAction altText="Try again">Try again</ToastAction>,
                    });
                }}
            >
                Show Action Toast
            </Button>
            <Button
                variant="destructive"
                onClick={() => {
                    toast({
                        variant: "destructive",
                        title: "Uh oh! Something went wrong.",
                        description: "There was a problem with your request.",
                        action: <ToastAction altText="Try again">Try again</ToastAction>,
                    });
                }}
            >
                Show Destructive Toast
            </Button>
            <Toaster />
        </div>
    );
};

const meta = {
    title: 'UI/Toast',
    component: ToastDemo,
    tags: ['autodocs'],
} satisfies Meta<typeof ToastDemo>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};
