'use client';

import { useState, useEffect, useRef } from 'react';
import { useSearchParams } from 'next/navigation';
import { Send, Bot, User, Play, TestTube, Code, Clock, CheckCircle, XCircle, Wifi, WifiOff, MessageSquare, Zap } from 'lucide-react';
import { getJobStatus, testApiEndpoint, executeApiEndpoint, JobResponse } from '@/lib/api';
import { ChatMessage, generateMessageId } from '@/lib/chatbot';
import { useJobStream } from '@/lib/sse';

export default function ChatbotPage() {
  const searchParams = useSearchParams();
  const jobId = searchParams.get('jobId');
  
  const [initialJob, setInitialJob] = useState<JobResponse | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [testResult, setTestResult] = useState<any>(null);
  const [showTestResult, setShowTestResult] = useState(false);
  const [isClient, setIsClient] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Ensure we're on client side
  useEffect(() => {
    setIsClient(true);
  }, []);

  // Use SSE for real-time updates (only on client side)
  const { job: streamJob, isConnected, error: streamError, usePolling } = useJobStream({
    jobId: isClient ? jobId : null,
    onUpdate: (jobUpdate) => {
      // Update messages based on job status changes
      updateMessagesForJobStatus(jobUpdate);
    },
    onError: (error) => {
      console.error('SSE Error:', error);
    },
    onComplete: () => {
      console.log('Job stream completed');
    }
  });

  // Use the stream job if available, otherwise use initial job
  const job = streamJob || initialJob;

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (jobId) {
      fetchInitialJob();
    } else {
      setIsLoading(false);
      // Show welcome message for new users
      setMessages([
        {
          id: generateMessageId(),
          type: 'assistant',
          content: 'Welcome! I\'m here to help you create and manage your scraping APIs. Start by creating a new scraping request from the home page, or let me know what you\'d like to do.',
          timestamp: new Date(),
        },
      ]);
    }
  }, [jobId]);

  const fetchInitialJob = async () => {
    if (!jobId) return;
    
    try {
      const jobData = await getJobStatus(jobId);
      setInitialJob(jobData);
      
      // Set initial messages based on job status
      updateMessagesForJobStatus(jobData);
      
      setIsLoading(false);
    } catch (error) {
      console.error('Failed to fetch initial job status:', error);
      setIsLoading(false);
    }
  };

  const updateMessagesForJobStatus = (jobData: JobResponse) => {
    // Only update messages if we don't have any yet or if status changed significantly
    if (messages.length === 0 || 
        (messages.length === 1 && messages[0].content.includes('working on'))) {
      
      if (jobData.status === 'ready') {
        setMessages([
          {
            id: generateMessageId(),
            type: 'assistant',
            content: `🎉 Your API is ready! I've successfully created a scraping API for ${jobData.url}.\n\nHere's what I extracted:\n${jobData.description}\n\nYou can now test the API or ask me to modify it. Try saying:\n• "Test the API" - to see sample data\n• "Show me the endpoint" - to get the API URL\n• "Add more fields" - to modify the extraction`,
            timestamp: new Date(),
          },
        ]);
      } else if (jobData.status === 'failed') {
        setMessages([
          {
            id: generateMessageId(),
            type: 'assistant',
            content: `❌ I encountered an issue while creating your API for ${jobData.url}.\n\nError: ${jobData.message || 'Unknown error'}\n\nWould you like me to:\n• Retry the job\n• Try a different approach\n• Help you modify the request`,
            timestamp: new Date(),
          },
        ]);
      } else if (['pending', 'analyzing', 'generating', 'testing'].includes(jobData.status)) {
        setMessages([
          {
            id: generateMessageId(),
            type: 'assistant',
            content: `🔄 I'm working on creating your API for ${jobData.url}...\n\nCurrent status: ${jobData.status}\nProgress: ${jobData.progress}%\n\nThis usually takes 1-2 minutes. I'll let you know when it's ready!`,
            timestamp: new Date(),
          },
        ]);
      }
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!inputValue.trim() || isProcessing) return;

    const userMessage: ChatMessage = {
      id: generateMessageId(),
      type: 'user',
      content: inputValue.trim(),
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsProcessing(true);

    try {
      // Simple command parsing for now
      const command = inputValue.toLowerCase().trim();
      let response = '';

      if (command.includes('test') || command.includes('sample')) {
        if (job && job.status === 'ready') {
          const result = await testApiEndpoint(job.id);
          setTestResult(result);
          setShowTestResult(true);
          response = 'Here\'s a sample of your API data:';
        } else {
          response = 'The API is not ready yet. Please wait for it to complete processing.';
        }
      } else if (command.includes('endpoint') || command.includes('url')) {
        if (job && job.api_endpoint_path) {
          response = `Your API endpoint is:\n\`${job.api_endpoint_path}\`\n\nYou can use this URL to make requests to your API.`;
        } else {
          response = 'The API endpoint is not available yet. Please wait for processing to complete.';
        }
      } else if (command.includes('execute') || command.includes('run')) {
        if (job && job.status === 'ready') {
          const result = await executeApiEndpoint(job.id);
          setTestResult(result);
          setShowTestResult(true);
          response = 'Here\'s the full API response:';
        } else {
          response = 'The API is not ready yet. Please wait for it to complete processing.';
        }
      } else {
        response = 'I understand you want to modify the API. This feature is coming soon! For now, you can:\n• Test the API\n• View the endpoint\n• Execute the API';
      }

      const assistantMessage: ChatMessage = {
        id: generateMessageId(),
        type: 'assistant',
        content: response,
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      const errorMessage: ChatMessage = {
        id: generateMessageId(),
        type: 'assistant',
        content: `Sorry, I encountered an error: ${error instanceof Error ? error.message : 'Unknown error'}`,
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsProcessing(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-background">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading your API...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-background">
      {/* Sidebar with past requests */}
      <div className="w-80 bg-card border-r border-border flex flex-col">
        <div className="p-6 border-b border-border">
          <div className="flex items-center space-x-3 mb-2">
            <div className="w-8 h-8 bg-primary/10 rounded-lg flex items-center justify-center">
              <MessageSquare className="w-4 h-4 text-primary" />
            </div>
            <h2 className="text-lg font-semibold text-foreground">Your APIs</h2>
          </div>
          <p className="text-sm text-muted-foreground">Recent scraping requests</p>
        </div>
        
        <div className="flex-1 overflow-y-auto p-4">
          {job ? (
            <div className="card bg-primary/5 border-primary/20 p-4 mb-4">
              <div className="flex items-center justify-between mb-2">
                <h3 className="font-medium text-foreground truncate">{job.url}</h3>
                <div className="flex items-center space-x-1">
                  {job.status === 'ready' ? (
                    <CheckCircle className="w-4 h-4 text-green-500" />
                  ) : job.status === 'failed' ? (
                    <XCircle className="w-4 h-4 text-red-500" />
                  ) : (
                    <Clock className="w-4 h-4 text-yellow-500" />
                  )}
                  {isClient && (
                    usePolling ? (
                      <div className="w-3 h-3 bg-orange-500 rounded-full animate-pulse" title="Using polling fallback" />
                    ) : isConnected ? (
                      <Wifi className="w-3 h-3 text-green-500" title="SSE connected" />
                    ) : (
                      <WifiOff className="w-3 h-3 text-red-500" title="SSE disconnected" />
                    )
                  )}
                </div>
              </div>
              <p className="text-sm text-muted-foreground mb-2">{job.description}</p>
              <div className="text-xs text-primary">
                Status: {job.status} • {job.progress}%
              </div>
              {streamError && (
                <div className="text-xs text-destructive mt-1">
                  Connection error: {streamError}
                </div>
              )}
            </div>
          ) : (
            <div className="text-center text-muted-foreground py-8">
              <Code className="w-8 h-8 mx-auto mb-2 text-muted-foreground" />
              <p>No APIs yet</p>
              <p className="text-sm">Create your first API from the home page</p>
            </div>
          )}
        </div>
      </div>

      {/* Main chat interface */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="bg-card border-b border-border p-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center space-x-3 mb-1">
                <div className="w-8 h-8 bg-primary/10 rounded-lg flex items-center justify-center">
                  <Bot className="w-4 h-4 text-primary" />
                </div>
                <h1 className="text-2xl font-bold text-foreground">API Assistant</h1>
              </div>
              <p className="text-muted-foreground">
                {job ? `Working on: ${job.url}` : 'Create and manage your scraping APIs'}
              </p>
            </div>
            
            {job && job.status === 'ready' && (
              <div className="flex space-x-2">
                <button
                  onClick={async () => {
                    try {
                      const result = await testApiEndpoint(job.id);
                      setTestResult(result);
                      setShowTestResult(true);
                    } catch (error) {
                      console.error('Failed to test API:', error);
                    }
                  }}
                  className="btn btn-outline btn-sm"
                >
                  <TestTube className="w-4 h-4 mr-1" />
                  Test
                </button>
                <button
                  onClick={async () => {
                    try {
                      const result = await executeApiEndpoint(job.id);
                      setTestResult(result);
                      setShowTestResult(true);
                    } catch (error) {
                      console.error('Failed to execute API:', error);
                    }
                  }}
                  className="btn btn-primary btn-sm"
                >
                  <Play className="w-4 h-4 mr-1" />
                  Execute
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`flex items-start space-x-3 max-w-2xl ${
                  message.type === 'user' ? 'flex-row-reverse space-x-reverse' : ''
                }`}
              >
                <div
                  className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                    message.type === 'user'
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-muted text-muted-foreground'
                  }`}
                >
                  {message.type === 'user' ? (
                    <User className="h-4 w-4" />
                  ) : (
                    <Bot className="h-4 w-4" />
                  )}
                </div>
                <div
                  className={`px-4 py-3 rounded-lg text-sm ${
                    message.type === 'user'
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-card border border-border text-foreground'
                  }`}
                >
                  <div className="whitespace-pre-wrap">{message.content}</div>
                </div>
              </div>
            </div>
          ))}
          
          {isProcessing && (
            <div className="flex justify-start">
              <div className="flex items-start space-x-3 max-w-2xl">
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-muted text-muted-foreground flex items-center justify-center">
                  <Bot className="h-4 w-4" />
                </div>
                <div className="px-4 py-3 rounded-lg bg-card border border-border">
                  <div className="flex items-center space-x-1">
                    <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                    <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                  </div>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="bg-card border-t border-border p-6">
          <form onSubmit={handleSubmit} className="flex space-x-4">
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder={job && job.status === 'ready' ? "Ask me to modify the API, test it, or show the endpoint..." : "The API is still processing..."}
              className="input flex-1"
              disabled={!job || job.status !== 'ready'}
            />
            <button
              type="submit"
              disabled={!inputValue.trim() || isProcessing || !job || job.status !== 'ready'}
              className="btn btn-primary"
            >
              <Send className="h-4 w-4" />
            </button>
          </form>
        </div>
      </div>

      {/* Test Result Modal */}
      {showTestResult && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-card rounded-lg p-6 max-w-4xl max-h-[80vh] overflow-auto border border-border">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-foreground">API Result</h3>
              <button
                onClick={() => setShowTestResult(false)}
                className="text-muted-foreground hover:text-foreground"
              >
                ✕
              </button>
            </div>
            <pre className="bg-muted p-4 rounded text-sm overflow-auto font-mono">
              {JSON.stringify(testResult, null, 2)}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}
