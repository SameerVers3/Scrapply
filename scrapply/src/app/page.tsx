'use client';

import { useState } from 'react';
import { ArrowRight, Globe, Code, TestTube, Sparkles } from 'lucide-react';
import { createScrapingRequest, ScrapingRequest } from '@/lib/api';
import Link from 'next/link';

export default function HomePage() {
  const [url, setUrl] = useState('');
  const [description, setDescription] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleCreateRequest = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!url.trim()) {
      setError('Please enter a URL');
      return;
    }

    if (!description.trim()) {
      setError('Please enter a description');
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      const request: ScrapingRequest = {
        url: url.trim(),
        description: description.trim(),
      };

      const job = await createScrapingRequest(request);
      
      // Redirect to the chatbot interface with the job ID
      window.location.href = `/chatbot?jobId=${job.id}`;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create scraping request');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="relative overflow-hidden bg-gradient-to-br from-blue-50 via-white to-purple-50 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900 min-h-screen flex items-center">
        {/* Animated background elements */}
        <div className="absolute inset-0">
          <div className="absolute top-20 left-10 w-72 h-72 bg-blue-400/10 rounded-full blur-3xl animate-pulse"></div>
          <div className="absolute bottom-20 right-10 w-96 h-96 bg-purple-400/10 rounded-full blur-3xl animate-pulse delay-1000"></div>
          <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-80 h-80 bg-gradient-to-r from-blue-400/5 to-purple-400/5 rounded-full blur-3xl animate-pulse delay-500"></div>
        </div>
        
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24 w-full">
          <div className="text-center">
            <div className="inline-flex items-center space-x-2 bg-gradient-to-r from-primary/20 to-purple-600/20 text-primary px-6 py-3 rounded-full text-sm font-medium mb-8 backdrop-blur-sm border border-primary/20 animate-fade-in">
              <Sparkles className="w-4 h-4 animate-pulse" />
              <span>AI-Powered Web Scraping</span>
            </div>
            
            <h1 className="text-6xl md:text-7xl font-bold text-foreground mb-8 leading-tight animate-fade-in-up">
              Convert Any Website to an
              <span className="bg-gradient-to-r from-primary via-purple-600 to-blue-600 bg-clip-text text-transparent animate-gradient"> API</span>
            </h1>
            
            <p className="text-xl md:text-2xl text-muted-foreground mb-16 max-w-4xl mx-auto leading-relaxed animate-fade-in-up delay-200">
              Describe what data you want to extract, and our AI will create a custom API for you. 
              No coding required. Just tell us what you need.
            </p>


          </div>

          {/* Create Request Form */}
          <div className="max-w-3xl mx-auto animate-fade-in-up delay-300">
            <div className="card shadow-2xl border-0 bg-white/90 backdrop-blur-xl dark:bg-slate-800/90 rounded-3xl overflow-hidden transform hover:scale-105 transition-all duration-300">
              <div className="card-header text-center p-8 bg-gradient-to-r from-primary/5 to-purple-600/5">
                <h2 className="card-title text-2xl font-bold bg-gradient-to-r from-primary to-purple-600 bg-clip-text text-transparent">Create Your Scraping API</h2>
                <p className="card-description text-lg mt-2">Enter a website URL and describe what data you want to extract</p>
              </div>
              
                              <div className="card-content p-8">
                <form onSubmit={handleCreateRequest} className="space-y-8">
                  <div>
                    <label htmlFor="url" className="block text-sm font-semibold text-foreground mb-3">
                      Website URL
                    </label>
                    <input
                      type="url"
                      id="url"
                      value={url}
                      onChange={(e) => setUrl(e.target.value)}
                      placeholder="https://example.com"
                      className="input text-base h-12 border-2 focus:border-primary/50 transition-all duration-200 bg-white/50 backdrop-blur-sm"
                      required
                    />
                  </div>

                  <div>
                    <label htmlFor="description" className="block text-sm font-semibold text-foreground mb-3">
                      What data do you want to extract?
                    </label>
                    <textarea
                      id="description"
                      value={description}
                      onChange={(e) => setDescription(e.target.value)}
                      placeholder="e.g., Extract product names, prices, and ratings from this e-commerce site..."
                      rows={4}
                      className="textarea text-base border-2 focus:border-primary/50 transition-all duration-200 bg-white/50 backdrop-blur-sm resize-none"
                      required
                    />
                  </div>

                  {error && (
                    <div className="bg-gradient-to-r from-red-50 to-red-100 dark:from-red-900/20 dark:to-red-800/20 border-2 border-red-200 dark:border-red-800 text-red-700 dark:text-red-300 rounded-xl p-4 text-sm font-medium backdrop-blur-sm">
                      {error}
                    </div>
                  )}

                  <button
                    type="submit"
                    disabled={isLoading}
                    className="w-full btn btn-primary btn-lg font-medium bg-gradient-to-r from-primary to-purple-600 hover:from-primary/90 hover:to-purple-600/90 transform hover:scale-105 transition-all duration-200 shadow-lg hover:shadow-xl"
                  >
                    {isLoading ? (
                      <>
                        <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                        <span>Creating API...</span>
                      </>
                    ) : (
                      <>
                        <span>Create API</span>
                        <ArrowRight className="w-5 h-5 animate-pulse" />
                      </>
                    )}
                  </button>
                </form>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-32 bg-gradient-to-b from-background to-slate-50 dark:to-slate-900/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-20">
            <h2 className="text-4xl md:text-5xl font-bold text-foreground mb-6 bg-gradient-to-r from-primary to-purple-600 bg-clip-text text-transparent">
              Everything you need to build powerful APIs
            </h2>
            <p className="text-xl text-muted-foreground max-w-3xl mx-auto leading-relaxed">
              From simple data extraction to complex web scraping, we&apos;ve got you covered with cutting-edge AI technology
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-12">
            <div className="group card p-10 text-center hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-2 bg-white/80 backdrop-blur-sm dark:bg-slate-800/80 rounded-3xl border-0">
              <div className="w-20 h-20 bg-gradient-to-br from-blue-100 to-blue-200 dark:from-blue-900/30 dark:to-blue-800/30 rounded-3xl flex items-center justify-center mx-auto mb-8 group-hover:scale-110 transition-transform duration-300">
                <Globe className="w-10 h-10 text-blue-600" />
              </div>
              <h3 className="text-2xl font-bold text-foreground mb-4">Smart Web Scraping</h3>
              <p className="text-muted-foreground text-lg leading-relaxed">
                Extract data from any website with natural language descriptions. Our AI understands context and adapts to different site structures.
              </p>
            </div>

            <div className="group card p-10 text-center hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-2 bg-white/80 backdrop-blur-sm dark:bg-slate-800/80 rounded-3xl border-0">
              <div className="w-20 h-20 bg-gradient-to-br from-green-100 to-green-200 dark:from-green-900/30 dark:to-green-800/30 rounded-3xl flex items-center justify-center mx-auto mb-8 group-hover:scale-110 transition-transform duration-300">
                <Code className="w-10 h-10 text-green-600" />
              </div>
              <h3 className="text-2xl font-bold text-foreground mb-4">Instant API Generation</h3>
              <p className="text-muted-foreground text-lg leading-relaxed">
                Automatically generate REST APIs from your scraping requirements. Get JSON endpoints ready for production use.
              </p>
            </div>

            <div className="group card p-10 text-center hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-2 bg-white/80 backdrop-blur-sm dark:bg-slate-800/80 rounded-3xl border-0">
              <div className="w-20 h-20 bg-gradient-to-br from-purple-100 to-purple-200 dark:from-purple-900/30 dark:to-purple-800/30 rounded-3xl flex items-center justify-center mx-auto mb-8 group-hover:scale-110 transition-transform duration-300">
                <TestTube className="w-10 h-10 text-purple-600" />
              </div>
              <h3 className="text-2xl font-bold text-foreground mb-4">Test & Iterate</h3>
              <p className="text-muted-foreground text-lg leading-relaxed">
                Test your APIs and refine them through natural language chat. Get instant feedback and make adjustments on the fly.
              </p>
            </div>
          </div>
        </div>
      </section>


    </div>
  );
}
