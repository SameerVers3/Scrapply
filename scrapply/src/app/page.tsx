'use client';

import { useState } from 'react';
import { ArrowRight, Globe, Zap, Code, TestTube, Sparkles, CheckCircle, Clock, Users, BarChart3 } from 'lucide-react';
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
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24">
          <div className="text-center">
            <div className="inline-flex items-center space-x-2 bg-primary/10 text-primary px-4 py-2 rounded-full text-sm font-medium mb-8">
              <Sparkles className="w-4 h-4" />
              <span>AI-Powered Web Scraping</span>
            </div>
            
            <h1 className="text-5xl md:text-6xl font-bold text-foreground mb-6 leading-tight">
              Convert Any Website to an
              <span className="bg-gradient-to-r from-primary to-purple-600 bg-clip-text text-transparent"> API</span>
            </h1>
            
            <p className="text-xl text-muted-foreground mb-12 max-w-3xl mx-auto leading-relaxed">
              Describe what data you want to extract, and our AI will create a custom API for you. 
              No coding required. Just tell us what you need.
            </p>

            {/* Stats */}
            <div className="flex justify-center items-center space-x-8 mb-16 text-sm text-muted-foreground">
              <div className="flex items-center space-x-2">
                <CheckCircle className="w-4 h-4 text-green-500" />
                <span>99.9% Success Rate</span>
              </div>
              <div className="flex items-center space-x-2">
                <Clock className="w-4 h-4 text-blue-500" />
                <span>1-2 Minute Setup</span>
              </div>
              <div className="flex items-center space-x-2">
                <Users className="w-4 h-4 text-purple-500" />
                <span>Trusted by 10K+ Users</span>
              </div>
            </div>
          </div>

          {/* Create Request Form */}
          <div className="max-w-2xl mx-auto">
            <div className="card shadow-xl border-0 bg-white/80 backdrop-blur-sm dark:bg-slate-800/80">
              <div className="card-header text-center">
                <h2 className="card-title">Create Your Scraping API</h2>
                <p className="card-description">Enter a website URL and describe what data you want to extract</p>
              </div>
              
              <div className="card-content">
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
                      className="input text-base"
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
                      className="textarea text-base"
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
                    className="w-full btn btn-primary btn-lg font-medium"
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
      </section>

      {/* Features Section */}
      <section className="py-24 bg-background">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-foreground mb-4">Everything you need to build powerful APIs</h2>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              From simple data extraction to complex web scraping, we've got you covered
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
