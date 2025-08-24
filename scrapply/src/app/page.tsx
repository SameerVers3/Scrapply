'use client';

import { useState } from 'react';
import { ArrowRight, Globe, Code, TestTube, Sparkles, CheckCircle, Clock, Users, BarChart3 } from 'lucide-react';
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
      <section className="relative overflow-hidden bg-gradient-to-br from-indigo-50 via-white to-cyan-50 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900">
        {/* Animated background elements */}
        <div className="absolute inset-0">
          <div className="absolute top-20 left-10 w-72 h-72 bg-purple-300 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob"></div>
          <div className="absolute top-40 right-10 w-72 h-72 bg-yellow-300 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob animation-delay-2000"></div>
          <div className="absolute -bottom-8 left-20 w-72 h-72 bg-pink-300 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob animation-delay-4000"></div>
        </div>
        
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-32">
          <div className="text-center">
            <div className="inline-flex items-center space-x-2 bg-gradient-to-r from-primary/20 to-purple-500/20 text-primary px-6 py-3 rounded-full text-sm font-semibold mb-10 shadow-lg backdrop-blur-sm border border-primary/20">
              <Sparkles className="w-5 h-5 animate-pulse" />
              <span>AI-Powered Web Scraping</span>
            </div>
            
            <h1 className="text-6xl md:text-7xl font-bold text-foreground mb-8 leading-tight">
              Convert Any Website to an
              <span className="bg-gradient-to-r from-primary via-purple-600 to-cyan-600 bg-clip-text text-transparent animate-gradient"> API</span>
            </h1>
            
            <p className="text-xl md:text-2xl text-muted-foreground mb-16 max-w-4xl mx-auto leading-relaxed font-medium">
              Describe what data you want to extract, and our AI will create a custom API for you. 
              <span className="text-foreground font-semibold"> No coding required.</span> Just tell us what you need.
            </p>


          </div>

          {/* Create Request Form */}
          <div className="max-w-3xl mx-auto">
            <div className="card shadow-2xl border-0 bg-white/90 backdrop-blur-xl dark:bg-slate-800/90 rounded-2xl overflow-hidden">
              <div className="card-header text-center p-8 bg-gradient-to-r from-primary/5 to-purple-500/5">
                <h2 className="card-title text-2xl font-bold text-foreground mb-3">Create Your Scraping API</h2>
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
                      className="input text-base w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all duration-200 bg-white/50 backdrop-blur-sm"
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
                      className="textarea text-base w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all duration-200 bg-white/50 backdrop-blur-sm resize-none"
                      required
                    />
                  </div>

                  {error && (
                    <div className="bg-red-50 border-2 border-red-200 text-red-700 rounded-xl p-4 text-sm font-medium">
                      {error}
                    </div>
                  )}

                  <button
                    type="submit"
                    disabled={isLoading}
                    className="w-full bg-gradient-to-r from-primary to-purple-600 hover:from-primary/90 hover:to-purple-600/90 text-white font-semibold py-4 px-6 rounded-xl shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
                  >
                    {isLoading ? (
                      <div className="flex items-center justify-center space-x-3">
                        <div className="w-6 h-6 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                        <span className="text-lg">Creating API...</span>
                      </div>
                    ) : (
                      <div className="flex items-center justify-center space-x-3">
                        <span className="text-lg">Create API</span>
                        <ArrowRight className="w-6 h-6" />
                      </div>
                    )}
                  </button>
                </form>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-32 bg-gradient-to-b from-background to-gray-50 dark:to-slate-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-20">
            <h2 className="text-4xl md:text-5xl font-bold text-foreground mb-6">Everything you need to build powerful APIs</h2>
            <p className="text-xl text-muted-foreground max-w-3xl mx-auto leading-relaxed">
              From simple data extraction to complex web scraping, we&apos;ve got you covered with cutting-edge AI technology
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-10">
            <div className="group relative">
              <div className="absolute inset-0 bg-gradient-to-r from-blue-500/10 to-purple-500/10 rounded-3xl blur-xl opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
              <div className="relative card p-10 text-center hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-2 bg-white/80 backdrop-blur-sm border-0 rounded-3xl">
                <div className="w-20 h-20 bg-gradient-to-br from-blue-500 to-blue-600 rounded-3xl flex items-center justify-center mx-auto mb-8 shadow-lg">
                  <Globe className="w-10 h-10 text-white" />
                </div>
                <h3 className="text-2xl font-bold text-foreground mb-4">Smart Web Scraping</h3>
                <p className="text-muted-foreground leading-relaxed">
                  Extract data from any website with natural language descriptions. Our AI understands context and adapts to different site structures.
                </p>
              </div>
            </div>

            <div className="group relative">
              <div className="absolute inset-0 bg-gradient-to-r from-green-500/10 to-teal-500/10 rounded-3xl blur-xl opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
              <div className="relative card p-10 text-center hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-2 bg-white/80 backdrop-blur-sm border-0 rounded-3xl">
                <div className="w-20 h-20 bg-gradient-to-br from-green-500 to-green-600 rounded-3xl flex items-center justify-center mx-auto mb-8 shadow-lg">
                  <Code className="w-10 h-10 text-white" />
                </div>
                <h3 className="text-2xl font-bold text-foreground mb-4">Instant API Generation</h3>
                <p className="text-muted-foreground leading-relaxed">
                  Automatically generate REST APIs from your scraping requirements. Get JSON endpoints ready for production use.
                </p>
              </div>
            </div>

            <div className="group relative">
              <div className="absolute inset-0 bg-gradient-to-r from-purple-500/10 to-pink-500/10 rounded-3xl blur-xl opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
              <div className="relative card p-10 text-center hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-2 bg-white/80 backdrop-blur-sm border-0 rounded-3xl">
                <div className="w-20 h-20 bg-gradient-to-br from-purple-500 to-purple-600 rounded-3xl flex items-center justify-center mx-auto mb-8 shadow-lg">
                  <TestTube className="w-10 h-10 text-white" />
                </div>
                <h3 className="text-2xl font-bold text-foreground mb-4">Test & Iterate</h3>
                <p className="text-muted-foreground leading-relaxed">
                  Test your APIs and refine them through natural language chat. Get instant feedback and make adjustments on the fly.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 bg-gradient-to-r from-primary via-purple-600 to-cyan-600 relative overflow-hidden">
        <div className="absolute inset-0 bg-black/10"></div>
        <div className="absolute inset-0">
          <div className="absolute top-10 left-10 w-32 h-32 bg-white/10 rounded-full blur-2xl"></div>
          <div className="absolute bottom-10 right-10 w-40 h-40 bg-white/10 rounded-full blur-2xl"></div>
        </div>
        <div className="relative max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">Ready to get started?</h2>
          <p className="text-xl md:text-2xl text-blue-100 mb-12 leading-relaxed">
            Join thousands of developers who are already using Scrapply to build powerful APIs
          </p>
          <div className="flex flex-col sm:flex-row gap-6 justify-center">
            <Link
              href="/dashboard"
              className="inline-flex items-center justify-center px-8 py-4 bg-white text-primary font-semibold rounded-xl shadow-lg hover:shadow-xl transform hover:-translate-y-1 transition-all duration-200"
            >
              <BarChart3 className="w-6 h-6 mr-3" />
              <span className="text-lg">View All APIs</span>
            </Link>
            <Link
              href="/settings"
              className="inline-flex items-center justify-center px-8 py-4 border-2 border-white text-white font-semibold rounded-xl hover:bg-white hover:text-primary transition-all duration-200"
            >
              <span className="text-lg">Settings</span>
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
