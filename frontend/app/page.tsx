"use client";

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Sparkles, Upload, MessageSquare } from 'lucide-react';
import { createConversation } from '@/lib/api/chat';
import { DocumentMetadata } from '@/lib/api/documents';
import { ChatInput, DataSource } from '@/components/chat-input';

export default function HomePage() {
  const router = useRouter();
  const [prompt, setPrompt] = useState("");
  const [dataSource, setDataSource] = useState<DataSource>('knowledge');
  const [model, setModel] = useState<string>("anthropic");
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);

  const handleStartChat = async (message: string, attachments?: DocumentMetadata[]) => {
    if (!message.trim() && !attachments?.length) return;

    try {
      // Create conversation
      const conversation = await createConversation();

      // Store prompt and files in localStorage for chat page to pick up
      localStorage.setItem('pendingMessage', JSON.stringify({
        content: message,
        files: attachments || [],
        model: model, // Save selected model
        agent: selectedAgent // Save selected agent
      }));

      // Navigate to chat
      router.push(`/chat?id=${conversation.id}`);
    } catch (error) {
      console.error("Failed to start chat", error);
    }
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-br from-slate-50 via-blue-50 to-purple-50 dark:from-slate-950 dark:via-blue-950 dark:to-purple-950 p-6">
      <div className="w-full max-w-4xl space-y-8 animate-in fade-in duration-700">
        {/* Hero Section */}
        <div className="text-center space-y-4">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-purple-500 to-blue-500 text-white rounded-full text-sm font-medium shadow-lg">
            <Sparkles className="h-4 w-4" />
            AI-Powered Enterprise Platform
          </div>
          <h1 className="text-5xl md:text-6xl font-bold bg-gradient-to-r from-purple-600 via-blue-600 to-purple-600 bg-clip-text text-transparent">
            Financial AI Assistant
          </h1>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            Start a conversation with your intelligent assistant. Upload documents, ask questions, and get instant insights.
          </p>
        </div>

        {/* Main Input Area with ChatInput */}
        <div className="bg-card border-2 border-primary/20 rounded-2xl shadow-2xl p-6">
          <ChatInput
            value={prompt}
            onChange={setPrompt}
            onSend={handleStartChat}
            placeholder="What would you like to know? (e.g., 'Analyze my financial data and provide insights...')"
            showDataSourceSelector={true}
            dataSource={dataSource}
            onDataSourceChange={setDataSource}
            model={model}
            onModelChange={setModel}
            selectedAgent={selectedAgent}
            onAgentChange={setSelectedAgent}
          />
        </div>

        {/* Features */}
        <div className="grid md:grid-cols-3 gap-6 pt-8">
          <div className="text-center space-y-2">
            <div className="mx-auto w-12 h-12 bg-purple-100 dark:bg-purple-900/20 rounded-xl flex items-center justify-center">
              <Sparkles className="h-6 w-6 text-purple-600" />
            </div>
            <h3 className="font-semibold">AI-Enhanced Prompts</h3>
            <p className="text-sm text-muted-foreground">Automatically improve your questions for better results</p>
          </div>
          <div className="text-center space-y-2">
            <div className="mx-auto w-12 h-12 bg-blue-100 dark:bg-blue-900/20 rounded-xl flex items-center justify-center">
              <Upload className="h-6 w-6 text-blue-600" />
            </div>
            <h3 className="font-semibold">Document Analysis</h3>
            <p className="text-sm text-muted-foreground">Upload and analyze your financial documents</p>
          </div>
          <div className="text-center space-y-2">
            <div className="mx-auto w-12 h-12 bg-green-100 dark:bg-green-900/20 rounded-xl flex items-center justify-center">
              <MessageSquare className="h-6 w-6 text-green-600" />
            </div>
            <h3 className="font-semibold">Real-time Insights</h3>
            <p className="text-sm text-muted-foreground">Get instant, intelligent responses with extended thinking</p>
          </div>
        </div>
      </div>
    </div>
  );
}
