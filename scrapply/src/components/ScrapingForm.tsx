'use client';

import { useState } from 'react';
import { createScrapingRequest, ScrapingRequest } from '@/lib/api';
import { ArrowRight, Globe, Sparkles } from 'lucide-react';

interface ScrapingFormProps {
  onJobCreated: (jobId: string) => void;
}

export default function ScrapingForm({ onJobCreated }: ScrapingFormProps) {
  const [url, setUrl] = useState('');
  const [description, setDescription] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
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
      onJobCreated(job.id);
      
      // Reset form
      setUrl('');
      setDescription('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create scraping request');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="card shadow-lg">
      <div className="card-header">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
            <Globe className="w-5 h-5 text-primary" />
          </div>
          <div>
            <h2 className="card-title">Create Scraping Request</h2>
            <p className="card-description">Extract data from any website with AI</p>
          </div>
        </div>
      </div>
      
      <div className="card-content">
        <form onSubmit={handleSubmit} className="space-y-6">
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
              className="input"
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
              placeholder="Describe what data you want to extract from this website..."
              rows={3}
              className="textarea"
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
                <span>Creating...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-5 h-5 mr-2" />
                <span>Create Scraping Job</span>
                <ArrowRight className="w-5 h-5 ml-2" />
              </>
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
