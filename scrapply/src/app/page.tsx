'use client';

import { useState } from 'react';
import { ArrowRight, Globe, Code, TestTube, Sparkles, BarChart3 } from 'lucide-react';
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
      <section className="relative overflow-hidden bg-gradient-to-br from-blue-50 via-white to-purple-50 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900">
        <div className="absolute inset-0 bg-grid-pattern opacity-5"></div>
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-32">
          <div className="text-center">
            <div className="inline-flex items-center space-x-2 bg-primary/10 text-primary px-6 py-3 rounded-full text-sm font-medium mb-10 shadow-lg backdrop-blur-sm">
              <Sparkles className="w-5 h-5" />
              <span>AI-Powered Web Scraping</span>
            </div>
            
            <h1 className="text-6xl md:text-7xl font-bold text-foreground mb-8 leading-tight">
              Convert Any Website to an
              <span className="bg-gradient-to-r from-primary to-purple-600 bg-clip-text text-transparent"> API</span>
            </h1>
            
            <p className="text-xl md:text-2xl text-muted-foreground mb-16 max-w-4xl mx-auto leading-relaxed">
              Describe what data you want to extract, and our AI will create a custom API for you. 
              No coding required. Just tell us what you need.
            </p>
          </div>

          {/* Create Request Form */}
          <div className="max-w-3xl mx-auto">
            <div className="card shadow-2xl border-0 bg-white/90 backdrop-blur-md dark:bg-slate-800/90 rounded-2xl overflow-hidden">
              <div className="card-header text-center p-8 border-b border-border/50">
                <h2 className="card-title text-2xl mb-3">Create Your Scraping API</h2>
                <p className="card-description text-muted-foreground">Enter a website URL and describe what data you want to extract</p>
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
                      className="input text-base w-full h-12 px-4 rounded-xl border-2 border-border focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all"
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
                      className="textarea text-base w-full px-4 py-3 rounded-xl border-2 border-border focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all resize-none"
                      required
                    />
                  </div>

                  {error && (
                    <div className="bg-destructive/10 border-2 border-destructive/20 text-destructive rounded-xl p-4 text-sm">
                      {error}
                    </div>
                  )}

                  <button
                    type="submit"
                    disabled={isLoading}
                    className="w-full btn btn-primary btn-lg font-semibold h-14 text-lg rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-[1.02]"
                  >
                    {isLoading ? (
                      <>
                        <div className="w-6 h-6 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                        <span>Creating API...</span>
                      </>
                    ) : (
                      <>
                        <span>Create API</span>
                        <ArrowRight className="w-6 h-6" />
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
      <section className="py-32 bg-background">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-20">
            <h2 className="text-4xl md:text-5xl font-bold text-foreground mb-6">Everything you need to build powerful APIs</h2>
            <p className="text-xl text-muted-foreground max-w-3xl mx-auto leading-relaxed">
              From simple data extraction to complex web scraping, we&apos;ve got you covered
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-10">
            <div className="card p-10 text-center hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-2 rounded-2xl border-0 bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20">
              <div className="w-20 h-20 bg-blue-100 dark:bg-blue-900/30 rounded-3xl flex items-center justify-center mx-auto mb-8 shadow-lg">
                <Globe className="w-10 h-10 text-blue-600" />
              </div>
              <h3 className="text-2xl font-bold text-foreground mb-4">Smart Web Scraping</h3>
              <p className="text-muted-foreground text-lg leading-relaxed">
                Extract data from any website with natural language descriptions. Our AI understands context and adapts to different site structures.
              </p>
            </div>

            <div className="card p-10 text-center hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-2 rounded-2xl border-0 bg-gradient-to-br from-green-50 to-green-100 dark:from-green-900/20 dark:to-green-800/20">
              <div className="w-20 h-20 bg-green-100 dark:bg-green-900/30 rounded-3xl flex items-center justify-center mx-auto mb-8 shadow-lg">
                <Code className="w-10 h-10 text-green-600" />
              </div>
              <h3 className="text-2xl font-bold text-foreground mb-4">Instant API Generation</h3>
              <p className="text-muted-foreground text-lg leading-relaxed">
                Automatically generate REST APIs from your scraping requirements. Get JSON endpoints ready for production use.
              </p>
            </div>

            <div className="card p-10 text-center hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-2 rounded-2xl border-0 bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-900/20 dark:to-purple-800/20">
              <div className="w-20 h-20 bg-purple-100 dark:bg-purple-900/30 rounded-3xl flex items-center justify-center mx-auto mb-8 shadow-lg">
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

      {/* CTA Section */}
      <section className="py-20 bg-gradient-to-r from-primary to-purple-600">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">Ready to get started?</h2>
          <p className="text-xl md:text-2xl text-blue-100 mb-10 leading-relaxed">
            Join thousands of developers who are already using Scrapply to build powerful APIs
          </p>
          <div className="flex flex-col sm:flex-row gap-6 justify-center">
            <Link
              href="/dashboard"
              className="btn btn-secondary btn-lg text-lg px-8 py-4 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105"
            >
              <BarChart3 className="w-6 h-6 mr-3" />
              View All APIs
            </Link>
            <Link
              href="/settings"
              className="btn btn-outline btn-lg text-lg px-8 py-4 rounded-xl text-white border-2 border-white hover:bg-white hover:text-primary shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105"
            >
              Settings
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
