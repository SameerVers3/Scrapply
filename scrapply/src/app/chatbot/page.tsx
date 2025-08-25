'use client';

import { Suspense, useCallback, useEffect, useRef, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { Bot, User, Play, TestTube, Code, Clock, CheckCircle, XCircle, MessageSquare, Send } from 'lucide-react';
import { getJobStatus, testApiEndpoint, executeApiEndpoint, JobResponse, sendIntelligentChatMessage } from '@/lib/api';
import { ChatMessage, generateMessageId } from '@/lib/chatbot';
import { useJobStream } from '@/lib/sse';
import { useToast } from '@/components/Toast';

function ChatbotPageInner() {
  const searchParams = useSearchParams();
  const jobId = searchParams.get('jobId');
  
  const [initialJob, setInitialJob] = useState<JobResponse | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [testResult, setTestResult] = useState<unknown>(null);
  const [showTestResult, setShowTestResult] = useState(false);
  const [isClient, setIsClient] = useState(false);
  const [isTesting, setIsTesting] = useState(false);
  const [isExecuting, setIsExecuting] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { success, error, info, ToastContainer } = useToast();

  // Ensure we're on client side
  useEffect(() => {
    setIsClient(true);
  }, []);

  // Use SSE for real-time updates (only on client side)
  const { job: streamJob, isConnected, error: streamError, usePolling } = useJobStream({
    jobId: isClient ? jobId : null,
    onUpdate: (jobUpdate) => {
      console.log('📦 SSE Update received:', jobUpdate);
      // Update messages based on job status changes
      updateMessagesForJobStatus(jobUpdate);
      // Set loading to false when we receive first update
      setIsLoading(false);
      // Ensure initial job data is preserved if SSE doesn't include url/description
      if (initialJob && (!jobUpdate.url || !jobUpdate.description)) {
        setInitialJob(prevJob => prevJob ? {
          ...prevJob,
          ...jobUpdate,
          url: prevJob.url || jobUpdate.url,
          description: prevJob.description || jobUpdate.description
        } : jobUpdate);
      }
    },
    onError: (error) => {
      console.error('SSE Error:', error);
      setIsLoading(false); // Stop loading on error
    },
    onComplete: () => {
      console.log('Job stream completed');
      setIsLoading(false); // Stop loading when complete
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

  const updateMessagesForJobStatus = useCallback((jobData: JobResponse) => {
    setMessages(prev => {
      // Handle completion/failure FIRST - always replace any existing processing message
      if (jobData.status === 'ready') {
        return [
          {
            id: generateMessageId(),
            type: 'assistant',
            content: `🎉 Your API is ready! I've successfully created a scraping API for ${jobData.url}.\n\nHere's what I extracted:\n${jobData.description}\n\nYou can now test the API or ask me to modify it. Try saying:\n• "Test the API" - to see sample data\n• "Show me the endpoint" - to get the API URL\n• "Add more fields" - to modify the extraction`,
            timestamp: new Date(),
            isAnimated: false, // No animation for completed jobs
          },
        ];
      }
      if (jobData.status === 'failed') {
        return [
          {
            id: generateMessageId(),
            type: 'assistant',
            content: `❌ I encountered an issue while creating your API for ${jobData.url}.\n\nError: ${jobData.message || 'Unknown error'}\n\nWould you like me to:\n• Retry the job\n• Try a different approach\n• Help you modify the request`,
            timestamp: new Date(),
            isAnimated: false, // No animation for failed jobs
          },
        ];
      }

      // Only update messages if we don't have any yet or if status changed significantly
      if (
        prev.length === 0 ||
        (prev.length === 1 && prev[0].content.includes('working on'))
      ) {
        if (['pending', 'analyzing', 'generating', 'testing'].includes(jobData.status)) {
          const statusMessages = {
            'pending': '� **Getting Started**\n\nI\'m preparing to analyze your website. This should just take a moment!',
            'analyzing': '🔍 **Analyzing Website**\n\nI\'m examining the website structure and figuring out the best way to extract your data...',
            'generating': '⚡ **Creating Your Scraper**\n\nNow I\'m writing custom code tailored specifically for this website. Almost there!',
            'testing': '🧪 **Testing & Validation**\n\nTesting the scraper to make sure it works perfectly and extracts the data you need.'
          };
          
          return [
            {
              id: generateMessageId(),
              type: 'assistant',
              content: statusMessages[jobData.status as keyof typeof statusMessages],
              timestamp: new Date(),
              isAnimated: true, // Add animation flag
            },
          ];
        }
      }
      
      // Update existing status message if it's a processing status
      if (prev.length === 1 && ['pending', 'analyzing', 'generating', 'testing'].includes(jobData.status)) {
        const statusMessages = {
          'pending': '� **Getting Started**\n\nI\'m preparing to analyze your website. This should just take a moment!',
          'analyzing': '🔍 **Analyzing Website**\n\nI\'m examining the website structure and figuring out the best way to extract your data...',
          'generating': '⚡ **Creating Your Scraper**\n\nNow I\'m writing custom code tailored specifically for this website. Almost there!',
          'testing': '🧪 **Testing & Validation**\n\nTesting the scraper to make sure it works perfectly and extracts the data you need.'
        };
        
        return [
          {
            ...prev[0],
            content: statusMessages[jobData.status as keyof typeof statusMessages],
            timestamp: new Date(),
            isAnimated: true, // Add animation flag
          },
        ];
      }
      
      return prev;
    });
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!inputValue.trim() || isProcessing || !jobId) return;

    const userMessageContent = inputValue.trim();
    const userMessage: ChatMessage = {
      id: generateMessageId(),
      type: 'user',
      content: userMessageContent,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsProcessing(true);

    try {
      // Use the intelligent chat API
      const chatResponse = await sendIntelligentChatMessage(jobId, userMessageContent);
      
      // Add the AI response to messages
      const aiMessage: ChatMessage = {
        id: generateMessageId(),
        type: 'assistant',
        content: chatResponse.ai_response,
        timestamp: new Date(),
        isAnimated: false, // AI responses are not animated since they're complete
      };
      
      setMessages(prev => [...prev, aiMessage]);
      
    } catch (error) {
      console.error('Error sending intelligent chat message:', error);
      
      // Fallback to simple responses if intelligent chat fails
      const errorMessage: ChatMessage = {
        id: generateMessageId(),
        type: 'assistant',
        content: `❌ I'm having trouble processing your request right now. Please try again or contact support if the issue persists.`,
        timestamp: new Date(),
      };
      
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsProcessing(false);
    }
  };

  if (isLoading && !job) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-background">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading your API...</p>
          {jobId && (
            <p className="text-sm text-muted-foreground mt-2">Job ID: {jobId}</p>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-gradient-to-br from-slate-50 via-white to-blue-50/30 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900">
      <ToastContainer />
      {/* Sidebar with past requests */}
      <div className="w-80 bg-white/80 dark:bg-slate-800/80 backdrop-blur-xl border-r border-slate-200/50 dark:border-slate-700/50 flex flex-col shadow-xl">
        <div className="p-6 border-b border-slate-200/50 dark:border-slate-700/50 bg-gradient-to-r from-blue-50/50 to-purple-50/50 dark:from-slate-800/50 dark:to-slate-700/50">
          <div className="flex items-center space-x-3 mb-3">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center shadow-lg">
              <MessageSquare className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-slate-800 dark:text-slate-100">Your APIs</h2>
              <p className="text-sm text-slate-600 dark:text-slate-400">Recent scraping requests</p>
            </div>
          </div>
        </div>
        
        <div className="flex-1 overflow-y-auto p-4">
          {job ? (
            <div className="bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 border border-blue-200/50 dark:border-blue-800/50 rounded-xl p-5 mb-4 shadow-lg backdrop-blur-sm">
              <div className="flex items-center justify-between mb-3">
                <div className="flex-1 min-w-0">
                  <h3 className="font-semibold text-slate-800 dark:text-slate-100 truncate text-sm">{job.url}</h3>
                  <p className="text-xs text-slate-600 dark:text-slate-400 mt-1 line-clamp-2">{job.description}</p>
                </div>
                <div className="flex items-center space-x-2 ml-3">
                  {job.status === 'ready' ? (
                    <div className="flex items-center space-x-1">
                      <CheckCircle className="w-4 h-4 text-emerald-500" />
                      <span className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse"></span>
                    </div>
                  ) : job.status === 'failed' ? (
                    <XCircle className="w-4 h-4 text-red-500" />
                  ) : (
                    <div className="flex items-center space-x-1">
                      <Clock className="w-4 h-4 text-amber-500" />
                      <div className="w-2 h-2 bg-amber-400 rounded-full animate-bounce"></div>
                    </div>
                  )}
                  {isClient && (
                    <div className="w-2 h-2 rounded-full" title={usePolling ? "Using polling fallback" : isConnected ? "Real-time connected" : "Disconnected"}>
                      {usePolling ? (
                        <div className="w-2 h-2 bg-orange-400 rounded-full animate-pulse" />
                      ) : isConnected ? (
                        <div className="w-2 h-2 bg-emerald-400 rounded-full" />
                      ) : (
                        <div className="w-2 h-2 bg-red-400 rounded-full" />
                      )}
                    </div>
                  )}
                </div>
              </div>
              
              <div className="space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-slate-600 dark:text-slate-400">Progress</span>
                  <span className="font-medium text-slate-700 dark:text-slate-300">{job.progress}%</span>
                </div>
                <div className="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-2 overflow-hidden">
                  <div 
                    className="h-full bg-gradient-to-r from-blue-500 to-purple-600 rounded-full transition-all duration-500 ease-out"
                    style={{ width: `${job.progress}%` }}
                  />
                </div>
                <div className="flex items-center justify-between mt-3">
                  <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium ${
                    job.status === 'ready' 
                      ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-300'
                      : job.status === 'failed'
                      ? 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300'
                      : 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300'
                  }`}>
                    {job.status}
                  </span>
                  {job.status === 'ready' && (
                    <div className="text-xs text-emerald-600 dark:text-emerald-400 font-medium">✨ Ready to use</div>
                  )}
                </div>
              </div>
              
              {streamError && (
                <div className="mt-3 text-xs text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 p-2 rounded-lg">
                  Connection: {streamError}
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-12">
              <div className="w-16 h-16 bg-gradient-to-br from-slate-100 to-slate-200 dark:from-slate-700 dark:to-slate-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <Code className="w-8 h-8 text-slate-400 dark:text-slate-500" />
              </div>
              <p className="text-slate-600 dark:text-slate-400 font-medium">No APIs yet</p>
              <p className="text-sm text-slate-500 dark:text-slate-500 mt-1">Create your first API from the home page</p>
            </div>
          )}
        </div>
      </div>

      {/* Main chat interface */}
      <div className="flex-1 flex flex-col bg-white/50 dark:bg-slate-800/50 backdrop-blur-sm">
        {/* Header */}
        <div className="bg-white/80 dark:bg-slate-800/80 backdrop-blur-xl border-b border-slate-200/50 dark:border-slate-700/50 p-6 shadow-sm">
          <div className="flex items-center justify-between">
            <div className="flex-1 min-w-0">
              <div className="flex items-center space-x-4 mb-3">
                <div className="w-12 h-12 bg-gradient-to-br from-blue-500 via-purple-600 to-pink-600 rounded-2xl flex items-center justify-center shadow-lg">
                  <Bot className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h1 className="text-2xl font-bold bg-gradient-to-r from-slate-800 to-slate-600 dark:from-slate-100 dark:to-slate-300 bg-clip-text text-transparent">
                    API Assistant
                  </h1>
                  <p className="text-slate-600 dark:text-slate-400 text-sm">
                    {job ? `Working on: ${job.url}` : 'Create and manage your scraping APIs'}
                  </p>
                </div>
              </div>
              
              {job && job.status === 'ready' && job.api_endpoint_path && (
                <div className="bg-gradient-to-r from-emerald-50 to-green-50 dark:from-emerald-900/20 dark:to-green-900/20 border border-emerald-200/50 dark:border-emerald-800/50 rounded-xl p-4 shadow-sm">
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-2 mb-2">
                        <div className="w-6 h-6 bg-emerald-500 rounded-lg flex items-center justify-center">
                          <CheckCircle className="w-4 h-4 text-white" />
                        </div>
                        <p className="text-sm font-semibold text-emerald-800 dark:text-emerald-200">
                          🎉 Your API is ready!
                        </p>
                      </div>
                      <div className="bg-white/60 dark:bg-slate-800/60 rounded-lg p-3 border border-emerald-200/30 dark:border-emerald-700/30">
                        <div className="flex items-center space-x-2">
                          <code className="text-xs font-mono bg-emerald-100 dark:bg-emerald-800/50 text-emerald-800 dark:text-emerald-200 px-2 py-1 rounded flex-1">
                            {`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}${job.api_endpoint_path}`}
                          </code>
                          <button
                            onClick={() => {
                              const apiUrl = `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}${job.api_endpoint_path}`;
                              navigator.clipboard.writeText(apiUrl);
                              success('Copied!', 'API URL copied to clipboard');
                            }}
                            className="p-1.5 bg-emerald-100 hover:bg-emerald-200 dark:bg-emerald-800/50 dark:hover:bg-emerald-700/50 text-emerald-600 dark:text-emerald-400 rounded-lg transition-colors"
                            title="Copy API URL"
                          >
                            📋
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
            
            {job && job.status === 'ready' && (
              <div className="flex space-x-3 ml-6">
                <button
                  onClick={async () => {
                    setIsTesting(true);
                    try {
                      const result = await testApiEndpoint(job.id);
                      setTestResult(result);
                      setShowTestResult(true);
                      success('API Test Successful', 'Your API is working correctly!');
                    } catch (err) {
                      console.error('Failed to test API:', err);
                      error('API Test Failed', err instanceof Error ? err.message : 'Unknown error occurred');
                    } finally {
                      setIsTesting(false);
                    }
                  }}
                  disabled={isTesting || isExecuting}
                  className="inline-flex items-center px-4 py-2.5 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-xl font-medium text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-sm hover:shadow-md"
                >
                  {isTesting ? (
                    <>
                      <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin mr-2"></div>
                      Testing...
                    </>
                  ) : (
                    <>
                      <TestTube className="w-4 h-4 mr-2" />
                      Test API
                    </>
                  )}
                </button>
                <button
                  onClick={async () => {
                    setIsExecuting(true);
                    try {
                      const result = await executeApiEndpoint(job.id);
                      setTestResult(result);
                      setShowTestResult(true);
                      success('API Executed Successfully', 'Fresh data retrieved from your API!');
                    } catch (err) {
                      console.error('Failed to execute API:', err);
                      error('API Execution Failed', err instanceof Error ? err.message : 'Unknown error occurred');
                    } finally {
                      setIsExecuting(false);
                    }
                  }}
                  disabled={isTesting || isExecuting}
                  className="inline-flex items-center px-4 py-2.5 bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white rounded-xl font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-lg hover:shadow-xl"
                >
                  {isExecuting ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                      Executing...
                    </>
                  ) : (
                    <>
                      <Play className="w-4 h-4 mr-2" />
                      Execute API
                    </>
                  )}
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6 bg-gradient-to-b from-transparent to-slate-50/30 dark:to-slate-900/30">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`flex items-start space-x-4 max-w-2xl ${
                  message.type === 'user' ? 'flex-row-reverse space-x-reverse' : ''
                }`}
              >
                <div
                  className={`flex-shrink-0 w-10 h-10 rounded-2xl flex items-center justify-center shadow-lg ${
                    message.type === 'user'
                      ? 'bg-gradient-to-br from-blue-500 to-purple-600 text-white'
                      : 'bg-gradient-to-br from-slate-100 to-slate-200 dark:from-slate-700 dark:to-slate-600 text-slate-600 dark:text-slate-300'
                  }`}
                >
                  {message.type === 'user' ? (
                    <User className="h-5 w-5" />
                  ) : (
                    <Bot className="h-5 w-5" />
                  )}
                </div>
                <div
                  className={`px-6 py-4 rounded-2xl shadow-sm backdrop-blur-sm text-sm leading-relaxed transition-all duration-500 ${
                    message.type === 'user'
                      ? 'bg-gradient-to-br from-blue-500 to-purple-600 text-white shadow-blue-500/20'
                      : 'bg-white/80 dark:bg-slate-800/80 border border-slate-200/50 dark:border-slate-700/50 text-slate-800 dark:text-slate-200 shadow-slate-200/50 dark:shadow-slate-800/50'
                  } ${message.isAnimated ? 'animate-pulse' : ''}`}
                >
                  <div className="whitespace-pre-wrap">
                    {message.content}
                    {message.isAnimated && (
                      <span className="inline-flex ml-2">
                        <div className="flex space-x-1">
                          <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce"></div>
                          <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                          <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                        </div>
                      </span>
                    )}
                  </div>
                  <div className={`text-xs mt-2 opacity-60 ${
                    message.type === 'user' ? 'text-white/70' : 'text-slate-500 dark:text-slate-400'
                  }`}>
                    {message.timestamp.toLocaleTimeString()}
                  </div>
                </div>
              </div>
            </div>
          ))}
          
          {isProcessing && (
            <div className="flex justify-start">
              <div className="flex items-start space-x-4 max-w-2xl">
                <div className="flex-shrink-0 w-10 h-10 rounded-2xl bg-gradient-to-br from-slate-100 to-slate-200 dark:from-slate-700 dark:to-slate-600 text-slate-600 dark:text-slate-300 flex items-center justify-center shadow-lg">
                  <Bot className="h-5 w-5" />
                </div>
                <div className="px-6 py-4 rounded-2xl bg-white/80 dark:bg-slate-800/80 border border-slate-200/50 dark:border-slate-700/50 shadow-sm backdrop-blur-sm">
                  <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-purple-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                    <div className="w-2 h-2 bg-pink-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                    <span className="text-sm text-slate-600 dark:text-slate-400 ml-2">Thinking...</span>
                  </div>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="bg-white/80 dark:bg-slate-800/80 backdrop-blur-xl border-t border-slate-200/50 dark:border-slate-700/50 p-6 shadow-sm">
          <form onSubmit={handleSubmit} className="flex space-x-4">
            <div className="flex-1 relative">
              <input
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                placeholder={job && job.status === 'ready' ? "Ask me to modify the API, test it, or show the endpoint..." : "The API is still processing..."}
                className="w-full px-6 py-4 bg-white/60 dark:bg-slate-700/60 border border-slate-300/50 dark:border-slate-600/50 rounded-2xl text-slate-800 dark:text-slate-200 placeholder-slate-500 dark:placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all duration-200 backdrop-blur-sm shadow-sm"
                disabled={!job || job.status !== 'ready'}
              />
              {inputValue.trim() && (
                <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                </div>
              )}
            </div>
            <button
              type="submit"
              disabled={!inputValue.trim() || isProcessing || !job || job.status !== 'ready'}
              className="px-6 py-4 bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 disabled:from-slate-300 disabled:to-slate-400 dark:disabled:from-slate-600 dark:disabled:to-slate-700 text-white rounded-2xl font-medium disabled:cursor-not-allowed transition-all duration-200 shadow-lg hover:shadow-xl disabled:shadow-sm flex items-center space-x-2"
            >
              {isProcessing ? (
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
              ) : (
                <Send className="h-5 w-5" />
              )}
              <span className="hidden sm:inline">
                {isProcessing ? 'Sending...' : 'Send'}
              </span>
            </button>
          </form>
          {job && job.status !== 'ready' && (
            <div className="mt-3 text-center">
              <p className="text-sm text-slate-500 dark:text-slate-400">
                💭 Your API is being created... You can chat once it's ready!
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Test Result Modal */}
      {showTestResult && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-start justify-center z-50 p-4 overflow-y-auto">
          <div className="bg-white dark:bg-slate-900 rounded-2xl max-w-7xl w-full my-8 shadow-2xl border border-slate-200 dark:border-slate-700">
            {/* Header */}
            <div className="flex items-center justify-between p-6 border-b border-slate-200 dark:border-slate-700 bg-gradient-to-r from-slate-50 to-blue-50 dark:from-slate-800 dark:to-slate-700">
              <div className="flex items-center space-x-4">
                <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center">
                  <Code className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h2 className="text-xl font-bold text-slate-800 dark:text-slate-100">API Documentation</h2>
                  <p className="text-sm text-slate-600 dark:text-slate-400">Live API response and usage examples</p>
                </div>
              </div>
              <button
                onClick={() => setShowTestResult(false)}
                className="w-10 h-10 flex items-center justify-center text-slate-500 hover:text-slate-700 dark:hover:text-slate-300 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-700 transition-all duration-200"
              >
                ✕
              </button>
            </div>

            <div className="flex h-[80vh]">
              {/* Left Panel - API Info */}
              <div className="w-1/2 border-r border-slate-200 dark:border-slate-700 overflow-y-auto">
                <div className="p-6 space-y-6">
                  {/* API Endpoint */}
                  <div>
                    <h3 className="text-lg font-semibold text-slate-800 dark:text-slate-100 mb-3 flex items-center">
                      <div className="w-6 h-6 bg-emerald-100 dark:bg-emerald-900/30 rounded-lg flex items-center justify-center mr-2">
                        <CheckCircle className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
                      </div>
                      API Endpoint
                    </h3>
                    <div className="bg-slate-50 dark:bg-slate-800 rounded-xl p-4 border border-slate-200 dark:border-slate-700">
                      <div className="flex items-center justify-between mb-2">
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300">
                          GET
                        </span>
                        <button
                          onClick={() => {
                            const fullUrl = `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}${job?.api_endpoint_path}`;
                            navigator.clipboard.writeText(fullUrl);
                            success('Copied!', 'API URL copied to clipboard');
                          }}
                          className="text-xs text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
                        >
                          📋 Copy URL
                        </button>
                      </div>
                      <code className="text-sm font-mono text-slate-700 dark:text-slate-300 break-all">
                        {`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}${job?.api_endpoint_path || ''}`}
                      </code>
                    </div>
                  </div>

                  {/* Description */}
                  <div>
                    <h3 className="text-lg font-semibold text-slate-800 dark:text-slate-100 mb-3">Description</h3>
                    <p className="text-slate-600 dark:text-slate-400 text-sm leading-relaxed">
                      {job?.description || 'This API extracts structured data from the specified website.'}
                    </p>
                  </div>

                  {/* cURL Example */}
                  <div>
                    <h3 className="text-lg font-semibold text-slate-800 dark:text-slate-100 mb-3 flex items-center">
                      <div className="w-6 h-6 bg-blue-100 dark:bg-blue-900/30 rounded-lg flex items-center justify-center mr-2">
                        <code className="text-blue-600 dark:text-blue-400 text-xs">$</code>
                      </div>
                      cURL Example
                    </h3>
                    <div className="bg-slate-900 dark:bg-slate-950 rounded-xl p-4 border border-slate-700">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-xs text-slate-400">Terminal</span>
                        <button
                          onClick={() => {
                            const curlCommand = `curl -X GET "${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}${job?.api_endpoint_path || ''}" \\
  -H "Accept: application/json" \\
  -H "Content-Type: application/json"`;
                            navigator.clipboard.writeText(curlCommand);
                            success('Copied!', 'cURL command copied to clipboard');
                          }}
                          className="text-xs text-green-400 hover:text-green-300"
                        >
                          📋 Copy
                        </button>
                      </div>
                      <pre className="text-sm text-green-400 font-mono overflow-x-auto">
{`curl -X GET "${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}${job?.api_endpoint_path || ''}" \\
  -H "Accept: application/json" \\
  -H "Content-Type: application/json"`}
                      </pre>
                    </div>
                  </div>

                  {/* JavaScript Example */}
                  <div>
                    <h3 className="text-lg font-semibold text-slate-800 dark:text-slate-100 mb-3 flex items-center">
                      <div className="w-6 h-6 bg-yellow-100 dark:bg-yellow-900/30 rounded-lg flex items-center justify-center mr-2">
                        <code className="text-yellow-600 dark:text-yellow-400 text-xs">JS</code>
                      </div>
                      JavaScript Example
                    </h3>
                    <div className="bg-slate-900 dark:bg-slate-950 rounded-xl p-4 border border-slate-700">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-xs text-slate-400">fetch</span>
                        <button
                          onClick={() => {
                            const jsCode = `fetch('${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}${job?.api_endpoint_path || ''}')
  .then(response => response.json())
  .then(data => console.log(data))
  .catch(error => console.error('Error:', error));`;
                            navigator.clipboard.writeText(jsCode);
                            success('Copied!', 'JavaScript code copied to clipboard');
                          }}
                          className="text-xs text-green-400 hover:text-green-300"
                        >
                          📋 Copy
                        </button>
                      </div>
                      <pre className="text-sm text-blue-400 font-mono overflow-x-auto">
{`fetch('${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}${job?.api_endpoint_path || ''}')
  .then(response => response.json())
  .then(data => console.log(data))
  .catch(error => console.error('Error:', error));`}
                      </pre>
                    </div>
                  </div>

                  {/* Python Example */}
                  <div>
                    <h3 className="text-lg font-semibold text-slate-800 dark:text-slate-100 mb-3 flex items-center">
                      <div className="w-6 h-6 bg-green-100 dark:bg-green-900/30 rounded-lg flex items-center justify-center mr-2">
                        <code className="text-green-600 dark:text-green-400 text-xs">PY</code>
                      </div>
                      Python Example
                    </h3>
                    <div className="bg-slate-900 dark:bg-slate-950 rounded-xl p-4 border border-slate-700">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-xs text-slate-400">requests</span>
                        <button
                          onClick={() => {
                            const pythonCode = `import requests

response = requests.get('${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}${job?.api_endpoint_path || ''}')
data = response.json()
print(data)`;
                            navigator.clipboard.writeText(pythonCode);
                            success('Copied!', 'Python code copied to clipboard');
                          }}
                          className="text-xs text-green-400 hover:text-green-300"
                        >
                          📋 Copy
                        </button>
                      </div>
                      <pre className="text-sm text-green-400 font-mono overflow-x-auto">
{`import requests

response = requests.get('${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}${job?.api_endpoint_path || ''}')
data = response.json()
print(data)`}
                      </pre>
                    </div>
                  </div>
                </div>
              </div>

              {/* Right Panel - Response */}
              <div className="w-1/2 overflow-y-auto">
                <div className="p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold text-slate-800 dark:text-slate-100 flex items-center">
                      <div className="w-6 h-6 bg-purple-100 dark:bg-purple-900/30 rounded-lg flex items-center justify-center mr-2">
                        <code className="text-purple-600 dark:text-purple-400 text-xs">{'{}'}</code>
                      </div>
                      Live Response
                    </h3>
                    <div className="flex items-center space-x-2">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300">
                        200 OK
                      </span>
                      <button
                        onClick={() => {
                          navigator.clipboard.writeText(JSON.stringify(testResult, null, 2));
                          success('Copied!', 'Response JSON copied to clipboard');
                        }}
                        className="text-xs text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
                      >
                        📋 Copy JSON
                      </button>
                    </div>
                  </div>

                  {testResult ? (
                    <div className="space-y-4">
                      {/* Summary */}
                      <div className="bg-emerald-50 dark:bg-emerald-900/20 border border-emerald-200 dark:border-emerald-800 rounded-xl p-4">
                        <div className="flex items-center space-x-3">
                          <CheckCircle className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
                          <div>
                            <p className="font-semibold text-emerald-800 dark:text-emerald-200">
                              {Array.isArray(testResult) ? `${testResult.length} items found` : 'Data received'}
                            </p>
                            <p className="text-sm text-emerald-600 dark:text-emerald-400">
                              Data successfully extracted from {job?.url}
                            </p>
                          </div>
                        </div>
                      </div>

                      {/* Schema - show for both arrays and objects */}
                      {((Array.isArray(testResult) && testResult.length > 0 && typeof testResult[0] === 'object') || 
                        (!Array.isArray(testResult) && typeof testResult === 'object')) && (
                        <div>
                          <h4 className="font-semibold text-slate-800 dark:text-slate-100 mb-3">Response Schema</h4>
                          <div className="bg-slate-50 dark:bg-slate-800 rounded-xl p-4 border border-slate-200 dark:border-slate-700">
                            <div className="space-y-2">
                              {Object.entries(Array.isArray(testResult) ? testResult[0] : testResult).map(([key, value]) => (
                                <div key={key} className="flex items-center justify-between py-1">
                                  <code className="text-sm font-mono text-blue-600 dark:text-blue-400">{key}</code>
                                  <span className="text-xs px-2 py-1 bg-slate-200 dark:bg-slate-700 rounded text-slate-600 dark:text-slate-400">
                                    {Array.isArray(value) ? 'array' : typeof value}
                                  </span>
                                </div>
                              ))}
                            </div>
                          </div>
                        </div>
                      )}

                      {/* Sample Data Table - only for arrays of objects */}
                      {Array.isArray(testResult) && testResult.length > 0 && typeof testResult[0] === 'object' ? (
                        <div>
                          <h4 className="font-semibold text-slate-800 dark:text-slate-100 mb-3">Sample Data</h4>
                          <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl overflow-hidden">
                            <div className="overflow-x-auto">
                              <table className="w-full text-sm">
                                <thead className="bg-slate-50 dark:bg-slate-700">
                                  <tr>
                                    {Object.keys(testResult[0]).map((key) => (
                                      <th key={key} className="p-3 text-left font-semibold text-slate-700 dark:text-slate-200 border-r border-slate-200 dark:border-slate-600 last:border-r-0">
                                        {key}
                                      </th>
                                    ))}
                                  </tr>
                                </thead>
                                <tbody>
                                  {testResult.slice(0, 3).map((item, index) => (
                                    <tr key={index} className="border-t border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700/50">
                                      {Object.values(item as Record<string, any>).map((value, cellIndex) => (
                                        <td key={cellIndex} className="p-3 border-r border-slate-200 dark:border-slate-700 last:border-r-0">
                                          <div className="max-w-xs truncate text-slate-700 dark:text-slate-300" title={String(value)}>
                                            {value === null ? 'null' : value === undefined ? 'undefined' : String(value)}
                                          </div>
                                        </td>
                                      ))}
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                            </div>
                          </div>
                          {testResult.length > 3 && (
                            <p className="text-sm text-slate-500 dark:text-slate-400 mt-2 text-center">
                              ... and {testResult.length - 3} more items
                            </p>
                          )}
                        </div>
                      ) : (
                        /* Full JSON view for non-tabular data or single objects */
                        <div>
                          <h4 className="font-semibold text-slate-800 dark:text-slate-100 mb-3">Full Response</h4>
                          <div className="bg-slate-900 dark:bg-slate-950 rounded-xl p-4 border border-slate-700">
                            <pre className="text-sm text-green-400 font-mono overflow-auto max-h-96">
                              {JSON.stringify(testResult, null, 2)}
                            </pre>
                          </div>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="text-center py-12">
                      <div className="w-16 h-16 bg-slate-100 dark:bg-slate-700 rounded-2xl flex items-center justify-center mx-auto mb-4">
                        <XCircle className="w-8 h-8 text-slate-400" />
                      </div>
                      <p className="text-slate-600 dark:text-slate-400 mb-4 font-medium">No data returned</p>
                      <div className="bg-slate-900 dark:bg-slate-950 rounded-xl p-4 border border-slate-700">
                        <pre className="text-sm text-green-400 font-mono overflow-auto">
                          {JSON.stringify(testResult, null, 2)}
                        </pre>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function ChatbotPage() {
  return (
    <Suspense
      fallback={
        <div className="flex items-center justify-center min-h-screen bg-background">
          <div className="text-center">
            <div className="w-16 h-16 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-muted-foreground">Loading...</p>
          </div>
        </div>
      }
    >
      <ChatbotPageInner />
    </Suspense>
  );
}
