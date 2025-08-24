'use client';

import { useState, useEffect } from 'react';
import { listJobs, JobResponse } from '@/lib/api';
import { Clock, CheckCircle, XCircle, Play, TestTube, Trash2, RotateCcw, RefreshCw, Plus, BarChart3, Zap } from 'lucide-react';
import Link from 'next/link';
import ProgressBar from '@/components/ProgressBar';

export default function DashboardPage() {
  const [jobs, setJobs] = useState<JobResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState('');

  const fetchJobs = async (showRefreshing = false) => {
    try {
      if (showRefreshing) {
        setIsRefreshing(true);
      } else {
        setIsLoading(true);
      }
      const jobList = await listJobs(50, 0);
      setJobs(jobList.jobs);
      setError('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load jobs');
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    fetchJobs();
  }, []);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pending':
      case 'analyzing':
      case 'generating':
      case 'testing':
        return <Clock className="h-5 w-5 text-yellow-500" />;
      case 'ready':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'failed':
        return <XCircle className="h-5 w-5 text-red-500" />;
      default:
        return <Clock className="h-5 w-5 text-muted-foreground" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending':
      case 'analyzing':
      case 'generating':
      case 'testing':
        return 'text-yellow-700 bg-yellow-100 dark:text-yellow-300 dark:bg-yellow-900/20';
      case 'ready':
        return 'text-green-700 bg-green-100 dark:text-green-300 dark:bg-green-900/20';
      case 'failed':
        return 'text-red-700 bg-red-100 dark:text-red-300 dark:bg-red-900/20';
      default:
        return 'text-muted-foreground bg-muted';
    }
  };

  const getStatusCounts = () => {
    const counts = {
      ready: 0,
      failed: 0,
      processing: 0,
    };
    
    jobs.forEach(job => {
      if (job.status === 'ready') counts.ready++;
      else if (job.status === 'failed') counts.failed++;
      else counts.processing++;
    });
    
    return counts;
  };

  const statusCounts = getStatusCounts();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-background">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading your APIs...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-foreground">Your APIs</h1>
              <p className="text-muted-foreground mt-2">Manage and monitor your scraping APIs</p>
            </div>
            <div className="flex items-center space-x-3">
              <button
                onClick={() => fetchJobs(true)}
                disabled={isRefreshing}
                className="btn btn-outline btn-sm"
              >
                <RefreshCw className={`w-4 h-4 mr-2 ${isRefreshing ? 'animate-spin' : ''}`} />
                Refresh
              </button>
              <Link
                href="/"
                className="btn btn-primary btn-sm"
              >
                <Plus className="w-4 h-4 mr-2" />
                Create New API
              </Link>
            </div>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="card p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Ready APIs</p>
                <p className="text-2xl font-bold text-foreground">{statusCounts.ready}</p>
              </div>
              <div className="w-12 h-12 bg-green-100 dark:bg-green-900/20 rounded-lg flex items-center justify-center">
                <CheckCircle className="w-6 h-6 text-green-600" />
              </div>
            </div>
          </div>
          
          <div className="card p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Processing</p>
                <p className="text-2xl font-bold text-foreground">{statusCounts.processing}</p>
              </div>
              <div className="w-12 h-12 bg-yellow-100 dark:bg-yellow-900/20 rounded-lg flex items-center justify-center">
                <Clock className="w-6 h-6 text-yellow-600" />
              </div>
            </div>
          </div>
          
          <div className="card p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Failed</p>
                <p className="text-2xl font-bold text-foreground">{statusCounts.failed}</p>
              </div>
              <div className="w-12 h-12 bg-red-100 dark:bg-red-900/20 rounded-lg flex items-center justify-center">
                <XCircle className="w-6 h-6 text-red-600" />
              </div>
            </div>
          </div>
        </div>

        {error && (
          <div className="bg-destructive/10 border border-destructive/20 text-destructive rounded-lg p-4 mb-6">
            <p>Error loading APIs: {error}</p>
            <button
              onClick={() => fetchJobs()}
              className="mt-2 text-sm underline hover:no-underline"
            >
              Try again
            </button>
          </div>
        )}

        {jobs.length === 0 ? (
          <div className="text-center py-16">
            <div className="w-24 h-24 bg-muted rounded-full flex items-center justify-center mx-auto mb-6">
              <BarChart3 className="w-12 h-12 text-muted-foreground" />
            </div>
            <h3 className="text-xl font-semibold text-foreground mb-2">No APIs yet</h3>
            <p className="text-muted-foreground mb-6">Create your first scraping API to get started</p>
            <Link
              href="/"
              className="btn btn-primary btn-lg"
            >
              <Zap className="w-5 h-5 mr-2" />
              Create Your First API
            </Link>
          </div>
        ) : (
          <div className="grid gap-6">
            {jobs.map((job) => (
              <div key={job.id} className="card hover:shadow-lg transition-shadow">
                <div className="p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center space-x-3 flex-1 min-w-0">
                      {getStatusIcon(job.status)}
                      <div className="flex-1 min-w-0">
                        <h3 className="text-lg font-medium text-foreground truncate">
                          {job.url}
                        </h3>
                        <p className="text-sm text-muted-foreground mt-1">{job.description}</p>
                      </div>
                    </div>
                    <span className={`badge ${getStatusColor(job.status)}`}>
                      {job.status}
                    </span>
                  </div>

                  <div className="mb-4">
                    <div className="flex items-center justify-between text-sm text-muted-foreground mb-2">
                      <span>Progress</span>
                      <span>{job.progress}%</span>
                    </div>
                    <ProgressBar progress={job.progress} />
                  </div>

                  {job.message && (
                    <div className="mb-4 text-sm text-muted-foreground bg-muted p-3 rounded-md">
                      {job.message}
                    </div>
                  )}

                  {job.api_endpoint_path && (
                    <div className="mb-4">
                      <p className="text-sm font-medium text-foreground mb-2">API Endpoint:</p>
                      <code className="text-xs bg-muted p-3 rounded block break-all font-mono">
                        {job.api_endpoint_path}
                      </code>
                    </div>
                  )}

                  <div className="flex items-center justify-between">
                    <div className="text-xs text-muted-foreground">
                      Created: {new Date(job.created_at).toLocaleDateString()}
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      {job.status === 'ready' && (
                        <Link
                          href={`/chatbot?jobId=${job.id}`}
                          className="btn btn-primary btn-sm"
                        >
                          <Play className="h-4 w-4 mr-1" />
                          Open
                        </Link>
                      )}
                      
                      {job.status === 'failed' && (
                        <button className="btn btn-outline btn-sm">
                          <RotateCcw className="h-4 w-4 mr-1" />
                          Retry
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
