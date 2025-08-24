'use client';

import { useState } from 'react';
import { ArrowRight, Globe, Code, TestTube, Sparkles, BarChart3, Zap, Shield, Layers } from 'lucide-react';
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
      <section className="relative overflow-hidden bg-gradient-to-br from-blue-50/80 via-white to-purple-50/80 dark:from-slate-900 dark:via-slate-800 dark:to-purple-900/20">
        <div className="absolute inset-0">
          <div className="absolute inset-0 bg-[radial-gradient(#e5e7eb_1px,transparent_1px)] [background-size:16px_16px] [mask-image:radial-gradient(ellipse_50%_50%_at_50%_50%,#000_70%,transparent_100%)] opacity-10"></div>
        </div>
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[800px] bg-gradient-to-r from-blue-400 to-purple-600 rounded-full blur-3xl opacity-10 -translate-y-1/2"></div>
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24">
          <div className="text-center">
            <div className="inline-flex items-center space-x-2 bg-gradient-to-r from-blue-500/10 to-purple-500/10 text-primary px-6 py-2.5 rounded-full text-sm font-medium mb-8 border border-primary/20 backdrop-blur-sm animate-fade-in">
              <Sparkles className="w-4 h-4 animate-pulse" />
              <span>AI-Powered Web Scraping</span>
            </div>
            
            <h1 className="text-5xl md:text-7xl font-bold text-foreground mb-6 leading-tight animate-fade-in-up">
              Convert Any Website to an
              <span className="bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 bg-clip-text text-transparent animate-gradient-x"> API</span>
            </h1>
            
            <p className="text-xl text-muted-foreground mb-16 max-w-3xl mx-auto leading-relaxed animate-fade-in-up animation-delay-200">
              Describe what data you want to extract, and our AI will create a custom API for you. 
              No coding required. Just tell us what you need.
            </p>


          </div>

          {/* Create Request Form */}
          <div className="max-w-2xl mx-auto animate-fade-in-up animation-delay-400">
            <div className="relative group">
              <div className="absolute -inset-1 bg-gradient-to-r from-blue-600 to-purple-600 rounded-2xl blur-xl opacity-25 group-hover:opacity-40 transition duration-500"></div>
              <div className="relative card shadow-2xl border-0 bg-white/90 backdrop-blur-md dark:bg-slate-800/90 rounded-2xl overflow-hidden">
              <div className="card-header text-center py-8 border-b border-border/50">
                <h2 className="card-title text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">Create Your Scraping API</h2>
                <p className="card-description mt-2">Enter a website URL and describe what data you want to extract</p>
              </div>
              
              <div className="card-content p-8">
                <form onSubmit={handleCreateRequest} className="space-y-6">
                  <div>
                    <label htmlFor="url" className="block text-sm font-medium text-foreground mb-2">
                      Website URL
                    </label>
                    <input
                      type="url"
                      id="url"
                      value={url}
                      onChange={(e) => setUrl(e.target.value)}
                      placeholder="https://example.com"
                      className="input text-base transition-all duration-200 focus:ring-2 focus:ring-primary/20 hover:border-primary/50"
                      required
                    />
                  </div>

                  <div>
                    <label htmlFor="description" className="block text-sm font-medium text-foreground mb-2">
                      What data do you want to extract?
                    </label>
                    <textarea
                      id="description"
                      value={description}
                      onChange={(e) => setDescription(e.target.value)}
                      placeholder="e.g., Extract product names, prices, and ratings from this e-commerce site..."
                      rows={4}
                      className="textarea text-base transition-all duration-200 focus:ring-2 focus:ring-primary/20 hover:border-primary/50 resize-none"
                      required
                    />
                  </div>

                  {error && (
                    <div className="bg-destructive/10 border border-destructive/20 text-destructive rounded-lg p-4 text-sm">
                      {error}
                    </div>
                  )}

                  <button
                    type="submit"
                    disabled={isLoading}
                    className="w-full btn btn-primary btn-lg font-medium bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 transition-all duration-300 shadow-lg hover:shadow-xl hover:-translate-y-0.5"
                  >
                    {isLoading ? (
                      <>
                        <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                        <span>Creating API...</span>
                      </>
                    ) : (
                      <>
                        <span>Create API</span>
                        <ArrowRight className="w-5 h-5" />
                      </>
                    )}
                  </button>
                </form>
              </div>
            </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-24 bg-background">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-foreground mb-4">Everything you need to build powerful APIs</h2>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              From simple data extraction to complex web scraping, we&apos;ve got you covered
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <div className="card p-8 text-center hover:shadow-lg transition-shadow">
              <div className="w-16 h-16 bg-blue-100 dark:bg-blue-900/20 rounded-2xl flex items-center justify-center mx-auto mb-6">
                <Globe className="w-8 h-8 text-blue-600" />
              </div>
              <h3 className="text-xl font-semibold text-foreground mb-3">Smart Web Scraping</h3>
              <p className="text-muted-foreground">
                Extract data from any website with natural language descriptions. Our AI understands context and adapts to different site structures.
              </p>
            </div>

            <div className="card p-8 text-center hover:shadow-lg transition-shadow">
              <div className="w-16 h-16 bg-green-100 dark:bg-green-900/20 rounded-2xl flex items-center justify-center mx-auto mb-6">
                <Code className="w-8 h-8 text-green-600" />
              </div>
              <h3 className="text-xl font-semibold text-foreground mb-3">Instant API Generation</h3>
              <p className="text-muted-foreground">
                Automatically generate REST APIs from your scraping requirements. Get JSON endpoints ready for production use.
              </p>
            </div>

            <div className="card p-8 text-center hover:shadow-lg transition-shadow">
              <div className="w-16 h-16 bg-purple-100 dark:bg-purple-900/20 rounded-2xl flex items-center justify-center mx-auto mb-6">
                <TestTube className="w-8 h-8 text-purple-600" />
              </div>
              <h3 className="text-xl font-semibold text-foreground mb-3">Test & Iterate</h3>
              <p className="text-muted-foreground">
                Test your APIs and refine them through natural language chat. Get instant feedback and make adjustments on the fly.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-16 bg-primary">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl font-bold text-white mb-4">Ready to get started?</h2>
          <p className="text-xl text-blue-100 mb-8">
            Join thousands of developers who are already using Scrapply to build powerful APIs
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              href="/dashboard"
              className="btn btn-secondary btn-lg"
            >
              <BarChart3 className="w-5 h-5 mr-2" />
              View All APIs
            </Link>
            <Link
              href="/settings"
              className="btn btn-outline btn-lg text-white border-white hover:bg-white hover:text-primary"
            >
              Settings
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
